# Fabric notebook source code export using cell-code-separator
# Cell [1] — Metadata / 11b_iot_processing v2 / Schedule: every 15 min
# Last updated: 2026-05-07

# =============================================================================
# 11b_iot_processing.py  (v2)
# Changes: extended sensor types, zone compliance, cost estimation columns
# =============================================================================

# Cell [2] — Setup
import logging
from datetime import datetime, timedelta, timezone
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType,
    IntegerType, BooleanType, TimestampType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("11b_iot_processing")

spark = SparkSession.builder.getOrCreate()
LOOKBACK_HOURS = int(spark.conf.get("lookback_hours", "2"))
DRY_RUN = spark.conf.get("dry_run", "false").lower() == "true"
logger.info(f"v2 | lookback={LOOKBACK_HOURS}h | dry_run={DRY_RUN}")

# Cell [3] — Bronze schema (v2: includes setpoint + cost fields)
BRONZE_SCHEMA = StructType([
    StructField("device_id",          StringType(),  True),
    StructField("building_id",        StringType(),  True),
    StructField("sensor_type",        StringType(),  True),
    StructField("sensor_location",    StringType(),  True),
    StructField("reading_value",      FloatType(),   True),
    StructField("reading_unit",       StringType(),  True),
    StructField("source_protocol",    StringType(),  True),
    StructField("timestamp",          StringType(),  True),
    StructField("reading_quality",    IntegerType(), True),
    StructField("setpoint_min",       FloatType(),   True),
    StructField("setpoint_max",       FloatType(),   True),
    StructField("baseline_value",     FloatType(),   True),
    StructField("in_setpoint",        BooleanType(), True),
    StructField("is_anomaly",         BooleanType(), True),
    StructField("anomaly_type",       StringType(),  True),
    StructField("anomaly_severity",   StringType(),  True),
    StructField("action_recommended", StringType(),  True),
    StructField("cost_eur_estimate",  FloatType(),   True),
])

# Cell [4] — Load bronze
logger.info("Loading bronze_iot_raw...")
try:
    df_bronze = spark.read.format("delta").table("bronze_iot_raw")
except Exception as e:
    logger.error(f"Cannot read bronze_iot_raw: {e}"); raise

df_bronze = df_bronze.withColumn(
    "event_ts", F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss'Z'")
)
cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
df_window = df_bronze.filter(F.col("event_ts") >= F.lit(cutoff))
row_count = df_window.count()
logger.info(f"Rows in window: {row_count:,}")
if row_count == 0:
    # 2026-05-21: Fabric uyumu — dbutils Databricks-spesifik, Fabric'te notebookutils kullanılır
    # Cross-platform graceful exit: notebookutils → mssparkutils → SystemExit fallback
    logger.warning("No new data.")
    try:
        import notebookutils
        notebookutils.notebook.exit("NO_DATA")
    except ImportError:
        try:
            import mssparkutils
            mssparkutils.notebook.exit("NO_DATA")
        except ImportError:
            raise SystemExit("NO_DATA — IoT lookback window'da veri yok (EventStream silinmişse normal)")

sensor_types_present = sorted([r[0] for r in df_window.select("sensor_type").distinct().collect()])
logger.info(f"Sensor types: {sensor_types_present}")

# Cell [5] — Load sensor master
try:
    df_sm = spark.read.format("delta").table("gold_iot_sensor_master").select(
        "building_id", "sensor_type", "sensor_location",
        F.col("setpoint_min").alias("sm_smin"),
        F.col("setpoint_max").alias("sm_smax"),
        F.col("alert_threshold_low").alias("sm_alo"),
        F.col("alert_threshold_high").alias("sm_ahi"),
        F.col("baseline_value").alias("sm_base"),
    )
    HAS_SM = True
    logger.info("Sensor master loaded.")
except Exception:
    HAS_SM = False
    logger.warning("No sensor master — using embedded setpoints from bronze.")

