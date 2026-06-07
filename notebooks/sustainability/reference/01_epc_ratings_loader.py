# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 01_epc_ratings_loader.py
# Layer: SILVER — EPC (Energy Performance Certificate) Ratings
# =============================================================================
#
# GÖREV (Purpose):
#   Demo binalar için EPC sertifika verilerini Silver katmanına yükle.
#   Gerçek üretimde: ulusal EPC veritabanından (DE: DEnsPI, NL: EP-Online,
#   AT: OIB) API veya CSV ile çekilir. Demo için inline tanımlı.
#
# EPC SINIF STANDARDI (AB Direktifi 2010/31/EU + 2018/844/EU):
#   Sınıf | Birincil Enerji (kWh/m²/yıl) | Renk
#   ------|-------------------------------|------
#   A     | ≤ 50                          | Koyu yeşil
#   B     | 51 – 100                      | Açık yeşil
#   C     | 101 – 150                     | Sarı-yeşil
#   D     | 151 – 200                     | Sarı
#   E     | 201 – 250                     | Turuncu
#   F     | 251 – 300                     | Kırmızı-turuncu
#   G     | > 300                         | Kırmızı
#
# ÜLKE NÜANSLARI:
#   Almanya (DE) : Energieausweis (Bedarfs- veya Verbrauchsausweis)
#   Hollanda (NL) : Energielabel (NTA 8800 metodolojisi, 2021 sonrası)
#   Avusturya (AT): Energieausweis (OIB RL 6, hwb_kwh_m2 bazlı)
#   Türkiye (TR)  : BEP (Binalarda Enerji Performansı Yönetmeliği)
#
# OUTPUT:
#   Tables/silver_epc_ratings
#   Kolonlar: building_id, epc_class, epc_score_kwh_m2, co2_kg_m2_year,
#             valid_from, valid_to, assessment_year, certifying_body,
#             country, methodology, updated_at
#
# NOT: Bu tablo Power BI Page 6'daki EPC portfolio kartını besler.
#      DAX: AVERAGEX(silver_epc_ratings, SWITCH([epc_class],"A",1,"B",2,...))
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType,
    TimestampType, DateType
)
from pyspark.sql.functions import current_timestamp, to_date, lit, col
from delta.tables import DeltaTable

spark.conf.set("spark.sql.shuffle.partitions", "8")

OUTPUT_TABLE = "Tables/silver_epc_ratings"
OUTPUT_TABLE_NAME = "silver_epc_ratings"

print("✅ EPC Ratings Loader başlatıldı")


# =============================================================================
# BÖLÜM 2 — ŞEMA TANIMI
# =============================================================================

EPC_SCHEMA = StructType([
    StructField("building_id",       StringType(),  False),  # B001-B006
    StructField("epc_class",         StringType(),  False),  # A / B / C / D / E / F / G
    StructField("epc_score_kwh_m2",  DoubleType(),  True),   # Birincil enerji kWh/m²/yıl
    StructField("co2_kg_m2_year",    DoubleType(),  True),   # CO₂ emisyonu kgCO₂/m²/yıl
    StructField("valid_from",        DateType(),    True),   # Sertifika başlangıç tarihi
    StructField("valid_to",          DateType(),    True),   # Sertifika bitiş tarihi
    StructField("assessment_year",   IntegerType(), True),   # Değerlendirme yılı
    StructField("certifying_body",   StringType(),  True),   # Sertifika veren kurum
    StructField("country",           StringType(),  False),  # ISO ülke kodu
    StructField("methodology",       StringType(),  True),   # Hesaplama yöntemi
])

print("✅ Şema tanımlandı")


