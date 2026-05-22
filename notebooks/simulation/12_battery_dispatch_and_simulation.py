# ============================================================
# Energy Copilot Platform – Battery Dispatch & Simulation
# Notebook : 12_battery_dispatch_and_simulation.py
# Layer    : Gold (Battery Strategy)
# Page     : 9 — Battery Dispatch Strategies & Financial Simulation
# Updated  : 2026-05-08
# ============================================================
#
# PURPOSE
# -------
# Processes raw battery + solar + energy data into three gold tables
# for Page 9 Power BI report:
#
#   gold_battery_dispatch       (daily dispatch: SoC, charge/discharge, savings)
#   gold_battery_simulation     (scenario comparison: NPV, IRR, payback per building)
#   gold_battery_daily_summary  (best-strategy aggregate + cumulative KPIs)
#
# INPUTS (attached Lakehouse)
# ---------------------------
#   bronze_battery_status       (15-min SoC, charge/discharge power readings)
#   bronze_solar_generation     (15-min PV generation + export)
#   bronze_energy_readings      (15-min building consumption)
#   silver_building_master      (building metadata: country, battery config, PV capacity)
#   gold_battery_technologies   (reference: battery specs, EU 2023/1670 compliance)
#
# BUILDINGS IN SCOPE
# ------------------
#   B001 – Berlin, 200 kWh LFP (CATL), Self-Consumption strategy, 120 kWp PV
#   B003 – Hamburg, 800 kWh LFP (Fluence), Peak-Shaving strategy, 500 kWp PV
#   B005 – Frankfurt, 400 kWh NMC (Samsung), Backup strategy, 200 kWp PV
#   B004 – Vienna, no battery (scenario simulation only), 80 kWp PV
#   B006 – Amsterdam, no battery (scenario simulation only), 150 kWp PV
#   B002 – Istanbul: excluded (no PV, no battery)
#
# STRATEGY DEFINITIONS
# --------------------
#   self_consumption : Charge from PV surplus, discharge evening peak
#   peak_shaving     : Charge overnight (off-peak grid), discharge demand peak
#   tou              : Buy cheap hours, discharge expensive hours (price arbitrage)
#   backup           : Maintain high SoC reserve, opportunistic discharge only
#
# PRICING (country-specific, 2026 market rates)
# -----------------------------------------------
#   DE: off-peak €0.062, mid €0.182, peak €0.285, demand €13.50/kW/month
#   AT: off-peak €0.055, mid €0.165, peak €0.248, demand €11.20/kW/month
#   NL: off-peak €0.071, mid €0.195, peak €0.302, demand €14.80/kW/month
#
# EU BATTERY REGULATION (2023/1670)
# ----------------------------------
#   All scenarios include only EU-compliant batteries (LFP) as recommended options.
#   B005's existing NMC battery is flagged as non-compliant in simulation output.
#   Replacement recommendation: CATL LFP 400 kWh at next maintenance cycle.
#
# BMAD PHASE : B2-A3-D4-L4 (Business logic + financial model)
# DP-600 HINTS: Delta MERGE upsert pattern, broadcast joins on small dims,
#               AQE enabled, vectorised window functions for cumulative metrics
# ============================================================

# ── 0. IMPORTS & SPARK CONFIGURATION ────────────────────────────────────────

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, BooleanType, DateType, LongType, IntegerType
)
from delta.tables import DeltaTable
import math

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "16")

# ── FABRIC LAKEHOUSE TABLE HELPER ─────────────────────────────────────────────
# In Microsoft Fabric, Lakehouse Delta tables are accessed by name, NOT by path.
#   READ  → spark.read.table("table_name")
#   WRITE → df.write.format("delta").mode("overwrite").saveAsTable("table_name")
#   MERGE → DeltaTable.forName(spark, "table_name")
#
# Files in the Files section (CSV, Parquet) are accessed via:
#   spark.read.format("csv").load("Files/sample-data/filename.csv")

def table_exists(name: str) -> bool:
    """Check if a table is registered in the attached Lakehouse."""
    return spark.catalog.tableExists(name)

