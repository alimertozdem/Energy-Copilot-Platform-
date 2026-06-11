# =============================================================================
# 30_residential_gold.py — Residential P3 (FLAT, top-level, paste-safe)
# silver_residential_consumption (+ silver_weather_daily) -> 3 gold tablo:
#   gold_residential_unit_kpi · gold_residential_common_split · gold_residential_uvi_monthly
# Tek hücreye yapıştır + çalıştır. EPC bandları SABİT (RESIDENTIAL_MF: 50/80/120/180).
# Ön koşul: 21 çalışmış (silver_residential_consumption + silver_unit_master dolu).
#           İklim-düzeltmesi için 02_openmeteo_weather_loader çalışmış olmalı (silver_weather_daily).
# İKLİM YÖNTEMİ (G1, 2026-06-12): commercial 03_gold_kpi_engine ile BİREBİR —
#   EUI_adj = EUI × REFERENCE_DD_DAY / ortalama_günlük_DD   (base-15, HDD+CDD, sabit referans=11).
#   TÜM EUI düzeltilir (ısıtma+DHW; product-owner onayı 2026-06-12). Weather yoksa faktör=1.0 (dürüst fallback).
# =============================================================================
from pyspark.sql import Window
from pyspark.sql.functions import (col, lit, sum as ssum, min as smin, max as smax,
    datediff, when, round as sround, avg, coalesce, year, month, count as scount)

S, U, W = "silver_residential_consumption", "silver_unit_master", "silver_weather_daily"
HD = ["heating", "dhw"]
HEAT = ["heating", "dhw", "district_heat", "gas", "oil"]
TA, TB, TC, TD = 50.0, 80.0, 120.0, 180.0   # RESIDENTIAL_MF EPC eşikleri (A/B/C/D)
REFERENCE_DD_DAY = 11.0   # 03_gold_kpi_engine (audit B1) ile AYNI sabit referans; base-15, HDD+CDD

# 0) Bina-seviyesi iklim faktörü — silver_weather_daily REUSE (commercial yöntemi).
#    factor = REFERENCE_DD_DAY / ortalama_günlük_DD (binanın tüketim penceresinde).
#    İklim bina-lokasyonu özelliğidir → bir binanın tüm birimleri AYNI faktörü paylaşır.
#    Weather tablosu/satırı yoksa → faktör NULL → aşağıda 1.0'a düşer (dürüst fallback).
_cons = spark.table(S).where(col("energy_type").isin(HD))
_span = _cons.groupBy("building_id").agg(smin("period_start").alias("ws"), smax("period_end").alias("we"))
if spark.catalog.tableExists(W):
    _wd = (spark.table(W).select("building_id", "date",
              (coalesce(col("hdd_day"), lit(0.0)) + coalesce(col("cdd_day"), lit(0.0))).alias("dd")))
    _wj = (_wd.join(_span, "building_id")
              .where((col("date") >= col("ws")) & (col("date") <= col("we")))
              .groupBy("building_id").agg(ssum("dd").alias("dd_sum"), scount("date").alias("wdays")))
    bcf = (_wj.withColumn("dd_daily", when(col("wdays") > 0, col("dd_sum") / col("wdays")).otherwise(lit(None)))
              .withColumn("climate_factor",
                  when(col("dd_daily") > lit(0.5), sround(lit(REFERENCE_DD_DAY) / col("dd_daily"), 4))
                  .otherwise(lit(None).cast("double")))
              .select("building_id", "climate_factor"))
else:
    bcf = _span.select("building_id").withColumn("climate_factor", lit(None).cast("double"))
    print("⚠️ silver_weather_daily yok — iklim faktörü 1.0 (fallback). 02_openmeteo_weather_loader'ı çalıştır.")

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
# bina-seviyesi iklim faktörünü bağla; weather yoksa 1.0 (caf)
k = k.join(bcf, "building_id", "left")
k = k.withColumn("caf", coalesce(col("climate_factor"), lit(1.0)))
(k.select("building_id", "unit_id", "is_heated", "area_m2",
    col("cs").alias("coverage_start"), col("ce").alias("coverage_end"), col("days").alias("cov_days"),
    sround("ann", 1).alias("heating_dhw_kwh_annual"), sround("eui", 1).alias("eui_kwh_m2_yr"),
    sround("caf", 4).alias("climate_adjustment_factor"),
    sround(col("eui") * col("caf"), 1).alias("eui_climate_adjusted_kwh_m2_yr"),
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

spark.table("gold_residential_unit_kpi").select("unit_id", "eui_kwh_m2_yr",
    "climate_adjustment_factor", "eui_climate_adjusted_kwh_m2_yr", "epc_band").orderBy("unit_id").show(10)
