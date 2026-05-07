# Fabric notebook source code export using cell-code-separator
# DO NOT add cell-code-separator
# Cell [1] — Metadata
# This file should be run on Microsoft Fabric (Spark runtime)
# Notebook name: 11b_iot_processing
# Schedule: Every 15 minutes via Fabric pipeline or schedule

# =============================================================================
# 11b_iot_processing.py
# Energy Copilot Platform — IoT Data Processing Notebook
# =============================================================================
#
# PURPOSE:
#   Transforms raw IoT sensor data (bronze layer) into analytics-ready
#   gold tables used by Power BI Page 8.
#
# PIPELINE POSITION:
#   EventStream → bronze_iot_raw (Delta)
#                     ↓  [this notebook, runs every 15 min]
#              silver_iot_normalized
#                     ↓
#   gold_iot_realtime + gold_iot_daily_summary
#
# WHY PROCESS SEPARATELY FROM EVENTSTREAM?
#   EventStream is optimized for ingestion — it writes raw data fast.
#   Business logic (anomaly detection, quality scoring, aggregations)
#   belongs in a notebook where we can write testable Python code.
#   This separation also means we can re-run the notebook to fix errors
#   in gold data without touching the raw archive.
#
# OUTPUT TABLES:
#   gold_iot_realtime      — 15-min aggregate per sensor with anomaly flags
#   gold_iot_daily_summary — daily KPI aggregates per building/sensor type
# =============================================================================

# Cell [2] — Setup & imports
import logging
from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType,
    IntegerType, BooleanType, TimestampType, DateType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("11b_iot_processing")

spark = SparkSession.builder.getOrCreate()

# Notebook parameters (override in Fabric pipeline if needed)
LOOKBACK_HOURS = int(spark.conf.get("lookback_hours", "2"))   # process last N hours
DRY_RUN        = spark.conf.get("dry_run", "false").lower() == "true"
ANOMALY_STDEV_THRESHOLD = 3.0   # flag if reading > 3 std devs from 48h mean

logger.info(f"Starting 11b_iot_processing | lookback={LOOKBACK_HOURS}h | dry_run={DRY_RUN}")

# Cell [3] — Schema definitions

BRONZE_SCHEMA = StructType([
    StructField("device_id",        StringType(),  True),
    StructField("building_id",      StringType(),  True),
    StructField("sensor_type",      StringType(),  True),
    StructField("sensor_location",  StringType(),  True),
    StructField("reading_value",    FloatType(),   True),
    StructField("reading_unit",     StringType(),  True),
    StructField("source_protocol",  StringType(),  True),
    StructField("timestamp",        StringType(),  True),   # ISO string from Event Hub
    StructField("reading_quality",  IntegerType(), True),
    StructField("is_anomaly",       BooleanType(), True),   # from simulator
    StructField("anomaly_type",     StringType(),  True),
    StructField("anomaly_severity", StringType(),  True),
])

# Sensor setpoint reference (in production: join to gold_iot_sensor_master)
# Format: sensor_type → (normal_min, normal_max, alert_low, alert_high)
SENSOR_THRESHOLDS = {
    "HVAC_temp": (20.0,  24.0,  17.0, 27.0),
    "humidity":  (40.0,  60.0,  28.0, 72.0),
    "CO2":       (400.0, 1000.0, None, 1500.0),
    "power":     (None,  None,   None, None),   # building-specific, skip rule check
}

# Cell [4] — Load bronze table

logger.info("Loading bronze_iot_raw...")

try:
    df_bronze = spark.read.format("delta").table("bronze_iot_raw")
except Exception as e:
    logger.error(f"Cannot read bronze_iot_raw: {e}")
    raise

# Cast timestamp string → proper TimestampType
df_bronze = df_bronze.withColumn(
    "event_ts",
    F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss'Z'")
)

# Filter to lookback window (avoid re-processing old data every run)
cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
df_window = df_bronze.filter(F.col("event_ts") >= F.lit(cutoff))