def read_table_or_csv(table_name: str, csv_path: str, **csv_opts):
    """
    Try to read a registered Lakehouse Delta table.
    If not found, fall back to reading a CSV from the Files section.
    This makes Notebook 12 self-contained — it does NOT require
    Notebooks 01/02 to have run first for battery/solar data.
    """
    if table_exists(table_name):
        print(f"  Reading table: {table_name}")
        return spark.read.table(table_name)
    else:
        print(f"  Table '{table_name}' not found — reading CSV: {csv_path}")
        return (
            spark.read
            .format("csv")
            .option("header", "true")
            .option("inferSchema", "true")
            .options(**csv_opts)
            .load(csv_path)
        )

# ── 1. LOAD SOURCE TABLES ─────────────────────────────────────────────────────
# FILES PATH: Upload the following CSVs to your Lakehouse → Files → sample-data/
#   raw_battery_status.csv
#   raw_solar_generation.csv
#   raw_energy_readings.csv
#   building_master.csv
#   gold_battery_technologies.csv
# These files are in your local repo: sample-data/

print("[1/6] Loading source tables...")

# Battery readings — bronze table OR raw CSV
df_battery_raw = read_table_or_csv(
    "bronze_battery_status",
    "Files/sample-data/raw_battery_status.csv"
)

# Solar generation — bronze table OR raw CSV
df_solar_raw = read_table_or_csv(
    "bronze_solar_generation",
    "Files/sample-data/raw_solar_generation.csv"
)

# Energy readings — bronze table OR raw CSV
df_energy_raw = read_table_or_csv(
    "bronze_energy_readings",
    "Files/sample-data/raw_energy_readings.csv"
)

# Building master — silver table OR CSV
df_building = read_table_or_csv(
    "silver_building_master",
    "Files/sample-data/building_master.csv"
)

# Battery technologies reference — inline data (EU 2023/1670 verified 2026-05-08)
# Hardcoded so the notebook is self-contained; no CSV upload required.
# If a registered table already exists it will be used instead.
if table_exists("gold_battery_technologies"):
    df_battery_tech = spark.read.table("gold_battery_technologies")
    print("  Reading table: gold_battery_technologies")
else:
    print("  Building gold_battery_technologies from inline reference data...")
    from pyspark.sql.types import (
        StructType, StructField, StringType, DoubleType, IntegerType, BooleanType
    )
    batt_tech_schema = StructType([
        StructField("battery_id",                    StringType(),  True),
        StructField("manufacturer",                  StringType(),  True),
        StructField("battery_type",                  StringType(),  True),
        StructField("capacity_kwh",                  DoubleType(),  True),
        StructField("battery_power_kw",              DoubleType(),  True),
        StructField("cost_eur_per_kwh",              DoubleType(),  True),
        StructField("expected_lifespan_years",       IntegerType(), True),
        StructField("design_cycles",                 IntegerType(), True),
        StructField("round_trip_efficiency_percent", DoubleType(),  True),
        StructField("degradation_rate_pct_per_1000_cycles", DoubleType(), True),
        StructField("carbon_footprint_kg_co2_per_kwh", DoubleType(), True),
        StructField("recycled_content_percent",      DoubleType(),  True),
        StructField("warranty_cycles",               IntegerType(), True),
        StructField("eu_compliant",                  BooleanType(), True),
        StructField("regions_approved",              StringType(),  True),
        StructField("suitable_strategies",           StringType(),  True),
    ])
    # fmt: off  (battery_id, mfr, type, cap_kwh, pwr_kw, €/kwh, life_yr, cycles,
    #            rte_%, degrad_%/1000c, co2_kg/kwh, recycled_%, warranty_c, eu_ok,
    #            regions, strategies)
    batt_tech_rows = [
        ("CATL_LFP_100",    "CATL",         "LFP", 100.0, 50.0,  140.0, 12, 6000, 94.5, 1.8, 45.0, 12.0, 6000, True,  "DE,AT,NL,FR,EU_avg", "self_consumption,peak_shaving,tou"),
        ("CATL_LFP_200",    "CATL",         "LFP", 200.0, 100.0, 138.0, 12, 6000, 94.5, 1.8, 45.0, 12.0, 6000, True,  "DE,AT,NL,FR,EU_avg", "self_consumption,peak_shaving,tou"),
        ("CATL_LFP_400",    "CATL",         "LFP", 400.0, 200.0, 135.0, 12, 5800, 94.0, 1.9, 46.0, 12.0, 5800, True,  "DE,AT,NL,FR,EU_avg", "peak_shaving,tou"),
        ("BYD_LFP_100",     "BYD",          "LFP", 100.0, 50.0,  135.0, 12, 5000, 93.0, 2.0, 48.0, 10.0, 5000, True,  "DE,EU_avg",           "self_consumption,peak_shaving"),
        ("BYD_LFP_200",     "BYD",          "LFP", 200.0, 100.0, 133.0, 12, 5000, 93.0, 2.0, 48.0, 10.0, 5000, True,  "DE,EU_avg",           "self_consumption,peak_shaving"),
        ("FLUENCE_LFP_800", "Fluence",      "LFP", 800.0, 400.0, 130.0, 15, 7000, 95.0, 1.5, 42.0, 15.0, 7000, True,  "DE,AT,NL,FR,EU_avg", "peak_shaving,tou"),
        ("SUNGROW_LFP_150", "Sungrow",      "LFP", 150.0, 75.0,  132.0, 12, 5500, 93.5, 2.0, 47.0, 11.0, 5500, True,  "DE,AT,NL,EU_avg",    "self_consumption,tou"),
        ("TESLA_NCA_100",   "Tesla",        "NCA", 100.0, 50.0,  155.0,  9, 4000, 91.0, 3.0, 60.0, 12.0, 4000, True,  "DE",                  "self_consumption,backup"),
        ("SAMSUNG_NMC_400", "Samsung SDI",  "NMC", 400.0, 180.0, 125.0,  8, 3000, 90.0, 3.5, 68.0,  8.0, 3000, False, "TR,EU_avg",           "backup,self_consumption"),
        ("PANASONIC_NCA_75","Panasonic",    "NCA",  75.0, 35.0,  145.0,  8, 3000, 90.0, 3.5, 65.0,  8.0, 3000, False, "EU_avg",              "backup"),
    ]
    # fmt: on
    df_battery_tech = spark.createDataFrame(batt_tech_rows, schema=batt_tech_schema)
    # Persist as a Lakehouse table for future runs
    df_battery_tech.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_technologies")
    print("  gold_battery_technologies registered as Lakehouse table.")