# =============================================================================
# BÖLÜM 3 — EPC VERİSİ (6 Demo Bina)
# =============================================================================
#
# Bina profilleri (silver_building_master'dan):
#   B001 → Frankfurt Office DE  (5.200 m², 1998 yapım, ofis)
#   B002 → Munich Retail DE     (8.400 m², 2005 yapım, perakende)
#   B003 → Vienna Hotel AT      (4.100 m², 2010 yapım, otel)
#   B004 → Amsterdam Office NL  (6.800 m², 2015 yapım, ofis — BREEAM Good)
#   B005 → Berlin Healthcare DE (3.200 m², 2008 yapım, sağlık)
#   B006 → Amsterdam Univ. NL  (7.500 m², 2018 yapım, eğitim)
#
# EPC sınıflandırması:
#   B001 Almanya ofis (1998) → D sınıfı (eski Alman ofisleri tipik 160-180 kWh/m²)
#   B002 Alman perakende     → E sınıfı (büyük retail, yüksek aydınlatma+klima)
#   B003 Avusturya otel      → C sınıfı (2010 sonrası, orta-iyi)
#   B004 NL ofis (2015)      → B sınıfı (modern, NL şartnameleri daha sıkı)
#   B005 Alman sağlık        → D sınıfı (hastane/klinik — 7/24 operasyon)
#   B006 NL üniversite(2018) → B sınıfı (modern kampüs binası, iyi yalıtım)
#
# CO₂ dönüşüm faktörleri:
#   DE grid 2023: ~0.38 kgCO₂/kWh (Umweltbundesamt)
#   NL grid 2023: ~0.28 kgCO₂/kWh (CBS / RVO)
#   AT grid 2023: ~0.20 kgCO₂/kWh (Statistik Austria — hidro ağırlıklı)
# =============================================================================

epc_rows = [
    # (building_id, epc_class, score_kwh, co2_kg, valid_from, valid_to, year, body, country, method)
    (
        "B001", "D", 172.0, 65.4,
        "2021-03-15", "2031-03-15",
        2021, "TÜV Rheinland", "DE",
        "Bedarfsausweis (DIN V 18599)"
    ),
    (
        "B002", "E", 224.0, 85.1,
        "2020-07-01", "2030-07-01",
        2020, "DEKRA Certification GmbH", "DE",
        "Verbrauchsausweis (EnEV 2016)"
    ),
    (
        "B003", "C", 138.0, 27.6,
        "2022-01-20", "2032-01-20",
        2022, "TÜV Austria", "AT",
        "Energieausweis (OIB RL 6:2019)"
    ),
    (
        "B004", "B", 87.0, 24.4,
        "2021-09-10", "2031-09-10",
        2021, "DGMR Bouw BV", "NL",
        "Energielabel (NTA 8800:2020)"
    ),
    (
        "B005", "D", 188.0, 71.4,
        "2019-04-05", "2029-04-05",
        2019, "TÜV Rheinland", "DE",
        "Bedarfsausweis (DIN V 18599)"
    ),
    (
        "B006", "B", 93.0, 26.0,
        "2023-02-28", "2033-02-28",
        2023, "Nieman Raadgevende Ingenieurs", "NL",
        "Energielabel (NTA 8800:2021)"
    ),
]

print(f"📋 {len(epc_rows)} bina için EPC verisi hazırlandı")
for r in epc_rows:
    print(f"   {r[0]} → Sınıf {r[1]}  ({r[2]:.0f} kWh/m²/yıl)  [{r[8]}]")


# =============================================================================
# BÖLÜM 4 — DATAFRAME OLUŞTURMA + TİP DÖNÜŞÜMÜ
# =============================================================================

_raw_schema = StructType([
    StructField("building_id",       StringType(),  False),
    StructField("epc_class",         StringType(),  False),
    StructField("epc_score_kwh_m2",  DoubleType(),  True),
    StructField("co2_kg_m2_year",    DoubleType(),  True),
    StructField("valid_from_str",    StringType(),  True),
    StructField("valid_to_str",      StringType(),  True),
    StructField("assessment_year",   IntegerType(), True),
    StructField("certifying_body",   StringType(),  True),
    StructField("country",           StringType(),  False),
    StructField("methodology",       StringType(),  True),
])

df_epc = (
    spark.createDataFrame(epc_rows, schema=_raw_schema)
    .withColumn("valid_from",  to_date(col("valid_from_str"), "yyyy-MM-dd"))
    .withColumn("valid_to",    to_date(col("valid_to_str"),   "yyyy-MM-dd"))
    .drop("valid_from_str", "valid_to_str")
    .withColumn("updated_at",  current_timestamp())
    .select(
        "building_id",
        "epc_class",
        "epc_score_kwh_m2",
        "co2_kg_m2_year",
        "valid_from",
        "valid_to",
        "assessment_year",
        "certifying_body",
        "country",
        "methodology",
        "updated_at",
    )
)

