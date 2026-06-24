# =============================================================================
# DIAGNOSTIC — why is [Realtime Building Power kW] BLANK while [IoT CO2 Live] works?
# Paste as a NEW cell in a Fabric notebook attached to the lakehouse (11b works).
# Run it, paste the FULL printed output back. Nothing is written/changed.
# =============================================================================
from pyspark.sql import functions as F

g = spark.table("gold_iot_realtime")

print("COLUMNS:", g.columns)
print("timestamp dtype:", dict(g.dtypes).get("timestamp"))
print("ROWS:", g.count())

print("\nDISTINCT sensor_type (repr shows exact case/spacing):")
for r in g.select("sensor_type").distinct().orderBy("sensor_type").collect():
    print("   ", repr(r[0]))

print("\nbuilding_kwh slice:")
g.filter(F.col("sensor_type") == "building_kwh").select(
    F.count("*").alias("n"),
    F.countDistinct("building_id").alias("blds"),
    F.min("timestamp").alias("min_ts"),
    F.max("timestamp").alias("max_ts"),
).show(truncate=False)

print("max timestamp per sensor_type (alignment check):")
g.groupBy("sensor_type").agg(F.max("timestamp").alias("max_ts")).orderBy("sensor_type").show(40, truncate=False)

print("latest building_kwh rows:")
g.filter(F.col("sensor_type") == "building_kwh").select(
    "timestamp", "building_id", "reading_value_avg", "baseline_value"
).orderBy(F.desc("timestamp")).show(8, truncate=False)

print("global max timestamp vs building_kwh max timestamp:")
print("   global   :", g.agg(F.max("timestamp")).first()[0])
print("   building :", g.filter(F.col("sensor_type") == "building_kwh").agg(F.max("timestamp")).first()[0])
print("   CO2      :", g.filter(F.col("sensor_type") == "CO2").agg(F.max("timestamp")).first()[0])