# Cell [6] — Action text UDF
def build_action(sensor_type, severity, anomaly_type):
    if not severity or not anomaly_type:
        return None
    actions = {
        ("HVAC_temp",        "High",   "threshold_exceeded"): "CRITICAL: HVAC temp out of range — inspect unit",
        ("HVAC_temp",        "Medium", "spike"):              "HVAC temp spike — check AHU thermostat",
        ("HVAC_temp",        "Low",    "drift"):              "HVAC temp drifting — monitor zone",
        ("humidity",         "High",   "threshold_exceeded"): "Humidity critical — check humidifier/dehumidifier",
        ("humidity",         "Medium", "spike"):              "Humidity spike — check sensor or water leak",
        ("CO2",              "High",   "threshold_exceeded"): "CRITICAL: CO2 >1500ppm — increase ventilation now",
        ("CO2",              "Medium", "spike"):              "CO2 elevated — check occupancy and ventilation",
        ("building_kwh",     "High",   "threshold_exceeded"): "Power spike >140% baseline — check equipment fault",
        ("building_kwh",     "Medium", "threshold_exceeded"): "Power above normal — review demand profile",
        ("building_kwh",     "High",   "spike"):              "Unexpected power peak — investigate load cause",
        ("hvac_kwh",         "High",   "threshold_exceeded"): "HVAC overconsumption — check controls/setpoints",
        ("hvac_kwh",         "Medium", "spike"):              "HVAC power spike — inspect staging controls",
        ("lighting_kwh",     "Medium", "threshold_exceeded"): "Lighting above baseline — check occupancy sensors",
        ("plug_load_kwh",    "High",   "threshold_exceeded"): "Plug load spike — check unauthorized equipment",
        ("HVAC_supply_temp", "High",   "threshold_exceeded"): "Supply air fault — check cooling coil/chilled water",
        ("HVAC_supply_temp", "Medium", "drift"):              "Supply temp drifting — inspect coil and valves",
        ("HVAC_return_temp", "High",   "threshold_exceeded"): "Poor delta-T — check air distribution",
        ("boiler_eff",       "High",   "threshold_exceeded"): "Boiler efficiency critical (<75%) — schedule service",
        ("boiler_eff",       "Medium", "drift"):              "Boiler efficiency declining — preventive maintenance",
        ("chiller_cop",      "High",   "threshold_exceeded"): "Chiller COP critically low — check refrigerant",
        ("chiller_cop",      "Medium", "drift"):              "Chiller COP declining — inspect heat exchangers",
        ("pump_pressure",    "High",   "threshold_exceeded"): "Pressure fault — check pump and expansion vessel",
        ("pump_pressure",    "Low",    "drift"):              "Low pressure — check for leaks",
        ("fan_rpm",          "High",   "threshold_exceeded"): "Fan overspeed — inspect VFD and belt",
        ("fan_rpm",          "Low",    "drift"):              "Fan underperforming — check filter and belt",
    }
    key = (sensor_type, severity, anomaly_type)
    if key in actions:
        return actions[key]
    label = sensor_type.replace("_", " ")
    if severity == "High":
        return f"ALERT: {label} — {anomaly_type} — inspect immediately"
    elif severity == "Medium":
        return f"WARNING: {label} — {anomaly_type} — investigate"
    return f"INFO: {label} — {anomaly_type} — monitor"

action_udf = F.udf(build_action, StringType())

def severity_from_setpoints(value, smin, smax, alo, ahi):
    if value is None: return None
    if ahi is not None and value > ahi: return "High"
    if alo is not None and value < alo: return "High"
    if smax is not None and value > smax: return "Medium"
    if smin is not None and value < smin: return "Medium"
    return None

severity_udf = F.udf(severity_from_setpoints, StringType())

# Cell [7] — Silver transformation
logger.info("Building silver_iot_normalized...")

# Defensive column check — bronze_iot_raw schema varies depending on simulator version
# and EventStream ingest path. Columns may or may not include setpoint/baseline fields.
bronze_cols = df_window.columns
logger.info(f"bronze_iot_raw columns present: {sorted(bronze_cols)}")

def safe_col(name, dtype=FloatType()):
    """Return F.col(name) if it exists in bronze, otherwise F.lit(None) cast to dtype."""
    return F.col(name) if name in bronze_cols else F.lit(None).cast(dtype)

if HAS_SM:
    df_enriched = df_window.join(df_sm, on=["building_id", "sensor_type", "sensor_location"], how="left") \
        .withColumn("eff_smin", F.coalesce("sm_smin", safe_col("setpoint_min"))) \
        .withColumn("eff_smax", F.coalesce("sm_smax", safe_col("setpoint_max"))) \
        .withColumn("eff_alo",  F.col("sm_alo")) \
        .withColumn("eff_ahi",  F.col("sm_ahi")) \
        .withColumn("eff_base", F.coalesce("sm_base", safe_col("baseline_value")))
else:
    df_enriched = df_window \
        .withColumn("eff_smin", safe_col("setpoint_min")) \
        .withColumn("eff_smax", safe_col("setpoint_max")) \
        .withColumn("eff_alo",  F.lit(None).cast(FloatType())) \
        .withColumn("eff_ahi",  F.lit(None).cast(FloatType())) \
        .withColumn("eff_base", safe_col("baseline_value"))

