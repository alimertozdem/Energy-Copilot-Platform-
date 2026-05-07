# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 09_ghg_scope_engine.py
# Layer: GOLD — GHG Scope Emissions Engine
# Updated: 2026-04-16
# =============================================================================
#
# GÖREV (Purpose):
#   GHG Protokolü kapsamlarına göre bina bazlı sera gazı emisyonlarını hesapla.
#   Çıktı tablosu Power BI'da Sayfa 6 (Sustainability & Compliance) için
#   Scope 1, Scope 2 (Location & Market), Scope 3 ayrımıyla raporlama sağlar.
#
# GHG PROTOKOL TANIMI (GHG Protocol Corporate Standard):
#   Scope 1 — Doğrudan emisyonlar: bina içi yakıt yakımı
#              (doğalgaz kazanı, dizel jeneratör, soğutucu gaz kaçağı)
#   Scope 2 Location — Satın alınan elektriğin şebeke ort. emisyonu
#              (IEA / Eurostat ülke bazlı ızgara faktörü)
#   Scope 2 Market  — Satın alınan elektriğin sözleşmeli/yeşil tarifeli
#              emisyonu (yeşil enerji kontratı yoksa Location ile aynı)
#   Scope 3 — Diğer dolaylı emisyonlar: malzeme, servis, ulaşım (tahmini)
#
# VARSAYIMLAR (Assumptions) — BMAD kuralı gereği açık bildirim:
#   A1: Doğalgaz için standart IPCC dönüşüm faktörü: 2.04 kgCO2/m³
#       (LHV bazlı, CH4 içeriği %88-92 varsayımı)
#   A2: Dizel jeneratör: 2.68 kgCO2/litre (DEFRA 2023)
#   A3: Şebeke emisyon faktörleri (kgCO2/kWh, 2024 tahmini):
#       DE: 0.380  |  TR: 0.430  |  EU default: 0.280
#       Kaynak: Agora Energiewende 2024, TEİAŞ 2023
#   A4: Scope 3 tahmini = toplam enerji tüketiminin %8'i oranında
#       tedarik zinciri + çalışan ulaşımı (sektörel ortalama)
#       Bu değer kesin değil — gerçek Scope 3 envanter çalışması gerektirir.
#   A5: Soğutucu gaz kaçağı verisi mevcut değil → Scope 1'e dahil edilmemiş
#       (gelecek versiyonda silver_refrigerant_log tablosuyla eklenecek)
#   A6: Doğalgaz tüketim verisi silver_building_master'da mevcut değilse
#       heating_energy_kwh kolonundan ters hesaplanır (verimlilik: %85 kazandı)
#
# INPUT TABLOLAR:
#   gold_kpi_daily          — günlük elektrik tüketimi, solar üretim
#   silver_building_master  — alan, ülke, doğalgaz bayrağı, bina türü
#   ref_grid_emission_factors (statik referans, bu notebook'ta hardcode)
#
# OUTPUT TABLO:
#   gold_ghg_scope          — aylık, bina bazlı, scope bazlı emisyon tablosu
#
# KOLONLAR (gold_ghg_scope):
#   building_id             STRING NOT NULL
#   year_month              DATE NOT NULL          (ayın ilk günü: YYYY-MM-01)
#   reporting_year          INT NOT NULL
#   reporting_month         INT NOT NULL
#   scope1_gas_tco2         DOUBLE                 Doğalgaz combustion
#   scope1_diesel_tco2      DOUBLE                 Jeneratör (varsa)
#   scope1_total_tco2       DOUBLE                 = gas + diesel
#   scope2_location_tco2    DOUBLE                 Elektrik × ülke faktörü
#   scope2_market_tco2      DOUBLE                 Elektrik × sözleşme faktörü
#   scope3_estimated_tco2   DOUBLE                 Tedarik zinciri tahmini
#   total_ghg_location_tco2 DOUBLE                 Scope1 + Scope2_location + Scope3
#   total_ghg_market_tco2   DOUBLE                 Scope1 + Scope2_market + Scope3
#   emission_factor_grid    DOUBLE                 Kullanılan şebeke faktörü (kgCO2/kWh)
#   data_quality_flag       STRING                 "complete" | "estimated" | "missing_gas"
#   updated_at              TIMESTAMP
#
# DP-600 KONULARI:
#   - date_trunc + GROUP BY (aylık agregasyon)
#   - broadcast join (küçük referans tablosu)
#   - Delta MERGE UPSERT (idempotent çalışma)
#   - Z-ORDER (building_id, year_month) — Power BI filtre hızı
#   - Adaptive Query Execution (shuffle partition optimizasyonu)
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast,
    date_trunc, to_date, year, month, dayofmonth,
    sum as spark_sum, avg as spark_avg, count,
    round as spark_round,
    current_timestamp, concat,
    add_months, last_day, trunc,
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType,
    DateType, TimestampType
)
from delta.tables import DeltaTable

