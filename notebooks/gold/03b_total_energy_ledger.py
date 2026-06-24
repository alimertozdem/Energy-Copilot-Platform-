# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 03b_total_energy_ledger.py
# Layer: GOLD — Total Final Energy Ledger (Path A)
# Created: 2026-06-19
# =============================================================================
#
# PURPOSE
#   Build a TRUE total-final-energy ledger (electricity + fuel) so EUI and cost
#   are benchmarked on the standard total-energy basis — not electricity-only.
#   Fixes the root cause behind "savings > bill", HP payback 529 yr, EUI 2–3×.
#
#   Design + validation: docs/strategy/total-energy-ledger.md (Mert, 2026-06-19).
#   Heating uses the approved residential degree-day method generalised to any
#   envelope:  q_heat = H_spec · Gt · 24 ÷ 1000  [kWh/m²·yr].
#
# INPUT
#   silver_building_master   envelope U-values, areas, heating type, COP
#   gold_kpi_daily           electricity kWh + € + HDD (already computed in 03)
#   ref_fuel_tariffs         gas/district €/kWh (optional; fallback constants)
#
# OUTPUT
#   gold_energy_ledger       building_id × year × month:
#       electricity_kwh, gas_fuel_kwh, district_heat_kwh, electric_heat_kwh,
#       total_final_energy_kwh, *_cost_eur, total_energy_cost_eur, gfa
#
# NOTE (v1): gas/district buildings' electricity is NOT yet de-inflated (the
#   generator still folds some heating into electricity via heat_mult). Their
#   total is therefore ~5–10% high until the generator regen step. HP/VRF/all-
#   electric buildings are already correct. See doc §5 + §10 step 1.
#
# BMAD PHASE: L3 (data) + L4 (logic).  DP-600: degree-day model, broadcast join,
#   monthly aggregation, idempotent Delta MERGE.
# =============================================================================


# =============================================================================
# CELL 0 — PARAMETERS  (mark as "Toggle parameter cell" in Fabric)
# -----------------------------------------------------------------------------
# ENERGY-REVIEW KNOBS (Mert / Energieberater). Tuning here is one-line, no rework.
# Defaults validated against the live mirror 2026-06-19 (doc §9). See doc §11.
# =============================================================================

# Envelope area-weighted U-value weights (sum = 1.0). [Tahmin] element-area shares.
U_W_WALL, U_W_WINDOW, U_W_ROOF, U_W_FLOOR = 0.40, 0.25, 0.20, 0.15

C_ENV       = 1.5    # envelope-to-floor (form factor). Residential worked ex ≈ 0.94. [Tahmin]
ROOM_H_M    = 3.2    # mean room height [m]. [Tahmin]
N50_DIV     = 20.0   # n50 (blower-door) -> natural infiltration ACH. air_tightness_ach reads as n50.
PHI_HDD     = 1.5    # base-15 HDD -> German Gradtagzahl 20/15 basis. [Tahmin] biggest knob.
ETA_BOILER  = 0.90   # condensing-gas seasonal efficiency (matches residential doc). [Kesin]

# Domestic-hot-water + small process add [kWh/m²·yr] by building type. [Tahmin]
DHW_EUI_BY_TYPE = {
    "Hotel": 35.0, "Healthcare": 30.0, "Lab": 25.0, "Retail": 12.0,
    "Education": 10.0, "Office": 8.0, "Logistics": 5.0, "Data_Center": 2.0,
}
DHW_EUI_DEFAULT = 10.0

# Fuel tariffs [€/kWh] fallback if ref_fuel_tariffs missing. [Muhtemel — verify]
GAS_TARIFF_BY_COUNTRY = {"DE": 0.11, "AT": 0.10, "NL": 0.12, "TR": 0.05,
                         "SE": 0.09, "DK": 0.10}
GAS_TARIFF_DEFAULT      = 0.10
DISTRICT_TARIFF_EUR_KWH = 0.12