df_silver = (
    df_enriched
    .withColumn("ts_bucket",
        F.from_unixtime((F.unix_timestamp("event_ts") / 900).cast("long") * 900).cast(TimestampType()))
    .withColumn("event_date", F.to_date("event_ts"))
    .withColumn("in_setpoint_calc",
        F.when((F.col("eff_smin").isNotNull()) & (F.col("reading_value") < F.col("eff_smin")), False)
         .when((F.col("eff_smax").isNotNull()) & (F.col("reading_value") > F.col("eff_smax")), False)
         .otherwise(True))
    .withColumn("in_setpoint_final",
        F.coalesce("in_setpoint_calc", safe_col("in_setpoint", BooleanType()), F.lit(True)))
    .withColumn("rule_severity",
        severity_udf("reading_value", "eff_smin", "eff_smax", "eff_alo", "eff_ahi"))
    .withColumn("anomaly_severity_final",
        F.coalesce("rule_severity", "anomaly_severity"))
    .withColumn("is_anomaly_final", F.col("anomaly_severity_final").isNotNull())
    .withColumn("action_final",
        F.coalesce(
            action_udf("sensor_type", "anomaly_severity_final", "anomaly_type"),
            safe_col("action_recommended", StringType())))
    .withColumn("reading_quality_adj",
        F.when(F.col("is_anomaly_final") & (F.col("reading_quality") > 80), 75)
         .otherwise(F.col("reading_quality")))
    .select(
        F.col("event_ts").alias("timestamp"),
        "ts_bucket", "event_date", "building_id", "device_id",
        "sensor_type", "sensor_location", "reading_value", "reading_unit",
        F.col("reading_quality_adj").alias("reading_quality"),
        "source_protocol",
        F.col("eff_smin").alias("setpoint_min"),
        F.col("eff_smax").alias("setpoint_max"),
        F.col("eff_base").alias("baseline_value"),
        F.col("in_setpoint_final").alias("in_setpoint"),
        F.col("is_anomaly_final").alias("is_anomaly"),
        "anomaly_type",
        F.col("anomaly_severity_final").alias("anomaly_severity"),
        F.col("action_final").alias("action_recommended"),
        F.coalesce(safe_col("cost_eur_estimate"), F.lit(0.0)).alias("cost_eur_estimate"),
    )
)

if not DRY_RUN:
    df_silver.write.format("delta").mode("overwrite") \
        .option("mergeSchema", "true") \
        .option("replaceWhere", f"timestamp >= '{cutoff.strftime('%Y-%m-%d %H:%M:%S')}'") \
        .partitionBy("event_date").saveAsTable("silver_iot_normalized")
    logger.info(f"silver_iot_normalized: {df_silver.count():,} rows")

# Cell [8] — Gold: 15-min aggregates
logger.info("Building gold_iot_realtime...")

df_gold_rt = (
    df_silver
    .groupBy("ts_bucket", "building_id", "sensor_type", "sensor_location",
             "reading_unit", "setpoint_min", "setpoint_max")
    .agg(
        F.avg("reading_value").alias("reading_value_avg"),
        F.min("reading_value").alias("reading_value_min"),
        F.max("reading_value").alias("reading_value_max"),
        F.count("*").alias("reading_count"),
        F.avg("reading_quality").alias("reading_quality_avg"),
        F.avg(F.col("in_setpoint").cast("int")).alias("in_setpoint_pct_raw"),
        F.sum(F.col("is_anomaly").cast("int")).alias("anomaly_count"),
        F.sum((F.col("anomaly_severity") == "High").cast("int")).alias("high_severity_count"),
        F.sum((F.col("anomaly_severity") == "Medium").cast("int")).alias("medium_severity_count"),
        F.max(
            F.when(F.col("anomaly_severity") == "High",   3)
             .when(F.col("anomaly_severity") == "Medium", 2)
             .when(F.col("anomaly_severity") == "Low",    1)
             .otherwise(0)
        ).alias("max_severity_rank"),
        F.sum("cost_eur_estimate").alias("cost_eur_window"),
        F.last("action_recommended", ignorenulls=True).alias("action_recommended"),
        F.first("source_protocol").alias("source_protocol"),
        F.first("baseline_value").alias("baseline_value"),
    )
    .withColumn("anomaly_severity_window",
        F.when(F.col("max_severity_rank") == 3, "High")
         .when(F.col("max_severity_rank") == 2, "Medium")
         .when(F.col("max_severity_rank") == 1, "Low")
         .otherwise(None))
    .withColumn("is_anomaly_window", F.col("anomaly_count") > 0)
    .withColumn("in_setpoint_pct", F.round(F.col("in_setpoint_pct_raw") * 100, 1))
    .withColumn("cost_eur_window", F.round("cost_eur_window", 2))
    .withColumn("event_date", F.to_date("ts_bucket"))
    # hour_bucket: "05-07 14:00" format — used as categorical X-axis in Power BI V1 chart
    # Avoids KQL DirectQuery datetime string issue; DirectLake on Delta handles this cleanly
    .withColumn("hour_bucket", F.date_format("ts_bucket", "MM-dd HH:00"))
    # hour_of_day: 0-23 integer — for DAX FILTER expressions and future forecasting
    .withColumn("hour_of_day", F.hour("ts_bucket"))
    .withColumnRenamed("ts_bucket", "timestamp")
    .drop("max_severity_rank", "in_setpoint_pct_raw")
)

