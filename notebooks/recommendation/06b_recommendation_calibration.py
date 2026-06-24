# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 06b_recommendation_calibration.py
# Layer: GOLD — Recommendation calibration (B1, Path A)
# Created: 2026-06-19
# =============================================================================
#
# PURPOSE
#   Stage 2 of the recommendation engine. Runs AFTER 06_recommendation_engine.
#   Fixes "savings > bill": re-bases every measure on TOTAL energy cost
#   (gold_energy_ledger, Path A) and enforces realistic ceilings.
#
#   Root cause (verified mirror 2026-06-19): 06 credits each measure as % of the
#   ELECTRICITY bill; heating measures (CHP 75%, heat-recovery, BMS) therefore
#   over-credit, and 7/10 buildings' total recommended saving exceeds the whole
#   annual bill. Heat-pump shows ~0 saving / 529-yr payback because on an
#   electricity-only ledger a gas→electric switch looks like a loss.
#
#   FIX (this notebook):
#     1. Per-measure cap = realistic band × TOTAL annual energy cost (doc §8).
#     2. Sub-metering = enabler → direct saving 0.
#     3. Heat pump = recompute properly: avoided gas cost − extra electricity.
#     4. Aggregate cap: Σ(measures) ≤ 35% of total annual cost (deep-retrofit
#        ceiling); scale a building's measures down proportionally if exceeded.
#     5. Recompute payback_years, npv_eur; scale co2_saving_kg with the € change.
#
#   Writes back to gold_recommendations via Delta MERGE (idempotent, in place).
#   Re-run order: 03b → 06 → 06b.  Design: docs/strategy/total-energy-ledger.md
# =============================================================================


# =============================================================================
# CELL 0 — PARAMETERS (Toggle parameter cell)
# =============================================================================

# Per-measure ceiling as a fraction of TOTAL annual energy cost. [Tahmin] screening.
MEASURE_CAP_PCT = {
    "UPGRADE_LIGHTING":        0.05,   # LED 2-5%
    "HVAC_SCHEDULING":         0.15,   # setback/scheduling 5-15%
    "BMS_OPTIMISATION":        0.10,   # ISO 50001 5-10%
    "IMPROVE_INSULATION":      0.20,   # envelope 10-20%
    "PEAK_DEMAND_MANAGEMENT":  0.08,   # demand-charge 3-8%
    "POWER_FACTOR_CORRECTION": 0.04,   # reactive penalties 1-4%
    "CHP_COGENERATION":        0.22,   # combined efficiency vs separate
    "BATTERY_EXPANSION":       0.08,   # self-consumption + peak 3-8%
    "SOLAR_THERMAL":           0.08,   # DHW/heating fraction
    "HEAT_RECOVERY":           0.10,   # HRV/ERV 5-10%
    "INSTALL_SOLAR":           0.25,   # PV offset of total cost
    "DEEP_RETROFIT":           0.35,   # combined package (aggregate cap also applies)
    "CHANGE_BATTERY_STRATEGY": 0.03,   # dispatch tweak
    "SUBMETERING_UPGRADE":     0.00,   # ENABLER — no direct kWh saving
}
MEASURE_CAP_DEFAULT = 0.10
TOTAL_CAP_PCT       = 0.35    # deep-retrofit ceiling on a building's TOTAL saving
# EPC-scaled ceiling: already-efficient buildings have less savings headroom (a net-plus
# A-rated bldg cannot save 35%). Effective ceiling = TOTAL_CAP_PCT × factor →
# A 12% · B 18% · C 25% · D 30% · E/F/G 35%. [Tahmin] Energieberater-tunable.
EPC_CAP_FACTOR = {"A": 0.35, "B": 0.50, "C": 0.70, "D": 0.85, "E": 1.0, "F": 1.0, "G": 1.0}
EPC_CAP_FACTOR_DEFAULT = 1.0
BM_TABLE = "silver_building_master"
ANNUITY_FACTOR      = 12.0    # npv ≈ annual_saving × factor − net_capex (~20yr @ 5%)
ETA_BOILER          = 0.90    # gas boiler seasonal efficiency (matches 03b)
ASSUMED_NEW_HP_COP  = 3.2     # ASHP retrofit seasonal COP (candidate has no HP yet) [Tahmin]
FALLBACK_ELEC_TARIFF = 0.30   # €/kWh if a building has no electricity in the ledger