# building_master.csv uses country_code column
if "country_code" not in df_building.columns and "country" in df_building.columns:
    df_building = df_building.withColumnRenamed("country", "country_code")

# Buildings in scope for Page 9 (solar + battery systems)
# 2026-05-21: B007 (Copenhagen Net-Plus HQ, 450 kWh LFP + 380 kWp PV + GSHP) eklendi
SCOPE_BUILDINGS = ["B001", "B003", "B004", "B005", "B006", "B007"]
df_building_p9 = df_building.filter(F.col("building_id").isin(SCOPE_BUILDINGS))

print(f"  Battery raw readings:    {df_battery_raw.count():,}")
print(f"  Solar raw readings:      {df_solar_raw.count():,}")
print(f"  Energy raw readings:     {df_energy_raw.count():,}")
print(f"  Buildings in scope:      {df_building_p9.count()}")

# ── 2. DAILY AGGREGATION ──────────────────────────────────────────────────────

print("[2/6] Aggregating raw data to daily granularity...")

# Battery daily: avg SoC, total charge/discharge
df_battery_daily = (
    df_battery_raw
    .filter(F.col("building_id").isin(SCOPE_BUILDINGS))
    .withColumn("date", F.to_date("timestamp_utc"))
    .groupBy("building_id", "date")
    .agg(
        F.first("battery_id").alias("battery_id"),
        F.avg("soc_raw").alias("avg_soc_raw"),
        F.first("soc_raw").alias("soc_start_raw"),
        F.last("soc_raw").alias("soc_end_raw"),
        F.sum(
            F.when(F.col("charge_power_raw") > 0, F.col("charge_power_raw") * (15.0/60.0))
            .otherwise(0)
        ).alias("charge_kwh_raw"),
        F.sum(
            F.when(F.col("discharge_power_raw") > 0, F.col("discharge_power_raw") * (15.0/60.0))
            .otherwise(0)
        ).alias("discharge_kwh_raw"),
        F.count("*").alias("readings_count"),
    )
)