# Heating types that legitimately sit on the ELECTRICITY meter (heat already in elec).
ELECTRIC_HEAT_HVAC = ("heat_pump", "gshp", "ashp", "vrf")

GOLD_LEDGER_TABLE = "gold_energy_ledger"

print("✅ CELL 0 params loaded "
      f"| C_ENV={C_ENV} PHI_HDD={PHI_HDD} N50_DIV={N50_DIV} ETA_BOILER={ETA_BOILER}")


# =============================================================================
# CELL 1 — SPARK + IMPORTS
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast,
    sum as spark_sum, max as spark_max,
    round as spark_round, upper, least, greatest,
)
from delta.tables import DeltaTable
from datetime import datetime

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.sql.adaptive.enabled", "true")


def log_step(step, count=None, table=None):
    ts = datetime.now().strftime("%H:%M:%S")
    msg = f"[{ts}] [03b] {step}"
    if table: msg += f" | {table}"
    if count is not None: msg += f" | {count:,} rows"
    print(msg)


def read_delta(name):
    """Schema-safe read: catalog first (metastore), then Tables/dbo, then Tables/.
    Mirrors 06_recommendation_engine.read_delta (mixed-lakehouse 2026-06-01 fix)."""
    try:
        return spark.table(name)
    except Exception:
        pass
    for _p in (f"Tables/dbo/{name}", f"Tables/{name}"):
        try:
            return spark.read.format("delta").load(_p)
        except Exception:
            continue
    raise Exception(f"{name} not found via catalog or Tables paths")


def table_exists(table_name):
    try:
        return spark.catalog.tableExists(table_name)
    except Exception:
        return False