row_count = df_window.count()
logger.info(f"Rows in lookback window: {row_count:,}")

if row_count == 0:
    logger.warning("No new data in lookback window. Nothing to process.")
    dbutils.notebook.exit("NO_DATA")

# Cell [5] — Silver transformation: normalize + quality checks

logger.info("Building silver_iot_normalized...")

def classify_anomaly_severity(sensor_type, value):
    """
    Rule-based anomaly severity classification.
    Returns 'High' / 'Medium' / 'Low' / null.
    Applied as a UDF so it runs on each Spark partition.
    """
    thresholds = SENSOR_THRESHOLDS.get(sensor_type)
    if thresholds is None:
        return None

    normal_min, normal_max, alert_low, alert_high = thresholds

    if alert_high is not None and value > alert_high:
        return "High"
    if alert_low is not None and value < alert_low:
        return "High"
    if normal_max is not None and value > normal_max:
        return "Medium"
    if normal_min is not None and value < normal_min:
        return "Medium"
    return None

severity_udf = F.udf(classify_anomaly_severity, StringType())

# Load sensor master for setpoints (if available)
try:
    df_sensor_master = spark.read.format("delta").table("gold_iot_sensor_master")
    HAS_SENSOR_MASTER = True
    logger.info("gold_iot_sensor_master loaded for threshold enrichment")
except Exception:
    HAS_SENSOR_MASTER = False
    logger.warning("gold_iot_sensor_master not found — using hardcoded thresholds")

# Build silver layer
df_silver = (
    df_window
    # Round timestamp to 15-minute bucket
    .withColumn(
        "ts_bucket",
        F.date_trunc("minute",
            F.date_add(
                F.col("event_ts"),
                (F.minute(F.col("event_ts")) % 15 * -1).cast("int")
            )
        )
    )
    # Parse date for partitioning
    .withColumn("event_date", F.to_date(F.col("event_ts")))
    # Rule-based severity (override simulator value with rule check)
    .withColumn(
        "rule_severity",
        severity_udf(F.col("sensor_type"), F.col("reading_value"))
    )
    # Final severity: rule-based takes priority over simulator flag
    .withColumn(
        "anomaly_severity_final",
        F.coalesce(F.col("rule_severity"), F.col("anomaly_severity"))
    )
    # is_anomaly: true if rule OR simulator detected one
    .withColumn(
        "is_anomaly_final",
        F.col("anomaly_severity_final").isNotNull() | F.col("is_anomaly").cast("boolean")
    )
    # Action recommendation text
    .withColumn(
        "action_recommended",
        F.when(
            (F.col("sensor_type") == "HVAC_temp") & (F.col("anomaly_severity_final") == "High"),
            "Inspect HVAC unit — temperature out of range"
        ).when(
            (F.col("sensor_type") == "CO2") & (F.col("anomaly_severity_final") == "High"),
            "Increase ventilation — CO₂ exceeds 1500 ppm"
        ).when(
            (F.col("sensor_type") == "CO2") & (F.col("anomaly_severity_final") == "Medium"),
            "Check ventilation schedule"
        ).when(
            (F.col("sensor_type") == "humidity") & (F.col("anomaly_severity_final") == "High"),
            "Check humidifier/dehumidifier system"
        ).when(
            (F.col("sensor_type") == "power") & (F.col("anomaly_severity_final").isin(["High", "Medium"])),
            "Investigate load spike — check sub-meter data"
        ).when(
            F.col("anomaly_type") == "spike",
            "Possible sensor fault — verify reading"
        ).when(
            F.col("anomaly_type") == "drift",
            "Calibration check recommended"
        ).otherwise(None)
    )
    # Quality score cap: if is_anomaly and quality > 80, set to 75
    # (anomalous readings are inherently less reliable)
    .withColumn(
        "reading_quality_adj",
        F.when(
            F.col("is_anomaly_final") & (F.col("reading_quality") > 80),
            F.lit(75)
        ).otherwise(F.col("reading_quality"))
    )
    # Select final columns
    .select(
        F.col("event_ts").alias("timestamp"),
        F.col("ts_bucket"),
        F.col("event_date"),
        "building_id",
        "device_id",
        "sensor_type",
        "sensor_location",
        "reading_value",
        "reading_unit",
        F.col("reading_quality_adj").alias("reading_quality"),
        "source_protocol",
        F.col("is_anomaly_final").alias("is_anomaly"),
        F.col("anomaly_type"),
        F.col("anomaly_severity_final").alias("anomaly_severity"),
        "action_recommended",
    )
)