if not DRY_RUN:
    df_gold_rt.write.format("delta").mode("overwrite") \
        .option("mergeSchema", "true") \
        .option("replaceWhere", f"event_date >= '{cutoff.date()}'") \
        .partitionBy("event_date").saveAsTable("gold_iot_realtime")
    logger.info(f"gold_iot_realtime: {df_gold_rt.count():,} rows")

# Cell [9] — Gold: Daily summary
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
        F.avg(F.col("in_setpoint").cast("int")).alias("compliance_pct_raw"),
        F.sum("cost_eur_estimate").alias("total_cost_eur_estimate"),
        F.countDistinct("sensor_location").alias("active_sensors"),
    )
    .withColumn("anomaly_rate_pct",
        F.round(F.col("anomaly_count") / F.col("total_readings") * 100, 2))
    .withColumn("compliance_pct",
        F.round(F.col("compliance_pct_raw") * 100, 1))
    .withColumn("total_cost_eur_estimate",
        F.round("total_cost_eur_estimate", 2))
    .withColumn("sensor_uptime_pct",
        F.round("avg_reading_quality", 1))
    .drop("compliance_pct_raw")
)

if not DRY_RUN:
    df_daily.write.format("delta").mode("overwrite") \
        .option("mergeSchema", "true") \
        .option("replaceWhere", f"event_date >= '{cutoff.date()}'") \
        .partitionBy("event_date").saveAsTable("gold_iot_daily_summary")
    logger.info(f"gold_iot_daily_summary: {df_daily.count():,} rows")

# Cell [10] — Validation
logger.info("Running validation...")
CHECKS_PASSED = True

def check(cond, msg):
    global CHECKS_PASSED
    logger.info(f"{'OK' if cond else 'FAIL'}: {msg}")
    if not cond: CHECKS_PASSED = False

if not DRY_RUN:
    grt = spark.read.format("delta").table("gold_iot_realtime")
    gds = spark.read.format("delta").table("gold_iot_daily_summary")

    n_bldg = grt.select("building_id").distinct().count()
    check(n_bldg >= 5, f"Buildings: {n_bldg} (expected >=5)")

    stypes = [r[0] for r in grt.select("sensor_type").distinct().collect()]
    for required in ["building_kwh", "hvac_kwh", "HVAC_temp", "CO2"]:
        check(required in stypes, f"{required} present in gold_iot_realtime")

    total_w = grt.count()
    anom_w = grt.filter(F.col("is_anomaly_window")).count()
    rate = anom_w / total_w * 100 if total_w > 0 else 0
    check(5 <= rate <= 30, f"Anomaly rate: {rate:.1f}% (5-30% expected)")

    cost_rows = grt.filter(F.col("cost_eur_window") > 0).count()
    check(cost_rows > 0, f"Windows with cost estimate: {cost_rows:,}")

    null_stp = grt.filter(F.col("in_setpoint_pct").isNull()).count()
    check(null_stp == 0, f"Null in_setpoint_pct: {null_stp} (expected 0)")

    cost_daily = gds.filter(F.col("total_cost_eur_estimate") > 0).count()
    check(cost_daily > 0, f"Daily rows with cost: {cost_daily:,}")

if CHECKS_PASSED:
    logger.info("All checks passed.")
else:
    logger.warning("Some checks failed — review tables.")

# Cell [11] — Summary
logger.info("=" * 60)
logger.info("11b_iot_processing v2 COMPLETE")
logger.info(f"  Bronze rows: {row_count:,} | Sensor types: {sensor_types_present}")
logger.info("  gold_iot_realtime      — 15-min, in_setpoint_pct, cost_eur_window")
logger.info("  gold_iot_daily_summary — compliance_pct, total_cost_eur_estimate")
logger.info("=" * 60)
