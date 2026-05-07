# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 00_diagnostic_and_reset.py
# Amaç: Pipeline sonrası veri katmanlarını teşhis et ve gerekirse sıfırla
#
# KULLANIM:
#   ADIM 1 — Önce sadece BÖLÜM A (Teşhis) çalıştır
#   ADIM 2 — Sonuçlara bakarak BÖLÜM B veya C'yi seç
#
# ⚠️ BÖLÜM C (Tam Sıfırlama) geri alınamaz — tüm Delta tabloları silinir.
#    Sadece geliştirme / simülasyon ortamında kullan.
# =============================================================================


# =============================================================================
# BÖLÜM A — TEŞHİS (Her zaman önce bunu çalıştır)
# =============================================================================
# Bu bölümü çalıştırdıktan sonra çıktıyı oku.
# Hangi katmanda veri var / yok göreceksin.

from pyspark.sql.functions import min as spark_min, max as spark_max, count

print("=" * 65)
print("⚡ ENERGY COPILOT — Pipeline Teşhis Raporu")
print("=" * 65)

# ── Watermark Durumu ────────────────────────────────────────────
print("\n📌 1) WATERMARK TABLOSU")
try:
    df_wm = spark.read.format("delta").load("Tables/bronze_watermarks")
    df_wm.show(truncate=False)
    print("   ↑ last_watermark_utc 2026 civarında olmalı.")
    print("   ↑ Eğer 2024-12-31 görüyorsan → incremental load çalışmadı.")
except Exception as e:
    print(f"   ❌ Watermark tablosu okunamadı: {e}")
    print("   → Bronze hiç çalışmamış veya tablo yok.")

# ── Bronze Katmanı ──────────────────────────────────────────────
print("\n📌 2) BRONZE — energy_readings tarih aralığı")
try:
    df_br = spark.read.format("delta").load("Tables/bronze_raw_energy_readings")
    df_br.agg(
        spark_min("timestamp_utc").alias("EN_ESKI"),
        spark_max("timestamp_utc").alias("EN_YENI"),
        count("*").alias("TOPLAM_SATIR")
    ).show(truncate=False)
    print("   ↑ EN_YENI 2026-04-18 civarında olmalı.")
    print("   ↑ TOPLAM_SATIR ~693,504 (6 bina × 115,584) olmalı.")
except Exception as e:
    print(f"   ❌ Bronze okunamadı: {e}")

# ── Silver Katmanı ──────────────────────────────────────────────
print("\n📌 3) SILVER — energy_readings_clean tarih aralığı")
try:
    df_sv = spark.read.format("delta").load("Tables/silver_energy_readings_clean")
    df_sv.agg(
        spark_min("timestamp_local").alias("EN_ESKI"),
        spark_max("timestamp_local").alias("EN_YENI"),
        count("*").alias("TOPLAM_SATIR")
    ).show(truncate=False)
    print("   ↑ EN_YENI 2026-04-18 civarında olmalı.")
except Exception as e:
    print(f"   ❌ Silver okunamadı: {e}")

# ── Gold KPI Daily ──────────────────────────────────────────────
print("\n📌 4) GOLD — gold_kpi_daily tarih aralığı (KPI kartlarının kaynağı)")
try:
    df_gd = spark.read.format("delta").load("Tables/gold_kpi_daily")
    df_gd.agg(
        spark_min("date").alias("EN_ESKI_GUN"),
        spark_max("date").alias("EN_YENI_GUN"),
        count("*").alias("TOPLAM_SATIR")
    ).show(truncate=False)
    # Yıl bazlı dağılım
    from pyspark.sql.functions import year
    print("   Yıl bazlı satır sayısı:")
    df_gd.groupBy(year("date").alias("yil")).count().orderBy("yil").show()
    print("   ↑ 2023, 2024, 2025, 2026 satırları olmalı.")
    print("   ↑ 2025 veya 2026 yoksa → Gold güncellenmemiş.")
except Exception as e:
    print(f"   ❌ gold_kpi_daily okunamadı: {e}")

# ── Gold Anomaly Log ─────────────────────────────────────────────
print("\n📌 5) GOLD — gold_anomaly_log tarih aralığı")
try:
    df_ga = spark.read.format("delta").load("Tables/gold_anomaly_log")
    df_ga.agg(
        spark_min("detected_date").alias("EN_ESKI"),
        spark_max("detected_date").alias("EN_YENI"),
        count("*").alias("TOPLAM_ANOMALI")
    ).show(truncate=False)
except Exception as e:
    print(f"   ❌ gold_anomaly_log okunamadı: {e}")

print("\n" + "=" * 65)
print("SONUÇ YORUMU:")
print("  • Tüm tablolar 2026 görüyorsa → Pipeline OK, Power BI refresh et")
print("  • Bronze OK ama Silver/Gold eski → BÖLÜM B çalıştır")
print("  • Bronze da eski (2024'te) → BÖLÜM C çalıştır (tam sıfırlama)")
print("=" * 65)


