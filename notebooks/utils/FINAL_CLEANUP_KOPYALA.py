# =============================================================================
# FINAL CLEANUP — KOPYALA & ÇALIŞTIR (TEK HÜCRE)
# Notebook: FINAL_CLEANUP_KOPYALA.py
# Tarih: 2026-05-15
#
# DURUM:
#   - Files/ kökünde 3 farklı raw_energy_readings* dosyası var (çift uzantılı 2 tane bug, 1 temiz)
#   - Dosyalar Files/sample-data/ KLASÖRÜNE değil Files/ köküne yüklenmiş
#   - Bronze notebook Files/sample-data/raw_energy_readings.csv arıyor
#
# BU NOTEBOOK NE YAPIYOR:
#   1. Files/ kökündeki TÜM dosyaları listeler (teşhis)
#   2. raw_energy_readings.csv (en temiz isim, 5/14/2026 tarihli) → v5.1 mi doğrular
#   3. Doğrulama OK ise → Files/sample-data/ klasörüne taşır
#   4. Çift uzantılı bug dosyalarını siler
#   5. Bronze tablosunu drop eder
#   6. SONRAKİ ADIM talimatını verir
#
# KULLANIM:
#   1. Fabric'te yeni notebook aç (ya da mevcut nuclear_fix'i kullan)
#   2. Lakehouse'a bağlı olduğundan emin ol
#   3. Bu dosyanın TAMAMINI tek hücreye yapıştır
#   4. Run all → 1-2 dakika sürer
# =============================================================================

print("=" * 70)
print("🔧 FINAL CLEANUP — Energy Copilot Platform")
print("=" * 70)
print()

# FS utility yükle
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
        print("❌ FS utility BULUNAMADI — duramaz, çık")
        raise SystemExit("FS utility yok")

print()

# ── 1. AŞAMA: Files/ kökünü listele ─────────────────────────────────────────
print("=" * 70)
print("📋 1. Files/ KÖKÜNDEKİ TÜM DOSYALAR")
print("=" * 70)

try:
    root_files = fs_util.ls("Files")
    for f in root_files:
        is_dir = f.isDir if hasattr(f, "isDir") else False
        size_mb = (f.size or 0) / 1024 / 1024
        marker = "📁" if is_dir else "📄"
        print(f"   {marker} {f.name:50s}  {size_mb:>8.1f} MB")
except Exception as e:
    print(f"   ❌ Listeleme başarısız: {e}")

print()

# ── 2. AŞAMA: sample-data/ klasörünü listele ────────────────────────────────
print("=" * 70)
print("📋 2. Files/sample-data/ KLASÖRÜNDEKI DOSYALAR")
print("=" * 70)

try:
    sample_files = fs_util.ls("Files/sample-data")
    for f in sample_files:
        size_mb = (f.size or 0) / 1024 / 1024
        print(f"   📄 {f.name:50s}  {size_mb:>8.1f} MB")
except Exception as e:
    print(f"   ⚠️ sample-data listeleme: {e}")

print()

# ── 3. AŞAMA: raw_energy_readings.csv'yi doğrula (eğer Files/ kökündeyse) ──
print("=" * 70)
print("🔍 3. raw_energy_readings.csv v5.1 DOĞRULAMASI (Files/ kökünde)")
print("=" * 70)

candidate_paths = [
    "Files/raw_energy_readings.csv",
    "Files/sample-data/raw_energy_readings.csv",
]

verified_path = None
for path in candidate_paths:
    try:
        df_check = spark.read.option("header", True).csv(path)
        from pyspark.sql.functions import col
        b006 = df_check.filter(
            (col("building_id") == "B006") &
            (col("timestamp_utc") == "2025-01-15 10:00:00")
        ).select("raw_value").collect()
        if b006:
            val = float(b006[0]["raw_value"])
            version = "v5.1" if 150 <= val <= 200 else ("v4" if 30 <= val <= 60 else "BİLİNMİYOR")
            print(f"   📄 {path}")
            print(f"      B006 2025-01-15 10:00 → {val} ({version})")
            if version == "v5.1":
                verified_path = path
                print(f"      ✅ v5.1 doğrulandı!")
        else:
            print(f"   📄 {path}: B006 kaydı yok")
    except Exception as e:
        msg = str(e)[:100]
        print(f"   📄 {path}: ❌ {msg}")

print()

# ── 4. AŞAMA: Eylem ─────────────────────────────────────────────────────────
print("=" * 70)
print("⚡ 4. EYLEM AŞAMASI")
print("=" * 70)

TARGET = "Files/sample-data/raw_energy_readings.csv"

if verified_path is None:
    print("❌ v5.1 raw_energy_readings.csv bulunamadı. Manuel kontrol gerek.")
elif verified_path == TARGET:
    print(f"✅ Dosya ZATEN doğru yerde: {TARGET}")
    print("   Yapacak: bronze drop + pipeline yeniden")
