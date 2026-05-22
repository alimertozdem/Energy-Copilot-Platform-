# =============================================================================
# NUCLEAR FIX — KOPYALA & ÇALIŞTIR
# Notebook: 01_NUCLEAR_FIX_KOPYALA.py
# Tarih: 2026-05-14
#
# AMAÇ:
#   Fabric Lakehouse'taki raw_energy_readings.csv hâlâ v4. Manuel upload
#   güvenilmez oldu. Bu notebook:
#     1. Mevcut CSV'yi (varsa) Fabric'ten siler
#     2. v5.1 CSV'yi Fabric Files'a yazdırır (DIRECT spark.write)
#     3. Bronze tablosunu siler (watermark dahil)
#     4. Doğrulama: bronze re-read sonrası v5.1 değerleri kontrol
#
# KULLANIM:
#   ÖNEMLİ ÖN HAZIRLIK:
#     1. Lokal v5.1 CSV'yi Fabric'e yükle: Lakehouse → Files → "Upload" →
#        local: C:\Energy Management App\Energy-copilot-platform\sample-data\
#               raw_energy_readings.csv
#     2. Yüklerken İSİM: "raw_energy_readings_NEW.csv" olarak değiştir
#        (mevcut v4'ün üzerine yazmasın diye)
#     3. Sonra bu notebook'u çalıştır → bu notebook v4'ü siler, NEW'i adlandırır
#
#   ALTERNATIF: Aşağıdaki "VERIFY_ONLY" modunu True yap → mevcut CSV'nin
#   sürümünü kontrol et, yeniden yüklemeden teşhis yap.
# =============================================================================

# ── KONFIG ──────────────────────────────────────────────────────────────────
VERIFY_ONLY        = True     # ← Önce bunu çalıştır, sonucu gör
DELETE_OLD_CSV     = False    # ← Eski v4 CSV'yi sil (Verify sonrası True yap)
RENAME_NEW_CSV     = False    # ← raw_energy_readings_NEW.csv → raw_energy_readings.csv
DROP_BRONZE        = False    # ← bronze_raw_energy_readings tablosunu sil

OLD_CSV_PATH = "Files/sample-data/raw_energy_readings.csv"
NEW_CSV_PATH = "Files/sample-data/raw_energy_readings_NEW.csv"

# ── FS utility (Fabric uyumlu) ──────────────────────────────────────────────
fs_util = None
try:
    import notebookutils
    fs_util = notebookutils.fs
    print("✅ FS utility: notebookutils.fs")
except (ImportError, NameError):
    try:
        fs_util = mssparkutils.fs  # noqa
        print("✅ FS utility: mssparkutils.fs")
    except NameError:
        print("⚠️  FS utility BULUNAMADI — dosya işlemleri yapılamayacak")

print()

# ── 1. VERIFY: Mevcut CSV'nin sürümünü oku ──────────────────────────────────
print("=" * 65)
print("📊 1. AŞAMA: Lakehouse'taki mevcut CSV'yi doğrula")
print("=" * 65)

try:
    df_check = spark.read.option("header", True).csv(OLD_CSV_PATH)

    # B001 ve B006 için kritik timestamps oku
    from pyspark.sql.functions import col

    b001_test = df_check.filter(
        (col("building_id") == "B001") &
        (col("timestamp_utc") == "2024-07-01 12:00:00")
    ).select("raw_value").collect()

    b006_test = df_check.filter(
        (col("building_id") == "B006") &
        (col("timestamp_utc") == "2025-01-15 10:00:00")
    ).select("raw_value").collect()

    b001_val = float(b001_test[0]["raw_value"]) if b001_test else None
    b006_val = float(b006_test[0]["raw_value"]) if b006_test else None

    print(f"   B001 2024-07-01 12:00 raw_value: {b001_val}")
    print(f"   B006 2025-01-15 10:00 raw_value: {b006_val}")
    print()

    # SÜRÜM TESPİTİ
    if b006_val is None:
        print("   ❌ B006 kayıt bulunamadı — CSV bozuk olabilir")
        csv_version = "UNKNOWN"
    elif 150 <= b006_val <= 200:
        print(f"   ✅ B006 raw_value {b006_val} → v5.1 RANGE (150-200) — DOĞRU!")
        csv_version = "v5.1"
    elif 30 <= b006_val <= 60:
        print(f"   ❌ B006 raw_value {b006_val} → v4 RANGE (30-60) — ESKİ!")
        csv_version = "v4"
    else:
        print(f"   ⚠️  B006 raw_value {b006_val} → beklenmedik aralık")
        csv_version = "UNKNOWN"

    print()
    print(f"📌 SONUÇ: Lakehouse Files'taki CSV → {csv_version}")

except Exception as e:
    print(f"   ❌ CSV okunamadı: {str(e)[:200]}")
    csv_version = "ERROR"

print()

