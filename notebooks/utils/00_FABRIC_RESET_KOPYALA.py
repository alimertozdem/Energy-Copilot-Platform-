# =============================================================================
# FABRIC TAM SIFIRLAMA — KOPYALA & ÇALIŞTIR (v2 — Fabric uyumlu)
# Notebook: 00_FABRIC_RESET_KOPYALA.py
# Tarih: 2026-05-14
#
# v2 FIX: dbutils Fabric'te yok. Bu sürüm Fabric için doğru API'yi kullanır:
#   1. spark.sql("DROP TABLE IF EXISTS") — primary method, her zaman çalışır
#   2. notebookutils.fs.rm() — Fabric file cleanup (varsa)
#   3. mssparkutils.fs.rm() — older Fabric fallback
#
# AMAÇ:
#   v5.1 sample data Fabric'te aktif olmuyor çünkü bronze watermark sistemi
#   "bu satırları zaten yükledim" diyerek atlıyor.
#   Bu notebook tüm Delta tabloları + watermark'ları temizler.
#
# KULLANIM:
#   1. Fabric'te bu notebook'u aç (reset_v5 olarak adlandırdığın)
#   2. Mevcut hücreyi SİL, yeni boş hücre aç
#   3. Bu dosyanın TAMAMINI tek bir hücreye yapıştır
#   4. Notebook'un Lakehouse'a bağlı olduğundan emin ol (sol panel — energy-copilot-lakehouse)
#   5. "Run all" tıkla
#   6. Output'un sonunda "✅ TAM SIFIRLAMA TAMAMLANDI" görmelisin
# =============================================================================

print("=" * 65)
print("💥 FABRIC TAM SIFIRLAMA BAŞLIYOR (v2)")
print("=" * 65)

# ── 1. FS utility'yi tespit et (Fabric → Databricks fallback) ──────────────
fs_util = None
fs_util_name = "NONE"

try:
    import notebookutils
    fs_util = notebookutils.fs
    fs_util_name = "notebookutils.fs (Fabric)"
except (ImportError, NameError):
    pass

if fs_util is None:
    try:
        fs_util = mssparkutils.fs  # noqa: F821 — Fabric runtime injected
        fs_util_name = "mssparkutils.fs (Fabric legacy)"
    except (NameError, AttributeError):
        pass

if fs_util is None:
    try:
        fs_util = dbutils.fs  # noqa: F821 — Databricks injected
        fs_util_name = "dbutils.fs (Databricks)"
    except (NameError, AttributeError):
        pass

print(f"🔍 FS utility: {fs_util_name}")
print()

# ── 2. Silinecek tüm tablolar ─────────────────────────────────────────────
ALL_TABLES = [
    # Watermark (bronze incremental tracking — KRİTİK, bu silinmezse v4 data kalır)
    "bronze_watermarks",
    # Bronze
    "bronze_raw_energy_readings",
    "bronze_raw_solar_generation",
    "bronze_raw_battery_status",
    "bronze_raw_weather_data",
    "bronze_building_master",
    # Silver
    "silver_energy_readings_clean",
    "silver_solar_generation_clean",
    "silver_battery_status_clean",
    "silver_weather_clean",
    "silver_building_master",
    # Gold — KPI + analytics
    "gold_kpi_hourly",
    "gold_kpi_daily",
    "gold_kpi_monthly",
    "gold_anomaly_log",
    "gold_ghg_scope",
    "gold_crrem_pathway",
    "gold_consumption_forecast",
    "gold_occupancy_profile",
    "gold_hvac_analytics",
    # Gold — compliance + battery (varsa silinir)
    "gold_compliance_results",
    "gold_battery_dispatch",
    "gold_battery_simulation",
    "gold_battery_daily_summary",
    "gold_battery_technologies",
]

# ── 3. PRİMARY: spark.sql DROP TABLE (her ortamda çalışır) ────────────────
print("📋 1. AŞAMA: Catalog'dan tablo registration'larını sil")
print("-" * 65)

drop_silinen = 0
drop_zaten_yok = 0
drop_hata = 0