# DP-600: GHG tablo çıktısı küçük (bina × ay) → 8 partition yeterli
spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

print("✅ Spark konfigürasyonu tamamlandı")


# =============================================================================
# BÖLÜM 2 — KONFİGÜRASYON VE SABİTLER
# =============================================================================

# Tablo yolları
GOLD_KPI_DAILY        = "Tables/gold_kpi_daily"
SILVER_BUILDING       = "Tables/silver_building_master"
OUTPUT_TABLE          = "Tables/gold_ghg_scope"

# =============================================================================
# GHG Emisyon Faktörleri (Assumption A1–A3)
# Bu değerleri periyodik olarak güncelleyin:
#   DE: Agora Energiewende yıllık yayını
#   TR: TEİAŞ Elektrik Üretim İstatistikleri
# =============================================================================

# Şebeke elektrik emisyon faktörleri (kgCO2/kWh, 2024)
GRID_EMISSION_FACTORS = {
    "DE": 0.380,   # Almanya — yenilenebilir penetrasyon artıkça düşüyor
    "TR": 0.430,   # Türkiye — doğalgaz + kömür ağırlıklı
    "AT": 0.158,   # Avusturya — hidroelektrik dominant
    "NL": 0.290,   # Hollanda
    "FR": 0.052,   # Fransa — nükleer dominant, çok düşük
    "PL": 0.720,   # Polonya — kömür dominant, yüksek
    "DEFAULT": 0.280,  # AB ortalaması (Eurostat 2023)
}

# Yakıt emisyon faktörleri
GAS_EF_KG_PER_M3       = 2.04    # kgCO2/m³ doğalgaz (IPCC, LHV bazlı) — Varsayım A1
GAS_BOILER_EFFICIENCY   = 0.85    # %85 — kondensasyon kazanı değil varsayımı — Varsayım A6
DIESEL_EF_KG_PER_LITRE  = 2.68   # kgCO2/litre dizel (DEFRA 2023) — Varsayım A2

# Scope 3 tahmini (Varsayım A4)
SCOPE3_RATIO_OF_ENERGY  = 0.08   # toplam enerji kaynaklı emisyonun %8'i

print("✅ Emisyon faktörleri yüklendi:")
for country, ef in GRID_EMISSION_FACTORS.items():
    if country != "DEFAULT":
        print(f"   {country}: {ef} kgCO2/kWh")
print(f"   Doğalgaz: {GAS_EF_KG_PER_M3} kgCO2/m³")
print(f"   Dizel   : {DIESEL_EF_KG_PER_LITRE} kgCO2/litre")


# =============================================================================
# BÖLÜM 3 — REFERANS TABLOLARI OKU
# =============================================================================

df_kpi = spark.read.format("delta").load(GOLD_KPI_DAILY)
df_building = spark.read.format("delta").load(SILVER_BUILDING)

print(f"✅ gold_kpi_daily: {df_kpi.count():,} satır okundu")
print(f"✅ silver_building_master: {df_building.count()} satır okundu")

# silver_building_master'dan ihtiyaç duyulan kolonlar
# Beklenen kolonlar:
#   building_id, country_code, building_type,
#   conditioned_area_m2, has_gas_heating, has_diesel_generator
# =============================================================================
# KOLON UYUMLULUK KATMANI
# silver_building_master şeması versiyona göre farklı kolonlar içerebilir.
# Bu blok mevcut kolonları kontrol edip eksikleri proxy ile türetir.
# =============================================================================

_avail = set(df_building.columns)

