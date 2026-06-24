# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 09b_ghg_gas_correction.py
# Layer: GOLD — Scope-1 gas correction (Path A)
# Created: 2026-06-19
# =============================================================================
#
# PURPOSE
#   Stage 2 of the GHG engine. Runs AFTER 09_ghg_scope_engine.
#   Replaces the Scope-1 gas PROXY (heating = flat 25% of electricity) with the
#   physics-based gas_fuel_kwh from gold_energy_ledger (03b degree-day model), then
#   recomputes scope1_total and total_ghg_location/market. Idempotent Delta MERGE.
#
#   Why a separate notebook: 09 is large + multi-cell. This avoids surgical edits —
#   paste in one clean cell, run after 09 (and after 03b). Same pattern as 06b.
#
#   Re-run order: 03b → 09 → 09b.  Design: docs/strategy/total-energy-ledger.md
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, coalesce, round as R, sum as S, max as SMAX
from delta.tables import DeltaTable

spark = SparkSession.builder.getOrCreate()

# Canonical natural-gas emission factor (DEFRA, matches 09 / ref_fuel_factors). [Kesin]
GAS_EF_KG_PER_KWH = 0.201
GHG_TABLE    = "gold_ghg_scope"
LEDGER_TABLE = "gold_energy_ledger"


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


ghg = read_delta(GHG_TABLE)
led = (
    read_delta(LEDGER_TABLE)
    .select(
        col("building_id").alias("_lb"),
        col("year").alias("_ly"),
        col("month").alias("_lm"),
        col("gas_fuel_kwh").alias("_gfk"),
    )
)

# Join ledger fuel onto the monthly GHG grain (building × reporting_year × reporting_month)
upd = (
    ghg.join(
        led,
        (col("building_id") == col("_lb"))
        & (col("reporting_year") == col("_ly"))
        & (col("reporting_month") == col("_lm")),
        "left",
    )
    # Scope-1 gas = real fuel kWh × EF (tonnes). Non-gas/absent rows → 0 fuel → 0.
    .withColumn("_gas",
        R(coalesce(col("_gfk"), lit(0.0)) * lit(GAS_EF_KG_PER_KWH) / lit(1000.0), 4))
    .withColumn("_s1",
        R(col("_gas")
          + coalesce(col("scope1_diesel_tco2"), lit(0.0))
          + coalesce(col("scope1_refrigerant_tco2"), lit(0.0)), 4))
    .withColumn("_loc",
        R(col("_s1")
          + coalesce(col("scope2_location_tco2"), lit(0.0))
          + coalesce(col("scope3_estimated_tco2"), lit(0.0)), 4))
    .withColumn("_mkt",
        R(col("_s1")
          + coalesce(col("scope2_market_tco2"), lit(0.0))
          + coalesce(col("scope3_estimated_tco2"), lit(0.0)), 4))
    .select(
        "building_id", "year_month",
        col("_gas").alias("scope1_gas_tco2"),
        col("_s1").alias("scope1_total_tco2"),
        col("_loc").alias("total_ghg_location_tco2"),
        col("_mkt").alias("total_ghg_market_tco2"),
    )
).cache()
_n = upd.count()
print(f"[09b] gas-corrected rows: {_n:,}")

tgt = DeltaTable.forName(spark, GHG_TABLE)
(tgt.alias("t")
    .merge(upd.alias("s"), "t.building_id = s.building_id AND t.year_month = s.year_month")
    .whenMatchedUpdate(set={
        "scope1_gas_tco2":         "s.scope1_gas_tco2",
        "scope1_total_tco2":       "s.scope1_total_tco2",
        "total_ghg_location_tco2": "s.total_ghg_location_tco2",
        "total_ghg_market_tco2":   "s.total_ghg_market_tco2",
    })
    .execute())
print("[09b] ✅ MERGE done — Scope-1 gas now from real degree-day fuel (gold_energy_ledger)")

# ── SANITY: annual Scope-1 gas (tCO2) by building, trailing 12 months ──
g2 = read_delta(GHG_TABLE).withColumn("_ym", col("reporting_year")*12 + col("reporting_month"))
_mx = g2.agg(SMAX("_ym")).first()[0]
print("\n── Annual Scope-1 gas (tCO2), trailing 12 months ──")
(
    g2.filter((col("_ym") > _mx - 12) & (col("_ym") <= _mx))
    .groupBy("building_id")
    .agg(R(S("scope1_gas_tco2"), 1).alias("scope1_gas_tco2_yr"))
    .orderBy(col("scope1_gas_tco2_yr").desc())
    .show(20, truncate=False)
)
print("[09b] ✅ complete")
