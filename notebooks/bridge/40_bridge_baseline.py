# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 40_bridge_baseline.py
# Layer: BRIDGE — Self-serve Fabric bridging for an upload-only (Tier-1) building
# =============================================================================
#
# PURPOSE (Access Layer 3, Phase 3.2):
#   Bridge ONE pending building (Postgres-only, baseline monthly kWh) into Fabric:
#     1. Read the building's bronze parquet from OneLake (landed by the backend).
#     2. Upsert a dimension row into silver_building_master.
#     3. Produce gold_kpi_monthly (true monthly grain) + gold_kpi_daily
#        (monthly distributed to days — STATED ASSUMPTION, see §C).
#   The notebook is PARAMETERISED by building and IDEMPOTENT (re-run safe via MERGE
#   on the natural key). It writes ONLY the energy tables the data can honestly fill;
#   solar / battery / weather / HVAC / IoT columns are left 0 / null, so the
#   module-gated pages (8/9) and solar visuals stay locked rather than show fake data.
#
# WHAT THIS NOTEBOOK DOES *NOT* DO:
#   - It does not invent sub-hourly, solar, battery, or HVAC data.
#   - It does not run the full 03_gold_kpi_engine (that needs hourly silver tables
#     this building doesn't have). It writes the baseline slice directly.
#   - It does not assign the fabric_building_id (the backend mints it and passes it
#     in as a parameter, then writes it back to Postgres after a successful run).
#
# DP-600 TOPICS: parameter cell, Delta MERGE (idempotent upsert), schema-conforming
#   write (resilient to gold schema drift), explode for monthly→daily expansion.
# =============================================================================


# =============================================================================
# CELL 0 — PARAMETERS  (mark as "Toggle parameter cell" in Fabric)
# -----------------------------------------------------------------------------
# These defaults are overridden by the Fabric job trigger (the backend passes the
# real values). Keep defaults harmless so a manual run without params fails loud
# rather than corrupting a real building.
# =============================================================================

building_uuid        = ""          # Postgres buildings.id (UUID string) — REQUIRED
fabric_building_id   = ""          # minted id, e.g. "B012" — REQUIRED
bronze_path          = ""          # OneLake abfss path to the building's parquet — REQUIRED
building_meta_json   = "{}"        # JSON: name, country_code, area_m2, building_type, pv_capacity_kwp, ...

print("📋 Bridge parameters")
print(f"   building_uuid      = {building_uuid!r}")
print(f"   fabric_building_id = {fabric_building_id!r}")
print(f"   bronze_path        = {bronze_path!r}")


# =============================================================================
# CELL 1 — IMPORTS, CONFIG, GUARDS
# =============================================================================

import json
from datetime import datetime

from pyspark.sql import functions as F
from delta.tables import DeltaTable

spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Fail loud on missing required params — never write a half-identified building.
_missing = [n for n, v in {
    "building_uuid": building_uuid,
    "fabric_building_id": fabric_building_id,
    "bronze_path": bronze_path,
}.items() if not v]
if _missing:
    raise ValueError(f"Missing required bridge parameters: {_missing}")

meta = json.loads(building_meta_json) if building_meta_json else {}

# --- Stated energy assumptions (Mert is the energy reviewer — flagged for sign-off) ---
# §A Emission factor: prefer meta-provided country factor; fall back to EU average.
#     Aligns with 03_gold_kpi_engine's ref_grid_emission_factors logic.
EU_EF_FALLBACK_KG_KWH = float(meta.get("emission_factor_kg_kwh") or 0.30)
# §B Tariff for cost estimation (EUR/kWh) — country-aware, else EU fallback.
TARIFF_FALLBACK_EUR_KWH = float(meta.get("tariff_eur_kwh") or 0.30)
# §C Monthly→daily distribution: a building that uploaded MONTHLY totals has no
#     daily resolution. We distribute each month's kWh UNIFORMLY across its days
#     (kWh_day = kWh_month / days_in_month). This is a STATED ASSUMPTION so that
#     daily-grain Power BI visuals (Overview/Trends) populate; it does NOT claim
#     real daily variation. Rows are flagged is_estimated_from_monthly = True.