# has_gas_heating: doğrudan varsa kullan; yoksa proxy:
#   geleneksel HVAC (has_hvac_traditional=True) VE ısı pompası yoksa (has_heat_pump=False)
#   → büyük olasılıkla gaz kazan veya fuel-oil ısıtma var (Avrupa bina stoku varsayımı)
if "has_gas_heating" in _avail:
    _gas_expr = col("has_gas_heating").cast("boolean")
else:
    _gas_expr = (
        coalesce(col("has_hvac_traditional"), lit(False)).cast("boolean") &
        ~coalesce(col("has_heat_pump"), lit(False)).cast("boolean")
    )
    print("⚠️  has_gas_heating kolonu yok → has_hvac_traditional & !has_heat_pump proxy kullanılıyor")

# has_diesel_generator: varsa kullan; yoksa False (şema güncellenince kaldırılır)
if "has_diesel_generator" in _avail:
    _diesel_expr = col("has_diesel_generator").cast("boolean")
else:
    _diesel_expr = lit(False)
    print("⚠️  has_diesel_generator kolonu yok → False sabit değeri kullanılıyor (Scope 1 etki: minimal)")

df_building_slim = df_building.select(
    "building_id",
    col("country_code").alias("country_code"),
    col("conditioned_area_m2").alias("area_m2"),
    _gas_expr.alias("has_gas"),
    _diesel_expr.alias("has_diesel"),
).distinct()

print(f"✅ Bina master proxy katmanı uygulandı: {df_building_slim.count()} bina")


# =============================================================================
# BÖLÜM 4 — AYLIK ELEKTRİK TÜKETİMİ HESAPLA (Scope 2 tabanı)
# =============================================================================

# DP-600: date_trunc → aylık granülarite
df_monthly = df_kpi.withColumn(
    "year_month", date_trunc("month", col("date")).cast(DateType())
).groupBy("building_id", "year_month").agg(
    spark_sum("total_consumption_kwh").alias("monthly_consumption_kwh"),
    spark_sum("net_grid_consumption_kwh").alias("monthly_grid_kwh"),
    spark_sum("co2_emissions_kg").alias("existing_co2_kg"),   # mevcut hesaplanan değer (referans)
).withColumn("reporting_year",  year(col("year_month"))) \
 .withColumn("reporting_month", month(col("year_month")))

print(f"✅ Aylık KPI agregasyonu: {df_monthly.count()} satır")


# =============================================================================
# BÖLÜM 5 — BİNA BİLGİSİ İLE BİRLEŞTİR
# =============================================================================

# DP-600: building_master küçük tablo → broadcast join
df_joined = df_monthly.join(
    broadcast(df_building_slim),
    on="building_id",
    how="left"
)

# Ülke bazlı şebeke emisyon faktörünü UDF olmadan map ile uygula
# (DP-600 best practice: UDF yerine Spark native when/otherwise)
df_with_ef = df_joined.withColumn(
    "emission_factor_grid",
    when(col("country_code") == "DE", lit(GRID_EMISSION_FACTORS["DE"]))
    .when(col("country_code") == "TR", lit(GRID_EMISSION_FACTORS["TR"]))
    .when(col("country_code") == "AT", lit(GRID_EMISSION_FACTORS["AT"]))
    .when(col("country_code") == "NL", lit(GRID_EMISSION_FACTORS["NL"]))
    .when(col("country_code") == "FR", lit(GRID_EMISSION_FACTORS["FR"]))
    .when(col("country_code") == "PL", lit(GRID_EMISSION_FACTORS["PL"]))
    .otherwise(lit(GRID_EMISSION_FACTORS["DEFAULT"]))
)


# =============================================================================
# BÖLÜM 6 — SCOPE HESAPLAMALARI
# =============================================================================