REC_TABLE    = "gold_recommendations"
LEDGER_TABLE = "gold_energy_ledger"

print(f"✅ CELL 0 | TOTAL_CAP={TOTAL_CAP_PCT} | {len(MEASURE_CAP_PCT)} measure bands")


# =============================================================================
# CELL 1 — SPARK + HELPERS
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce,
    sum as spark_sum, max as smax, round as spark_round, least, greatest,
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable
from datetime import datetime

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.adaptive.enabled", "true")


def log_step(step, count=None, table=None):
    ts = datetime.now().strftime("%H:%M:%S")
    msg = f"[{ts}] [06b] {step}"
    if table: msg += f" | {table}"
    if count is not None: msg += f" | {count:,} rows"
    print(msg)


def read_delta(name):
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


# =============================================================================
# CELL 2 — BUILDING ANNUAL TOTAL ENERGY COST (trailing 12 months, dynamic)
# =============================================================================

led = read_delta(LEDGER_TABLE).withColumn("ym", col("year")*12 + col("month"))
_mx = led.agg(smax("ym")).first()[0]
led12 = led.filter((col("ym") > _mx - 12) & (col("ym") <= _mx))

bldg = (
    led12.groupBy("building_id")
    .agg(
        spark_sum("total_energy_cost_eur").alias("annual_total_cost"),
        spark_sum("gas_cost_eur").alias("annual_gas_cost"),
        spark_sum("gas_fuel_kwh").alias("annual_gas_kwh"),
        spark_sum("electricity_cost_eur").alias("annual_elec_cost"),
        spark_sum("electricity_kwh").alias("annual_elec_kwh"),
    )
    .withColumn("elec_tariff_eff",
        when(col("annual_elec_kwh") > 0, col("annual_elec_cost")/col("annual_elec_kwh"))
        .otherwise(lit(FALLBACK_ELEC_TARIFF)))
)

# EPC-scaled total ceiling per building
_epc = read_delta(BM_TABLE).select("building_id", "energy_certificate")
_epc_expr = lit(EPC_CAP_FACTOR_DEFAULT)
for _g, _f in EPC_CAP_FACTOR.items():
    _epc_expr = when(col("energy_certificate") == _g, lit(_f)).otherwise(_epc_expr)
_epc = _epc.withColumn("_epc_factor", _epc_expr)
bldg = (
    bldg.join(_epc, on="building_id", how="left")
    .withColumn("_cap_total_pct",
        lit(TOTAL_CAP_PCT) * coalesce(col("_epc_factor"), lit(EPC_CAP_FACTOR_DEFAULT)))
)
log_step("building annual cost (trailing 12mo)", bldg.count(),
         f"latest ym={_mx} → {_mx-11}..{_mx}")


# =============================================================================
# CELL 3 — JOIN + PER-MEASURE CAP
# =============================================================================

df_rec = read_delta(REC_TABLE)

# cap_pct lookup by action_type
cap_expr = lit(MEASURE_CAP_DEFAULT)
for _a, _p in MEASURE_CAP_PCT.items():
    cap_expr = when(col("action_type") == _a, lit(_p)).otherwise(cap_expr)

df = (
    df_rec.join(bldg, on="building_id", how="left")
    .withColumn("_cap_pct", cap_expr)
    .withColumn("_cop_new", lit(ASSUMED_NEW_HP_COP))
    # Heat pump recompute: avoided gas € − extra electricity € (fuel switch).
    .withColumn("_hp_saving",
        greatest(lit(0.0),
            coalesce(col("annual_gas_cost"), lit(0.0))
            - (coalesce(col("annual_gas_kwh"), lit(0.0)) * lit(ETA_BOILER) / col("_cop_new"))
              * col("elec_tariff_eff")))
    # Capped saving per measure
    .withColumn("_saving_capped",
        when(col("action_type") == "SUBMETERING_UPGRADE", lit(0.0))
        .when(col("action_type") == "ENERGY_AUDIT", col("annual_saving_eur"))  # compliance, keep (null)
        .when(col("action_type") == "INSTALL_HEAT_PUMP", col("_hp_saving"))
        .otherwise(
            least(coalesce(col("annual_saving_eur"), lit(0.0)),
                  col("_cap_pct") * coalesce(col("annual_total_cost"), lit(0.0)))))
)


