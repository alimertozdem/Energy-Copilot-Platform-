# =============================================================================
# NOTEBOOK: 15 — gold_battery_hourly_dispatch (Building-Specific Hourly Profiles)
# File    : 15_gold_battery_hourly_dispatch.py
# Date    : 2026-05-10
#
# PURPOSE:
#   Creates a building-specific 24-hour dispatch profile by combining:
#     a) Actual daily averages from gold_battery_dispatch (real per-building data)
#     b) Hourly distribution patterns from gold_battery_hourly_profile (notebook 13)
#
#   Result: gold_battery_hourly_dispatch
#   → Each row: one building × one strategy × one hour (0-23)
#   → Shows actual kWh values (not generic 0-1 rates)
#   → Has building_id column → building slicer works in Power BI
#   → Has strategy column → strategy tile slicer works
#
# WHY THIS IS BETTER THAN gold_battery_hourly_profile:
#   Old approach: 96 rows, generic 0-1 rates, no building context
#   New approach: building_id + actual kWh → energy manager sees
#                 "Hamburg discharges ~1,400 kWh during morning peak"
#                 vs "Berlin discharges ~80 kWh during morning peak"
#                 Same strategy pattern, scaled to real building capacity & usage
#
# DESIGN LOGIC:
#   Step 1: Compute avg daily charge_kwh and discharge_kwh per building per strategy
#           from gold_battery_dispatch (active strategy = real data)
#           For non-active strategies: scale from simulation savings ratios
#
#   Step 2: Read hourly distribution patterns from gold_battery_hourly_profile
#           (charge_rate and discharge_rate = fractional hourly distribution)
#
#   Step 3: Scale patterns by building's actual daily volumes:
#           charge_kwh[hour] = charge_rate[hour] / sum(charge_rate) × daily_charge_kwh
#           discharge_kwh[hour] = discharge_rate[hour] / sum(discharge_rate) × daily_discharge_kwh
#
#   Step 4: Estimate SoC curve from cumulative charge/discharge
#
# POWER BI INTEGRATION:
#   Relationship: gold_battery_hourly_dispatch[building_id]
#                 → silver_building_master[building_id]   (Many-to-One, Both direction)
#   Strategy slicer: gold_battery_hourly_dispatch[strategy_label] (dedicated tile)
#   Building slicer: S1 (same silver_building_master slicer as rest of page)
#   X-axis: hour_label (Sort by Column → hour_of_day)
#
# NEW DAX MEASURES (replace V6 measures — use these instead):
#   [V6 Charge kWh]    = AVERAGE(gold_battery_hourly_dispatch[charge_kwh])
#   [V6 Discharge kWh] = AVERAGE(gold_battery_hourly_dispatch[discharge_kwh])
#   [V6 SoC Pct]       = AVERAGE(gold_battery_hourly_dispatch[soc_percent])
#   [V6 Price Index]   = AVERAGE(gold_battery_hourly_dispatch[grid_price_index])
#
# Output table: gold_battery_hourly_dispatch
# Rows: 5 buildings × 4 strategies × 24 hours = 480 rows
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import pandas as pd

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.adaptive.enabled", "true")

print("=" * 70)
print("Notebook 15 — gold_battery_hourly_dispatch (building-specific)")
print("=" * 70)


# ─── STEP 1: LOAD SOURCE DATA ─────────────────────────────────────────────────

print("\n[1/5] Loading gold_battery_dispatch and gold_battery_hourly_profile...")

# Active strategy daily dispatch — real per-building data
df_dispatch = spark.table("gold_battery_dispatch")

# Reference hourly patterns (0-1 rates, 96 rows: 4 strategies × 24 hours)
df_hourly_ref = spark.table("gold_battery_hourly_profile")

# Simulation table — for non-active strategy savings ratios
df_sim = spark.table("gold_battery_simulation")

print(f"  dispatch rows     : {df_dispatch.count():,}")
print(f"  hourly_profile rows: {df_hourly_ref.count()}")
print(f"  simulation rows   : {df_sim.count()}")


# ─── STEP 2: COMPUTE DAILY AVERAGES PER BUILDING PER STRATEGY ────────────────

print("\n[2/5] Computing average daily charge/discharge per building per strategy...")