# Solar daily: total generation and export
df_solar_daily = (
    df_solar_raw
    .filter(F.col("building_id").isin(SCOPE_BUILDINGS))
    .withColumn("date", F.to_date("timestamp_utc"))
    .groupBy("building_id", "date")
    .agg(
        F.first("inverter_id").alias("inverter_id"),
        F.sum("generated_raw").alias("pv_generation_kwh"),
        F.sum("exported_raw").alias("pv_export_kwh"),
    )
)

# Energy daily: total building consumption
df_energy_daily = (
    df_energy_raw
    .filter(F.col("building_id").isin(SCOPE_BUILDINGS))
    .withColumn("date", F.to_date("timestamp_utc"))
    .groupBy("building_id", "date")
    .agg(
        F.sum("raw_value").alias("consumption_kwh"),
    )
)

print(f"  Battery daily rows: {df_battery_daily.count():,}")
print(f"  Solar daily rows:   {df_solar_daily.count():,}")
print(f"  Energy daily rows:  {df_energy_daily.count():,}")

# ── 3. BUILD DISPATCH TABLE (gold_battery_dispatch) ───────────────────────────

print("[3/6] Computing dispatch metrics and financial KPIs...")

# Country-specific pricing lookup (broadcast join candidate)
pricing_data = [
    ("DE", 0.062, 0.182, 0.285, 13.50, 0.082, 380.0),
    ("AT", 0.055, 0.165, 0.248, 11.20, 0.075, 210.0),
    ("NL", 0.071, 0.195, 0.302, 14.80, 0.095, 320.0),
    ("TR", 0.040, 0.085, 0.120,  8.50, 0.045, 450.0),
]
pricing_schema = StructType([
    StructField("country", StringType()),
    StructField("offpeak_eur_kwh", DoubleType()),
    StructField("midpeak_eur_kwh", DoubleType()),
    StructField("peak_eur_kwh", DoubleType()),
    StructField("demand_eur_kw_month", DoubleType()),
    StructField("feed_in_eur_kwh", DoubleType()),
    StructField("co2_g_kwh", DoubleType()),
])
df_pricing = spark.createDataFrame(pricing_data, schema=pricing_schema)

# Building config: join battery metadata + pricing
df_bldg_config = (
    df_building_p9.select(
        "building_id", "building_name", "country_code",
        "has_battery", "battery_capacity_kwh", "battery_technology",
        "battery_strategy", "pv_capacity_kwp",
    )
    .join(F.broadcast(df_pricing), df_building_p9["country_code"] == df_pricing["country"], "left")
)

# Join daily aggregates
df_joined = (
    df_solar_daily
    .join(df_battery_daily, ["building_id", "date"], "left")
    .join(df_energy_daily,  ["building_id", "date"], "left")
    .join(df_bldg_config,   "building_id", "left")
)