COUNTRY = (meta.get("country_code") or "EU").upper()
AREA_M2 = float(meta.get("area_m2") or meta.get("conditioned_area_m2") or 0.0)
BUILDING_TYPE = meta.get("building_type") or "office"
PV_KWP = float(meta.get("pv_capacity_kwp") or 0.0)
SUB_TIER = meta.get("subscription_tier") or "basic"

print(f"✅ Guards passed. country={COUNTRY} area_m2={AREA_M2} type={BUILDING_TYPE} "
      f"EF={EU_EF_FALLBACK_KG_KWH} tariff={TARIFF_FALLBACK_EUR_KWH}")


# =============================================================================
# CELL 2 — READ BRONZE (the building's uploaded baseline, landed by the backend)
# -----------------------------------------------------------------------------
# The backend OneLake writer lands a CSV (stdlib-only, no pyarrow dependency) at
# bronze_path with a header row and columns:
#   period_month : string  "YYYY-MM"
#   kwh          : double   monthly consumption
#   cost_eur     : double   optional, may be empty
# We normalise to a monthly DataFrame keyed by fabric_building_id.
# =============================================================================

df_bronze = (
    spark.read.option("header", True).option("inferSchema", True).csv(bronze_path)
)
print(f"✅ Bronze read: {df_bronze.count()} rows from {bronze_path}")
df_bronze.show(5, truncate=False)

# Normalise: parse period → first-of-month date, coerce numeric.
df_month = (
    df_bronze
    .select(
        F.lit(fabric_building_id).alias("building_id"),
        F.to_date(F.concat_ws("-", F.substring(F.col("period_month"), 1, 4),
                               F.substring(F.col("period_month"), 6, 2),
                               F.lit("01"))).alias("month_start"),
        F.col("kwh").cast("double").alias("total_consumption_kwh"),
        (F.col("cost_eur").cast("double") if "cost_eur" in df_bronze.columns
         else F.lit(None).cast("double")).alias("uploaded_cost_eur"),
    )
    .filter(F.col("month_start").isNotNull() & (F.col("total_consumption_kwh") > 0))
    .withColumn("year", F.year("month_start"))
    .withColumn("month", F.month("month_start"))
    .withColumn("days_in_month", F.dayofmonth(F.last_day("month_start")))
)
n_months = df_month.count()
if n_months == 0:
    raise ValueError("No valid monthly rows after parsing bronze — aborting bridge.")
print(f"✅ Normalised to {n_months} monthly rows.")


# =============================================================================
# CELL 3 — UPSERT DIMENSION (silver_building_master)
# -----------------------------------------------------------------------------
# The gold engine + many DAX measures join to this dim. We insert/refresh exactly
# this building's row. has_pv/has_battery/has_heat_pump default False so the
# module-gated pages stay locked until real device data arrives.
# =============================================================================

