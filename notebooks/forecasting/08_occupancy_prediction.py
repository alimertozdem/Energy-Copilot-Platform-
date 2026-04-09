# Fabric Notebook — 08_occupancy_prediction
# ============================================================
# Phase 2 ML | Energy Copilot Platform
# ============================================================
# PURPOSE
#   Generates an hourly occupancy probability profile (0.0–1.0)
#   for each building, for each hour of each day-of-week (168
#   combinations per building = 7 days × 24 hours).
#
#   Output feeds into:
#   - after-hours waste detection (anomaly_detection.py)
#   - consumption forecasting as an occupancy regressor (07_consumption_forecast.py)
#
# APPROACH — Two-step hybrid
#   Step 1  Base Profile   : Rule-based archetype by building_type.
#                            Works even with zero historical data.
#   Step 2  Calibration    : Normalize actual hourly consumption from
#                            silver_energy_readings to a 0–1 signal,
#                            then blend with the base profile using a
#                            confidence-weighted average.
#                            Requires ≥ MIN_WEEKS_FOR_CALIBRATION weeks.
#
# OUTPUT TABLE : gold_occupancy_profile
#   (building_id, day_of_week, hour_of_day) → occupancy_probability
#
# INPUTS
#   silver_energy_readings  — hourly consumption with timestamp_utc
#   silver_building_master  — building_type, timezone_offset_hours
#
# SCHEDULE : runs after silver transformation, before gold KPI
#            (fits between Stage_2_Silver and Stage_3_Gold in orchestrator)
# ============================================================

# Cell 1 — Imports & Constants
# ============================================================

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType, TimestampType, BooleanType
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# ── Paths ────────────────────────────────────────────────────
LAKEHOUSE_ROOT = "abfss://energy-copilot@onelake.dfs.fabric.microsoft.com/EnergyLakehouse.Lakehouse/Tables"

PATHS = {
    "energy_readings" : f"{LAKEHOUSE_ROOT}/silver_energy_readings",
    "building"        : f"{LAKEHOUSE_ROOT}/silver_building_master",
    "occupancy"       : f"{LAKEHOUSE_ROOT}/gold_occupancy_profile",
}

# ── Tuning ───────────────────────────────────────────────────
LOOKBACK_DAYS            = 90   # how many days of readings to use for calibration
MIN_WEEKS_FOR_CALIBRATION = 2   # below this → base-profile-only, no blending
BLEND_WEIGHT_DATA        = 0.60  # weight for consumption-derived signal
BLEND_WEIGHT_BASE        = 0.40  # weight for rule-based base profile
MODEL_VERSION            = "v1.2.0"

# ── Logging helper ───────────────────────────────────────────
def log(msg: str):
    print(f"[08_occupancy] {datetime.now(timezone.utc).strftime('%H:%M:%S')} | {msg}")

# ── Graceful exit (mssparkutils / dbutils / SystemExit) ──────
def notebook_exit(message: str):
    print(f"\n⏹️  Notebook durduruluyor: {message}")
    try:
        mssparkutils.notebook.exit(message)
    except NameError:
        try:
            dbutils.notebook.exit(message)
        except NameError:
            raise SystemExit(message)

# ── Table existence check ────────────────────────────────────
def table_exists(path: str) -> bool:
    try:
        spark.read.format("delta").load(path).limit(0).count()
        return True
    except Exception:
        return False

log("Notebook başlatıldı — constants loaded.")


# Cell 2 — Base Occupancy Archetypes
# ============================================================
# Each archetype is a 168-element list indexed by:
#   day_of_week (0=Mon … 6=Sun) × hour_of_day (0–23)
# Values represent "typical fraction of maximum occupancy".
#
# Archetypes are derived from ASHRAE 90.1 standard occupancy
# schedules, adapted for European commercial buildings.

