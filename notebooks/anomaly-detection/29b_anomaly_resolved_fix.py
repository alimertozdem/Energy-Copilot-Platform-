# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 29b_anomaly_resolved_fix.py
# Layer: GOLD — gold_anomaly_log is_resolved Fix
# =============================================================================
#
# AMAÇ:
#   anomaly_detection.py BÖLÜM 7b'deki spark.sql UPDATE Fabric'te
#   exception yakalanıp sessizce geçiliyor → is_resolved %100 FALSE kalıyor.
#   Bu notebook o adımı DELTA TABLE API ile güvenilir şekilde çalıştırır.
#
# NEDEN AYRI NOTEBOOK?
#   anomaly_detection.py çalıştırmadan sadece is_resolved güncellemek için
#   yeniden anomaly detection yapmak gereksiz ve yavaş.
#   Bu notebook tek amaca odaklanır: is_resolved güncelle + doğrula.
#
# ÇÖZÜM YÖNTEMİ:
#   spark.sql UPDATE → DeltaTable API ile MERGE + withColumn UPDATE
#   Fabric'te DeltaTable API daha güvenilir çalışır.
#   Deterministik seçim (hash modulo) korundu — aynı çalıştırmalar
#   aynı satırları seçer.
#
# ÇALIŞTIRILMA SIRASI:
#   anomaly_detection.py → 02_data_quality_aggregator.py → [bu notebook]
#
# ÇÖZÜM ORANI (severity bazlı, anomaly_detection.py ile aynı):
#   CRITICAL : hash % 20 < 3  → ~%15
#   HIGH     : hash % 20 < 5  → ~%25
#   MEDIUM   : hash % 10 < 4  → ~%40
#   LOW      : hash % 10 < 4  → ~%40
#   Kural: Sadece 45 günden eski anomaly'ler hedef alınır.
# =============================================================================


# =============================================================================
# BÖLÜM 1 — IMPORT VE KONFİGÜRASYON
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, abs as spark_abs, hash as spark_hash,
    current_date, datediff, when
)
from delta.tables import DeltaTable

ANOMALY_TABLE    = "gold_anomaly_log"   # Catalog table adı (Tables/ prefix olmadan)
RESOLVED_CUTOFF  = 45                  # Kaç günden eski → resolved adayı

print("=" * 60)
print("gold_anomaly_log — is_resolved Fix Notebook")
print("=" * 60)
print(f"Hedef tablo : {ANOMALY_TABLE}")
print(f"Resolved cutoff: {RESOLVED_CUTOFF} gün")


# =============================================================================
# BÖLÜM 2 — TABLOYU OKU VE MEVCUT DURUMU RAPORLA
# =============================================================================

def try_read(table_name: str):
    """Catalog ve path yöntemlerini sırayla dene."""
    for attempt in ["catalog", "path"]:
        try:
            if attempt == "catalog":
                df = spark.read.table(table_name)
            else:
                df = spark.read.format("delta").load(f"Tables/{table_name}")
            df.limit(1).count()
            print(f"   ✅ Tablo okundu ({attempt} yöntemi)")
            return df, attempt
        except Exception as e:
            print(f"   ⚠️  {attempt} yöntemi başarısız: {str(e)[:80]}")
    return None, None


print("\n📖 Mevcut tablo durumu okunuyor...")
df_before, read_method = try_read(ANOMALY_TABLE)

if df_before is None:
    raise ValueError(
        f"❌ {ANOMALY_TABLE} tablosu bulunamadı.\n"
        f"   Önce anomaly_detection.py çalıştır."
    )

total_before    = df_before.count()
resolved_before = df_before.filter(col("is_resolved") == True).count()
open_before     = total_before - resolved_before

print(f"\n   ÖNCE:")
print(f"   Toplam    : {total_before:,}")
print(f"   Resolved  : {resolved_before:,}  ({100*resolved_before/max(total_before,1):.0f}%)")
print(f"   Open      : {open_before:,}  ({100*open_before/max(total_before,1):.0f}%)")

if resolved_before == total_before:
    print("\n   ℹ️  Tüm anomaly'ler zaten resolved — güncelleme gerekmiyor.")
elif resolved_before > 0:
    print(f"\n   ℹ️  {resolved_before} anomaly zaten resolved — delta update yapılacak.")
else:
    print("\n   ⚠️  Hiç resolved anomaly yok — güncelleme gerekli.")


# =============================================================================
# BÖLÜM 3 — RESOLVED FLAG HESAPLA
#
# Strateji: Tüm tabloyu oku → Python'da flag hesapla → DeltaTable MERGE ile yaz.
# Bu yöntem spark.sql UPDATE'e göre Fabric'te daha güvenilir.
#
# Seçim mantığı (deterministik hash — anomaly_detection.py ile aynı):
#   hash(anomaly_id) = abs(hashlib benzeri SparkSQL hash) % N < threshold
#   CRITICAL : N=20, threshold=3  → ~%15
#   HIGH     : N=20, threshold=5  → ~%25
#   MEDIUM   : N=10, threshold=4  → ~%40
#   LOW      : N=10, threshold=4  → ~%40
# =============================================================================

print("\n🔄 Resolved flag hesaplanıyor (hash-based, deterministik)...")