# Average daily volumes from actual dispatch (active strategy for each building)
df_daily_avg = (
    df_dispatch
    .groupBy("building_id", "building_name", "strategy")
    .agg(
        F.avg("charge_kwh").alias("avg_daily_charge_kwh"),
        F.avg("discharge_kwh").alias("avg_daily_discharge_kwh"),
        F.avg("soc_start_pct").alias("avg_soc_start"),
        F.avg("soc_end_pct").alias("avg_soc_end"),
        F.last("capacity_kwh").alias("battery_capacity_kwh"),
        F.count("date").alias("n_days"),
    )
    .filter(F.col("avg_daily_charge_kwh") > 0)
)

print("  Active strategy daily averages:")
df_daily_avg.select(
    "building_id", "strategy", "avg_daily_charge_kwh", "avg_daily_discharge_kwh"
).show(10, truncate=False)

# For each building, get all 4 strategies using simulation savings ratios
# Strategy multipliers relative to peak_shaving (from notebook 14 design)
# These scale the active strategy's volume to estimate alternative strategy volumes
STRATEGY_VOLUME_FACTORS = {
    # (active_strategy) → {target_strategy: volume_factor}
    # Volume scales with charge/discharge activity level, not just savings
    "peak_shaving":     {"peak_shaving": 1.00, "tou": 0.92, "self_consumption": 0.78, "backup": 0.22},
    "self_consumption": {"self_consumption": 1.00, "peak_shaving": 1.18, "tou": 1.08, "backup": 0.25},
    "tou":              {"tou": 1.00, "peak_shaving": 1.09, "self_consumption": 0.82, "backup": 0.24},
    "backup":           {"backup": 1.00, "peak_shaving": 3.20, "tou": 2.80, "self_consumption": 2.10},
}

ALL_STRATEGIES = ["peak_shaving", "self_consumption", "tou", "backup"]
STRATEGY_LABELS = {
    "peak_shaving":     "Peak-Shaving",
    "self_consumption": "Self-Consumption",
    "tou":              "Time-of-Use (ToU)",
    "backup":           "Backup + Opportunistic",
}

# Expand: for each building's active strategy row, create all 4 strategy rows
daily_rows = []
for row in df_daily_avg.collect():
    bid = row["building_id"]
    bname = row["building_name"]
    active_strat = row["strategy"]
    base_charge = row["avg_daily_charge_kwh"]
    base_discharge = row["avg_daily_discharge_kwh"]
    capacity = row["battery_capacity_kwh"] or 400.0
    avg_soc_start = row["avg_soc_start"] or 50.0

    factor_map = STRATEGY_VOLUME_FACTORS.get(active_strat, {})

    for strat in ALL_STRATEGIES:
        factor = factor_map.get(strat, 1.0)
        daily_rows.append({
            "building_id":            bid,
            "building_name":          bname,
            "strategy":               strat,
            "strategy_label":         STRATEGY_LABELS[strat],
            "active_strategy":        active_strat,
            "is_active_strategy":     str(strat == active_strat),
            "daily_charge_kwh":       round(base_charge * factor, 2),
            "daily_discharge_kwh":    round(base_discharge * factor, 2),
            "battery_capacity_kwh":   capacity,
            "avg_soc_start":          avg_soc_start,
        })

df_buildings_strategies = pd.DataFrame(daily_rows)
print(f"\n  Expanded to {len(df_buildings_strategies)} building×strategy combinations")
print(df_buildings_strategies[["building_id", "strategy", "daily_charge_kwh", "daily_discharge_kwh"]].to_string())


# ─── STEP 3: LOAD HOURLY PATTERNS AND COMPUTE SUM FOR NORMALIZATION ──────────

print("\n[3/5] Loading hourly rate patterns and normalizing...")

# Collect hourly reference profiles to pandas for computation
df_ref_pd = df_hourly_ref.select(
    "strategy", "hour_of_day", "hour_label",
    "charge_rate", "discharge_rate", "soc_percent",
    "grid_price_eur_mwh", "grid_price_index",
    "is_cheap_hour", "is_peak_price_hour"
).toPandas()