def build_base_profiles() -> pd.DataFrame:
    """
    Returns a DataFrame with columns:
        building_type, day_of_week, hour_of_day, base_probability
    covering all 7 × 24 = 168 rows per building_type.
    """

    # ── Hour-of-day profiles (weekday vs weekend) ─────────────
    # Shape: (24,) float array, values 0.0–1.0

    def _office_weekday():
        h = np.zeros(24)
        h[7]  = 0.30   # arrival
        h[8]  = 0.65
        h[9]  = 0.90
        h[10] = 0.95
        h[11] = 0.95
        h[12] = 0.75   # lunch dip
        h[13] = 0.80
        h[14] = 0.90
        h[15] = 0.90
        h[16] = 0.85
        h[17] = 0.65
        h[18] = 0.35
        h[19] = 0.10
        return h

    def _retail_weekday():
        h = np.zeros(24)
        h[9]  = 0.20
        h[10] = 0.50
        h[11] = 0.70
        h[12] = 0.85
        h[13] = 0.85
        h[14] = 0.75
        h[15] = 0.75
        h[16] = 0.80
        h[17] = 0.85
        h[18] = 0.70
        h[19] = 0.40
        h[20] = 0.20
        return h

    def _retail_weekend():
        h = np.zeros(24)
        h[10] = 0.40
        h[11] = 0.70
        h[12] = 0.90
        h[13] = 0.90
        h[14] = 0.85
        h[15] = 0.80
        h[16] = 0.75
        h[17] = 0.60
        h[18] = 0.30
        return h

    def _hotel_weekday():
        # Hotels are occupied 24 h but peak at night (guests) and daytime (check-in/out)
        h = np.full(24, 0.50)   # baseline: always some guests
        for hh in range(0, 6):
            h[hh] = 0.80        # peak night occupancy
        h[6]  = 0.70
        h[7]  = 0.60
        h[8]  = 0.55
        h[9]  = 0.45
        h[14] = 0.65            # check-in wave
        h[15] = 0.70
        h[22] = 0.75
        h[23] = 0.80
        return h

    def _residential_weekday():
        h = np.zeros(24)
        # Morning peak (wake up) + evening peak (return home)
        for hh in range(0, 7):
            h[hh] = 0.90        # sleeping
        h[7]  = 0.75
        h[8]  = 0.40
        h[9]  = 0.25
        for hh in range(10, 17):
            h[hh] = 0.20        # daytime mostly empty
        h[17] = 0.40
        h[18] = 0.65
        h[19] = 0.80
        h[20] = 0.85
        h[21] = 0.85
        h[22] = 0.80
        h[23] = 0.90
        return h

    def _residential_weekend():
        h = np.zeros(24)
        for hh in range(0, 9):
            h[hh] = 0.90        # sleep in
        for hh in range(9, 23):
            h[hh] = 0.70        # home / leisure
        h[23] = 0.85
        return h

    def _industrial_weekday():
        h = np.zeros(24)
        # Two-shift operation typical for light industry
        for hh in range(6, 14):   # first shift
            h[hh] = 0.90
        for hh in range(14, 22):  # second shift
            h[hh] = 0.70
        return h

    def _generic_weekday():
        h = np.zeros(24)
        for hh in range(8, 18):
            h[hh] = 0.70
        return h

    # ── Assemble per-type schedule (7 days × 24 hours) ────────
    archetypes = {
        "office"      : [_office_weekday()   if d < 5 else np.zeros(24) for d in range(7)],
        "retail"      : [_retail_weekday()   if d < 5 else _retail_weekend() for d in range(7)],
        "hotel"       : [_hotel_weekday()    for _ in range(7)],        # hotels don't close
        "residential" : [_residential_weekday() if d < 5 else _residential_weekend() for d in range(7)],
        "industrial"  : [_industrial_weekday() if d < 5 else np.zeros(24) for d in range(7)],
        "mixed_use"   : None,  # will be handled as 0.5×office + 0.5×retail
        "warehouse"   : [_industrial_weekday() if d < 5 else np.zeros(24) for d in range(7)],
        "other"       : [_generic_weekday()  if d < 5 else np.zeros(24) for d in range(7)],
    }

    # mixed_use = blend of office + retail
    archetypes["mixed_use"] = [
        (archetypes["office"][d] * 0.5 + archetypes["retail"][d] * 0.5)
        for d in range(7)
    ]

    # ── Flatten to DataFrame ───────────────────────────────────
    rows = []
    for btype, weekly in archetypes.items():
        for day in range(7):
            for hour in range(24):
                rows.append({
                    "building_type"    : btype,
                    "day_of_week"      : day,
                    "hour_of_day"      : hour,
                    "base_probability" : float(np.clip(weekly[day][hour], 0.0, 1.0)),
                })

    return pd.DataFrame(rows)


