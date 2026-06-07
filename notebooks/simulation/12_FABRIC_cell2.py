# ===== NOTEBOOK 12 — CELL 2 of 2 (run AFTER cell 1, same session) =====
# Simulation scenarios + daily summary + validation. Uses df_dispatch/df_battery_tech from cell 1.
# ── 5. SIMULATION SCENARIOS (gold_battery_simulation) ────────────────────────

print("[5/6] Computing financial simulation scenarios...")

# Financial parameters
DISCOUNT_RATE   = 0.05   # 5% — EU standard for energy investment NPV
INFLATION_RATE  = 0.03   # 3% — EU energy price inflation assumption
NPV_HORIZON_YR  = 10     # 10-year analysis window
INSTALL_OVERHEAD = 0.08  # 8% installation cost on top of hardware CAPEX

# Annualized savings from last 365 days of dispatch data
df_cutoff = df_dispatch.agg(F.max("date").alias("max_date")).collect()[0]["max_date"]
df_recent = df_dispatch.filter(
    F.col("date") >= F.date_sub(F.lit(df_cutoff), 365)
)

df_annual = (
    df_recent
    .groupBy("building_id", "strategy")
    .agg(
        F.count("date").alias("n_days"),
        F.sum("net_savings_eur").alias("sum_savings"),
        F.sum("co2_avoided_kg").alias("sum_co2"),
        F.avg("round_trip_efficiency").alias("avg_rte"),
        F.avg("soc_end_pct").alias("avg_soc"),
        F.max("cycle_depth_pct").alias("max_cycle_depth"),
        F.last("eu_compliant").alias("eu_compliant"),
        F.last("battery_type").alias("battery_type"),
        F.last("capacity_kwh").alias("capacity_kwh"),
    )
    .withColumn("annual_savings_eur",
        F.when(F.col("n_days") >= 30,
            F.col("sum_savings") / F.col("n_days") * 365
        ).otherwise(F.col("sum_savings") * (365.0 / F.greatest(F.col("n_days"), F.lit(1))))
    )
    .withColumn("annual_co2_kg",
        F.col("sum_co2") / F.col("n_days") * 365
    )
)

# Join building metadata for CAPEX
df_sim_base = (
    df_annual
    .join(
        df_building_p9.select(
            "building_id", "building_name", "country_code",
            "battery_capacity_kwh", "battery_technology", "pv_capacity_kwp",
        ),
        "building_id", "left"
    )
    .join(
        df_battery_tech.select(
            "battery_type", "cost_eur_per_kwh",
            "expected_lifespan_years", "battery_power_kw",
            # eu_compliant already present in df_annual — omit to avoid ambiguous reference
        ).withColumnRenamed("battery_type", "tech_type"),
        df_annual["battery_type"] == F.col("tech_type"), "left"
    )
)

# NPV and payback (using Spark UDF for multi-year calculation)
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType as DT

def compute_npv(annual_savings, total_capex, discount_rate=0.05, inflation=0.03, years=10, salvage_pct=0.20):
    """10-year NPV with inflation-adjusted cash flows and salvage value."""
    if annual_savings is None or total_capex is None or annual_savings <= 0:
        return -float(total_capex or 0)
    cash_flows = [-total_capex]
    for yr in range(1, years + 1):
        cf = annual_savings * ((1 + inflation) ** yr)
        if yr == years:
            cf += total_capex * salvage_pct
        cash_flows.append(cf)
    return sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(cash_flows))