df_scoped = df_with_ef.withColumn(
    # -----------------------------------------------------------------
    # SCOPE 1 — Doğalgaz yakımı
    # Varsayım A6: doğalgaz tüketimi mevcut değil →
    # heating_energy = toplam tüketimin %25'i (iklimsel ortalama)
    # Sonra m³'e çevir: kWh / 10.55 (doğalgazın ısıl değeri) / verimlilik
    # Gerçek veri varsa: silver_gas_meter[monthly_m3] tablosunu kullan
    # -----------------------------------------------------------------
    "scope1_gas_tco2",
    when(
        col("has_gas").cast("boolean"),
        # Enerji tabanlı ters hesaplama (Varsayım A6)
        spark_round(
            col("monthly_consumption_kwh") * 0.25  # ısıtma payı tahmini
            / 10.55                                  # kWh/m³ doğalgaz ısıl değeri
            / GAS_BOILER_EFFICIENCY                  # kazandan kayıp
            * GAS_EF_KG_PER_M3                       # kgCO2/m³
            / 1000,                                  # kg → tonne
            4
        )
    ).otherwise(lit(0.0))
).withColumn(
    # Scope 1 — Dizel jeneratör (küçük katkı, has_diesel varsa)
    "scope1_diesel_tco2",
    when(
        col("has_diesel").cast("boolean"),
        # Bekleme modu: toplam tüketimin %1'i dizel kabul (seçim kesintisi)
        spark_round(
            col("monthly_consumption_kwh") * 0.01
            / 10.0          # kWh/litre dizel yaklaşık ısıl değeri
            * DIESEL_EF_KG_PER_LITRE
            / 1000,
            4
        )
    ).otherwise(lit(0.0))
).withColumn(
    "scope1_total_tco2",
    spark_round(col("scope1_gas_tco2") + col("scope1_diesel_tco2"), 4)

).withColumn(
    # -----------------------------------------------------------------
    # SCOPE 2 — Location-based (şebeke ort. faktörü)
    # Formül: net şebeke tüketimi × şebeke emisyon faktörü
    # -----------------------------------------------------------------
    "scope2_location_tco2",
    spark_round(
        coalesce(col("monthly_grid_kwh"), col("monthly_consumption_kwh"))
        * col("emission_factor_grid")
        / 1000,   # kg → tonne
        4
    )
).withColumn(
    # Scope 2 Market — şimdilik Location ile aynı (yeşil enerji kontratı yoksa)
    # Gerçek veri: utility_contract tablosundan supplier_ef getir
    "scope2_market_tco2",
    col("scope2_location_tco2")

).withColumn(
    # -----------------------------------------------------------------
    # SCOPE 3 — Tahmini tedarik zinciri emisyonları (Varsayım A4)
    # Scope 3 Category 1 (purchased goods) + Category 7 (employee commuting)
    # = %8 of (Scope1 + Scope2) — sektörel CRREM/GRESB varsayımı
    # -----------------------------------------------------------------
    "scope3_estimated_tco2",
    spark_round(
        (col("scope1_total_tco2") + col("scope2_location_tco2"))
        * SCOPE3_RATIO_OF_ENERGY,
        4
    )

).withColumn(
    "total_ghg_location_tco2",
    spark_round(
        col("scope1_total_tco2")
        + col("scope2_location_tco2")
        + col("scope3_estimated_tco2"),
        4
    )
).withColumn(
    "total_ghg_market_tco2",
    spark_round(
        col("scope1_total_tco2")
        + col("scope2_market_tco2")
        + col("scope3_estimated_tco2"),
        4
    )
).withColumn(
    # Veri kalitesi bayrağı
    "data_quality_flag",
    when(
        col("has_gas").cast("boolean") & col("monthly_grid_kwh").isNotNull(),
        lit("complete")
    ).when(
        col("has_gas").cast("boolean") & col("monthly_grid_kwh").isNull(),
        lit("estimated")
    ).otherwise(
        lit("missing_gas")   # has_gas=False → Scope 1 hesabı yapılmadı
    )
).withColumn("updated_at", current_timestamp())

print("✅ Scope 1 / 2 / 3 hesaplamaları tamamlandı")


# =============================================================================
# BÖLÜM 7 — ÇIKTI TABLOSUNU HAZIRLA
# =============================================================================

FINAL_COLS = [
    "building_id",
    "year_month",
    "reporting_year",
    "reporting_month",
    "scope1_gas_tco2",
    "scope1_diesel_tco2",
    "scope1_total_tco2",
    "scope2_location_tco2",
    "scope2_market_tco2",
    "scope3_estimated_tco2",
    "total_ghg_location_tco2",
    "total_ghg_market_tco2",
    "emission_factor_grid",
    "data_quality_flag",
    "updated_at",
]