log("Base archetypes definition loaded.")


# Cell 3 — Load Input Data
# ============================================================

# Guard: silver_energy_readings must exist
if not table_exists(PATHS["energy_readings"]):
    notebook_exit("silver_energy_readings tablosu bulunamadı. Silver transformation önce çalışmalı.")

if not table_exists(PATHS["building"]):
    notebook_exit("silver_building_master tablosu bulunamadı. Silver transformation önce çalışmalı.")

log("Reading silver_building_master …")
df_building = (
    spark.read.format("delta").load(PATHS["building"])
    .select(
        "building_id",
        "building_type",
        F.coalesce(F.col("timezone_offset_hours"), F.lit(0)).alias("tz_offset"),
    )
)
building_count = df_building.count()
log(f"  → {building_count} buildings loaded.")

if building_count == 0:
    notebook_exit("silver_building_master boş — önce reference data ve silver transformation çalışmalı.")

log(f"Reading silver_energy_readings (last {LOOKBACK_DAYS} days) …")
cutoff_ts = F.date_sub(F.current_date(), LOOKBACK_DAYS)

df_readings = (
    spark.read.format("delta").load(PATHS["energy_readings"])
    .filter(F.col("date") >= cutoff_ts)
    .select(
        "building_id",
        "timestamp_utc",
        "consumption_kwh",
    )
    .filter(F.col("consumption_kwh").isNotNull())
    .filter(F.col("consumption_kwh") >= 0)
)

reading_count = df_readings.count()
log(f"  → {reading_count:,} readings loaded.")


# Cell 4 — Derive Local Hour and Day-of-Week from Readings
# ============================================================
# silver_energy_readings stores timestamp_utc (UTC).
# We convert to local time using building's timezone_offset_hours
# so that "08:00 office arrival" maps correctly regardless of country.

log("Computing local hour/day from UTC timestamps …")

df_readings_local = (
    df_readings
    .join(F.broadcast(df_building.select("building_id", "tz_offset")), "building_id", "left")
    .withColumn(
        "local_ts",
        # Add timezone offset in hours; Fabric/Spark supports expr arithmetic on timestamps
        (F.col("timestamp_utc").cast("long") + F.col("tz_offset") * 3600).cast("timestamp")
    )
    .withColumn("hour_of_day",  F.hour("local_ts"))
    .withColumn("day_of_week",  F.dayofweek("local_ts") - 2)  # Spark: 1=Sun, convert to 0=Mon
    # day_of_week fix: Spark dayofweek → 1=Sun … 7=Sat → remap to 0=Mon … 6=Sun
    .withColumn(
        "day_of_week",
        F.when(F.col("day_of_week") < 0, 6).otherwise(F.col("day_of_week"))
    )
    .withColumn("week_number", F.weekofyear("local_ts"))
    .withColumn("year_number",  F.year("local_ts"))
    .select("building_id", "hour_of_day", "day_of_week", "week_number", "year_number", "consumption_kwh")
)

log("Local time derivation complete.")


# Cell 5 — Compute Consumption-Derived Occupancy Signal
# ============================================================
# For each building, aggregate mean consumption by (day_of_week, hour_of_day).
# Normalize to [0, 1] using per-building min-max.
# This raw signal is a proxy for occupancy — high consumption = high occupancy.
#
# We also compute:
#   - distinct_weeks: how many different weeks of data we have
#   - used for confidence scoring and blend weighting

log("Aggregating hourly consumption signal per building …")

