# 12c — Patch gold_battery_simulation (correct, capped payback).
# Your live gold_battery_simulation is stale (old logic -> payback ~500,000).
# This rebuilds it from the CURRENT gold_battery_dispatch with the correct
# finance (payback = least(25, capex/savings); NPV/IRR guarded). Standalone &
# idempotent (overwrite). ~70 lines -> pastes into Fabric without truncation.
# Run -> Refresh. Then the scatter's raw payback_years is correct (0-25).

from pyspark.sql import functions as F, Window
from pyspark.sql.types import DoubleType as DT
from pyspark.sql.functions import udf

INSTALL_OVERHEAD = 0.08

disp = spark.read.table("gold_battery_dispatch")
tech = spark.read.table("gold_battery_technologies")
bm   = spark.read.table("silver_building_master")

# 1) annualized savings per (building, strategy) from the last 365 days
cutoff = disp.agg(F.max("date").alias("m")).collect()[0]["m"]
recent = disp.filter(F.col("date") >= F.date_sub(F.lit(cutoff), 365))
annual = (recent.groupBy("building_id", "strategy").agg(
        F.count("date").alias("n_days"),
        F.sum("net_savings_eur").alias("sum_savings"),
        F.sum("co2_avoided_kg").alias("sum_co2"),
        F.avg("round_trip_efficiency").alias("avg_rte"),
        F.last("eu_compliant").alias("eu_compliant"),
        F.last("battery_type").alias("battery_type"),
        F.last("capacity_kwh").alias("capacity_kwh"),
        F.last("building_name").alias("building_name"),
        F.last("pv_capacity_kwp").alias("pv_capacity_kwp"))
    .withColumn("annual_savings_eur", F.when(F.col("n_days") >= 30, F.col("sum_savings") / F.col("n_days") * 365).otherwise(F.col("sum_savings") * (365.0 / F.greatest(F.col("n_days"), F.lit(1)))))
    .withColumn("annual_co2_kg", F.col("sum_co2") / F.col("n_days") * 365))

# 2) country_code (per building) + cost_eur_per_kwh (one row per battery_type)
cc   = bm.select("building_id", "country_code")
cost = tech.groupBy("battery_type").agg(F.avg("cost_eur_per_kwh").alias("cost_eur_per_kwh"))
base = annual.join(F.broadcast(cc), "building_id", "left").join(F.broadcast(cost), "battery_type", "left")

# 3) finance UDFs (guard savings <= 0)
def _npv(s, c, dr=0.05, inf=0.03, yrs=10, sv=0.20):
    if s is None or c is None or s <= 0: return -float(c or 0)
    cfs = [-c]
    for yr in range(1, yrs + 1):
        v = s * ((1 + inf) ** yr)
        if yr == yrs: v += c * sv
        cfs.append(v)
    return sum(v / ((1 + dr) ** i) for i, v in enumerate(cfs))

def _irr(s, c, inf=0.03, yrs=10, sv=0.20):
    if s is None or c is None or s <= 0: return 0.0
    cfs = [-c]
    for yr in range(1, yrs + 1):
        v = s * ((1 + inf) ** yr)
        if yr == yrs: v += c * sv
        cfs.append(v)
    r = s / c
    for _ in range(100):
        f = sum(v / ((1 + r) ** i) for i, v in enumerate(cfs))
        d = sum(-i * v / ((1 + r) ** (i + 1)) for i, v in enumerate(cfs) if i > 0)
        if abs(d) < 1e-10: break
        r -= f / d; r = max(-0.99, min(5.0, r))
    return r * 100.0

npv_udf = udf(lambda s, c: _npv(s, c) if s and c else None, DT())
irr_udf = udf(lambda s, c: _irr(s, c) if s and c else None, DT())

# 4) capex, payback (capped 25), NPV, IRR, score, ids
sim = (base
    .withColumn("battery_cost_eur", F.coalesce(F.col("cost_eur_per_kwh"), F.lit(140.0)) * F.col("capacity_kwh"))
    .withColumn("total_capex_eur", F.col("battery_cost_eur") * (1.0 + INSTALL_OVERHEAD))
    .withColumn("payback_years", F.when(F.col("annual_savings_eur") > 0, F.least(F.lit(25.0), F.col("total_capex_eur") / F.col("annual_savings_eur"))).otherwise(F.lit(25.0)))
    .withColumn("npv_10yr_eur", npv_udf(F.col("annual_savings_eur").cast(DT()), F.col("total_capex_eur").cast(DT())))
    .withColumn("irr_percent", irr_udf(F.col("annual_savings_eur").cast(DT()), F.col("total_capex_eur").cast(DT())))
    .withColumn("score_irr", F.least(F.lit(40.0), F.greatest(F.lit(0.0), F.coalesce(F.col("irr_percent"), F.lit(0.0)) * 2.0)))
    .withColumn("score_payback", F.greatest(F.lit(0.0), F.lit(30.0) - (F.col("payback_years") - F.lit(3.0)) * F.lit(2.0)))
    .withColumn("score_co2", F.least(F.lit(20.0), F.col("annual_co2_kg") / F.lit(500.0)))
    .withColumn("score_eu", F.when(F.col("eu_compliant") == True, F.lit(10.0)).otherwise(F.lit(-15.0)))
    .withColumn("comparison_score", F.greatest(F.lit(0.0), F.least(F.lit(100.0), F.col("score_irr") + F.col("score_payback") + F.col("score_co2") + F.col("score_eu"))))
    .withColumn("scenario_id", F.concat(F.col("building_id"), F.lit("_"), F.upper(F.substring(F.col("strategy"), 1, 3)), F.lit("_"), F.col("capacity_kwh").cast("int").cast("string"), F.lit("kWh")))
    .withColumn("strategy_label", F.when(F.col("strategy") == "self_consumption", F.lit("Self-Consumption")).when(F.col("strategy") == "peak_shaving", F.lit("Peak-Shaving")).when(F.col("strategy") == "tou", F.lit("Time-of-Use (ToU)")).when(F.col("strategy") == "backup", F.lit("Backup + Opportunistic")).otherwise(F.col("strategy")))
    .withColumn("processed_at", F.current_timestamp())
    .select("scenario_id", "building_id", "building_name", "country_code", "battery_type", "eu_compliant",
        F.col("capacity_kwh").alias("battery_capacity_kwh"), "pv_capacity_kwp",
        F.round("battery_cost_eur", 0).alias("battery_cost_eur"), F.round("total_capex_eur", 0).alias("total_capex_eur"),
        "strategy", "strategy_label", F.round("annual_savings_eur", 2).alias("annual_savings_eur"),
        F.round("annual_co2_kg", 2).alias("annual_co2_avoided_kg"), F.round("payback_years", 2).alias("payback_years"),
        F.round("npv_10yr_eur", 2).alias("npv_10yr_eur"), F.round("irr_percent", 2).alias("irr_percent"),
        F.round("avg_rte", 2).alias("avg_round_trip_efficiency_pct"), F.round("comparison_score", 1).alias("comparison_score"), "processed_at")
    .withColumn("is_active_strategy", F.row_number().over(Window.partitionBy("building_id").orderBy(F.col("comparison_score").desc())) == 1))

sim.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_simulation")
print("gold_battery_simulation rewritten:", sim.count(), "rows")
sim.select("building_name", "strategy_label", "total_capex_eur", "annual_savings_eur", "payback_years").orderBy("payback_years").show(12, truncate=False)
print("DONE — payback is now capped 0-25. Refresh DirectLake.")