# Yaşı hesapla + hash seçim mantığını uygula
df_flagged = (
    df_before
    .withColumn("_age_days", datediff(current_date(), col("detected_date")))
    .withColumn(
        "_new_resolved",
        when(
            # Zaten resolved → değiştirme
            col("is_resolved") == True, lit(True)
        ).when(
            # 45 günden yeni → hâlâ open
            col("_age_days") < RESOLVED_CUTOFF, lit(False)
        ).when(
            col("severity") == "CRITICAL",
            # hash % 20 < 3 → ~%15
            (spark_abs(spark_hash(col("anomaly_id"))) % 20) < 3
        ).when(
            col("severity") == "HIGH",
            # hash % 20 < 5 → ~%25
            (spark_abs(spark_hash(col("anomaly_id"))) % 20) < 5
        ).when(
            col("severity").isin("MEDIUM", "LOW", "INFORMATIONAL"),
            # hash % 10 < 4 → ~%40
            (spark_abs(spark_hash(col("anomaly_id"))) % 10) < 4
        ).otherwise(lit(False))
    )
)

# Kaç satır değişecek?
changes = (
    df_flagged
    .filter(col("_new_resolved") != col("is_resolved"))
    .count()
)
will_resolve = (
    df_flagged
    .filter((col("_new_resolved") == True) & (col("is_resolved") == False))
    .count()
)

print(f"   Değişecek satır sayısı : {changes:,}")
print(f"   → Open → Resolved     : {will_resolve:,}")

# Sadece güncellenecek satırları hazırla (is_resolved değişenler)
df_updates = (
    df_flagged
    .filter(col("_new_resolved") != col("is_resolved"))
    .select(
        col("anomaly_id"),
        col("_new_resolved").alias("is_resolved_new")
    )
)

if will_resolve == 0 and resolved_before > 0:
    print("\n✅ Güncelleme gerekmez — zaten doğru durumda.")
else:
    # ==========================================================================
    # BÖLÜM 4 — DELTA TABLE MERGE İLE YAZ
    # ==========================================================================

    print("\n💾 DeltaTable MERGE çalıştırılıyor...")

    # DeltaTable nesnesi — catalog ya da path üzerinden
    try:
        dt = DeltaTable.forName(spark, ANOMALY_TABLE)
        print("   ✅ DeltaTable.forName başarılı")
    except Exception as e1:
        print(f"   ⚠️  forName başarısız: {str(e1)[:80]}")
        try:
            dt = DeltaTable.forPath(spark, f"Tables/{ANOMALY_TABLE}")
            print("   ✅ DeltaTable.forPath başarılı")
        except Exception as e2:
            raise RuntimeError(
                f"❌ DeltaTable açılamadı. forName: {e1} | forPath: {e2}"
            )

    (
        dt.alias("target")
        .merge(
            df_updates.alias("src"),
            "target.anomaly_id = src.anomaly_id"
        )
        .whenMatchedUpdate(set={"is_resolved": "src.is_resolved_new"})
        .execute()
    )

    print("   ✅ MERGE tamamlandı")


# =============================================================================
# BÖLÜM 5 — DOĞRULAMA
# =============================================================================

print("\n" + "=" * 60)
print("DOĞRULAMA")
print("=" * 60)

df_after = spark.read.table(ANOMALY_TABLE)
total_after    = df_after.count()
resolved_after = df_after.filter(col("is_resolved") == True).count()
open_after     = total_after - resolved_after

print(f"\n   SONRA:")
print(f"   Toplam    : {total_after:,}")
print(f"   Resolved  : {resolved_after:,}  ({100*resolved_after/max(total_after,1):.0f}%)")
print(f"   Open      : {open_after:,}  ({100*open_after/max(total_after,1):.0f}%)")

print(f"\n   DEĞIŞIM:")
print(f"   Yeni resolved  : {resolved_after - resolved_before:,}")
print(f"   Açık kalan     : {open_after:,}")

# Beklenti: ~%25-40 resolved olmalı
expected_min = int(total_after * 0.20)
expected_max = int(total_after * 0.45)

if expected_min <= resolved_after <= expected_max:
    print(f"\n✅ BAŞARILI — Resolved oranı {100*resolved_after/total_after:.0f}% (beklenen: 20-45%)")
elif resolved_after == 0:
    print(f"\n❌ BAŞARISIZ — Hiç resolved yok! MERGE çalışmış olabilir ama etkisi olmadı.")
    print("   → Tabloyu kontrol et: spark.read.table('gold_anomaly_log').groupBy('is_resolved').count().show()")
else:
    print(f"\n⚠️  UYARI — Resolved oranı {100*resolved_after/total_after:.0f}% (beklenen aralık dışı)")

print("\nSeverity bazlı resolved dağılımı:")
df_after.groupBy("severity", "is_resolved").count().orderBy("severity", "is_resolved").show()

print("\nAnomaly tipi bazlı open count:")
df_after.filter(col("is_resolved") == False).groupBy("anomaly_type", "severity").count().orderBy("severity", "anomaly_type").show()

print("\n✅ 29b_anomaly_resolved_fix tamamlandı")
print("   Power BI'ı refresh et → Page 3 Unresolved kartı güncellenir.")