for tbl in ALL_TABLES:
    try:
        # Önce tablonun var olup olmadığını kontrol et
        exists = spark.catalog.tableExists(tbl)
        if exists:
            spark.sql(f"DROP TABLE IF EXISTS {tbl}")
            print(f"   ✅ DROP TABLE: {tbl}")
            drop_silinen += 1
        else:
            print(f"   ⏭️  Catalog'da yok: {tbl}")
            drop_zaten_yok += 1
    except Exception as e:
        err_msg = str(e)[:80]
        print(f"   ⚠️  DROP failed: {tbl} — {err_msg}")
        drop_hata += 1

print()
print(f"   Catalog DROP özeti: ✅{drop_silinen}  ⏭️{drop_zaten_yok}  ⚠️{drop_hata}")
print()

# ── 4. SECONDARY: File path cleanup (Delta dosyalarını fiziksel sil) ──────
print("📋 2. AŞAMA: Fiziksel Delta dosyalarını temizle (Tables/ yolu)")
print("-" * 65)

if fs_util is None:
    print("   ⚠️  FS utility yok — fiziksel temizleme atlanıyor")
    print("   ℹ️  DROP TABLE genellikle fiziksel dosyaları da siler, yine de OK olmalı")
else:
    fs_silinen = 0
    fs_zaten_yok = 0
    fs_hata = 0
    for tbl in ALL_TABLES:
        path = f"Tables/{tbl}"
        try:
            fs_util.rm(path, recurse=True)
            print(f"   ✅ Path silindi: {path}")
            fs_silinen += 1
        except Exception as e:
            err_msg = str(e)[:80]
            if any(kw in err_msg.lower() for kw in ["not found", "filenotfound", "does not exist"]):
                # Zaten silinmiş — sorun yok
                fs_zaten_yok += 1
            else:
                print(f"   ⚠️  Path silinemedi: {path} — {err_msg}")
                fs_hata += 1
    print()
    print(f"   Path RM özeti: ✅{fs_silinen}  ⏭️{fs_zaten_yok} (zaten yok)  ⚠️{fs_hata}")

# ── 5. SONUÇ ÖZETİ ─────────────────────────────────────────────────────────
print()
print("=" * 65)
print("📊 TAM SIFIRLAMA SONUCU")
print("=" * 65)
print(f"   Catalog'dan silinen:    {drop_silinen} tablo")
print(f"   Catalog'da yoktu:       {drop_zaten_yok} tablo")
print(f"   Catalog hatası:         {drop_hata} tablo")
print("=" * 65)

if drop_hata == 0:
    print()
    print("✅ TAM SIFIRLAMA TAMAMLANDI")
    print()
    print("=" * 65)
    print("🚀 SONRAKI ADIMLAR")
    print("=" * 65)
    print()
    print("ADIM 1 — CSV doğrulama:")
    print("   Lakehouse → Files → sample-data klasörü")
    print("   raw_energy_readings.csv → Properties → Size = 74,220,717 bytes (~74 MB)")
    print("   Eğer farklı boyutta ise → CSV'yi tekrar yükle (overwrite)")
    print()
    print("ADIM 2 — Pipeline notebooks (sırayla, her birini bitir → sonraki):")
    print("   1. 01_bronze_ingestion.py        (~3-5 dk)")
    print("   2. 02_silver_transformation.py   (~2-3 dk)")
    print("   3. 03_gold_kpi_engine.py         (~3-5 dk)")
    print("   4. 10_crrem_pathway_loader.py    (~30s)")
    print("   5. 11_hvac_envelope.py           (~1-2 dk)")
    print("   6. 12_battery_dispatch...py      (~2 dk)")
    print()
    print("ADIM 3 — Doğrulama SQL:")
    print("   SELECT building_id, ROUND(SUM(total_consumption_kwh), 0)")
    print("   FROM gold_kpi_daily WHERE YEAR(date) = 2025")
    print("   GROUP BY building_id ORDER BY building_id;")
    print()
    print("   Beklenen v5.1 değerleri:")
    print("     B001 ~424,000   |  B002 ~2,137,000")
    print("     B003 ~1,651,000 |  B004 ~2,252,000")
    print("     B005 ~7,509,000 |  B006 ~1,643,000")
    print()
    print("ADIM 4 — Power BI Desktop → Home → Refresh")
else:
    print()
    print(f"⚠️  {drop_hata} tablo silinemedi — manuel kontrol gerekebilir.")