else:
    # Source = Files/ kökünde, hedef = Files/sample-data/
    SOURCE = verified_path
    print(f"📍 Source: {SOURCE}")
    print(f"📍 Target: {TARGET}")
    print()

    # Önce hedef var mı? Varsa sil
    try:
        existing = fs_util.ls(TARGET)
        print(f"   ⚠️ Hedef zaten var, siliniyor...")
        fs_util.rm(TARGET, True)
        print(f"   ✅ Eski hedef silindi")
    except Exception:
        print(f"   ℹ️ Hedef yok, devam")

    # Taşı (cp + rm)
    try:
        # mv() doğrudan çalışmazsa cp + rm yedek planı
        try:
            fs_util.mv(SOURCE, TARGET)
            print(f"   ✅ MV: {SOURCE} → {TARGET}")
        except Exception as e_mv:
            print(f"   ⚠️ mv başarısız ({str(e_mv)[:80]}), cp+rm deneniyor...")
            fs_util.cp(SOURCE, TARGET)
            fs_util.rm(SOURCE, True)
            print(f"   ✅ CP+RM: {SOURCE} → {TARGET}")
    except Exception as e:
        print(f"   ❌ Taşıma başarısız: {str(e)[:200]}")

print()

# ── 5. AŞAMA: Çift uzantılı bug dosyalarını sil ────────────────────────────
print("=" * 70)
print("🧹 5. ÇİFT UZANTILI BUG DOSYALARINI TEMİZLE")
print("=" * 70)

bug_files = [
    "Files/raw_energy_readings.csv.csv",
    "Files/raw_energy_readings_NEW.csv.csv",
    "Files/raw_energy_readings_NEW.csv",
]

for bug in bug_files:
    try:
        fs_util.rm(bug, True)
        print(f"   ✅ Silindi: {bug}")
    except Exception as e:
        msg = str(e)[:80]
        if "not found" in msg.lower() or "FileNotFound" in msg:
            print(f"   ⏭️ Zaten yok: {bug}")
        else:
            print(f"   ⚠️ Silinemedi: {bug} — {msg}")

print()

# ── 6. AŞAMA: Bronze tablosunu drop et ──────────────────────────────────────
print("=" * 70)
print("💥 6. BRONZE TABLOSUNU DROP ET")
print("=" * 70)

drop_tables = ["bronze_raw_energy_readings", "bronze_watermarks"]
for tbl in drop_tables:
    try:
        spark.sql(f"DROP TABLE IF EXISTS {tbl}")
        print(f"   ✅ DROP TABLE: {tbl}")
    except Exception as e:
        print(f"   ⚠️ DROP failed: {tbl} — {str(e)[:100]}")

print()

# ── 7. SON DOĞRULAMA ────────────────────────────────────────────────────────
print("=" * 70)
print("✅ 7. SON DOĞRULAMA — Files/sample-data/")
print("=" * 70)

try:
    final_files = fs_util.ls("Files/sample-data")
    for f in final_files:
        size_mb = (f.size or 0) / 1024 / 1024
        print(f"   📄 {f.name:50s}  {size_mb:>8.1f} MB")
except Exception as e:
    print(f"   ❌ Listeleme: {e}")

# v5.1 son test
try:
    df_final = spark.read.option("header", True).csv(TARGET)
    from pyspark.sql.functions import col
    b006_final = df_final.filter(
        (col("building_id") == "B006") &
        (col("timestamp_utc") == "2025-01-15 10:00:00")
    ).select("raw_value").collect()
    if b006_final:
        val = float(b006_final[0]["raw_value"])
        print()
        print(f"   🎯 {TARGET}")
        print(f"   🎯 B006 2025-01-15 10:00 → {val}")
        if 150 <= val <= 200:
            print(f"   🎯 ✅✅✅ v5.1 DOĞRULANDI — HER ŞEY HAZIR!")
        else:
            print(f"   🎯 ⚠️ Beklenmedik değer ({val}) — manuel kontrol")
except Exception as e:
    print(f"   ❌ Son test başarısız: {e}")

print()
print("=" * 70)
print("🚀 SONRAKI ADIM")
print("=" * 70)
print("""
1. Pipeline'ı sırayla çalıştır:
   01_bronze_ingestion → 02_silver_transformation → 03_gold_kpi_engine
   → anomaly_detection → 09_ghg_scope_engine → 10_crrem_pathway_loader
   → 11_hvac_analytics_engine → 07_consumption_forecast
   → 05_compliance_checker → 06_recommendation_engine
   → 12_battery_dispatch_and_simulation

2. SQL doğrulama:
   SELECT building_id, ROUND(SUM(total_consumption_kwh), 0) AS gold_kwh_2025
   FROM gold_kpi_daily WHERE YEAR(date) = 2025
   GROUP BY building_id ORDER BY building_id;

   Beklenen v5.1:
     B001 ~424,000   |  B002 ~2,137,000  ← KRİTİK
     B003 ~1,651,000 |  B004 ~2,252,000
     B005 ~7,509,000 |  B006 ~1,643,000  ← KRİTİK

3. Power BI Desktop kapat → 15-30 dk bekle → tekrar aç → Refresh
""")
