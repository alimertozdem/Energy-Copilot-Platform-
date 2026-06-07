# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 02_data_quality_aggregator.py
# Layer: SILVER — Data Quality Summary Table
# =============================================================================
#
# GÖREV (Purpose):
#   silver_energy_consumption tablosundaki data_quality_flag kolonunu aylık
#   bazda bina başına özetle. Power BI Page 3 "Data Quality Score" kartını besler.
#
# KAYNAK TABLO: silver_energy_consumption
#   data_quality_flag değerleri:
#     "OK"           → Orijinal, doğrulanmış okuma
#     "INTERPOLATED" → Eksik veri interpolasyonla tamamlandı
#     "MISSING"      → Veri yok, 0 / null ile dolduruldu
#     "ANOMALY"      → Anlamsız değer tespit edildi
#
# HESAPLAMA MANTIĞI:
#   quality_score_pct = OK_readings / total_readings × 100
#   completeness_pct  = (total - MISSING) / total × 100
#   interpolation_pct = INTERPOLATED / total × 100
#
# OUTPUT:
#   Tables/silver_data_quality
#   Kolonlar: building_id, report_month, total_readings, ok_readings,
#             interpolated_readings, missing_readings, anomaly_readings,
#             quality_score_pct, completeness_pct, interpolation_pct,
#             quality_grade, updated_at
#
# NOT: Pipeline'da 02_silver_transformation.py'den SONRA çalıştırılmalı.
#      Her çalışmada overwrite — küçük tablo, incremental'a gerek yok.
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, LongType,
    TimestampType, DateType
)
from pyspark.sql.functions import (
    col, lit, current_timestamp, date_trunc,
    count, sum as spark_sum, when,
    round as spark_round, expr
)
from delta.tables import DeltaTable

spark.conf.set("spark.sql.shuffle.partitions", "8")

SOURCE_TABLE  = "Tables/silver_energy_readings_clean"   # 02_silver_transformation.py çıktısı
OUTPUT_TABLE  = "Tables/silver_data_quality"
OUTPUT_NAME   = "silver_data_quality"

print("✅ Data Quality Aggregator başlatıldı")


# =============================================================================
# BÖLÜM 2 — KAYNAK VERİYİ OKU
# =============================================================================

def try_read_table(table_name: str):
    """Tabloyu okumayı dene — hem catalog hem path üzerinden dener."""
    try:
        # Önce catalog adıyla dene (saveAsTable ile yazılmışsa)
        df = spark.read.table(table_name)
        df.limit(1).count()
        return df
    except Exception:
        pass
    try:
        # Sonra Tables/ path'iyle dene (spark.sql ile yazılmışsa)
        df = spark.read.format("delta").load(f"Tables/{table_name}")
        df.limit(1).count()
        return df
    except Exception:
        return None


_src_name = SOURCE_TABLE.replace("Tables/", "")
df_silver = try_read_table(_src_name)

if df_silver is None:
    raise ValueError(
        f"❌ Kaynak tablo bulunamadı: {_src_name}\n"
        f"   Önce 02_silver_transformation.py notebook'unu çalıştır\n"
        f"   ve EnergyCopilotLakehouse bağlı olduğundan emin ol."
    )

# Schema kontrolü — timestamp kolonu silver'da timestamp_utc adıyla geliyor
required_cols = {"building_id", "timestamp_utc", "data_quality_flag"}
present_cols  = set(df_silver.columns)
missing_cols  = required_cols - present_cols
if missing_cols:
    raise ValueError(f"❌ Eksik kolonlar silver_energy_readings_clean'de: {missing_cols}")

total_silver = df_silver.count()
print(f"📥 silver_energy_readings_clean: {total_silver:,} satır okundu")
print(f"   Kolon sayısı: {len(df_silver.columns)}")

print("\ndata_quality_flag dağılımı (kaynak):")
df_silver.groupBy("data_quality_flag").count().orderBy("count", ascending=False).show()


# =============================================================================
# BÖLÜM 3 — AYLIK KALİTE SKORLARINı HESAPLA
# =============================================================================
#
# report_month: timestamp kolonundan ay başı DATE (örn. 2023-01-01)
# Her bina × ay için ayrı satır.
#
# quality_grade (A-F skalası):
#   A → quality_score_pct ≥ 95%  (mükemmel — 1/20 okuma bile bozuk değil)
#   B → 85% ≤ score < 95%        (iyi)
#   C → 70% ≤ score < 85%        (orta — interpolasyon artıyor)
#   D → 50% ≤ score < 70%        (zayıf — dikkat gerekli)
#   E → 30% ≤ score < 50%        (kötü — çok fazla missing/anomaly)
#   F → score < 30%               (kritik — veri güvenilmez)
# =============================================================================