# Compute dispatch KPIs
# --- Round-trip efficiency per battery type ---
# LFP: 94.5%, NMC: 90.5% (standard datasheet values)
df_dispatch = (
    df_joined
    .withColumn("battery_type_clean",
        F.when(F.col("battery_technology").isin("LFP"), "LFP")
         .when(F.col("battery_technology").isin("NMC", "NCA"), F.col("battery_technology"))
         .otherwise("LFP")
    )
    .withColumn("round_trip_efficiency",
        F.when(F.col("battery_type_clean") == "LFP",  0.945)
         .when(F.col("battery_type_clean") == "NMC",  0.905)
         .when(F.col("battery_type_clean") == "NCA",  0.910)
         .otherwise(0.930)
    )
    # Normalize SoC to 0-1 range (input is already %)
    .withColumn("soc_start_pct", F.coalesce(F.col("soc_start_raw"), F.lit(20.0)))
    .withColumn("soc_end_pct",   F.coalesce(F.col("soc_end_raw"),   F.lit(20.0)))
    # Charge/discharge with safety bounds
    .withColumn("charge_kwh",    F.greatest(F.lit(0.0), F.coalesce(F.col("charge_kwh_raw"),    F.lit(0.0))))
    .withColumn("discharge_kwh", F.greatest(F.lit(0.0), F.coalesce(F.col("discharge_kwh_raw"), F.lit(0.0))))
    # PV to load (direct consumption without storage)
    .withColumn("pv_to_load_kwh",
        F.least(
            F.coalesce(F.col("pv_generation_kwh"), F.lit(0.0)),
            F.coalesce(F.col("consumption_kwh"), F.lit(0.0))
        )
    )
    # Grid charge = total charge - PV charge (estimated)
    .withColumn("pv_charge_kwh",
        F.greatest(F.lit(0.0),
            F.coalesce(F.col("pv_generation_kwh"), F.lit(0.0))
            - F.col("pv_to_load_kwh")
        )
    )
    .withColumn("grid_charge_kwh",
        F.greatest(F.lit(0.0), F.col("charge_kwh") - F.col("pv_charge_kwh"))
    )
    # Cycle depth: discharge / capacity
    .withColumn("cycle_depth_pct",
        F.when(
            (F.col("battery_capacity_kwh").isNotNull()) & (F.col("battery_capacity_kwh") > 0),
            F.col("discharge_kwh") / F.col("battery_capacity_kwh") * 100.0
        ).otherwise(0.0)
    )
    # Financial KPIs
    .withColumn("cost_avoided_eur",
        F.col("discharge_kwh") * F.col("peak_eur_kwh")
    )
    .withColumn("grid_charge_cost_eur",
        F.col("grid_charge_kwh") * F.col("offpeak_eur_kwh")
    )
    # Peak-shaving demand charge reduction (daily share of monthly saving)
    .withColumn("demand_reduction_eur",
        F.when(
            F.col("battery_strategy") == "peak_shaving",
            (F.col("discharge_kwh") / F.greatest(F.lit(1.0), F.col("battery_capacity_kwh")))
            * F.col("battery_capacity_kwh") * 0.25  # 25% of capacity as peak demand reduction
            * F.col("demand_eur_kw_month") / 30.0
        ).otherwise(0.0)
    )
    .withColumn("net_savings_eur",
        F.col("cost_avoided_eur") + F.col("demand_reduction_eur") - F.col("grid_charge_cost_eur")
    )
    .withColumn("co2_avoided_kg",
        F.col("discharge_kwh") * F.col("co2_g_kwh") / 1000.0
    )
    # EU compliance flag from gold_battery_technologies (join below)
    .withColumn("is_simulated",
        F.when(F.col("has_battery") == True, False).otherwise(True)
    )
    # Select and rename final columns
    .select(
        F.col("date"),
        F.col("building_id"),
        F.col("building_name"),
        F.col("country_code").alias("country"),
        F.coalesce(F.col("battery_id"), F.concat(F.col("building_id"), F.lit("_BATT_SIM"))).alias("battery_id"),
        F.col("battery_technology").alias("battery_type"),
        F.col("battery_strategy").alias("strategy"),
        F.coalesce(F.col("battery_capacity_kwh"), F.lit(0.0)).alias("capacity_kwh"),
        F.coalesce(F.col("pv_capacity_kwp"), F.lit(0.0)).alias("pv_capacity_kwp"),
        F.coalesce(F.col("pv_generation_kwh"), F.lit(0.0)).alias("pv_generation_kwh"),
        F.col("pv_to_load_kwh"),
        F.col("pv_charge_kwh"),
        F.col("grid_charge_kwh"),
        F.col("charge_kwh"),
        F.col("discharge_kwh"),
        F.col("soc_start_pct"),
        F.col("soc_end_pct"),
        F.col("round_trip_efficiency"),
        F.col("cycle_depth_pct"),
        F.col("cost_avoided_eur"),
        F.col("grid_charge_cost_eur"),
        F.col("demand_reduction_eur"),
        F.col("net_savings_eur"),
        F.col("co2_avoided_kg"),
        F.col("peak_eur_kwh").alias("grid_price_peak_eur_kwh"),
        F.col("offpeak_eur_kwh").alias("grid_price_offpeak_eur_kwh"),
        F.col("co2_g_kwh").alias("grid_co2_intensity_g_kwh"),
        F.col("is_simulated"),
        F.current_timestamp().alias("processed_at"),
    )
    .filter(F.col("date").isNotNull())
)

# Annotate EU compliance from battery tech reference
df_eu_map = (
    df_battery_tech
    .select("battery_type", "eu_compliant")
    .distinct()
)
df_dispatch = df_dispatch.join(
    F.broadcast(df_eu_map), "battery_type", "left"
).withColumn("eu_compliant", F.coalesce(F.col("eu_compliant"), F.lit(False)))