def compute_irr(annual_savings, total_capex, inflation=0.03, years=10, salvage_pct=0.20):
    """Newton-Raphson IRR approximation."""
    if annual_savings is None or total_capex is None or annual_savings <= 0:
        return 0.0
    cash_flows = [-total_capex]
    for yr in range(1, years + 1):
        cf = annual_savings * ((1 + inflation) ** yr)
        if yr == years:
            cf += total_capex * salvage_pct
        cash_flows.append(cf)
    r = annual_savings / total_capex  # initial guess
    for _ in range(100):
        f  = sum(cf / ((1 + r) ** i) for i, cf in enumerate(cash_flows))
        df = sum(-i * cf / ((1 + r) ** (i + 1)) for i, cf in enumerate(cash_flows) if i > 0)
        if abs(df) < 1e-10:
            break
        r -= f / df
        r = max(-0.99, min(5.0, r))
    return r * 100.0

npv_udf = udf(lambda s, c: compute_npv(s, c) if s and c else None, DT())
irr_udf = udf(lambda s, c: compute_irr(s, c) if s and c else None, DT())

df_simulation = (
    df_sim_base
    .withColumn("battery_cost_eur",
        F.coalesce(F.col("cost_eur_per_kwh"), F.lit(140.0)) * F.col("capacity_kwh")
    )
    .withColumn("total_capex_eur",
        F.col("battery_cost_eur") * (1.0 + INSTALL_OVERHEAD)
    )
    .withColumn("payback_years",
        F.when(F.col("annual_savings_eur") > 0,
            F.least(F.lit(25.0), F.col("total_capex_eur") / F.col("annual_savings_eur"))
        ).otherwise(F.lit(25.0))
    )
    .withColumn("npv_10yr_eur",
        npv_udf(F.col("annual_savings_eur").cast(DT()), F.col("total_capex_eur").cast(DT()))
    )
    .withColumn("irr_percent",
        irr_udf(F.col("annual_savings_eur").cast(DT()), F.col("total_capex_eur").cast(DT()))
    )
    # Comparison score (composite: IRR + payback + CO2 + EU compliance)
    .withColumn("score_irr",     F.least(F.lit(40.0), F.greatest(F.lit(0.0), F.coalesce(F.col("irr_percent"), F.lit(0.0)) * 2.0)))
    .withColumn("score_payback", F.greatest(F.lit(0.0), F.lit(30.0) - (F.col("payback_years") - F.lit(3.0)) * F.lit(2.0)))
    .withColumn("score_co2",     F.least(F.lit(20.0), F.col("annual_co2_kg") / F.lit(500.0)))
    .withColumn("score_eu",
        F.when(F.col("eu_compliant") == True, F.lit(10.0)).otherwise(F.lit(-15.0))
    )
    .withColumn("comparison_score",
        F.greatest(F.lit(0.0), F.least(F.lit(100.0),
            F.col("score_irr") + F.col("score_payback") + F.col("score_co2") + F.col("score_eu")
        ))
    )
    .withColumn("scenario_id",
        F.concat(
            F.col("building_id"), F.lit("_"),
            F.upper(F.substring(F.col("strategy"), 1, 3)), F.lit("_"),
            F.col("capacity_kwh").cast("int").cast("string"), F.lit("kWh")
        )
    )
    .withColumn("strategy_label",
        F.when(F.col("strategy") == "self_consumption", F.lit("Self-Consumption"))
         .when(F.col("strategy") == "peak_shaving",     F.lit("Peak-Shaving"))
         .when(F.col("strategy") == "tou",               F.lit("Time-of-Use (ToU)"))
         .when(F.col("strategy") == "backup",            F.lit("Backup + Opportunistic"))
         .otherwise(F.col("strategy"))
    )
    .withColumn("processed_at", F.current_timestamp())
    .select(
        "scenario_id", "building_id", "building_name", "country_code",
        "battery_type", "eu_compliant",
        F.col("capacity_kwh").alias("battery_capacity_kwh"),
        "pv_capacity_kwp",
        F.round("battery_cost_eur", 0).alias("battery_cost_eur"),
        F.round("total_capex_eur", 0).alias("total_capex_eur"),
        "strategy", "strategy_label",
        F.round("annual_savings_eur", 2).alias("annual_savings_eur"),
        F.round("annual_co2_kg", 2).alias("annual_co2_avoided_kg"),
        F.round("payback_years", 2).alias("payback_years"),
        F.round("npv_10yr_eur", 2).alias("npv_10yr_eur"),
        F.round("irr_percent", 2).alias("irr_percent"),
        F.round("avg_rte", 2).alias("avg_round_trip_efficiency_pct"),
        F.round("comparison_score", 1).alias("comparison_score"),
        "processed_at",
    )
    # 2026-06-01: is_active_strategy = best (highest comparison_score) strategy per building (C1/C2 measures)
    .withColumn("is_active_strategy",
        F.row_number().over(Window.partitionBy("building_id").orderBy(F.col("comparison_score").desc())) == 1)
    .orderBy("building_id", F.col("comparison_score").desc())
)