print("\n📊 EPC DataFrame şeması:")
df_epc.printSchema()
df_epc.show(truncate=False)


# =============================================================================
# BÖLÜM 5 — SILVER'A YAZ (MERGE ile upsert)
# =============================================================================
#
# Strateji: building_id bazında MERGE (upsert).
#   → Aynı bina için EPC güncellendiğinde mevcut satırı günceller.
#   → Yeni bina geldiğinde insert eder.
#   → Overwrite kullanmıyoruz: diğer bina sertifikaları korunur.
# =============================================================================

def table_exists_epc(table_name: str) -> bool:
    # spark.read.format("delta").load() relative path Fabric'te çalışmıyor.
    # Catalog sorgusu güvenilir — saveAsTable ile oluşturulan tablolar burada görünür.
    try:
        return spark.catalog.tableExists(table_name)
    except Exception:
        return False


if not table_exists_epc(OUTPUT_TABLE_NAME):
    # İlk çalıştırma — tablo henüz yok, overwrite ile oluştur
    print(f"\n🆕 Tablo yok — ilk kez oluşturuluyor: {OUTPUT_TABLE_NAME}")
    (df_epc.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(OUTPUT_TABLE_NAME)
    )
    print(f"✅ {OUTPUT_TABLE_NAME} oluşturuldu: {df_epc.count()} satır")
else:
    # Tablo mevcut — building_id bazında MERGE/upsert
    print(f"\n🔄 Mevcut tablo güncelleniyor (MERGE): {OUTPUT_TABLE_NAME}")
    dt = DeltaTable.forName(spark, OUTPUT_TABLE_NAME)
    (dt.alias("tgt")
       .merge(
           df_epc.alias("src"),
           "tgt.building_id = src.building_id"
       )
       .whenMatchedUpdateAll()
       .whenNotMatchedInsertAll()
       .execute()
    )
    total = spark.read.table(OUTPUT_TABLE_NAME).count()
    print(f"✅ MERGE tamamlandı — Toplam {total} bina EPC kaydı")


# =============================================================================
# BÖLÜM 6 — VALİDASYON
# =============================================================================

print("\n" + "="*60)
print("VALİDASYON — silver_epc_ratings")
print("="*60)

# spark.read.table() catalog üzerinden okur — relative path hatası olmaz
df_check = spark.read.table(OUTPUT_TABLE_NAME)
total_rows = df_check.count()
print(f"Toplam kayıt: {total_rows}")

print("\nEPC Sınıf Dağılımı:")
df_check.groupBy("epc_class", "country") \
    .agg(
        {"epc_score_kwh_m2": "avg", "co2_kg_m2_year": "avg", "building_id": "count"}
    ) \
    .withColumnRenamed("avg(epc_score_kwh_m2)", "avg_score_kwh_m2") \
    .withColumnRenamed("avg(co2_kg_m2_year)", "avg_co2_kg_m2") \
    .withColumnRenamed("count(building_id)", "bina_sayisi") \
    .orderBy("epc_class", "country") \
    .show(truncate=False)

print("\nDetaylı liste (bina bazlı):")
df_check.select(
    "building_id", "epc_class", "epc_score_kwh_m2",
    "co2_kg_m2_year", "valid_from", "valid_to", "country"
).orderBy("building_id").show(truncate=False)

# Beklenen kontroller
assert total_rows >= 6, f"❌ Beklenen en az 6 satır, var: {total_rows}"
classes_present = [r.epc_class for r in df_check.select("epc_class").distinct().collect()]
print(f"\nMevcut EPC sınıfları: {sorted(classes_present)}")
assert len(classes_present) >= 3, "❌ En az 3 farklı EPC sınıfı bekleniyor"

print("\n✅ Validasyon BAŞARILI — silver_epc_ratings hazır")
print(f"   Power BI Page 6 EPC kartı bu tabloyu okuyacak.")
print(f"   Semantic model refresh sonrası aktif hale gelir.")