print(f"  Dispatch rows computed: {df_dispatch.count():,}")

# ── 4. UPSERT → gold_battery_dispatch ────────────────────────────────────────

print("[4/6] Writing gold_battery_dispatch (Delta MERGE upsert)...")

DISPATCH_TABLE = "gold_battery_dispatch"
merge_keys = ["building_id", "date", "strategy"]

if table_exists(DISPATCH_TABLE):
    delta_table = DeltaTable.forName(spark, DISPATCH_TABLE)
    (
        delta_table.alias("target")
        .merge(
            df_dispatch.alias("source"),
            " AND ".join([f"target.{k} = source.{k}" for k in merge_keys])
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    print("  MERGE complete (upsert).")
else:
    df_dispatch.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(DISPATCH_TABLE)
    print("  Initial write complete — table registered in Lakehouse.")

# ── 5. SIMULATION SCENARIOS (gold_battery_simulation) ────────────────────────

print("[5/6] Computing financial simulation scenarios...")

# Financial parameters
DISCOUNT_RATE   = 0.05   # 5% — EU standard for energy investment NPV
INFLATION_RATE  = 0.03   # 3% — EU energy price inflation assumption
NPV_HORIZON_YR  = 10     # 10-year analysis window
INSTALL_OVERHEAD = 0.08  # 8% installation cost on top of hardware CAPEX

# Annualized savings from last 365 days of dispatch data
df_cutoff = df_dispatch.agg(F.max("date").alias("max_date")).collect()[0]["max_date"]
df_recent = df_dispatch.filter(
    F.col("date") >= F.date_sub(F.lit(df_cutoff), 365)
)

df_annual = (
    df_recent
    .groupBy("building_id", "strategy")
    .agg(
        F.count("date").alias("n_days"),
        F.sum("net_savings_eur").alias("sum_savings"),
        F.sum("co2_avoided_kg").alias("sum_co2"),
        F.avg("round_trip_efficiency").alias("avg_rte"),
        F.avg("soc_end_pct").alias("avg_soc"),
        F.max("cycle_depth_pct").alias("max_cycle_depth"),
        F.last("eu_compliant").alias("eu_compliant"),
        F.last("battery_type").alias("battery_type"),
        F.last("capacity_kwh").alias("capacity_kwh"),
    )
    .withColumn("annual_savings_eur",
        F.when(F.col("n_days") >= 30,
            F.col("sum_savings") / F.col("n_days") * 365
        ).otherwise(F.col("sum_savings") * (365.0 / F.greatest(F.col("n_days"), F.lit(1))))
    )
    .withColumn("annual_co2_kg",
        F.col("sum_co2") / F.col("n_days") * 365
    )
)

# Join building metadata for CAPEX
df_sim_base = (
    df_annual
    .join(
        df_building_p9.select(
            "building_id", "building_name", "country_code",
            "battery_capacity_kwh", "battery_technology", "pv_capacity_kwp",
        ),
        "building_id", "left"
    )
    .join(
        df_battery_tech.select(
            "battery_type", "cost_eur_per_kwh",
            "expected_lifespan_years", "battery_power_kw",
            # eu_compliant already present in df_annual — omit to avoid ambiguous reference
        ).withColumnRenamed("battery_type", "tech_type"),
        df_annual["battery_type"] == F.col("tech_type"), "left"
    )
)

# NPV and payback (using Spark UDF for multi-year calculation)
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType as DT

def compute_npv(annual_savings, total_capex, discount_rate=0.05, inflation=0.03, years=10, salvage_pct=0.20):
    """10-year NPV with inflation-adjusted cash flows and salvage value."""
    if annual_savings is None or total_capex is None or annual_savings <= 0:
        return -float(total_capex or 0)
    cash_flows = [-total_capex]
    for yr in range(1, years + 1):
        cf = annual_savings * ((1 + inflation) ** yr)
        if yr == years:
            cf += total_capex * salvage_pct
        cash_flows.append(cf)
    return sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))

