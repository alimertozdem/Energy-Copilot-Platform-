# =============================================================================
# 21b_fix_B011_building_master.py — Residential G2.1 (FLAT, paste-safe, TEK HÜCRE)
# -----------------------------------------------------------------------------
# WHY: 21_residential_ingestion seeds B011 into silver_building_master with only
# 7 fields; every boolean flag (has_heat_pump / has_pv / has_battery /
# has_led_lighting / iso50001_certified) is left NULL. In Spark,
# `col("has_heat_pump") == False` is NULL for a NULL cell, so the row is DROPPED
# by the recommendation filters → INSTALL_HEAT_PUMP / DEEP_RETROFIT / SOLAR / LED
# never fire for B011 and the Landlord investment case cannot reconcile with
# docs/strategy/residential-retrofit-calculations.md.
#
# FIX: surgically set the flags + a few attributes on the B011 row ONLY
# (whenMatchedUpdate). Idempotent, paste-safe, touches no other building.
# Mirrors the 00b_add_B011_sim_input.py pattern.
#
# ENERGY ASSUMPTIONS (Mert-approved 2026-06-12, screening-grade):
#   has_heat_pump=False, has_pv=False, has_battery=False  -> 1970s gas MFH, no DER
#   has_led_lighting=False, iso50001_certified=False, has_ev_charging=False
#   epc_class='E'  -> ~156 kWh/m2.yr computed EUI ≈ German final-energy band E
#                     (<160); triggers MEPS stranding (D-G). cf. calc doc "EPC ~E/F".
#   roof_area_m2=600.0  -> footprint ≈ conditioned_area/num_floors (2400/4); usable
#                          fraction applied downstream in 06 INSTALL_SOLAR sizing.
#   emission_factor_kg_kwh=0.363 -> DE grid 2024 (UBA), used for HP/solar CO2.
#   pv_capacity_kwp=0.0, battery_capacity_kwh=0.0 -> keep downstream null-math clean.
#
# Schema-safe: only columns that actually exist in silver_building_master are
# applied (others printed + skipped). Run order after this: 04 -> 05 -> 06.
# =============================================================================
from delta.tables import DeltaTable
from pyspark.sql import Row
import pyspark.sql.functions as F

NAME = "silver_building_master"
BID = "B011"


def _delta():
    # schema-enabled lakehouse: catalog first, then Tables/dbo, then Tables/
    try:
        return DeltaTable.forName(spark, NAME)
    except Exception:
        for p in (f"Tables/dbo/{NAME}", f"Tables/{NAME}"):
            try:
                return DeltaTable.forPath(spark, p)
            except Exception:
                continue
    raise Exception(NAME + " not found (catalog/Tables path) — run 02_silver + 21 first")


dt = _delta()
tgt = dt.toDF()
cols = set(tgt.columns)

# Desired flags/attributes for B011 (only those present in schema are applied).
desired = {
    "year_built": 1973,
    "has_heat_pump": False,
    "has_pv": False,
    "has_battery": False,
    "has_led_lighting": False,
    "iso50001_certified": False,
    "has_ev_charging": False,
    "epc_class": "E",
    "roof_area_m2": 600.0,
    "emission_factor_kg_kwh": 0.363,
    "pv_capacity_kwp": 0.0,
    "battery_capacity_kwh": 0.0,
}
applied = {k: v for k, v in desired.items() if k in cols}
skipped = [k for k in desired if k not in cols]
print("→ applying to B011:", applied)
if skipped:
    print("⚠️  skipped (not in silver_building_master schema):", skipped)

# Build a one-row patch aligned to the full target schema (PK + applied cols set,
# everything else NULL so it never overwrites untouched columns on update).
payload = {"building_id": BID, **applied}
row_df = spark.createDataFrame([Row(**payload)])
for c in tgt.columns:
    if c not in row_df.columns:
        row_df = row_df.withColumn(c, F.lit(None))
row_df = row_df.select([F.col(c).cast(tgt.schema[c].dataType).alias(c) for c in tgt.columns])

# MERGE: update ONLY the applied columns on the matching B011 row.
update_map = {c: F.col(f"s.{c}") for c in applied}
(dt.alias("t")
   .merge(row_df.alias("s"), "t.building_id = s.building_id")
   .whenMatchedUpdate(set=update_map)
   .execute())

out = _delta().toDF().where(F.col("building_id") == BID)
print("✅ B011 rows in", NAME, ":", out.count())
show_cols = ["building_id"] + list(applied.keys())
out.select(*[c for c in show_cols if c in out.columns]).show(truncate=False)
print("Next: re-run 04_simulation_engine → 05_compliance_checker → 06_recommendation_engine")