# 2026-05-21: overwriteSchema=true — B007 eklendi, schema değişti
df_simulation.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_simulation")
print(f"  Simulation scenarios written: {df_simulation.count()}")

# ── 6. DAILY SUMMARY (gold_battery_daily_summary) ────────────────────────────

print("[6/6] Building daily summary (best strategy per day)...")

# Best strategy = highest net_savings_eur per building per day
window_best = Window.partitionBy("building_id", "date").orderBy(F.col("net_savings_eur").desc())

df_best_strategy = (
    df_dispatch
    .withColumn("rank", F.row_number().over(window_best))
    .filter(F.col("rank") == 1)
    .drop("rank")
)

# Cumulative metrics (running totals per building)
window_cum = Window.partitionBy("building_id").orderBy("date").rowsBetween(Window.unboundedPreceding, 0)

df_daily_summary = (
    df_best_strategy
    .withColumn("total_cycles_cumulative",
        F.sum(F.col("cycle_depth_pct") / 100.0).over(window_cum)
    )
    .withColumn("total_cost_avoided_eur",
        F.sum("net_savings_eur").over(window_cum)
    )
    .withColumn("total_co2_avoided_kg",
        F.sum("co2_avoided_kg").over(window_cum)
    )
    .select(
        "date", "building_id", "building_name", "country",
        "strategy", "battery_type", "eu_compliant",
        F.col("soc_start_pct").alias("avg_soc_start_percent"),
        F.col("soc_end_pct").alias("avg_soc_end_percent"),
        "charge_kwh", "discharge_kwh", "pv_generation_kwh",
        F.round("round_trip_efficiency", 4).alias("round_trip_efficiency"),
        F.round("net_savings_eur", 4).alias("daily_net_savings_eur"),
        F.round("co2_avoided_kg", 4).alias("daily_co2_avoided_kg"),
        F.round("total_cycles_cumulative", 3).alias("total_cycles_cumulative"),
        F.round("total_cost_avoided_eur", 2).alias("total_cost_avoided_eur"),
        F.round("total_co2_avoided_kg", 2).alias("total_co2_avoided_kg"),
        "is_simulated",
        F.current_timestamp().alias("processed_at"),
    )
    .orderBy("building_id", "date")
)

df_daily_summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_battery_daily_summary")
print(f"  Daily summary rows written: {df_daily_summary.count():,}")

# ── VALIDATION REPORT ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("VALIDATION REPORT — gold_battery_* tables")
print("="*60)
for _t in ["gold_battery_dispatch", "gold_battery_simulation", "gold_battery_daily_summary"]:
    _df = spark.read.table(_t)
    print(f"  {_t}: {_df.count():,} rows, {len(_df.columns)} cols")

_disp = spark.read.table("gold_battery_dispatch")
for _c in ["battery_health_percent", "cumulative_cycles", "annual_cycles", "years_until_replacement", "install_date"]:
    print(f"    V7 column present: {_c:28s} -> {_c in _disp.columns}")

print("="*60)
print("DONE — re-run complete. Refresh DirectLake, then run page9_fix2_v7.cs in TE2.")