# Envelope / compliance fields for the downstream report notebooks (05 GEG §10
# U-value check, 09 GHG Scope-1 gas flag). We MUST use the EXACT
# silver_building_master column names — conform_to_target() drops any column whose
# name doesn't match the target, so a typo here = silent null = locked GEG report.
def _f(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None

def _i(v):
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None

WALL_U     = _f(meta.get("wall_u_value"))
ROOF_U     = _f(meta.get("roof_u_value"))
WINDOW_U   = _f(meta.get("window_u_value"))
INSUL_YR   = _i(meta.get("insulation_year"))
YEAR_BUILT = _i(meta.get("construction_year"))
EPC        = meta.get("epc_class") or None
CITY       = meta.get("city") or None
_gas       = meta.get("has_gas_heating")
HAS_GAS    = bool(_gas) if _gas is not None else None
print(f"   envelope: wall={WALL_U} roof={ROOF_U} window={WINDOW_U} "
      f"insul={INSUL_YR} year_built={YEAR_BUILT} gas={HAS_GAS} epc={EPC}")

# Build the dimension row with proper booleans via an explicit DDL schema.
df_dim_new = spark.createDataFrame(
    [(fabric_building_id, meta.get("name") or fabric_building_id, COUNTRY, AREA_M2,
      PV_KWP, 0.0, PV_KWP > 0, False, bool(meta.get("has_heat_pump") or False),
      EU_EF_FALLBACK_KG_KWH, SUB_TIER, BUILDING_TYPE,
      YEAR_BUILT, CITY, WALL_U, ROOF_U, WINDOW_U, INSUL_YR, EPC, HAS_GAS)],
    schema="building_id string, building_name string, country_code string, "
           "conditioned_area_m2 double, pv_capacity_kwp double, battery_capacity_kwh double, "
           "has_pv boolean, has_battery boolean, has_heat_pump boolean, "
           "emission_factor_kg_kwh double, subscription_tier string, building_type string, "
           "year_built int, city string, wall_u_value double, roof_u_value double, "
           "window_u_value double, insulation_year int, energy_certificate string, "
           "has_gas_heating boolean",
)


def conform_to_target(df_new, target_table):
    """Add any columns the target table has but df_new lacks (as null), drop
    extras, and order to match the target. Resilient to schema drift in gold —
    a recurring pain point in this project."""
    target = spark.table(target_table)
    target_fields = target.schema.fields
    out = df_new
    have = set(df_new.columns)
    for f in target_fields:
        if f.name not in have:
            out = out.withColumn(f.name, F.lit(None).cast(f.dataType))
    return out.select([f.name for f in target_fields])


def merge_upsert(df_new, target_table, keys, partition_cols=None):
    """Idempotent MERGE; first write creates the table. Conforms df_new to the
    existing target schema when the table already exists."""
    if not spark.catalog.tableExists(target_table):
        w = df_new.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
        if partition_cols:
            w = w.partitionBy(*partition_cols)
        w.saveAsTable(target_table)
        print(f"✅ Created {target_table} ({df_new.count()} rows)")
        return
    conformed = conform_to_target(df_new, target_table)
    tgt = DeltaTable.forName(spark, target_table)
    cond = " AND ".join([f"t.{k} = s.{k}" for k in keys])
    (tgt.alias("t").merge(conformed.alias("s"), cond)
        .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
    print(f"✅ Merged into {target_table} on {keys}")


merge_upsert(df_dim_new, "silver_building_master", keys=["building_id"])


# =============================================================================
# CELL 4 — GOLD MONTHLY (true grain) + GOLD DAILY (distributed — stated assumption)
# =============================================================================

tariff = TARIFF_FALLBACK_EUR_KWH
ef = EU_EF_FALLBACK_KG_KWH

# ---- gold_kpi_monthly: honest monthly grain ----
df_gold_monthly = (
    df_month
    .withColumn("net_grid_consumption_kwh", F.col("total_consumption_kwh"))  # no solar/battery
    .withColumn("co2_emissions_kg", F.round(F.col("total_consumption_kwh") * F.lit(ef), 4))
    .withColumn("co2_savings_from_solar_kg", F.lit(0.0))
    .withColumn("solar_generated_kwh", F.lit(0.0))
    .withColumn("battery_charged_kwh", F.lit(0.0))
    .withColumn("battery_discharged_kwh", F.lit(0.0))
    .withColumn("floor_area_m2", F.lit(AREA_M2))
    .withColumn("pv_capacity_kwp", F.lit(PV_KWP))
    .withColumn("battery_capacity_kwh", F.lit(0.0))
    .withColumn("emission_factor_kg_kwh", F.lit(ef))
    .withColumn("country_code", F.lit(COUNTRY))
    .withColumn("has_pv", F.lit(PV_KWP > 0))
    .withColumn("has_battery", F.lit(False))
    .withColumn("subscription_tier", F.lit(SUB_TIER))
    .withColumn("monthly_eui_kwh_m2",
        F.when(F.lit(AREA_M2) > 0, F.round(F.col("total_consumption_kwh") / F.lit(AREA_M2), 4))
         .otherwise(F.lit(None)))
    .withColumn("total_cost_eur",
        F.round(F.coalesce(F.col("uploaded_cost_eur"),
                           F.col("total_consumption_kwh") * F.lit(tariff)), 2))
    .withColumn("total_savings_eur", F.lit(0.0))
    .withColumn("data_source", F.lit("baseline_upload"))
    .withColumn("processed_at", F.current_timestamp())
)
merge_upsert(df_gold_monthly, "gold_kpi_monthly",
             keys=["building_id", "year", "month"])

# ---- gold_kpi_daily: distribute month → days (UNIFORM, flagged estimated) ----
# explode a sequence 1..days_in_month, build a date per day, divide kWh evenly.
df_gold_daily = (
    df_month
    .withColumn("day_no", F.explode(F.sequence(F.lit(1), F.col("days_in_month"))))
    .withColumn("date", F.expr("date_add(month_start, day_no - 1)"))
    .withColumn("daily_kwh", F.round(F.col("total_consumption_kwh") / F.col("days_in_month"), 4))
    .select(
        "building_id", "date", "year", "month",
        F.col("daily_kwh").alias("total_consumption_kwh"),
        F.col("daily_kwh").alias("net_grid_consumption_kwh"),
    )
    .withColumn("co2_emissions_kg", F.round(F.col("net_grid_consumption_kwh") * F.lit(ef), 4))
    .withColumn("co2_savings_from_solar_kg", F.lit(0.0))
    .withColumn("solar_generated_kwh", F.lit(0.0))
    .withColumn("solar_self_consumed_kwh", F.lit(0.0))
    .withColumn("solar_exported_kwh", F.lit(0.0))
    .withColumn("battery_charged_kwh", F.lit(0.0))
    .withColumn("battery_discharged_kwh", F.lit(0.0))
    .withColumn("floor_area_m2", F.lit(AREA_M2))
    .withColumn("pv_capacity_kwp", F.lit(PV_KWP))
    .withColumn("battery_capacity_kwh", F.lit(0.0))
    .withColumn("emission_factor_kg_kwh", F.lit(ef))
    .withColumn("country_code", F.lit(COUNTRY))
    .withColumn("has_pv", F.lit(PV_KWP > 0))
    .withColumn("has_battery", F.lit(False))
    .withColumn("has_heat_pump", F.lit(bool(meta.get("has_heat_pump") or False)))
    .withColumn("subscription_tier", F.lit(SUB_TIER))
    .withColumn("eui_kwh_m2",
        F.when(F.lit(AREA_M2) > 0, F.round(F.col("total_consumption_kwh") / F.lit(AREA_M2), 4))
         .otherwise(F.lit(None)))
    .withColumn("carbon_intensity_kg_m2",
        F.when(F.lit(AREA_M2) > 0, F.round(F.col("co2_emissions_kg") / F.lit(AREA_M2), 6))
         .otherwise(F.lit(None)))
    .withColumn("estimated_cost_eur",
        F.round(F.col("net_grid_consumption_kwh") * F.lit(tariff), 2))
    .withColumn("estimated_savings_eur", F.lit(0.0))
    .withColumn("solar_specific_yield_kwh_kwp", F.lit(None).cast("double"))
    .withColumn("is_estimated_from_monthly", F.lit(True))
    .withColumn("data_source", F.lit("baseline_upload"))
    .withColumn("processed_at", F.current_timestamp())
)
print(f"✅ Daily rows synthesised: {df_gold_daily.count()} "
      f"(uniform monthly distribution, flagged is_estimated_from_monthly)")
merge_upsert(df_gold_daily, "gold_kpi_daily",
             keys=["building_id", "date"])


# =============================================================================
# CELL 5 — RESULT MARKER (the backend reads job output / polls success)
# =============================================================================

result = {
    "status": "ok",
    "building_uuid": building_uuid,
    "fabric_building_id": fabric_building_id,
    "months_loaded": int(n_months),
    "daily_rows": int(df_gold_daily.count()),
    "data_tier": "baseline",
    "notes": "monthly→daily uniform distribution (estimated); solar/battery/HVAC/IoT left empty",
    "finished_at": datetime.utcnow().isoformat() + "Z",
}
print("BRIDGE_RESULT " + json.dumps(result))

# In Fabric, expose the result to the job runner:
try:
    mssparkutils.notebook.exit(json.dumps(result))  # noqa: F821
except Exception:
    pass
