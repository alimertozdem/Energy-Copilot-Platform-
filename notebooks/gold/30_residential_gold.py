# =============================================================================
# 30_residential_gold.py — Residential P3 (FLAT, top-level, paste-safe)
# silver_residential_consumption -> 3 gold tablo:
#   gold_residential_unit_kpi · gold_residential_common_split · gold_residential_uvi_monthly
# Tek hücreye yapıştır + çalıştır. EPC bandları SABİT (RESIDENTIAL_MF: 50/80/120/180).
# Ön koşul: 21 çalışmış (silver_residential_consumption + silver_unit_master dolu).
# =============================================================================
from pyspark.sql import Window
from pyspark.sql.functions import (col, lit, sum as ssum, min as smin, max as smax,
    datediff, when, round as sround, avg, coalesce, year, month)

S, U = "silver_residential_consumption", "silver_unit_master"
HD = ["heating", "dhw"]
HEAT = ["heating", "dhw", "district_heat", "gas", "oil"]
TA, TB, TC, TD = 50.0, 80.0, 120.0, 180.0   # RESIDENTIAL_MF EPC eşikleri (A/B/C/D)

# 1) gold_residential_unit_kpi
c = spark.table(S).where((col("grain") == "unit") & col("energy_type").isin(HD))
a = (c.groupBy("building_id", "unit_id").agg(ssum("consumption_kwh").alias("tk"),
        smin("period_start").alias("cs"), smax("period_end").alias("ce"))
     .withColumn("days", datediff(col("ce"), col("cs")) + lit(1)))
a = a.withColumn("ann", when(col("days") > 0, col("tk") * lit(365.0) / col("days")).otherwise(col("tk")))
k = a.join(spark.table(U).select("unit_id", "area_m2", "is_heated"), "unit_id", "left")
k = k.withColumn("eui", when((col("area_m2").isNotNull()) & (col("area_m2") > 0),
        col("ann") / col("area_m2")).otherwise(lit(None).cast("double")))
e = col("eui")
k = k.withColumn("epc_band", when(e.isNull(), lit(None).cast("string")).when(e <= lit(TA), lit("A"))
        .when(e <= lit(TB), lit("B")).when(e <= lit(TC), lit("C")).when(e <= lit(TD), lit("D")).otherwise(lit("E")))
w = Window.partitionBy("building_id")
k = k.withColumn("bavg", avg("eui").over(w))
k = k.withColumn("vsb", when((col("bavg").isNotNull()) & (col("bavg") > 0),
        sround((col("eui") / col("bavg") - lit(1.0)) * lit(100.0), 1)).otherwise(lit(None).cast("double")))
(k.select("building_id", "unit_id", "is_heated", "area_m2",
    col("cs").alias("coverage_start"), col("ce").alias("coverage_end"), col("days").alias("cov_days"),
    sround("ann", 1).alias("heating_dhw_kwh_annual"), sround("eui", 1).alias("eui_kwh_m2_yr"),
    lit(1.0).alias("climate_adjustment_factor"), sround(col("eui") * lit(1.0), 1).alias("eui_climate_adjusted_kwh_m2_yr"),
    "epc_band", sround("bavg", 1).alias("building_avg_eui_kwh_m2_yr"), col("vsb").alias("vs_building_pct"))
 .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_residential_unit_kpi"))
print("✅ gold_residential_unit_kpi:", spark.table("gold_residential_unit_kpi").count())

# 2) gold_residential_common_split (HKVO 70/30)
cons = spark.table(S).where(col("energy_type").isin(HEAT))
du = (cons.where(col("grain") == "unit").groupBy("building_id", "unit_id")
      .agg(ssum("consumption_kwh").alias("uc"), smin("period_start").alias("cs"), smax("period_end").alias("ce"))
      .join(spark.table(U).select("unit_id", "area_m2"), "unit_id", "left"))
bt = cons.where(col("grain") == "building").groupBy("building_id").agg(ssum("consumption_kwh").alias("bill"))
sm = du.groupBy("building_id").agg(ssum("uc").alias("sc"), ssum("area_m2").alias("sa"))
tt = sm.join(bt, "building_id", "left").withColumn("tot", coalesce(col("bill"), col("sc")))
sp = (du.join(tt, "building_id", "left")
      .withColumn("cons_share", when(col("sc") > 0, col("uc") / col("sc")).otherwise(lit(0.0)))
      .withColumn("area_share", when(col("sa") > 0, col("area_m2") / col("sa")).otherwise(lit(0.0))))
sp = sp.withColumn("alloc", lit(0.70) * col("cons_share") + lit(0.30) * col("area_share")).withColumn("ualloc", col("tot") * col("alloc"))
(sp.select("building_id", "unit_id", col("cs").alias("coverage_start"), col("ce").alias("coverage_end"),
    sround("uc", 1).alias("unit_metered_kwh"), "area_m2", lit(0.70).alias("cons_weight"), lit(0.30).alias("area_weight"),
    sround("cons_share", 4).alias("cons_share"), sround("area_share", 4).alias("area_share"),
    sround("alloc", 4).alias("allocation_share"), sround("tot", 1).alias("building_total_kwh"), sround("ualloc", 1).alias("unit_allocated_kwh"))
 .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_residential_common_split"))
print("✅ gold_residential_common_split:", spark.table("gold_residential_common_split").count())

# 3) gold_residential_uvi_monthly
mm = (spark.table(S).where((col("grain") == "unit") & col("energy_type").isin(HD))
      .withColumn("year", year("period_start")).withColumn("month", month("period_start")))
ag = mm.groupBy("building_id", "unit_id", "year", "month", "energy_type").agg(ssum("consumption_kwh").alias("kwh"), ssum("cost_eur").alias("cost_eur"))
w2 = Window.partitionBy("building_id", "year", "month", "energy_type")
ag = ag.withColumn("bavg", avg("kwh").over(w2))
ag = ag.withColumn("vsb", when(col("bavg") > 0, sround((col("kwh") / col("bavg") - lit(1.0)) * lit(100.0), 1)).otherwise(lit(None).cast("double")))
(ag.select("building_id", "unit_id", "year", "month", "energy_type", sround("kwh", 1).alias("kwh"),
    sround("cost_eur", 2).alias("cost_eur"), sround("bavg", 1).alias("building_avg_kwh"), col("vsb").alias("vs_building_pct"))
 .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_residential_uvi_monthly"))
print("✅ gold_residential_uvi_monthly:", spark.table("gold_residential_uvi_monthly").count())

spark.table("gold_residential_unit_kpi").select("unit_id", "eui_kwh_m2_yr", "epc_band", "vs_building_pct").orderBy("unit_id").show(10)