df_final = df_scoped.select(FINAL_COLS)

# Doğrulama
print("\n📊 Çıktı özeti (portföy toplamı):")
df_final.agg(
    spark_sum("scope1_total_tco2").alias("Scope1_tCO2"),
    spark_sum("scope2_location_tco2").alias("Scope2_Location_tCO2"),
    spark_sum("scope3_estimated_tco2").alias("Scope3_tCO2"),
    spark_sum("total_ghg_location_tco2").alias("Total_GHG_tCO2"),
).show()

print("\n📋 Veri kalitesi dağılımı:")
df_final.groupBy("data_quality_flag").count().show()


# =============================================================================
# BÖLÜM 8 — DELTA MERGE UPSERT (idempotent)
# =============================================================================

# DP-600: MERGE → yeniden çalıştırıldığında duplicate oluşturmaz
try:
    gold_table = DeltaTable.forPath(spark, OUTPUT_TABLE)

    gold_table.alias("tgt").merge(
        df_final.alias("src"),
        "tgt.building_id = src.building_id AND tgt.year_month = src.year_month"
    ).whenMatchedUpdateAll() \
     .whenNotMatchedInsertAll() \
     .execute()

    print(f"✅ Delta MERGE tamamlandı: {OUTPUT_TABLE}")

except Exception:
    # Tablo yoksa ilk kez oluştur
    # saveAsTable: hem Tables/ klasörüne yazar hem Lakehouse kataloğuna kaydeder
    _tbl_name_init = OUTPUT_TABLE.replace("Tables/", "")
    df_final.write \
        .format("delta") \
        .partitionBy("reporting_year") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(_tbl_name_init)

    print(f"✅ Delta tablo ilk kez oluşturuldu ve kataloğa kaydedildi: {_tbl_name_init}")


# =============================================================================
# BÖLÜM 9 — Z-ORDER OPTIMIZE (DP-600)
# =============================================================================

spark.sql(f"""
    OPTIMIZE delta.`{OUTPUT_TABLE}`
    ZORDER BY (building_id, year_month)
""")

print("✅ Z-ORDER OPTIMIZE tamamlandı")


# =============================================================================
# BÖLÜM 9b — LAKEHOUSE KATALOG SYNC (Direct Lake için)
# =============================================================================
# Fabric'te CREATE TABLE ... LOCATION relative path KABUL ETMEZ (absolute ABFS lazım).
# Bunun yerine: tablo katalogda varsa cache'i temizle, yoksa Fabric otomatik keşfeder.

_tbl_name = OUTPUT_TABLE.replace("Tables/", "")

try:
    spark.catalog.refreshTable(_tbl_name)
    print(f"✅ Katalog cache temizlendi: {_tbl_name}")
except Exception as _ex:
    print(f"ℹ️  '{_tbl_name}' katalogda henüz yok — Fabric otomatik keşfeder (1-2 dk beklenir)")
    print(f"   Semantic model hata verirse: Lakehouse → Tables → ⟳ Refresh → Model → Refresh now")


# =============================================================================
# BÖLÜM 10 — SON DOĞRULAMA
# =============================================================================

df_check = spark.read.format("delta").load(OUTPUT_TABLE)

print(f"\n📊 gold_ghg_scope istatistikleri:")
print(f"   Toplam satır        : {df_check.count():,}")
print(f"   Benzersiz bina      : {df_check.select('building_id').distinct().count()}")
print(f"   Yıl aralığı        : {df_check.agg({'reporting_year': 'min'}).collect()[0][0]} – {df_check.agg({'reporting_year': 'max'}).collect()[0][0]}")

df_check.agg(
    spark_sum("total_ghg_location_tco2").alias("Toplam_GHG_tCO2")
).show()

print("""
📋 SONRAKI ADIMLAR:
   1. Power BI Semantic Model'e gold_ghg_scope tablosunu ekle
   2. building_id üzerinden silver_building_master ile ilişki kur
   3. year_month üzerinden Date tablosuyla ilişki kur
   4. 12_dax_v7_ghg_crrem.dax dosyasındaki ölçüleri ekle
   5. Scope 3 verisini gelecekte silver_scope3_inventory tablosuyla güçlendir
""")