def compute_irr(annual_savings, total_capex, inflation=0.03, years=10, salvage_pct=0.20):
    """Newton-Raphson IRR approximation."""
    if annual_savings is None or total_capex is None or annual_savings <= 0:
        return 0.0
    cash_flows = [-total_capex]
    for yr in range(1, years + 1):
        cf = annual_savings * ((1 + inflation) ** yr)
        if yr == years:
            cf += total_capex * salvage_pct
        cash_flows.append(cf)
    r = annual_savings / total_capex  # initial guess
    for _ in range(100):
        f  = sum(cf / ((1 + r) ** i) for i, cf in enumerate(cash_flows))
        df = sum(-i * cf / ((1 + r) ** (i + 1)) for i, cf in enumerate(cash_flows) if i > 0)
        if abs(df) < 1e-10:
            break
        r -= f / df
        r = max(-0.99, min(5.0, r))
    return r * 100.0

npv_udf = udf(lambda s, c: compute_npv(s, c) if s and c else None, DT())
irr_udf = udf(lambda s, c: compute_irr(s, c) if s and c else None, DT())

df_simulation = (
    df_sim_base
    .withColumn("battery_cost_eur",
        F.coalesce(F.col("cost_eur_per_kwh"), F.lit(140.0)) * F.col("capacity_kwh")
    )
    .withColumn("total_capex_eur",
        F.col("battery_cost_eur") * (1.0 + INSTALL_OVERHEAD)
    )
    .withColumn("payback_years",
        F.when(F.col("annual_savings_eur") > 0,
            F.least(F.lit(25.0), F.col("total_capex_eur") / F.col("annual_savings_eur"))
        ).otherwise(F.lit(25.0))
    )
    .withColumn("npv_10yr_eur",
        npv_udf(F.col("annual_savings_eur").cast(DT()), F.col("total_capex_eur").cast(DT()))
    )
    .withColumn("irr_percent",
        irr_udf(F.col("annual_savings_eur").cast(DT()), F.col("total_capex_eur").cast(DT()))
    )
    # Comparison score (composite: IRR + payback + CO2 + EU compliance)
    .withColumn("score_irr",     F.least(F.lit(40.0), F.greatest(F.lit(0.0), F.coalesce(F.col("irr_percent"), F.lit(0.0)) * 2.0)))
    .withColumn("score_payback", F.greatest(F.lit(0.0), F.lit(30.0) - (F.col("payback_years") - F.lit(3.0)) * F.lit(2.0)))
    .withColumn("score_co2",     F.least(F.lit(20.0), F.col("annual_co2_kg") / F.lit(500.0)))
    .withColumn("score_eu",
        F.when(F.col("eu_compliant") == True, F.lit(10.0)).otherwise(F.lit(-15.0))
    )
    .withColumn("comparison_score",
        F.greatest(F.lit(0.0), F.least(F.lit(100.0),
            F.col("score_irr") + F.col("score_payback") + F.col("score_co2") + F.col("score_eu")
        ))
    )
    .withColumn("scenario_id",
        F.concat(
            F.col("building_id"), F.lit("_"),
            F.upper(F.substring(F.col("strategy"), 1, 3)), F.lit("_"),
            F.col("capacity_kwh").cast("int").cast("string"), F.lit("kWh")
        )
    )
    .withColumn("strategy_label",
        F.when(F.col("strategy") == "self_consumption", F.lit("Self-Consumption"))
         .when(F.col("strategy") == "peak_shaving",     F.lit("Peak-Shaving"))
         .when(F.col("strategy") == "tou",               F.lit("Time-of-Use (ToU)"))
         .when(F.col("strategy") == "backup",            F.lit("Backup + Opportunistic"))
         .otherwise(F.col("strategy"))
    )
    .withColumn("processed_at", F.current_timestamp())
    .select(
        "scenario_id", "building_id", "building_name", "country_code",
        "battery_type", "eu_compliant",
        F.col("capacity_kwh").alias("battery_capacity_kwh"),
        "pv_capacity_kwp",
        F.round("battery_cost_eur", 0).alias("battery_cost_eur"),
        F.round("total_capex_eur", 0).alias("total_capex_eur"),
        "strategy", "strategy_label",
        F.round("annual_savings_eur", 2).alias("annual_savings_eur"),
        F.round("annual_co2_kg", 2).alias("annual_co2_avoided_kg"),
        F.round("payback_years", 2).alias("payback_years"),
        F.round("npv_10yr_eur", 2).alias("npv_10yr_eur"),
        F.round("irr_percent", 2).alias("irr_percent"),
        F.round("avg_rte", 2).alias("avg_round_trip_efficiency_pct"),
        F.round("comparison_score", 1).alias("comparison_score"),
        "processed_at",
    )
    .orderBy("building_id", F.col("comparison_score").desc())
)