df_hourly_agg = (
    df_readings_local
    .groupBy("building_id", "day_of_week", "hour_of_day")
    .agg(
        F.mean("consumption_kwh").alias("mean_kwh"),
        F.countDistinct(
            F.concat_ws("-", F.col("year_number"), F.col("week_number"))
        ).alias("distinct_weeks"),
    )
)

# Per-building min / max for normalization
window_bldg = Window.partitionBy("building_id")

df_normalized = (
    df_hourly_agg
    .withColumn("bldg_min_kwh", F.min("mean_kwh").over(window_bldg))
    .withColumn("bldg_max_kwh", F.max("mean_kwh").over(window_bldg))
    .withColumn(
        "consumption_signal",
        F.when(
            (F.col("bldg_max_kwh") - F.col("bldg_min_kwh")) > 0,
            (F.col("mean_kwh") - F.col("bldg_min_kwh")) /
            (F.col("bldg_max_kwh") - F.col("bldg_min_kwh"))
        ).otherwise(0.5)   # flat profile → neutral occupancy
    )
    .withColumn(
        "consumption_signal",
        F.greatest(F.lit(0.0), F.least(F.lit(1.0), F.col("consumption_signal")))  # clip [0,1]
    )
)

log("Normalization complete.")


# Cell 6 — Load and Broadcast Base Profiles
# ============================================================

log("Building base archetype profiles …")

base_profiles_pd = build_base_profiles()
base_profiles_spark = spark.createDataFrame(base_profiles_pd)

log(f"  → {base_profiles_pd['building_type'].nunique()} archetypes × 168 slots = {len(base_profiles_pd)} rows.")

# Join building_type onto each reading-derived row
df_with_base = (
    df_normalized
    .join(F.broadcast(df_building.select("building_id", "building_type")), "building_id", "left")
    # Normalize building_type: lowercase, replace spaces/hyphens, fallback to "other"
    .withColumn(
        "building_type_norm",
        F.lower(F.regexp_replace(F.col("building_type"), r"[ \-]", "_"))
    )
    .withColumn(
        "building_type_norm",
        F.when(F.col("building_type_norm").isin(
            "office", "retail", "hotel", "residential",
            "industrial", "mixed_use", "warehouse"
        ), F.col("building_type_norm")).otherwise(F.lit("other"))
    )
    .join(
        F.broadcast(base_profiles_spark.withColumnRenamed("building_type", "building_type_norm")),
        on=["building_type_norm", "day_of_week", "hour_of_day"],
        how="left"
    )
    .withColumn("base_probability", F.coalesce(F.col("base_probability"), F.lit(0.5)))
)

log("Base profiles joined.")


# Cell 7 — Blend: Data Signal + Base Profile
# ============================================================
# For each (building_id, day_of_week, hour_of_day):
#
#   If distinct_weeks >= MIN_WEEKS_FOR_CALIBRATION:
#       occupancy_probability = BLEND_WEIGHT_DATA × consumption_signal
#                             + BLEND_WEIGHT_BASE × base_probability
#       profile_source = 'calibrated'
#       confidence_score = min(distinct_weeks / 12, 1.0)
#   Else:
#       occupancy_probability = base_probability
#       profile_source = 'base_only'
#       confidence_score = 0.0

log("Blending data signal with base profiles …")

df_blended = (
    df_with_base
    .withColumn(
        "has_enough_data",
        F.col("distinct_weeks") >= MIN_WEEKS_FOR_CALIBRATION
    )
    .withColumn(
        "occupancy_probability",
        F.when(
            F.col("has_enough_data"),
            F.col("consumption_signal") * BLEND_WEIGHT_DATA +
            F.col("base_probability")   * BLEND_WEIGHT_BASE
        ).otherwise(F.col("base_probability"))
    )
    .withColumn(
        "occupancy_probability",
        F.greatest(F.lit(0.0), F.least(F.lit(1.0), F.col("occupancy_probability")))
    )
    .withColumn(
        "profile_source",
        F.when(F.col("has_enough_data"), F.lit("calibrated")).otherwise(F.lit("base_only"))
    )
    .withColumn(
        "confidence_score",
        F.when(
            F.col("has_enough_data"),
            F.least(F.lit(1.0), F.col("distinct_weeks") / F.lit(12.0))
        ).otherwise(F.lit(0.0))
    )
    .withColumn("model_version",   F.lit(MODEL_VERSION))
    .withColumn("computed_at",     F.current_timestamp())
    .select(
        "building_id",
        "day_of_week",
        "hour_of_day",
        "occupancy_probability",
        "profile_source",
        F.col("distinct_weeks").alias("calibration_weeks"),
        "confidence_score",
        "model_version",
        "computed_at",
    )
)