df_monthly = (
    df_silver
    .withColumn(
        "report_month",
        date_trunc("month", col("timestamp_utc")).cast(DateType())
    )
    .groupBy("building_id", "report_month")
    .agg(
        count("*").alias("total_readings"),
        spark_sum(when(col("data_quality_flag") == "OK",           1).otherwise(0)).alias("ok_readings"),
        spark_sum(when(col("data_quality_flag") == "INTERPOLATED", 1).otherwise(0)).alias("interpolated_readings"),
        spark_sum(when(col("data_quality_flag") == "MISSING",      1).otherwise(0)).alias("missing_readings"),
        spark_sum(when(col("data_quality_flag") == "ANOMALY",      1).otherwise(0)).alias("anomaly_readings"),
    )
)

df_scored = (
    df_monthly
    .withColumn(
        "quality_score_pct",
        spark_round(
            col("ok_readings") * 100.0 / col("total_readings"),
            1
        )
    )
    .withColumn(
        "completeness_pct",
        spark_round(
            (col("total_readings") - col("missing_readings")) * 100.0 / col("total_readings"),
            1
        )
    )
    .withColumn(
        "interpolation_pct",
        spark_round(
            col("interpolated_readings") * 100.0 / col("total_readings"),
            1
        )
    )
    .withColumn(
        "quality_grade",
        when(col("quality_score_pct") >= 95, lit("A"))
        .when(col("quality_score_pct") >= 85, lit("B"))
        .when(col("quality_score_pct") >= 70, lit("C"))
        .when(col("quality_score_pct") >= 50, lit("D"))
        .when(col("quality_score_pct") >= 30, lit("E"))
        .otherwise(lit("F"))
    )
    .withColumn("updated_at", current_timestamp())
    .orderBy("building_id", "report_month")
)

row_count = df_scored.count()
print(f"\n📊 Hesaplanan kayıt sayısı: {row_count} (bina × ay)")

print("\nÖrnek sonuçlar:")
df_scored.select(
    "building_id", "report_month",
    "total_readings", "ok_readings", "missing_readings",
    "quality_score_pct", "quality_grade"
).show(20, truncate=False)


# =============================================================================
# BÖLÜM 4 — SILVER'A YAZ
# =============================================================================
#
# Strateji: Tam overwrite.
#   - Tablo küçük (bina sayısı × ay sayısı — tipik ~100-500 satır)
#   - Silver transformation her çalıştıktan sonra bu da çalışır
#   - Incremental logic gereksiz karmaşıklık ekler
# =============================================================================

print(f"\n💾 {OUTPUT_NAME} yazılıyor...")

(df_scored.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(OUTPUT_NAME)
)

written = spark.read.table(OUTPUT_NAME).count()
print(f"✅ {OUTPUT_NAME}: {written} satır yazıldı")


# =============================================================================
# BÖLÜM 5 — VALİDASYON
# =============================================================================

print("\n" + "="*60)
print("VALİDASYON — silver_data_quality")
print("="*60)

df_val = spark.read.table(OUTPUT_NAME)

print(f"Toplam kayıt    : {df_val.count()}")
print(f"Benzersiz bina  : {df_val.select('building_id').distinct().count()}")
print(f"Tarih aralığı   : ", end="")
date_range = df_val.agg(
    {"report_month": "min"}
).collect()[0][0], df_val.agg({"report_month": "max"}).collect()[0][0]
print(f"{date_range[0]} → {date_range[1]}")

print("\nKalite Notu Dağılımı (quality_grade):")
df_val.groupBy("quality_grade").count().orderBy("quality_grade").show()

print("\nBina Bazlı Ortalama Kalite Skoru:")
df_val.groupBy("building_id") \
    .agg(
        {"quality_score_pct": "avg", "completeness_pct": "avg", "total_readings": "sum"}
    ) \
    .withColumnRenamed("avg(quality_score_pct)", "avg_quality_pct") \
    .withColumnRenamed("avg(completeness_pct)", "avg_completeness_pct") \
    .withColumnRenamed("sum(total_readings)", "total_readings") \
    .orderBy("building_id") \
    .show(truncate=False)

# NULL kontrol
null_scores = df_val.filter(col("quality_score_pct").isNull()).count()
if null_scores > 0:
    print(f"⚠️  quality_score_pct NULL olan {null_scores} satır var — kontrol et")
else:
    print("✅ NULL değer yok — quality_score_pct tamam")

print("\n✅ Validasyon BAŞARILI — silver_data_quality hazır")
print("   Power BI Page 3 Data Quality Score kartı bu tabloyu kullanabilir.")
