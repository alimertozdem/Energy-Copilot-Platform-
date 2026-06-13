# =============================================================================
# 09_ghg_scope_engine — FABRIC CELL 2 / 2  (SCOPE CALC + OUTPUT)
# CELL 1'i çalıştırdıktan SONRA bunu sonraki hücreye yapıştır → çalıştır.
# df_with_ef ve tüm sabitler CELL 1'den gelir (hücreler state paylaşır).
# =============================================================================

# =============================================================================
# BÖLÜM 6 — SCOPE HESAPLAMALARI
# =============================================================================
df_scoped = df_with_ef.withColumn(
    # SCOPE 1 — gaz (ısıtma payı %25 proxy / kazan verimi; gaz faktörü ref'ten)
    "scope1_gas_tco2",
    when(col("has_gas").cast("boolean"),
         spark_round(col("monthly_consumption_kwh") * 0.25 / GAS_BOILER_EFFICIENCY
                     * lit(GAS_EF_KG_PER_KWH) / 1000, 4)).otherwise(lit(0.0))
).withColumn(
    "scope1_diesel_tco2",
    when(col("has_diesel").cast("boolean"),
         spark_round(col("monthly_consumption_kwh") * 0.01 / 10.0
                     * DIESEL_EF_KG_PER_LITRE / 1000, 4)).otherwise(lit(0.0))
).withColumn(
    # WP3: Scope 1 toplam = gaz + dizel + refrigerant fugitive
    "scope1_total_tco2",
    spark_round(col("scope1_gas_tco2") + col("scope1_diesel_tco2") + col("scope1_refrigerant_tco2"), 4)
).withColumn(
    # SCOPE 2 location = net grid × ülke faktörü
    "scope2_location_tco2",
    spark_round(coalesce(col("monthly_grid_kwh"), col("monthly_consumption_kwh"))
                * col("emission_factor_grid") / 1000, 4)
).withColumn(
    # WP2/WP-max: SCOPE 2 market — hiyerarşi: contract → supplier → residual mix → location
    "scope2_market_tco2",
    spark_round(coalesce(col("monthly_grid_kwh"), col("monthly_consumption_kwh"))
                * coalesce(col("contract_supplier_ef"), col("supplier_ef"), col("res_ef"), col("emission_factor_grid"))
                / 1000, 4)
).withColumn(
    "scope2_market_factor",
    coalesce(col("contract_supplier_ef"), col("supplier_ef"), col("res_ef"), col("emission_factor_grid"))
).withColumn(
    "scope2_method",
    when(coalesce(col("contract_supplier_ef"), col("supplier_ef")).isNotNull(), lit("market_based_contract"))
    .when(col("res_ef").isNotNull(), lit("residual_mix_no_instrument"))
    .otherwise(lit("location_fallback_full_disclosure"))
).withColumn(
    # WP4: Scope 3 Cat 1 (embodied) = alan × benchmark / amortizasyon / 12 / 1000
    "scope3_cat1_embodied_tco2",
    spark_round(coalesce(col("area_m2"), lit(0.0)) * coalesce(col("embodied_kgco2e_m2"), lit(700.0))
                / coalesce(col("amortization_years"), lit(60)) / 12.0 / 1000.0, 4)
).withColumn(
    # WP-max: Cat 3 (yakıt&enerji upstream) = grid×(WTT+T&D) + gaz_yakıt×WTT. Ekstra veri YOK.
    "scope3_cat3_fuelenergy_tco2",
    spark_round((coalesce(col("monthly_grid_kwh"), col("monthly_consumption_kwh")) * (lit(ELEC_WTT_KG_KWH) + lit(ELEC_TD_KG_KWH))
                 + when(col("has_gas").cast("boolean"),
                        col("monthly_consumption_kwh") * 0.25 / GAS_BOILER_EFFICIENCY * lit(GAS_WTT_KG_KWH)).otherwise(lit(0.0))
                 ) / 1000.0, 4)
).withColumn(
    # WP-max: Cat 13 (kiracı enerjisi) = tenant_kwh × location faktörü
    "scope3_cat13_leased_tco2",
    spark_round(coalesce(col("tenant_kwh"), lit(0.0)) * col("emission_factor_grid") / 1000.0, 4)
).withColumn(
    # WP-max: Cat 6/7/5 (seyahat/işe gidiş/atık) = headcount × per-emp / 12 / 1000
    "scope3_cat6_travel_tco2",
    spark_round(coalesce(col("headcount"), lit(0)) * lit(BIZTRAVEL_KG_EMP_YR) / 12.0 / 1000.0, 4)
).withColumn(
    "scope3_cat7_commute_tco2",
    spark_round(coalesce(col("headcount"), lit(0)) * lit(COMMUTE_KG_EMP_YR) / 12.0 / 1000.0, 4)
).withColumn(
    "scope3_cat5_waste_tco2",
    spark_round(coalesce(col("headcount"), lit(0)) * lit(WASTE_KG_EMP_YR) / 12.0 / 1000.0, 4)
).withColumn(
    # Scope 3 toplam = Cat 1+3+5+6+7+13 (hâlâ tahmin → disclosure_grade=False)
    "scope3_estimated_tco2",
    spark_round(col("scope3_cat1_embodied_tco2") + col("scope3_cat3_fuelenergy_tco2")
                + col("scope3_cat5_waste_tco2") + col("scope3_cat6_travel_tco2")
                + col("scope3_cat7_commute_tco2") + col("scope3_cat13_leased_tco2"), 4)
).withColumn(
    "total_ghg_location_tco2",
    spark_round(col("scope1_total_tco2") + col("scope2_location_tco2") + col("scope3_estimated_tco2"), 4)
).withColumn(
    "total_ghg_market_tco2",
    spark_round(col("scope1_total_tco2") + col("scope2_market_tco2") + col("scope3_estimated_tco2"), 4)
).withColumn(
    "scope3_method", lit("cat1_embodied+cat3_fuelenergy+cat5_6_7_headcount+cat13_leased")
).withColumn(
    "scope3_disclosure_grade", lit(False)
).withColumn(
    "data_quality_flag",
    when(col("has_gas").cast("boolean") & col("monthly_grid_kwh").isNotNull(), lit("complete"))
    .when(col("has_gas").cast("boolean") & col("monthly_grid_kwh").isNull(), lit("estimated"))
    .otherwise(lit("missing_gas"))
).withColumn("updated_at", current_timestamp())