log("Blending complete.")


# Cell 8 — Buildings with No Readings → Use Base Profile Only
# ============================================================
# Some buildings may have no readings in the lookback window
# (e.g. newly onboarded). We still generate a 168-row profile
# for them using their base archetype.

log("Checking for buildings with no readings in lookback window …")

buildings_with_data = df_blended.select("building_id").distinct()
buildings_all       = df_building.select("building_id", "building_type")

buildings_no_data = (
    buildings_all
    .join(buildings_with_data, "building_id", "left_anti")
)

no_data_count = buildings_no_data.count()
log(f"  → {no_data_count} buildings have no readings → applying base-only profile.")

if no_data_count > 0:
    # Cross-join with full 7×24 grid
    hour_grid = spark.range(24).withColumnRenamed("id", "hour_of_day")
    day_grid  = spark.range(7).withColumnRenamed("id", "day_of_week")
    full_grid = day_grid.crossJoin(hour_grid)

    df_no_data_buildings = (
        buildings_no_data
        .crossJoin(full_grid)
        .withColumn(
            "building_type_norm",
            F.lower(F.regexp_replace(F.col("building_type"), r"[ \-]", "_"))
        )
        .withColumn(
            "building_type_norm",
            F.when(F.col("building_type_norm").isin(
                "office", "retail", "hotel", "residential",
                "industrial", "mixed_use", "warehouse"
            ), F.col("building_type_norm")).otherwise(F.lit("other"))
        )
        .join(
            F.broadcast(base_profiles_spark.withColumnRenamed("building_type", "building_type_norm")),
            on=["building_type_norm", "day_of_week", "hour_of_day"],
            how="left"
        )
        .withColumn("base_probability", F.coalesce(F.col("base_probability"), F.lit(0.5)))
        .withColumn("occupancy_probability", F.col("base_probability"))
        .withColumn("profile_source",       F.lit("base_only"))
        .withColumn("calibration_weeks",    F.lit(0))
        .withColumn("confidence_score",     F.lit(0.0))
        .withColumn("model_version",        F.lit(MODEL_VERSION))
        .withColumn("computed_at",          F.current_timestamp())
        .select(
            "building_id",
            F.col("day_of_week").cast("integer"),
            F.col("hour_of_day").cast("integer"),
            F.col("occupancy_probability").cast("double"),
            "profile_source",
            F.col("calibration_weeks").cast("integer"),
            F.col("confidence_score").cast("double"),
            "model_version",
            "computed_at",
        )
    )

    # Union with main blended result
    df_final = df_blended.unionByName(df_no_data_buildings)
    log(f"  → Base-only profiles added for {no_data_count} buildings.")
else:
    df_final = df_blended

log(f"Final profile count: {df_final.count():,} rows (expect {building_count * 168} = {building_count} buildings × 168 slots).")


# Cell 9 — Write to gold_occupancy_profile (Delta MERGE)
# ============================================================
# Merge key: (building_id, day_of_week, hour_of_day)
# On match: update all analytics columns
# On not matched: insert new row
# Each pipeline run refreshes the full 168-row profile per building.

log("Writing to gold_occupancy_profile …")

OUTPUT_SCHEMA = StructType([
    StructField("building_id",          StringType(),  False),
    StructField("day_of_week",          IntegerType(), False),
    StructField("hour_of_day",          IntegerType(), False),
    StructField("occupancy_probability", DoubleType(), True),
    StructField("profile_source",       StringType(),  True),
    StructField("calibration_weeks",    IntegerType(), True),
    StructField("confidence_score",     DoubleType(),  True),
    StructField("model_version",        StringType(),  True),
    StructField("computed_at",          TimestampType(), True),
])