# Compute sum of rates per strategy (for normalization)
rate_sums = (
    df_ref_pd
    .groupby("strategy")
    .agg(
        sum_charge_rate=("charge_rate", "sum"),
        sum_discharge_rate=("discharge_rate", "sum"),
    )
    .reset_index()
)
df_ref_pd = df_ref_pd.merge(rate_sums, on="strategy")

print("  Rate sums per strategy:")
print(rate_sums.to_string(index=False))


# ─── STEP 4: SCALE PATTERNS TO BUILDING-SPECIFIC kWh VALUES ─────────────────

print("\n[4/5] Scaling hourly patterns to actual building kWh values...")

hourly_rows = []

for _, bldg in df_buildings_strategies.iterrows():
    bid          = bldg["building_id"]
    bname        = bldg["building_name"]
    strat        = bldg["strategy"]
    strat_label  = bldg["strategy_label"]
    is_active    = bldg["is_active_strategy"]
    daily_charge = bldg["daily_charge_kwh"]
    daily_disch  = bldg["daily_discharge_kwh"]
    capacity     = bldg["battery_capacity_kwh"]
    soc_start    = bldg["avg_soc_start"]

    # Get this strategy's reference pattern
    pattern = df_ref_pd[df_ref_pd["strategy"] == strat].copy()
    if pattern.empty:
        continue

    sum_c = pattern["sum_charge_rate"].iloc[0]
    sum_d = pattern["sum_discharge_rate"].iloc[0]

    # Scale: hourly_kwh = rate[hour] / sum(rates) × daily_total
    pattern = pattern.copy()
    pattern["charge_kwh"] = (
        pattern["charge_rate"] / max(sum_c, 0.001) * daily_charge
    ).round(2)
    pattern["discharge_kwh"] = (
        pattern["discharge_rate"] / max(sum_d, 0.001) * daily_disch
    ).round(2)

    # Estimate SoC: start from avg_soc_start, apply hourly charge/discharge
    # SoC changes: +charge × RTE − discharge (simplified, capacity-relative)
    rte = 0.945 if "LFP" in str(bldg.get("battery_type", "LFP")) else 0.900
    soc = soc_start
    soc_values = []
    for _, hr in pattern.sort_values("hour_of_day").iterrows():
        soc_values.append(round(soc, 1))
        delta = (hr["charge_kwh"] * rte - hr["discharge_kwh"]) / capacity * 100
        soc = max(5.0, min(100.0, soc + delta))

    pattern = pattern.sort_values("hour_of_day").copy()
    pattern["soc_percent"] = soc_values

    # Build output rows
    for i, hr_row in pattern.iterrows():
        hourly_rows.append({
            "building_id":          bid,
            "building_name":        bname,
            "strategy":             strat,
            "strategy_label":       strat_label,
            "is_active_strategy":   is_active,
            "hour_of_day":          int(hr_row["hour_of_day"]),
            "hour_label":           hr_row["hour_label"],
            "charge_kwh":           hr_row["charge_kwh"],
            "discharge_kwh":        hr_row["discharge_kwh"],
            "soc_percent":          hr_row["soc_percent"],
            "battery_capacity_kwh": capacity,
            "grid_price_eur_mwh":   hr_row["grid_price_eur_mwh"],
            "grid_price_index":     hr_row["grid_price_index"],
            "is_cheap_hour":        hr_row["is_cheap_hour"],
            "is_peak_price_hour":   hr_row["is_peak_price_hour"],
        })

pdf_hourly = pd.DataFrame(hourly_rows)
print(f"  Total hourly rows generated: {len(pdf_hourly)}")
print(f"  Buildings: {pdf_hourly['building_id'].nunique()}")
print(f"  Strategies: {pdf_hourly['strategy'].nunique()}")

# Quick sanity check: Hamburg peak_shaving should show much higher kWh than Berlin
sample = pdf_hourly[
    (pdf_hourly["strategy"] == "peak_shaving") &
    (pdf_hourly["hour_of_day"] == 9)
][["building_id", "building_name", "charge_kwh", "discharge_kwh", "soc_percent"]]
print("\n  Sanity check — Peak-Shaving at 09:00h per building:")
print(sample.to_string(index=False))


