# 12b — Patch gold_battery_dispatch with V7 (SoH) columns.
# Standalone + idempotent. Reads the existing table, adds the battery-health
# columns, overwrites (no MERGE -> avoids DELTA_MULTIPLE_SOURCE). ~30 lines so
# copy-paste into Fabric won't truncate. Run, then Refresh, then page9_fix2_v7.cs.
# SoH = 100 - cycle_fade - calendar_fade ; end-of-life = 80% SoH.  [Mert-approved]

from pyspark.sql import functions as F, Window

CAL_FADE_PCT_PER_YR = 1.5
EOL_SOH_PCT = 80.0

disp = spark.read.table("gold_battery_dispatch")
tech = spark.read.table("gold_battery_technologies")

# idempotent: drop any prior V7 helper columns before recomputing
for c in ["annual_cycles", "install_date", "cumulative_cycles", "battery_health_percent",
          "years_until_replacement", "_age_yr", "_cycle_fade", "_cal_fade", "_annual_fade",
          "degradation_rate_pct_per_1000_cycles"]:
    if c in disp.columns:
        disp = disp.drop(c)

_max_date = disp.agg(F.max("date").alias("m")).collect()[0]["m"]
_w_b = Window.partitionBy("building_id", "strategy")

disp = disp.withColumn("annual_cycles", F.round(F.avg(F.col("cycle_depth_pct") / 100.0).over(_w_b) * 365.0, 1))
disp = (disp
    .withColumn("_age_yr", F.round(F.lit(0.5) + (F.abs(F.hash(F.col("building_id"))) % 46) / 10.0, 2))
    .withColumn("install_date", F.date_sub(F.to_date(F.lit(_max_date)), (F.col("_age_yr") * 365).cast("int")))
    .withColumn("cumulative_cycles", F.round(F.col("_age_yr") * F.col("annual_cycles"), 1)))

_degr = tech.groupBy("battery_type").agg(F.avg("degradation_rate_pct_per_1000_cycles").alias("degr"))
disp = (disp.join(F.broadcast(_degr), "battery_type", "left")
    .withColumn("_cycle_fade", F.col("cumulative_cycles") * F.coalesce(F.col("degr"), F.lit(2.0)) / F.lit(1000.0))
    .withColumn("_cal_fade", F.col("_age_yr") * F.lit(CAL_FADE_PCT_PER_YR))
    .withColumn("battery_health_percent", F.round(F.greatest(F.lit(70.0), F.lit(100.0) - F.col("_cycle_fade") - F.col("_cal_fade")), 1))
    .withColumn("_annual_fade", F.greatest(F.lit(0.1), (F.col("_cycle_fade") + F.col("_cal_fade")) / F.greatest(F.col("_age_yr"), F.lit(0.5))))
    .withColumn("years_until_replacement", F.round(F.greatest(F.lit(0.0), (F.col("battery_health_percent") - F.lit(EOL_SOH_PCT)) / F.col("_annual_fade")), 1))
    .drop("degr", "_cycle_fade", "_cal_fade", "_annual_fade", "_age_yr"))

disp.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_dispatch")

_d = spark.read.table("gold_battery_dispatch")
print("PATCHED gold_battery_dispatch — rows:", _d.count())
for c in ["battery_health_percent", "cumulative_cycles", "annual_cycles", "years_until_replacement", "install_date"]:
    print(f"  V7 column present: {c:26s} -> {c in _d.columns}")
print("DONE — Refresh DirectLake, then run page9_fix2_v7.cs in TE2.")