print("✅ Scope 1 / 2 / 3 (6 kategori) hesaplandı")


# =============================================================================
# BÖLÜM 7 — ÇIKTI TABLOSU
# =============================================================================
FINAL_COLS = [
    "building_id", "year_month", "reporting_year", "reporting_month",
    "scope1_gas_tco2", "scope1_diesel_tco2", "scope1_refrigerant_tco2", "scope1_total_tco2",
    "scope2_location_tco2", "scope2_market_tco2", "scope2_market_factor", "scope2_method",
    "scope3_cat1_embodied_tco2", "scope3_cat3_fuelenergy_tco2", "scope3_cat5_waste_tco2",
    "scope3_cat6_travel_tco2", "scope3_cat7_commute_tco2", "scope3_cat13_leased_tco2",
    "scope3_estimated_tco2", "scope3_method", "scope3_disclosure_grade",
    "total_ghg_location_tco2", "total_ghg_market_tco2",
    "emission_factor_grid", "emission_factor_source", "data_quality_flag", "updated_at",
]
df_final = df_scoped.select(FINAL_COLS)

print("\n📊 Çıktı özeti (portföy toplamı):")
df_final.agg(
    spark_sum("scope1_total_tco2").alias("Scope1"),
    spark_sum("scope2_location_tco2").alias("Scope2_Location"),
    spark_sum("scope2_market_tco2").alias("Scope2_Market"),
    spark_sum("scope3_estimated_tco2").alias("Scope3"),
    spark_sum("total_ghg_location_tco2").alias("Total_Location"),
).show()


# =============================================================================
# BÖLÜM 8 — DELTA MERGE (idempotent), tablo yoksa overwrite fallback
# =============================================================================
_tbl = OUTPUT_TABLE.rstrip("/").split("/")[-1]
try:
    gold_table = DeltaTable.forPath(spark, OUTPUT_TABLE)
    (gold_table.alias("tgt").merge(
        df_final.alias("src"),
        "tgt.building_id = src.building_id AND tgt.year_month = src.year_month")
     .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
    print(f"✅ Delta MERGE tamam: {_tbl}")
except Exception as e:
    print(f"ℹ️  MERGE atlandı ({type(e).__name__}: {str(e)[:120]}) → ilk kez overwrite")
    (df_final.write.format("delta").partitionBy("reporting_year")
     .mode("overwrite").option("overwriteSchema", "true").saveAsTable(_tbl))
    print(f"✅ Tablo oluşturuldu + kataloga kaydedildi: {_tbl}")


# =============================================================================
# BÖLÜM 9 — OPTIMIZE + katalog sync
# =============================================================================
try:
    spark.sql(f"OPTIMIZE delta.`{OUTPUT_TABLE}` ZORDER BY (building_id, year_month)")
    print("✅ Z-ORDER OPTIMIZE tamam")
except Exception as e:
    print(f"⚠️  OPTIMIZE atlandı (yeni tabloda normal): {type(e).__name__}")

try:
    spark.catalog.refreshTable(_tbl)
    print(f"✅ Katalog cache temizlendi: {_tbl}")
except Exception:
    print(f"ℹ️  '{_tbl}' katalogda 1-2 dk içinde keşfedilir")

df_check = spark.read.format("delta").load(OUTPUT_TABLE)
print(f"\n📊 gold_ghg_scope: {df_check.count():,