# =============================================================================
# BÖLÜM B — KISMÎ DÜZELTME
# Sadece Silver ve Gold'u sil + yeniden oluştur (Bronze korunur)
# Bronze 2025-2026 satırları zaten varsa bunu kullan
# =============================================================================
# ⚠️ Aşağıdaki satırı UNCOMMENT et ve sadece bu bölümü çalıştır

# KISMI_SIFIRLAMA = True
# if KISMI_SIFIRLAMA:
#     print("🔄 Silver ve Gold tabloları siliniyor...")
#     paths_to_drop = [
#         "Tables/silver_energy_readings_clean",
#         "Tables/silver_solar_generation_clean",
#         "Tables/silver_battery_status_clean",
#         "Tables/silver_weather_clean",
#         "Tables/silver_building_master",
#         "Tables/gold_kpi_hourly",
#         "Tables/gold_kpi_daily",
#         "Tables/gold_kpi_monthly",
#         "Tables/gold_anomaly_log",
#         "Tables/gold_ghg_scope",
#         "Tables/gold_crrem_pathway",
#         "Tables/gold_consumption_forecast",
#         "Tables/gold_occupancy_profile",
#         "Tables/gold_hvac_analytics",
#     ]
#     for p in paths_to_drop:
#         try:
#             dbutils.fs.rm(p, recurse=True)
#             print(f"   ✅ Silindi: {p}")
#         except Exception as e:
#             print(f"   ⚠️  Silinemedi (zaten yok olabilir): {p} — {str(e)[:50]}")
#     print("\n✅ Silver + Gold temizlendi.")
#     print("   → Şimdi sırayla çalıştır: 02 → 03 → (09, 10, 11) → Power BI Refresh")


# =============================================================================
# BÖLÜM C — TAM SIFIRLAMA (Nuclear Option)
# Tüm Bronze + Silver + Gold + Watermark silinir
# Ardından baştan: 01 → 02 → 03 → 09 → 10 → 11
# =============================================================================
# ⚠️ Bu seçenek HER ŞEYİ siler. Sadece geliştirme ortamında kullan.
# ⚠️ Production'da KULLANMA.

# TAM_SIFIRLAMA = True
# if TAM_SIFIRLAMA:
#     print("💥 TAM SIFIRLAMA — tüm Delta tablolar siliniyor...")
#     all_paths = [
#         # Watermark
#         "Tables/bronze_watermarks",
#         # Bronze
#         "Tables/bronze_raw_energy_readings",
#         "Tables/bronze_raw_solar_generation",
#         "Tables/bronze_raw_battery_status",
#         "Tables/bronze_raw_weather_data",
#         "Tables/bronze_building_master",
#         # Silver
#         "Tables/silver_energy_readings_clean",
#         "Tables/silver_solar_generation_clean",
#         "Tables/silver_battery_status_clean",
#         "Tables/silver_weather_clean",
#         "Tables/silver_building_master",
#         # Gold
#         "Tables/gold_kpi_hourly",
#         "Tables/gold_kpi_daily",
#         "Tables/gold_kpi_monthly",
#         "Tables/gold_anomaly_log",
#         "Tables/gold_ghg_scope",
#         "Tables/gold_crrem_pathway",
#         "Tables/gold_consumption_forecast",
#         "Tables/gold_occupancy_profile",
#         "Tables/gold_hvac_analytics",
#     ]
#     for p in all_paths:
#         try:
#             dbutils.fs.rm(p, recurse=True)
#             print(f"   ✅ Silindi: {p}")
#         except Exception as e:
#             print(f"   ⚠️  Silinemedi: {p} — {str(e)[:50]}")
#     print("\n✅ TAM SIFIRLAMA TAMAMLANDI.")
#     print("   → Şimdi sırayla çalıştır: 01 → 02 → 03 → 09 → 10 → 11")
#     print("   → Son adım: Power BI Desktop → Transform data → Close & Apply → Refresh")


# =============================================================================
# BÖLÜM D — POWER BI SEMANTIC MODEL REFRESH HATIRLATICI
# =============================================================================
print("""
╔══════════════════════════════════════════════════════════════╗
║  Power BI Refresh Adımları (pipeline sonrası)               ║
╠══════════════════════════════════════════════════════════════╣
║  1. Power BI Desktop'ı aç                                   ║
║  2. Home → Transform data → Close & Apply (varsa)           ║
║  3. Home → Refresh  (veya F5)                               ║
║     → "Refreshing..." mesajı görünmeli                      ║
║  4. Yükleme bittikten sonra bir KPI kartı sağ tıkla         ║
║     → "Refresh visuals" seç                                 ║
║                                                              ║
║  Workspace üzerinden yenileme (Fabric Service):             ║
║  1. Power BI Workspace'e git                                ║
║  2. Semantic model → "..." → Refresh now                    ║
║  3. ~2-5 dk bekle → tekrar aç                               ║
╠══════════════════════════════════════════════════════════════╣
║  Hâlâ blank dönüyorsa:                                      ║
║  Model view → Date[Date] → "Mark as date table" kontrol et  ║
║  + Date[Date] → gold_kpi_daily[date] ilişkisi aktif mi?     ║
╚══════════════════════════════════════════════════════════════╝
""")