# 2026-05-21: overwriteSchema=true — B007 eklendi, schema değişti
df_simulation.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_simulation")
print(f"  Simulation scenarios written: {df_simulation.count()}")

# ── 6. DAILY SUMMARY (gold_battery_daily_summary) ────────────────────────────

print("[6/6] Building daily summary (best strategy per day)...")

# Best strategy = highest net_savings_eur per building per day
window_best = Window.partitionBy("building_id", "date").orderBy(F.col("net_savings_eur").desc())

df_best_strategy = (
    df_dispatch
    .withColumn("rank", F.row_number().over(window_best))
    .filter(F.col("rank") == 1)
    .drop("rank")
)

# Cumulative metrics (running totals per building)
window_cum = Window.partitionBy("building_id").orderBy("date").rowsBetween(Window.unboundedPreceding, 0)

df_daily_summary = (
    df_best_strategy
    .withColumn("total_cycles_cumulative",
        F.sum(F.col("cycle_depth_pct") / 100.0).over(window_cum)
    )
    .withColumn("total_cost_avoided_eur",
        F.sum("net_savings_eur").over(window_cum)
    )
    .withColumn("total_co2_avoided_kg",
        F.sum("co2_avoided_kg").over(window_cum)
    )
    .select(
        "date", "building_id", "building_name", "country",
        "strategy", "battery_type", "eu_compliant",
        F.col("soc_start_pct").alias("avg_soc_start_percent"),
        F.col("soc_end_pct").alias("avg_soc_end_percent"),
        "charge_kwh", "discharge_kwh", "pv_generation_kwh",
        F.round("round_trip_efficiency", 4).alias("round_trip_efficiency"),
        F.round("net_savings_eur", 4).alias("daily_net_savings_eur"),
        F.round("co2_avoided_kg", 4).alias("daily_co2_avoided_kg"),
        F.round("total_cycles_cumulative", 3).alias("total_cycles_cumulative"),
        F.round("total_cost_avoided_eur", 2).alias("total_cost_avoided_eur"),
        F.round("total_co2_avoided_kg", 2).alias("total_co2_avoided_kg"),
        "is_simulated",
        F.current_timestamp().alias("processed_at"),
    )
    .orderBy("building_id", "date")
)

df_daily_summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_daily_summary")
print(f"  Daily summary rows written: {df_daily_summary.count():,}")

# ── VALIDATION REPORT ─────────────────────────────────────────────────────────

print("\n" + "="*60)
print("VALIDATION REPORT — gold_battery_* tables")
print("="*60)

dispatch_check = spark.read.table("gold_battery_dispatch")
sim_check      = spark.read.table("gold_battery_simulation")
summary_check  = spark.read.table("gold_battery_daily_summary")

print(f"\ngold_battery_dispatch:")
print(f"  Total rows:         {dispatch_check.count():,}")
print(f"  Buildings:          {dispatch_check.select('building_id').distinct().count()}")
print(f"  Strategies:         {dispatch_check.select('strategy').distinct().count()}")
print(f"  Date range:         {dispatch_check.agg(F.min('date'), F.max('date')).collect()[0]}")
print(f"  Avg net savings/day: {dispatch_check.agg(F.avg('net_savings_eur')).collect()[0][0]:.2f} EUR")
print(f"  EU compliant rows:  {dispatch_check.filter(F.col('eu_compliant') == True).count():,}")

print(f"\ngold_battery_simulation:")
print(f"  Scenarios total:    {sim_check.count()}")
print(f"  Best scenario:      top comparison_score per building")
sim_check.select("building_id", "strategy_label", "payback_years", "irr_percent", "comparison_score", "eu_compliant") \
    .orderBy(F.col("comparison_score").desc()).show(10, truncate=False)

print(f"\ngold_battery_daily_summary:")
print(f"  Total rows:         {summary_check.count():,}")
max_savings = summary_check.groupBy("building_id").agg(F.max("total_cost_avoided_eur").alias("total_eur")).orderBy("building_id")
max_savings.show()

print("\nNotebook 12 complete. All gold_battery_* tables ready for Power BI Page 9.")