# =============================================================================
# CELL 4 — AGGREGATE CAP (Σ measures ≤ 35% of total annual cost)
# =============================================================================

w = Window.partitionBy("building_id")
df = (
    df.withColumn("_bldg_sum", spark_sum(coalesce(col("_saving_capped"), lit(0.0))).over(w))
    .withColumn("_cap_eur", col("annual_total_cost") * col("_cap_total_pct"))
    .withColumn("_scale",
        when(col("_bldg_sum") > col("_cap_eur"), col("_cap_eur") / col("_bldg_sum"))
        .otherwise(lit(1.0)))
    .withColumn("_saving_final",
        when(col("_saving_capped").isNull(), lit(None).cast("double"))
        .otherwise(spark_round(col("_saving_capped") * col("_scale"), 0)))
    # scale CO2 with the € change (physical proportionality); HP/submeter handled by ratio
    .withColumn("_co2_ratio",
        when((coalesce(col("annual_saving_eur"), lit(0.0)) > 0) & col("_saving_final").isNotNull(),
             col("_saving_final") / col("annual_saving_eur"))
        .otherwise(lit(1.0)))
    .withColumn("_co2_final",
        when(col("action_type") == "SUBMETERING_UPGRADE", lit(0.0))
        .when(col("action_type") == "INSTALL_HEAT_PUMP", col("co2_saving_kg"))  # physical CO2, keep
        .when(col("_saving_final").isNull(), col("co2_saving_kg"))
        .otherwise(spark_round(coalesce(col("co2_saving_kg"), lit(0.0)) * col("_co2_ratio"), 0)))
    # recompute payback + npv from the final saving
    .withColumn("_payback_final",
        when((col("_saving_final").isNotNull()) & (col("_saving_final") > 0),
             spark_round(col("net_capex_eur") / col("_saving_final"), 1))
        .otherwise(lit(None).cast("double")))
    .withColumn("_npv_final",
        when(col("_saving_final").isNotNull(),
             spark_round(col("_saving_final") * lit(ANNUITY_FACTOR) - col("net_capex_eur"), 0))
        .otherwise(col("npv_eur")))
)

df_updates = df.select(
    "building_id", "action_type",
    col("_saving_final").alias("annual_saving_eur"),
    col("_co2_final").alias("co2_saving_kg"),
    col("_payback_final").alias("payback_years"),
    col("_npv_final").alias("npv_eur"),
).cache()
_n = df_updates.count()
log_step("calibrated updates computed", _n)


# =============================================================================
# CELL 5 — MERGE back into gold_recommendations (in place)
# =============================================================================

tgt = DeltaTable.forName(spark, REC_TABLE)
(tgt.alias("t")
    .merge(df_updates.alias("s"), "t.building_id = s.building_id AND t.action_type = s.action_type")
    .whenMatchedUpdate(set={
        "annual_saving_eur": "s.annual_saving_eur",
        "co2_saving_kg":     "s.co2_saving_kg",
        "payback_years":     "s.payback_years",
        "npv_eur":           "s.npv_eur",
    })
    .execute())
log_step("✅ MERGE done", table=REC_TABLE)


# =============================================================================
# CELL 6 — SANITY: total saving vs total bill per building (must be ≤ ~35%)
# =============================================================================

print("\n── Total recommended saving as % of total annual energy cost ──")
(
    read_delta(REC_TABLE)
    .groupBy("building_id")
    .agg(spark_sum("annual_saving_eur").alias("total_saving"))
    .join(bldg.select("building_id", "annual_total_cost"), on="building_id", how="left")
    .withColumn("pct_of_bill",
        spark_round(lit(100.0) * col("total_saving") / col("annual_total_cost"), 0))
    .orderBy(col("pct_of_bill").desc())
    .show(20, truncate=False)
)
log_step("✅ 06b complete — recommendations calibrated to total-energy cost")