# ── 2. VERIFY: NEW CSV varsa onu da kontrol et ─────────────────────────────
print("=" * 65)
print("📊 2. AŞAMA: NEW CSV (eğer yüklendiyse) doğrulama")
print("=" * 65)

new_csv_version = None
try:
    df_new = spark.read.option("header", True).csv(NEW_CSV_PATH)
    b006_new = df_new.filter(
        (col("building_id") == "B006") &
        (col("timestamp_utc") == "2025-01-15 10:00:00")
    ).select("raw_value").collect()

    if b006_new:
        b006_new_val = float(b006_new[0]["raw_value"])
        print(f"   NEW CSV B006 raw_value: {b006_new_val}")
        if 150 <= b006_new_val <= 200:
            print(f"   ✅ NEW CSV → v5.1 (kullanılabilir)")
            new_csv_version = "v5.1"
        else:
            print(f"   ❌ NEW CSV → v5.1 değil")
            new_csv_version = "OTHER"
    else:
        print("   ⚠️  NEW CSV var ama B006 kaydı yok")
except Exception:
    print(f"   ℹ️  NEW CSV henüz yok (yüklenmemiş)")
    new_csv_version = None

print()

# ── 3. ÖNERİ ──────────────────────────────────────────────────────────────
print("=" * 65)
print("📌 ÖNERİ")
print("=" * 65)

if csv_version == "v5.1":
    print("✅ Mevcut CSV ZATEN v5.1 — başka bir cache problemi var.")
    print("   Yapacak: bronze_raw_energy_readings tablosunu drop edip")
    print("            bronze notebook'u tekrar çalıştır.")
elif csv_version == "v4" and new_csv_version == "v5.1":
    print("🔄 v4 CSV var, v5.1 NEW CSV yüklenmiş.")
    print("   Yapacak: Aşağıdaki konfigleri True yap, hücreyi tekrar çalıştır:")
    print("     DELETE_OLD_CSV  = True")
    print("     RENAME_NEW_CSV  = True")
    print("     DROP_BRONZE     = True")
elif csv_version == "v4":
    print("❌ v4 CSV var, NEW CSV yüklenmemiş.")
    print("   Yapacak:")
    print("     1. Lokal v5.1 dosyayı Lakehouse'a yükle:")
    print("        - Lakehouse → Files → sample-data → Upload")
    print("        - Lokal dosya: C:\\Energy Management App\\")
    print("          Energy-copilot-platform\\sample-data\\")
    print("          raw_energy_readings.csv")
    print("        - ÖNEMLİ: Yükleme sırasında dosya adını şu şekilde değiştir:")
    print("          'raw_energy_readings_NEW.csv'")
    print("     2. Sonra bu notebook'u tekrar çalıştır")
    print("        DELETE_OLD_CSV/RENAME_NEW_CSV/DROP_BRONZE = True yap")
else:
    print("⚠️  Belirsiz durum. Yukarıdaki output'u oku, manuel kontrol gerek.")

print()

# ── 4. EYLEM AŞAMASI ────────────────────────────────────────────────────────

if not VERIFY_ONLY:
    print("=" * 65)
    print("⚡ 3. AŞAMA: EYLEMLER")
    print("=" * 65)

    if DELETE_OLD_CSV and fs_util is not None:
        try:
            fs_util.rm(OLD_CSV_PATH)
            print(f"   ✅ Silindi: {OLD_CSV_PATH}")
        except Exception as e:
            print(f"   ⚠️  Silinemedi: {str(e)[:100]}")

    if RENAME_NEW_CSV and fs_util is not None:
        try:
            # Rename = copy + delete (Fabric'te direct rename yok)
            df_new = spark.read.option("header", True).csv(NEW_CSV_PATH)
            df_new.coalesce(1).write.mode("overwrite").option("header", True).csv(OLD_CSV_PATH)
            print(f"   ✅ Kopyalandı: {NEW_CSV_PATH} → {OLD_CSV_PATH}")
            # Note: bu coalesce(1) ile tek dosya olarak yazar
            # Ama yine de subdirectory yaratabilir, dikkat
        except Exception as e:
            print(f"   ⚠️  Rename başarısız: {str(e)[:200]}")

    if DROP_BRONZE:
        try:
            spark.sql("DROP TABLE IF EXISTS bronze_raw_energy_readings")
            print("   ✅ DROP TABLE: bronze_raw_energy_readings")
            spark.sql("DROP TABLE IF EXISTS bronze_watermarks")
            print("   ✅ DROP TABLE: bronze_watermarks")
        except Exception as e:
            print(f"   ⚠️  DROP failed: {str(e)[:200]}")

    print()
    print("🚀 SONRAKİ ADIM: 01_bronze_ingestion.py notebook'u çalıştır")

print()
print("=" * 65)
print("✅ İŞLEM TAMAMLANDI")
print("=" * 65)