def merge_to_gold(df_new, merge_keys, table_name):
    """Idempotent upsert (03 convention): first run saveAsTable overwrite, then MERGE."""
    if not table_exists(table_name):
        (df_new.write.format("delta").mode("overwrite")
            .option("overwriteSchema", "true").saveAsTable(table_name))
        log_step("✅ first write (saveAsTable)", df_new.count(), table_name)
    else:
        cond = " AND ".join([f"target.{k} = source.{k}" for k in merge_keys])
        (DeltaTable.forName(spark, table_name).alias("target")
            .merge(df_new.alias("source"), cond)
            .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
        log_step("✅ MERGE done", table=table_name)


# =============================================================================
# CELL 2 — READ INPUTS
# =============================================================================

df_bm  = read_delta("silver_building_master")
df_kpi = read_delta("gold_kpi_daily")
log_step("inputs loaded", table="silver_building_master + gold_kpi_daily")

# Optional fuel tariffs (fallback to constants if table missing)
try:
    _ft = {r["fuel_country"]: r["gas_eur_kwh"]
           for r in read_delta("ref_fuel_tariffs")
                     .select(col("country_code").alias("fuel_country"),
                             col("gas_eur_kwh")).collect()}
    log_step("ref_fuel_tariffs loaded", len(_ft))
except Exception as _e:
    _ft = {}
    log_step(f"⚠️ ref_fuel_tariffs missing → fallback gas tariffs ({str(_e)[:40]})")

_has_hvac_col = "primary_hvac_system" in df_bm.columns


# =============================================================================
# CELL 3 — MONTHLY ELECTRICITY + HDD (from gold_kpi_daily)
# =============================================================================

df_month = (
    df_kpi.groupBy("building_id", "year", "month")
    .agg(
        spark_sum("total_consumption_kwh").alias("electricity_kwh"),
        spark_sum("estimated_cost_eur").alias("electricity_cost_eur"),
        spark_sum("hdd_day").alias("month_hdd"),
    )
)

# Annual HDD per building (denominator for monthly heat distribution)
df_annual_hdd = (
    df_kpi.groupBy("building_id").agg(spark_sum("hdd_day").alias("annual_hdd"))
)
log_step("monthly electricity aggregated", df_month.count())


# =============================================================================
# CELL 4 — DEGREE-DAY HEATING MODEL (per building)
# -----------------------------------------------------------------------------
#   U_eff   = weighted envelope U                 [W/m²K]
#   H_spec  = U_eff·C_env + 0.34·(n50/20)·h       [W/m²K per conditioned m²]
#   q_heat  = H_spec · (annual_hdd·phi) · 24/1000 [kWh/m²·yr space heat]
#   + DHW (type table). Carrier by heating type.
# =============================================================================

dhw_expr = lit(DHW_EUI_DEFAULT)
for _t, _v in DHW_EUI_BY_TYPE.items():
    dhw_expr = when(col("building_type") == _t, lit(_v)).otherwise(dhw_expr)

# Heating type flags (robust to a missing primary_hvac_system column)
is_gas = coalesce(col("has_gas_heating"), lit(False)) == True
if _has_hvac_col:
    hvac = coalesce(col("primary_hvac_system"), lit(""))
    is_district = hvac == "district"
    is_elec_heat = coalesce(col("has_heat_pump"), lit(False)) | hvac.isin(*ELECTRIC_HEAT_HVAC)
else:
    is_district  = lit(False)
    is_elec_heat = coalesce(col("has_heat_pump"), lit(False))

df_b = (
    df_bm.join(df_annual_hdd, on="building_id", how="left")
    .withColumn("u_eff",
        col("wall_u_value")*U_W_WALL + col("window_u_value")*U_W_WINDOW
        + col("roof_u_value")*U_W_ROOF + col("floor_u_value")*U_W_FLOOR)
    .withColumn("h_spec",
        col("u_eff")*lit(C_ENV) + lit(0.34)*(col("air_tightness_ach")/lit(N50_DIV))*lit(ROOM_H_M))
    .withColumn("q_heat_eui",
        col("h_spec") * (col("annual_hdd")*lit(PHI_HDD)) * lit(24.0/1000.0))
    .withColumn("dhw_eui", dhw_expr)
    .withColumn("annual_space_heat_kwh", col("q_heat_eui")*col("conditioned_area_m2"))
    .withColumn("annual_dhw_kwh",        col("dhw_eui")*col("conditioned_area_m2"))
    .withColumn("_is_gas", is_gas)
    .withColumn("_is_district", is_district)
    .withColumn("_is_elec_heat", is_elec_heat)
    .withColumn("_cop", coalesce(col("heat_pump_cop_rated"), lit(3.5)))
    .withColumn("_gas_tariff",
        coalesce(*([when(col("country_code")==c, lit(_ft.get(c, GAS_TARIFF_BY_COUNTRY.get(c))))
                    for c in set(list(GAS_TARIFF_BY_COUNTRY)+list(_ft))]
                   + [lit(GAS_TARIFF_DEFAULT)])))
    .select("building_id", "building_type", "country_code", "gross_floor_area_m2",
            "conditioned_area_m2", "annual_hdd", "u_eff", "h_spec", "q_heat_eui",
            "dhw_eui", "annual_space_heat_kwh", "annual_dhw_kwh",
            "_is_gas", "_is_district", "_is_elec_heat", "_cop", "_gas_tariff")
)
log_step("heating model computed", df_b.count())


# =============================================================================
# CELL 5 — MONTHLY CARRIERS + COSTS + TOTAL
# -----------------------------------------------------------------------------
#   space heat distributed by monthly HDD share; DHW spread evenly (/12).
#   gas: heat/eta_boiler | district: heat (delivered) | elec-heat: heat/COP (already in elec, NOT re-added)
# =============================================================================

df = (
    df_month.join(broadcast(df_b), on="building_id", how="inner")
    .withColumn("_hdd_share",
        when(col("annual_hdd") > 0, col("month_hdd")/col("annual_hdd")).otherwise(lit(0.0)))
    .withColumn("month_space_heat_kwh", col("annual_space_heat_kwh")*col("_hdd_share"))
    .withColumn("month_dhw_kwh", col("annual_dhw_kwh")/lit(12.0))
    .withColumn("month_heat_delivered_kwh", col("month_space_heat_kwh")+col("month_dhw_kwh"))
    # Carriers
    .withColumn("gas_fuel_kwh",
        when(col("_is_gas"), col("month_heat_delivered_kwh")/lit(ETA_BOILER)).otherwise(lit(0.0)))
    .withColumn("district_heat_kwh",
        when(col("_is_district"), col("month_heat_delivered_kwh")).otherwise(lit(0.0)))
    .withColumn("electric_heat_kwh",   # informational only — already inside electricity_kwh
        when(col("_is_elec_heat"), col("month_heat_delivered_kwh")/col("_cop")).otherwise(lit(0.0)))
    # Total final energy = electricity + fuel carriers (elec-heat already in electricity)
    .withColumn("total_final_energy_kwh",
        col("electricity_kwh") + col("gas_fuel_kwh") + col("district_heat_kwh"))
    # Costs
    .withColumn("gas_cost_eur",      col("gas_fuel_kwh")*col("_gas_tariff"))
    .withColumn("district_cost_eur", col("district_heat_kwh")*lit(DISTRICT_TARIFF_EUR_KWH))
    .withColumn("total_energy_cost_eur",
        coalesce(col("electricity_cost_eur"), lit(0.0))
        + col("gas_cost_eur") + col("district_cost_eur"))
    .select(
        "building_id", "building_type", "country_code", "year", "month",
        spark_round("electricity_kwh", 1).alias("electricity_kwh"),
        spark_round("gas_fuel_kwh", 1).alias("gas_fuel_kwh"),
        spark_round("district_heat_kwh", 1).alias("district_heat_kwh"),
        spark_round("electric_heat_kwh", 1).alias("electric_heat_kwh"),
        spark_round("total_final_energy_kwh", 1).alias("total_final_energy_kwh"),
        spark_round("electricity_cost_eur", 2).alias("electricity_cost_eur"),
        spark_round("gas_cost_eur", 2).alias("gas_cost_eur"),
        spark_round("district_cost_eur", 2).alias("district_cost_eur"),
        spark_round("total_energy_cost_eur", 2).alias("total_energy_cost_eur"),
        col("gross_floor_area_m2"),
    )
)
log_step("monthly ledger assembled", df.count())


# =============================================================================
# CELL 6 — WRITE gold_energy_ledger (idempotent MERGE)
# =============================================================================

merge_to_gold(df, merge_keys=["building_id", "year", "month"], table_name=GOLD_LEDGER_TABLE)
try:
    spark.sql(f"OPTIMIZE {GOLD_LEDGER_TABLE} ZORDER BY (building_id, year, month)")
    log_step("⚡ Z-ORDER OPTIMIZE", table=GOLD_LEDGER_TABLE)
except Exception as _e:
    log_step(f"⚠️ OPTIMIZE skipped: {str(_e)[:60]}")


# =============================================================================
# CELL 7 — SANITY: annual total-energy EUI per building (for review)
# =============================================================================

print("\n── Annual total-final-energy EUI by building (kWh/m²·yr) ──")
(
    df.groupBy("building_id", "building_type")
    .agg(
        spark_sum("electricity_kwh").alias("elec_kwh"),
        spark_sum("gas_fuel_kwh").alias("gas_kwh"),
        spark_sum("district_heat_kwh").alias("district_kwh"),
        spark_sum("total_final_energy_kwh").alias("total_kwh"),
        spark_max("gross_floor_area_m2").alias("gfa"),
    )
    .withColumn("elec_eui",  spark_round(col("elec_kwh")/col("gfa"), 0))
    .withColumn("total_eui", spark_round(col("total_kwh")/col("gfa"), 0))
    .orderBy(col("total_eui").desc())
    .show(20, truncate=False)
)
log_step("✅ 03b complete — gold_energy_ledger ready")