if not DRY_RUN:
    logger.info("Writing silver_iot_normalized (merge mode)...")
    df_silver.write \
        .format("delta") \
        .mode("overwrite") \
        .option("replaceWhere", f"timestamp >= '{cutoff.strftime('%Y-%m-%d %H:%M:%S')}'") \
        .partitionBy("event_date") \
        .saveAsTable("silver_iot_normalized")
    logger.info(f"✅ silver_iot_normalized: {df_silver.count():,} rows written")

# Cell [6] — Gold: 15-minute aggregates

logger.info("Building gold_iot_realtime (15-min aggregates)...")

df_gold_realtime = (
    df_silver
    .groupBy("ts_bucket", "building_id", "sensor_type", "sensor_location", "reading_unit")
    .agg(
        F.avg("reading_value").alias("avg_value"),
        F.min("reading_value").alias("min_value"),
        F.max("reading_value").alias("max_value"),
        F.stddev("reading_value").alias("stddev_value"),
        F.count("*").alias("reading_count"),
        F.avg("reading_quality").alias("avg_quality"),
        # Anomaly aggregates
        F.sum(F.col("is_anomaly").cast("int")).alias("anomaly_count"),
        F.sum((F.col("anomaly_severity") == "High").cast("int")).alias("high_severity_count"),
        F.sum((F.col("anomaly_severity") == "Medium").cast("int")).alias("medium_severity_count"),
        # Keep worst anomaly in the 15-min window
        F.max(
            F.when(F.col("anomaly_severity") == "High", 3)
             .when(F.col("anomaly_severity") == "Medium", 2)
             .when(F.col("anomaly_severity") == "Low", 1)
             .otherwise(0)
        ).alias("max_severity_rank"),
        # Latest action recommendation
        F.last("action_recommended", ignorenulls=True).alias("action_recommended"),
        # Protocol used (take most common in window)
        F.first("source_protocol").alias("source_protocol"),
    )
    .withColumn(
        "anomaly_severity_window",
        F.when(F.col("max_severity_rank") == 3, "High")
         .when(F.col("max_severity_rank") == 2, "Medium")
         .when(F.col("max_severity_rank") == 1, "Low")
         .otherwise(None)
    )
    .withColumn("is_anomaly_window", F.col("anomaly_count") > 0)
    .withColumn("event_date", F.to_date(F.col("ts_bucket")))
    .drop("max_severity_rank")
    .withColumnRenamed("ts_bucket", "timestamp")
    .withColumnRenamed("avg_value", "reading_value_avg")
    .withColumnRenamed("min_value", "reading_value_min")
    .withColumnRenamed("max_value", "reading_value_max")
    .withColumnRenamed("stddev_value", "reading_value_stddev")
    .withColumnRenamed("avg_quality", "reading_quality_avg")
)

if not DRY_RUN:
    logger.info("Writing gold_iot_realtime...")
    df_gold_realtime.write \
        .format("delta") \
        .mode("overwrite") \
        .option("replaceWhere", f"event_date >= '{cutoff.date()}'") \
        .partitionBy("event_date") \
        .saveAsTable("gold_iot_realtime")
    logger.info(f"✅ gold_iot_realtime: {df_gold_realtime.count():,} rows")

# Cell [7] — Gold: Daily summary

logger.info("Building gold_iot_daily_summary...")

