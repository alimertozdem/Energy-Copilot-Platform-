# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 29c_anomaly_status_column_patch.py
# Layer: GOLD — gold_anomaly_log schema patch
# =============================================================================
#
# AMAÇ:
#   Direct Lake modunda DAX calculated column eklenemiyor.
#   Bu notebook gold_anomaly_log Delta tablosuna doğrudan
#   "anomaly_status" string kolonu ekler:
#     is_resolved = TRUE  → "Resolved"
#     is_resolved = FALSE → "Open"
#
#   Power BI bu kolonu Direct Lake üzerinden otomatik görür (refresh sonrası).
#
# ÇALIŞTIRILMA:
#   29b_anomaly_resolved_fix.py'dan SONRA çalıştır (is_resolved güncel olsun)
#   Fabric workspace → bu notebook → Run All
#   Power BI → Refresh (semantic model) → "anomaly_status" kolonu gelir
# =============================================================================

from pyspark.sql.functions import col, when, lit
from delta.tables import DeltaTable

ANOMALY_TABLE = "gold_anomaly_log"

print("=" * 60)
print("gold_anomaly_log — anomaly_status Kolon Patch")
print("=" * 60)

# ── Tabloyu oku
try:
    df = spark.read.table(ANOMALY_TABLE)
    print(f"✅ Tablo okundu: {df.count():,} satır")
except Exception as e:
    raise RuntimeError(f"❌ Tablo okunamadı: {e}")

# ── Mevcut kolon kontrolü
if "anomaly_status" in df.columns:
    print("ℹ️  'anomaly_status' kolonu zaten var — güncelleniyor...")
else:
    print("➕ 'anomaly_status' kolonu ekleniyor...")

# ── Yeni kolon hesapla
df_patched = df.withColumn(
    "anomaly_status",
    when(col("is_resolved") == True, lit("Resolved"))
    .otherwise(lit("Open"))
)

# ── Dağılımı göster
print("\nAnomaly Status dağılımı (yeni kolon):")
df_patched.groupBy("anomaly_status").count().show()

# ── Delta tablosuna overwrite yaz
print(f"\n💾 {ANOMALY_TABLE} yeniden yazılıyor (overwriteSchema=true)...")
(
    df_patched.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(ANOMALY_TABLE)
)

# ── Doğrulama
df_check = spark.read.table(ANOMALY_TABLE)
print(f"\n✅ Tamamlandı — {df_check.count():,} satır yazıldı")
print(f"   Kolonlar: {df_check.columns}")
print("\nSon 3 satır:")
df_check.select("building_id", "anomaly_type", "severity", "is_resolved", "anomaly_status") \
        .orderBy("detected_date", ascending=False) \
        .limit(3).show(truncate=False)

print("\n✅ Power BI semantic model'i refresh et → 'anomaly_status' kolonu görünür.")