df_final_typed = spark.createDataFrame(df_final.rdd, schema=OUTPUT_SCHEMA)

if table_exists(PATHS["occupancy"]):
    log("  Table exists — performing MERGE …")
    delta_table = DeltaTable.forPath(spark, PATHS["occupancy"])

    (
        delta_table.alias("target")
        .merge(
            df_final_typed.alias("source"),
            "target.building_id = source.building_id AND "
            "target.day_of_week  = source.day_of_week  AND "
            "target.hour_of_day  = source.hour_of_day"
        )
        .whenMatchedUpdate(set={
            "occupancy_probability" : "source.occupancy_probability",
            "profile_source"        : "source.profile_source",
            "calibration_weeks"     : "source.calibration_weeks",
            "confidence_score"      : "source.confidence_score",
            "model_version"         : "source.model_version",
            "computed_at"           : "source.computed_at",
        })
        .whenNotMatchedInsertAll()
        .execute()
    )
    log("  MERGE complete.")

else:
    log("  Table does not exist — creating with initial write …")
    (
        df_final_typed
        .write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .partitionBy("day_of_week")
        .save(PATHS["occupancy"])
    )
    log("  Initial write complete (partitioned by day_of_week).")


# Cell 10 — Optimize & Z-Order
# ============================================================
log("Running OPTIMIZE + ZORDER on gold_occupancy_profile …")

spark.sql(f"""
    OPTIMIZE delta.`{PATHS["occupancy"]}`
    ZORDER BY (building_id, hour_of_day)
""")

log("OPTIMIZE complete.")


# Cell 11 — Validation & Summary Report
# ============================================================
log("=== Validation Report ===")

df_check = spark.read.format("delta").load(PATHS["occupancy"])

total_rows     = df_check.count()
total_buildings = df_check.select("building_id").distinct().count()
expected_rows   = total_buildings * 168

log(f"  Total rows      : {total_rows:,}")
log(f"  Total buildings : {total_buildings}")
log(f"  Expected rows   : {expected_rows:,}  (buildings × 7 days × 24 hours)")
log(f"  Row check OK    : {total_rows == expected_rows}")

# Profile source distribution
log("\n  Profile source distribution:")
(
    df_check
    .groupBy("profile_source")
    .agg(
        F.count("*").alias("rows"),
        F.countDistinct("building_id").alias("buildings"),
        F.round(F.mean("confidence_score"), 3).alias("avg_confidence"),
    )
    .show(truncate=False)
)

# Sample: peak occupancy hours per building type (calibrated buildings only)
log("  Sample: average peak occupancy by building_type + hour (calibrated only):")
(
    df_check
    .filter(F.col("profile_source") == "calibrated")
    .join(F.broadcast(df_building.select("building_id", "building_type")), "building_id", "left")
    .groupBy("building_type", "hour_of_day")
    .agg(F.round(F.mean("occupancy_probability"), 3).alias("avg_occ"))
    .orderBy("building_type", "hour_of_day")
    .show(48, truncate=False)
)

# Check for null occupancy values
null_count = df_check.filter(F.col("occupancy_probability").isNull()).count()
log(f"\n  Null occupancy_probability rows: {null_count} (expect 0)")

# Check value range
range_check = df_check.agg(
    F.min("occupancy_probability").alias("min_occ"),
    F.max("occupancy_probability").alias("max_occ"),
).collect()[0]
log(f"  Occupancy range : [{range_check['min_occ']:.3f}, {range_check['max_occ']:.3f}] (expect [0.0, 1.0])")


# Cell 12 — Notebook Exit
# ============================================================
summary_msg = (
    f"08_occupancy_prediction OK — "
    f"{total_buildings} buildings, "
    f"{total_rows:,} profile rows, "
    f"rows_match={total_rows == expected_rows}, "
    f"nulls={null_count}, "
    f"range=[{range_check['min_occ']:.2f},{range_check['max_occ']:.2f}]"
)

log(summary_msg)
notebook_exit(summary_msg)