# ─── STEP 5: WRITE TO LAKEHOUSE ──────────────────────────────────────────────

print("\n[5/5] Writing gold_battery_hourly_dispatch to Lakehouse...")

schema = StructType([
    StructField("building_id",          StringType(),  False),
    StructField("building_name",        StringType(),  False),
    StructField("strategy",             StringType(),  False),
    StructField("strategy_label",       StringType(),  False),
    StructField("is_active_strategy",   StringType(),  False),
    StructField("hour_of_day",          IntegerType(), False),
    StructField("hour_label",           StringType(),  False),
    StructField("charge_kwh",           DoubleType(),  False),
    StructField("discharge_kwh",        DoubleType(),  False),
    StructField("soc_percent",          DoubleType(),  False),
    StructField("battery_capacity_kwh", DoubleType(),  False),
    StructField("grid_price_eur_mwh",   DoubleType(),  False),
    StructField("grid_price_index",     DoubleType(),  False),
    StructField("is_cheap_hour",        StringType(),  False),
    StructField("is_peak_price_hour",   StringType(),  False),
])

sdf = spark.createDataFrame(pdf_hourly, schema=schema)

sdf.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold_battery_hourly_dispatch")

print("  ✅ gold_battery_hourly_dispatch saved to Lakehouse")

# Verify
df_v = spark.table("gold_battery_hourly_dispatch")
print(f"\n  Row count: {df_v.count()}")

print("\n  Peak discharge hour per building (peak_shaving):")
df_v.filter("strategy = 'peak_shaving'") \
    .groupBy("building_id", "building_name") \
    .agg(
        F.round(F.max("discharge_kwh"), 1).alias("max_discharge_kwh"),
        F.round(F.sum("discharge_kwh"), 0).alias("total_daily_discharge_kwh"),
    ) \
    .orderBy("total_daily_discharge_kwh", ascending=False) \
    .show(truncate=False)

# =============================================================================
# AFTER RUNNING THIS NOTEBOOK:
#
# 1. Power BI Desktop → Home → Refresh
#    gold_battery_hourly_dispatch appears in the model
#
# 2. Model view: Add relationship
#    gold_battery_hourly_dispatch[building_id]
#    → silver_building_master[building_id]
#    Direction: Both  (so building S1 slicer filters the chart)
#
# 3. REPLACE the V6 chart:
#    Delete the old V6 combo chart (based on gold_battery_hourly_profile)
#    Insert new Line and Clustered Column Chart
#
#    X-axis : gold_battery_hourly_dispatch[hour_label]
#    Column Y: [V6 Charge kWh]      (blue  #00B4D8)
#    Column Y: [V6 Discharge kWh]   (amber #F4A261)
#    Line Y  : [V6 SoC Pct]         (green #2DC653)
#    Line Y  : [V6 Price Index]      (grey  #888888, dashed)
#    Legend  : EMPTY
#
# 4. Sort X-axis: Data view → hour_label → Sort by Column → hour_of_day
#
# 5. NEW DAX MEASURES (Modeling → New Measure):
#    [V6 Charge kWh]    = AVERAGE(gold_battery_hourly_dispatch[charge_kwh])
#    [V6 Discharge kWh] = AVERAGE(gold_battery_hourly_dispatch[discharge_kwh])
#    [V6 SoC Pct]       = AVERAGE(gold_battery_hourly_dispatch[soc_percent])
#    [V6 Price Index]   = AVERAGE(gold_battery_hourly_dispatch[grid_price_index])
#
# 6. SLICER: Change the tile slicer field from
#    gold_battery_hourly_profile[strategy_label]
#    TO: gold_battery_hourly_dispatch[strategy_label]
#
# 7. The old gold_battery_hourly_profile table can remain in the model
#    (unused) — or hide it via "Hide in report view"
#
# WHAT CHANGES FOR THE ENERGY MANAGER:
#   Old chart: "Peak-Shaving charges at 0.85 rate at 03:00"  ← meaningless
#   New chart: "Hamburg charges 1,120 kWh at 03:00" ← actionable
#              "Berlin charges 40 kWh at 03:00"      ← clear scale difference
#   Building slicer now works → switch from Hamburg to Frankfurt → kWh values update
# =============================================================================