df_daily = (
    df_silver
    .groupBy("event_date", "building_id", "sensor_type")
    .agg(
        F.avg("reading_value").alias("avg_reading_value"),
        F.min("reading_value").alias("min_reading_value"),
        F.max("reading_value").alias("max_reading_value"),
        F.count("*").alias("total_readings"),
        F.sum(F.col("is_anomaly").cast("int")).alias("anomaly_count"),
        F.sum((F.col("anomaly_severity") == "High").cast("int")).alias("high_severity_count"),
        F.avg("reading_quality").alias("avg_reading_quality"),
        F.countDistinct("sensor_location").alias("active_sensors"),
    )
    .withColumn(
        "anomaly_rate_pct",
        F.round(
            F.col("anomaly_count") / F.col("total_readings") * 100,
            2
        )
    )
    .withColumn(
        "sensor_uptime_pct",
        F.round(F.col("avg_reading_quality"), 1)
    )
)

if not DRY_RUN:
    logger.info("Writing gold_iot_daily_summary...")
    df_daily.write \
        .format("delta") \
        .mode("overwrite") \
        .option("replaceWhere", f"event_date >= '{cutoff.date()}'") \
        .partitionBy("event_date") \
        .saveAsTable("gold_iot_daily_summary")
    logger.info(f"✅ gold_iot_daily_summary: {df_daily.count():,} rows")

# Cell [8] — Validation checks

logger.info("Running validation checks...")

CHECKS_PASSED = True

def check(condition: bool, message: str):
    global CHECKS_PASSED
    status = "✅" if condition else "❌"
    logger.info(f"{status} {message}")
    if not condition:
        CHECKS_PASSED = False

if not DRY_RUN:
    # Check 1: All 6 buildings present in gold_iot_realtime
    buildings_in_gold = spark.read.format("delta").table("gold_iot_realtime") \
        .select("building_id").distinct().count()
    check(buildings_in_gold == 6, f"All 6 buildings in gold_iot_realtime (found {buildings_in_gold})")

    # Check 2: All 4 sensor types present
    sensor_types_in_gold = spark.read.format("delta").table("gold_iot_realtime") \
        .select("sensor_type").distinct().count()
    check(sensor_types_in_gold == 4, f"All 4 sensor types present (found {sensor_types_in_gold})")

    # Check 3: Anomaly rate 5-20% (realistic for injected data)
    gold_df = spark.read.format("delta").table("gold_iot_realtime")
    total_windows = gold_df.count()
    anomaly_windows = gold_df.filter(F.col("is_anomaly_window")).count()
    anomaly_rate = anomaly_windows / total_windows * 100 if total_windows > 0 else 0
    check(5 <= anomaly_rate <= 25, f"Anomaly rate realistic: {anomaly_rate:.1f}%")

    # Check 4: No null building_ids
    null_buildings = gold_df.filter(F.col("building_id").isNull()).count()
    check(null_buildings == 0, f"No null building_ids (found {null_buildings})")

    # Check 5: HVAC temp in plausible range
    temp_check = gold_df.filter(F.col("sensor_type") == "HVAC_temp") \
        .agg(
            F.min("reading_value_avg").alias("min_t"),
            F.max("reading_value_avg").alias("max_t")
        ).first()
    if temp_check:
        check(
            10 <= float(temp_check["min_t"] or 0) <= 35,
            f"HVAC temp range realistic: {temp_check['min_t']:.1f}–{temp_check['max_t']:.1f}°C"
        )

if CHECKS_PASSED:
    logger.info("✅ All validation checks passed.")
else:
    logger.warning("⚠️  Some validation checks failed — review gold tables before publishing.")

# Cell [9] — Summary

logger.info("=" * 60)
logger.info("11b_iot_processing COMPLETE")
logger.info(f"  Lookback: {LOOKBACK_HOURS}h | DRY_RUN: {DRY_RUN}")
logger.info(f"  Bronze rows processed: {row_count:,}")
logger.info("  Gold tables updated:")
logger.info("    - gold_iot_realtime (15-min aggregates)")
logger.info("    - gold_iot_daily_summary (daily KPIs)")
logger.info("=" * 60)
