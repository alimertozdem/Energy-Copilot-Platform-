# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 03_gold_kpi_engine.py
# Layer: GOLD — KPI Hesaplama, Anomali Tespiti
# =============================================================================
#
# GÖREV (Purpose):
#   Silver verisinden iş değeri taşıyan KPI'ları hesapla.
#   Power BI'ın doğrudan bağlanacağı Gold tablolarını oluştur.
#
# OUTPUT TABLOLAR:
#   gold_kpi_hourly     — Saatlik enerji, solar, batarya, karbon metrikleri
#   gold_kpi_daily      — Günlük KPI + HDD/CDD normalize EUI
#   gold_kpi_monthly    — Aylık ESG özeti (CSRD, EU Taxonomy)
#   gold_anomaly_log    — Anomali olayları (6 kural)
#
# DP-600 KONULARI:
#   - Window Functions (rolling avg — anomali tespiti için same-hour-of-day)
#   - Broadcast Join (building_master küçük tablo, 3 satır)
#   - Delta MERGE (upsert — idempotent çalışma, yeniden çalıştırılabilir)
#   - Z-ORDER OPTIMIZE (data skipping — Power BI sorgu hızı)
#   - date_trunc aggregation (saat/gün/ay granülarite)
#   - Filter push-down (erken filtreleme, Delta statistics kullanımı)
#   - Lazy evaluation (count() sadece gerektiğinde)
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce,
    date_trunc, to_date, year, month, dayofmonth, hour,
    sum as spark_sum, max as spark_max, min as spark_min,
    avg as spark_avg, count,
    round as spark_round,
    broadcast,
    lag, current_timestamp,
    concat, abs as spark_abs,
    greatest,
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable
from functools import reduce
from pyspark.sql import DataFrame

# DP-600: Küçük Gold dataset için shuffle partition optimizasyonu
# Gold tablolar küçük — 8 partition yeterli, 200 gereksiz overhead
spark.conf.set("spark.sql.shuffle.partitions", "8")

# DP-600: 10MB altındaki tablolar (building_master = 3 satır) otomatik broadcast
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))

# DP-600: Adaptive Query Execution — runtime'da plan optimize et
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

print("✅ Spark konfigürasyonu tamamlandı")
print(f"   shuffle.partitions     = {spark.conf.get('spark.sql.shuffle.partitions')}")
print(f"   adaptive.enabled       = {spark.conf.get('spark.sql.adaptive.enabled')}")
print(f"   broadcastJoinThreshold = 10 MB")


# =============================================================================
# BÖLÜM 2 — KONFİGÜRASYON
# =============================================================================

# Silver kaynak yolları
SILVER_PATHS = {
    "energy_readings": "Tables/silver_energy_readings_clean",
    "solar_generation": "Tables/silver_solar_generation_clean",
    "battery_status":   "Tables/silver_battery_status_clean",
    "weather_data":     "Tables/silver_weather_clean",
    "building_master":  "Tables/silver_building_master",
}

# Gold hedef yolları
GOLD_PATHS = {
    "kpi_hourly":  "Tables/gold_kpi_hourly",
    "kpi_daily":   "Tables/gold_kpi_daily",
    "kpi_monthly": "Tables/gold_kpi_monthly",
    "anomaly_log": "Tables/gold_anomaly_log",
}

# Anomali eşikleri (production'da veritabanından/config'den gelir)
MIN_IRRADIANCE_WM2  = 50.0   # Bu değerin altında PR hesaplanmaz (gece/gölge)
MIN_PR_THRESHOLD    = 0.65   # Bu altı = solar panel sorunu (soiling, arıza)
SOC_MIN_THRESHOLD   = 10.0   # % — batarya over-discharge eşiği
SOC_MAX_THRESHOLD   = 98.0   # % — batarya over-charge eşiği
SPIKE_MULTIPLIER    = 2.5    # x — rolling average'ın bu katı = tüketim spike'ı

# Gece saatleri (UTC bazlı — local time için utc_offset_hours ekle)
NIGHT_HOURS = [22, 23, 0, 1, 2, 3, 4, 5]

# Tarife (EUR/kWh) — production'da ülke/bina bazlı config'den gelir
ELECTRICITY_TARIFF_EUR_KWH = 0.30  # Almanya 2024 ortalama ticari tarife

print(f"\n📋 Gold KPI Engine konfigürasyonu:")
print(f"   PR eşiği           = {MIN_PR_THRESHOLD}")
print(f"   SOC min            = %{SOC_MIN_THRESHOLD}")
print(f"   Spike çarpanı      = {SPIKE_MULTIPLIER}x rolling avg")
print(f"   Tarife             = {ELECTRICITY_TARIFF_EUR_KWH} EUR/kWh")


# =============================================================================
# BÖLÜM 3 — YARDIMCI FONKSİYONLAR
# =============================================================================

def log_step(step, count=None, table=None):
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")
    msg = f"[{ts}] {step}"
    if table:  msg += f" | {table}"
    if count is not None: msg += f" | {count:,} satır"
    print(msg)


def table_exists(path):
    """Delta tablosunun var olup olmadığını kontrol et."""
    try:
        spark.read.format("delta").load(path).limit(1)
        return True
    except:
        return False


def merge_to_gold(df_new, target_path, merge_keys, table_name, partition_cols=None):
    """
    DP-600: Gold tablolarına idempotent MERGE (upsert).
    Notebook'u ikinci kez çalıştırırsan duplicate oluşmaz.
    İlk çalıştırmada overwrite (tablo yoksa), sonrasında MERGE.
    """
    if not table_exists(target_path):
        writer = df_new.write.format("delta").mode("overwrite")
        if partition_cols:
            writer = writer.partitionBy(*partition_cols)
        writer.save(target_path)
        log_step("✅ İlk yazma (overwrite)", df_new.count(), table_name)
    else:
        delta_tbl = DeltaTable.forPath(spark, target_path)
        cond = " AND ".join([f"target.{k} = source.{k}" for k in merge_keys])
        (delta_tbl.alias("target")
            .merge(df_new.alias("source"), cond)
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute())
        log_step("✅ MERGE tamamlandı", table=table_name)


def optimize_gold(path, table_name, zorder_cols):
    """
    DP-600: Z-ORDER OPTIMIZE — data skipping.
    Sık filtrelenen kolonlara göre dosyaları fiziksel olarak düzenle.
    Power BI'dan gelen building_id + tarih filtrelerini hızlandırır.
    """
    try:
        zorder_str = ", ".join(zorder_cols)
        spark.sql(f"OPTIMIZE delta.`{path}` ZORDER BY ({zorder_str})")
        log_step("⚡ Z-ORDER OPTIMIZE", table=f"{table_name} [{zorder_str}]")
    except Exception as e:
        log_step(f"⚠️  OPTIMIZE atlandı: {str(e)[:80]}", table=table_name)


# =============================================================================
# BÖLÜM 4 — SILVER VERİ OKUMA
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 4 — Silver Veri Okuma")
print("="*60)

# DP-600: Lazy loading — DataFrame oluşturmak Spark action değil.
# count() veya write'a kadar gerçek okuma olmaz (execution plan hazırlanır).
df_energy  = spark.read.format("delta").load(SILVER_PATHS["energy_readings"])
df_solar   = spark.read.format("delta").load(SILVER_PATHS["solar_generation"])
df_battery = spark.read.format("delta").load(SILVER_PATHS["battery_status"])
df_weather = spark.read.format("delta").load(SILVER_PATHS["weather_data"])
df_building = spark.read.format("delta").load(SILVER_PATHS["building_master"])

log_step("Silver energy okundu (lazy)", table="silver_energy_readings_clean")
log_step("Silver solar okundu (lazy)",  table="silver_solar_generation_clean")
log_step("Silver battery okundu (lazy)",table="silver_battery_status_clean")
log_step("Silver weather okundu (lazy)",table="silver_weather_clean")
log_step("Silver building_master okundu", df_building.count(), "silver_building_master")

# DP-600: Broadcast join için building_master'ı hazırla.
# 3 satır = sıfır shuffle maliyeti. Her join'de tüm worker'lara kopyalanır.
df_bld_lookup = broadcast(df_building.select(
    "building_id", "country_code",
    col("conditioned_area_m2").alias("floor_area_m2"),  # EUI hesabında kondisyonlu alan kullan
    "pv_capacity_kwp", "battery_capacity_kwh",
    "has_pv", "has_battery", "has_heat_pump",
    "emission_factor_kg_kwh", "subscription_tier"
))

# DP-600: Filter push-down — MISSING/ANOMALY veriyi erken at.
# Spark bu filtreyi Delta dosya istatistiklerine iter (data skipping).
# Gold KPI hesaplamalarında sadece güvenilir veri kullan.
df_energy_q  = df_energy.filter(col("data_quality_flag").isin(["OK", "INTERPOLATED"]))
df_solar_q   = df_solar.filter(col("data_quality_flag").isin(["OK", "INTERPOLATED"]))
df_battery_q = df_battery.filter(col("data_quality_flag").isin(["OK", "INTERPOLATED"]))
df_weather_q = df_weather.filter(col("data_quality_flag").isin(["OK", "INTERPOLATED"]))

print("✅ Filter push-down uygulandı — sadece OK + INTERPOLATED veri kullanılacak")


# =============================================================================
# BÖLÜM 5 — SAATLİK KPI (gold_kpi_hourly)
# =============================================================================
# Strateji: Her Silver tabloyu önce saatlik aggregate et, sonra join yap.
# Bu yaklaşım 15-dk seviyesinde join yapmaktan çok daha verimli:
#   - energy_q:  105K satır → 8,760 saatlik satır (3 bina)
#   - solar_q:    70K satır → 5,840 saatlik satır (2 bina)
#   - battery_q:  70K satır → 5,840 saatlik satır (2 bina)
#   - weather_q: 105K satır → 8,760 saatlik satır (3 bina)
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 5 — Saatlik KPI Hesaplama")
print("="*60)

# ── 5A: Enerji saatlik aggregate ──────────────────────────────
# DP-600: date_trunc("hour", timestamp) ile saat bazlı gruplama
# 15-dk → saatlik dönüşüm:
#   toplam kWh = SUM(4 x 15-dk okuma)
#   peak kW   = MAX(15-dk okuma) * 4  (kWh/15dk → kW)
#   avg kW    = toplam kWh (1 saatlik enerji = 1 saatlik ortalama güç)

df_energy_h = (
    df_energy_q
    .withColumn("hour_utc", date_trunc("hour", col("timestamp_utc")))
    .groupBy("building_id", "hour_utc")
    .agg(
        spark_sum("consumption_kwh").alias("total_consumption_kwh"),
        (spark_max("consumption_kwh") * 4).alias("peak_demand_kw"),
        count("*").alias("reading_count"),
    )
    # Load Factor = avg kW / peak kW (1 = düz profil, 0.5 = tipik ofis)
    # avg kW = hourly kWh (1 saat için kWh numerik olarak kW'a eşit)
    .withColumn("load_factor",
        spark_round(
            when(col("peak_demand_kw") > 0,
                 col("total_consumption_kwh") / col("peak_demand_kw"))
            .otherwise(lit(0.0)), 4)
    )
    # Gece saati flag — anomali kuralı 2 için
    .withColumn("is_night_hour", hour(col("hour_utc")).isin(NIGHT_HOURS))
)

# ── 5B: Solar saatlik aggregate ───────────────────────────────
df_solar_h = (
    df_solar_q
    .withColumn("hour_utc", date_trunc("hour", col("timestamp_utc")))
    .groupBy("building_id", "hour_utc")
    .agg(
        spark_sum("generated_kwh").alias("solar_generated_kwh"),
        spark_sum("self_consumed_kwh").alias("solar_self_consumed_kwh"),
        spark_sum("exported_kwh").alias("solar_exported_kwh"),
    )
)

# ── 5C: Batarya saatlik aggregate ─────────────────────────────
# Silver tablosunda charge_kw ve discharge_kw ayrı kolonlar olarak var.
# kWh = kW * 0.25 (15 dakikalık aralık = 0.25 saat)
df_battery_h = (
    df_battery_q
    .withColumn("hour_utc", date_trunc("hour", col("timestamp_utc")))
    .groupBy("building_id", "hour_utc")
    .agg(
        spark_sum(col("charge_kw") * 0.25).alias("battery_charged_kwh"),
        spark_sum(col("discharge_kw") * 0.25).alias("battery_discharged_kwh"),
        spark_min("soc_pct").alias("battery_soc_min_pct"),
        spark_max("soc_pct").alias("battery_soc_max_pct"),
        spark_avg("soc_pct").alias("battery_soc_avg_pct"),
    )
    # Round-Trip Efficiency = deşarj / şarj (gerçekçi: ~%90-95 LFP için)
    .withColumn("roundtrip_efficiency",
        spark_round(
            when(col("battery_charged_kwh") > 0.1,
                 col("battery_discharged_kwh") / col("battery_charged_kwh"))
            .otherwise(lit(None)), 4)
    )
)

# ── 5D: Hava durumu saatlik aggregate + irradiance kWh/m² ─────
df_weather_h = (
    df_weather_q
    .withColumn("hour_utc", date_trunc("hour", col("timestamp_utc")))
    .groupBy("building_id", "hour_utc")
    .agg(
        spark_avg("temperature_c").alias("avg_temperature_c"),
        spark_avg("solar_irradiance").alias("avg_irradiance_wm2"),
        spark_sum("heating_degree_day").alias("hdd_hour"),
        spark_sum("cooling_degree_day").alias("cdd_hour"),
    )
    # irradiance kWh/m²/h = ortalama W/m² / 1000
    # PR hesabında bu değer kullanılır
    .withColumn("irradiance_kwh_per_m2", col("avg_irradiance_wm2") / 1000.0)
)

# ── 5E: Tüm saatlik verileri birleştir + KPI hesapla ──────────
# DP-600: En büyük tablo sol tarafta, küçük tablolar left join.
# Son join = broadcast(building_master) — shuffle yok.

df_gold_hourly = (
    df_energy_h
    .join(df_solar_h,   ["building_id", "hour_utc"], how="left")
    .join(df_battery_h, ["building_id", "hour_utc"], how="left")
    .join(df_weather_h, ["building_id", "hour_utc"], how="left")
    .join(df_bld_lookup, on="building_id", how="left")  # DP-600: Broadcast join

    # Null güvenliği: solar/batarya olmayan binalar için 0 kullan
    .withColumn("solar_generated_kwh",     coalesce(col("solar_generated_kwh"),     lit(0.0)))
    .withColumn("solar_self_consumed_kwh", coalesce(col("solar_self_consumed_kwh"), lit(0.0)))
    .withColumn("solar_exported_kwh",      coalesce(col("solar_exported_kwh"),      lit(0.0)))
    .withColumn("battery_charged_kwh",     coalesce(col("battery_charged_kwh"),     lit(0.0)))
    .withColumn("battery_discharged_kwh",  coalesce(col("battery_discharged_kwh"),  lit(0.0)))

    # Net şebeke tüketimi = toplam - solar self-consumption - batarya deşarj
    # NOT: Bu basitleştirilmiş formüldür. Batarya şarjının kaynağı (solar vs şebeke)
    # ayrımı için sub-meter verisi gerekir (Phase 2).
    .withColumn("net_grid_consumption_kwh",
        spark_round(
            greatest(
                col("total_consumption_kwh")
                - col("solar_self_consumed_kwh")
                - col("battery_discharged_kwh"),
                lit(0.0)  # Şebekeden negatif çekim fiziksel olarak imkânsız
            ), 4)
    )

    # CO₂ Emisyonu (Scope 2) = net şebeke tüketimi × ülke emisyon faktörü
    # DE: 0.380 kg CO₂/kWh (UBA 2024), TR: 0.442 kg CO₂/kWh (TEİAŞ 2024)
    .withColumn("co2_emissions_kg",
        spark_round(col("net_grid_consumption_kwh") * col("emission_factor_kg_kwh"), 4))

    # CO₂ Tasarrufu = solar self-consumption × emisyon faktörü
    # (Bu enerji şebekeden alınmadı, bu kadar emisyon üretilmedi)
    .withColumn("co2_savings_from_solar_kg",
        spark_round(col("solar_self_consumed_kwh") * col("emission_factor_kg_kwh"), 4))

    # Performance Ratio = gerçek üretim / (kapasite × gelen radyasyon)
    # PR = E_actual / (P_STC × H_irr / G_STC)
    # İyi sistem: PR 0.75-0.85, sorunlu: PR < 0.65
    # Sadece gündüz (irradiance > 50 W/m²) ve solar olan binalar için hesapla
    .withColumn("solar_performance_ratio",
        spark_round(
            when(
                (col("has_pv") == True) &
                (col("avg_irradiance_wm2") > MIN_IRRADIANCE_WM2) &
                (col("pv_capacity_kwp") > 0) &
                (col("irradiance_kwh_per_m2") > 0),
                col("solar_generated_kwh") / (col("pv_capacity_kwp") * col("irradiance_kwh_per_m2"))
            ).otherwise(lit(None)), 4)
    )

    # Self-Consumption Rate = self_consumed / generated
    # "Ürettiğin enerjinin ne kadarını kendin kullandın?"
    # Hedef: > %70 (düşükse depolama veya esneklik öner)
    .withColumn("self_consumption_rate",
        spark_round(
            when(col("solar_generated_kwh") > 0.1,
                 col("solar_self_consumed_kwh") / col("solar_generated_kwh"))
            .otherwise(lit(None)), 4)
    )

    # Self-Sufficiency Rate = self_consumed / total_consumption
    # "Tüketiminin ne kadarını güneşten karşıladın?"
    # Hedef: > %30-50 (bölge ve sisteme göre)
    .withColumn("self_sufficiency_rate",
        spark_round(
            when(col("total_consumption_kwh") > 0,
                 col("solar_self_consumed_kwh") / col("total_consumption_kwh"))
            .otherwise(lit(0.0)), 4)
    )

    # Batarya cycle katkısı (bu saate ait şarj / toplam batarya kapasitesi)
    # Aylık toplamı = o aydaki toplam cycle sayısı
    .withColumn("battery_cycle_fraction",
        spark_round(
            when(
                (col("has_battery") == True) & (col("battery_capacity_kwh") > 0),
                col("battery_charged_kwh") / col("battery_capacity_kwh")
            ).otherwise(lit(0.0)), 6)
    )

    # Zaman boyutları — Power BI date hierarchy ve partition için
    .withColumn("year",  year(col("hour_utc")))
    .withColumn("month", month(col("hour_utc")))
    .withColumn("day",   dayofmonth(col("hour_utc")))
    .withColumn("hour",  hour(col("hour_utc")))
    .withColumn("date",  to_date(col("hour_utc")))
    .withColumn("processed_at", current_timestamp())

    .select(
        # Boyutlar
        "building_id", "hour_utc", "year", "month", "day", "hour", "date",
        # Enerji
        "total_consumption_kwh", "peak_demand_kw", "load_factor",
        "is_night_hour", "reading_count",
        # Solar
        "solar_generated_kwh", "solar_self_consumed_kwh", "solar_exported_kwh",
        "solar_performance_ratio", "self_consumption_rate", "self_sufficiency_rate",
        # Batarya
        "battery_charged_kwh", "battery_discharged_kwh",
        "battery_soc_min_pct", "battery_soc_max_pct", "battery_soc_avg_pct",
        "roundtrip_efficiency", "battery_cycle_fraction",
        # Hava & İklim
        "avg_temperature_c", "avg_irradiance_wm2", "hdd_hour", "cdd_hour",
        # Şebeke & Karbon
        "net_grid_consumption_kwh", "co2_emissions_kg", "co2_savings_from_solar_kg",
        # Meta
        "emission_factor_kg_kwh", "floor_area_m2", "pv_capacity_kwp",
        "battery_capacity_kwh", "has_pv", "has_battery", "has_heat_pump",
        "subscription_tier", "processed_at"
    )
)

hourly_count = df_gold_hourly.count()
log_step("Gold saatlik KPI tamamlandı", hourly_count, "gold_kpi_hourly")

print(f"\n📊 Saatlik KPI örneği (ilk 3 satır):")
df_gold_hourly.select(
    "building_id", "hour_utc", "total_consumption_kwh",
    "solar_generated_kwh", "solar_performance_ratio",
    "co2_emissions_kg", "net_grid_consumption_kwh"
).show(3, truncate=False)

merge_to_gold(
    df_gold_hourly,
    GOLD_PATHS["kpi_hourly"],
    merge_keys=["building_id", "hour_utc"],
    table_name="gold_kpi_hourly",
    partition_cols=["building_id", "year", "month"]
)


# =============================================================================
# BÖLÜM 6 — GÜNLÜK KPI (gold_kpi_daily)
# =============================================================================
# Gold saatlik tablosundan oku — Silver'ı tekrar işleme gerek yok.
# EUI ve HDD normalize EUI burada hesaplanır.
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 6 — Günlük KPI Hesaplama")
print("="*60)

# Gold hourly'yi Delta'dan oku (yazılan verinin üstünde çalış)
df_h = spark.read.format("delta").load(GOLD_PATHS["kpi_hourly"])

df_gold_daily = (
    df_h
    .groupBy("building_id", "date", "year", "month")
    .agg(
        # Enerji
        spark_sum("total_consumption_kwh").alias("total_consumption_kwh"),
        spark_max("peak_demand_kw").alias("peak_demand_kw"),
        spark_avg("load_factor").alias("avg_load_factor"),

        # Solar
        spark_sum("solar_generated_kwh").alias("solar_generated_kwh"),
        spark_sum("solar_self_consumed_kwh").alias("solar_self_consumed_kwh"),
        spark_sum("solar_exported_kwh").alias("solar_exported_kwh"),
        spark_avg("solar_performance_ratio").alias("avg_solar_pr"),
        spark_avg("self_consumption_rate").alias("avg_self_consumption_rate"),
        spark_avg("self_sufficiency_rate").alias("avg_self_sufficiency_rate"),

        # Batarya
        spark_sum("battery_charged_kwh").alias("battery_charged_kwh"),
        spark_sum("battery_discharged_kwh").alias("battery_discharged_kwh"),
        spark_sum("battery_cycle_fraction").alias("battery_cycles_day"),
        spark_min("battery_soc_min_pct").alias("battery_soc_min_pct"),
        spark_max("battery_soc_max_pct").alias("battery_soc_max_pct"),

        # Hava & İklim
        spark_avg("avg_temperature_c").alias("avg_temperature_c"),
        spark_sum("hdd_hour").alias("hdd_day"),
        spark_sum("cdd_hour").alias("cdd_day"),

        # Şebeke & Karbon
        spark_sum("net_grid_consumption_kwh").alias("net_grid_consumption_kwh"),
        spark_sum("co2_emissions_kg").alias("co2_emissions_kg"),
        spark_sum("co2_savings_from_solar_kg").alias("co2_savings_from_solar_kg"),

        # Meta
        spark_max("floor_area_m2").alias("floor_area_m2"),
        spark_max("pv_capacity_kwp").alias("pv_capacity_kwp"),
        spark_max("battery_capacity_kwh").alias("battery_capacity_kwh"),
        spark_max("emission_factor_kg_kwh").alias("emission_factor_kg_kwh"),
        spark_max("has_pv").alias("has_pv"),
        spark_max("has_battery").alias("has_battery"),
        spark_max("has_heat_pump").alias("has_heat_pump"),
        spark_max("subscription_tier").alias("subscription_tier"),
    )

    # EUI (Energy Use Intensity) = kWh/m²/gün
    # Yıllık EUI için bu değerleri topla (365 gün * günlük EUI = yıllık EUI/365)
    # Benchmark: İyi ofis ≤ 100 kWh/m²/yıl = 0.274 kWh/m²/gün
    .withColumn("eui_kwh_m2",
        spark_round(
            when(col("floor_area_m2") > 0,
                 col("total_consumption_kwh") / col("floor_area_m2"))
            .otherwise(lit(None)), 4)
    )

    # HDD Normalize EUI = günlük EUI / günlük HDD
    # Farklı iklim koşullarındaki binaları adil karşılaştırır.
    # Berlin kışı (HDD yüksek) vs İstanbul kışı (HDD düşük) aynı kalan üstünde karşılaştırılabilir.
    .withColumn("hdd_normalized_eui",
        spark_round(
            when(col("hdd_day") > 0.5,
                 col("eui_kwh_m2") / col("hdd_day"))
            .otherwise(lit(None)), 6)
    )

    # Carbon Intensity = kg CO₂ / m² / gün
    # ESG raporlama metriği — CSRD Scope 2 için
    .withColumn("carbon_intensity_kg_m2",
        spark_round(
            when(col("floor_area_m2") > 0,
                 col("co2_emissions_kg") / col("floor_area_m2"))
            .otherwise(lit(None)), 6)
    )

    # Tahmini enerji maliyeti (EUR)
    .withColumn("estimated_cost_eur",
        spark_round(col("net_grid_consumption_kwh") * lit(ELECTRICITY_TARIFF_EUR_KWH), 2))

    # Tahmini tasarruf (EUR) — solar self-consumption'ın şebekeden alınmaması
    .withColumn("estimated_savings_eur",
        spark_round(col("solar_self_consumed_kwh") * lit(ELECTRICITY_TARIFF_EUR_KWH), 2))

    .withColumn("processed_at", current_timestamp())
)

daily_count = df_gold_daily.count()
log_step("Gold günlük KPI tamamlandı", daily_count, "gold_kpi_daily")

print(f"\n📊 Günlük KPI örneği (ilk 5 satır):")
df_gold_daily.select(
    "building_id", "date", "total_consumption_kwh",
    "eui_kwh_m2", "hdd_day", "co2_emissions_kg", "estimated_cost_eur"
).orderBy("building_id", "date").show(5, truncate=False)

merge_to_gold(
    df_gold_daily,
    GOLD_PATHS["kpi_daily"],
    merge_keys=["building_id", "date"],
    table_name="gold_kpi_daily",
    partition_cols=["building_id", "year", "month"]
)


# =============================================================================
# BÖLÜM 7 — AYLIK KPI / ESG ÖZETİ (gold_kpi_monthly)
# =============================================================================
# CSRD (Corporate Sustainability Reporting Directive) uyumlu aylık özet.
# Bu tablo ESG dashboard'una ve düzenleyici raporlara doğrudan beslenir.
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 7 — Aylık ESG KPI Hesaplama")
print("="*60)

df_d = spark.read.format("delta").load(GOLD_PATHS["kpi_daily"])

df_gold_monthly = (
    df_d
    .groupBy("building_id", "year", "month")
    .agg(
        spark_sum("total_consumption_kwh").alias("total_consumption_kwh"),
        spark_max("peak_demand_kw").alias("peak_demand_kw"),
        spark_avg("avg_load_factor").alias("avg_load_factor"),

        spark_sum("solar_generated_kwh").alias("solar_generated_kwh"),
        spark_sum("solar_self_consumed_kwh").alias("solar_self_consumed_kwh"),
        spark_sum("solar_exported_kwh").alias("solar_exported_kwh"),
        spark_avg("avg_solar_pr").alias("avg_solar_pr"),
        spark_avg("avg_self_sufficiency_rate").alias("avg_self_sufficiency_rate"),

        spark_sum("battery_charged_kwh").alias("battery_charged_kwh"),
        spark_sum("battery_discharged_kwh").alias("battery_discharged_kwh"),
        spark_sum("battery_cycles_day").alias("battery_cycles_month"),

        spark_avg("avg_temperature_c").alias("avg_temperature_c"),
        spark_sum("hdd_day").alias("hdd_month"),
        spark_sum("cdd_day").alias("cdd_month"),

        spark_sum("net_grid_consumption_kwh").alias("net_grid_consumption_kwh"),
        spark_sum("co2_emissions_kg").alias("co2_emissions_kg"),
        spark_sum("co2_savings_from_solar_kg").alias("co2_savings_from_solar_kg"),
        spark_sum("estimated_cost_eur").alias("total_cost_eur"),
        spark_sum("estimated_savings_eur").alias("total_savings_eur"),

        spark_max("floor_area_m2").alias("floor_area_m2"),
        spark_max("pv_capacity_kwp").alias("pv_capacity_kwp"),
        spark_max("battery_capacity_kwh").alias("battery_capacity_kwh"),
        spark_max("emission_factor_kg_kwh").alias("emission_factor_kg_kwh"),
        spark_max("has_pv").alias("has_pv"),
        spark_max("has_battery").alias("has_battery"),
        spark_max("has_heat_pump").alias("has_heat_pump"),
        spark_max("subscription_tier").alias("subscription_tier"),
        count("date").alias("days_in_month"),
    )

    # Aylık EUI (kWh/m²)
    .withColumn("monthly_eui_kwh_m2",
        spark_round(
            when(col("floor_area_m2") > 0,
                 col("total_consumption_kwh") / col("floor_area_m2"))
            .otherwise(lit(None)), 4)
    )

    # Solar Specific Yield (kWh/kWp) — panel performans göstergesi
    # Benchmark: Berlin ~900 kWh/kWp/yıl, İstanbul ~1400 kWh/kWp/yıl
    .withColumn("solar_specific_yield_kwh_kwp",
        spark_round(
            when((col("has_pv") == True) & (col("pv_capacity_kwp") > 0),
                 col("solar_generated_kwh") / col("pv_capacity_kwp"))
            .otherwise(lit(None)), 2)
    )

    # Carbon Intensity (kg CO₂/m²/ay) — ESG benchmark metriği
    .withColumn("carbon_intensity_kg_m2",
        spark_round(
            when(col("floor_area_m2") > 0,
                 col("co2_emissions_kg") / col("floor_area_m2"))
            .otherwise(lit(None)), 4)
    )

    # CO₂ Tasarruf Yüzdesi = savings / (emissions + savings) * 100
    .withColumn("co2_savings_pct",
        spark_round(
            when((col("co2_emissions_kg") + col("co2_savings_from_solar_kg")) > 0,
                 col("co2_savings_from_solar_kg") /
                 (col("co2_emissions_kg") + col("co2_savings_from_solar_kg")) * 100)
            .otherwise(lit(0.0)), 2)
    )

    .withColumn("processed_at", current_timestamp())
)

monthly_count = df_gold_monthly.count()
log_step("Gold aylık ESG KPI tamamlandı", monthly_count, "gold_kpi_monthly")

print(f"\n📊 Aylık KPI özeti:")
df_gold_monthly.select(
    "building_id", "year", "month",
    "total_consumption_kwh", "monthly_eui_kwh_m2",
    "co2_emissions_kg", "co2_savings_pct",
    "total_cost_eur", "total_savings_eur"
).orderBy("building_id", "year", "month").show(6, truncate=False)

merge_to_gold(
    df_gold_monthly,
    GOLD_PATHS["kpi_monthly"],
    merge_keys=["building_id", "year", "month"],
    table_name="gold_kpi_monthly"
)


# =============================================================================
# BÖLÜM 8 — ANOMALİ TESPİTİ (gold_anomaly_log)
# =============================================================================
# 6 fizik tabanlı kural. Her kural bir anomali tipi üretir.
# Tespit edilen anomaliler injected test verisindeki olayları yakalamalı:
#   B001 Ağustos — Solar PR drop (panel soiling)
#   B001 Kasım   — Batarya over-discharge
#   B002 15 Mart — Tüketim spike (+%80)
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 8 — Anomali Tespiti (6 Kural)")
print("="*60)

# Gold hourly'yi yeniden oku (Delta'dan — garanti edilmiş veri)
df_gh = spark.read.format("delta").load(GOLD_PATHS["kpi_hourly"])

anomaly_frames = []

# ──────────────────────────────────────────────────────────────
# KURAL 1 — CONSUMPTION_SPIKE
# Her saat için aynı saatin (örn. her gün saat 14:00) son 30 günlük
# ortalamasını al. Bu saatlik değer ortalamanın SPIKE_MULTIPLIER katını
# geçiyorsa spike anomalisi.
#
# DP-600: Window function — partitionBy(building_id, hour_of_day)
# rowsBetween(-30, -1) = son 30 gün (aynı saat diliminden)
# ──────────────────────────────────────────────────────────────

window_spike = (
    Window
    .partitionBy("building_id", "hour")  # Aynı saat dilimini karşılaştır
    .orderBy(col("hour_utc").cast("long"))
    .rowsBetween(-30, -1)  # Son 30 gün (aynı saat), mevcut saat hariç
)

df_spike = (
    df_gh
    .filter(col("total_consumption_kwh") > 0)
    .withColumn("rolling_avg_kwh", spark_avg("total_consumption_kwh").over(window_spike))
    .filter(
        col("rolling_avg_kwh").isNotNull() &
        (col("total_consumption_kwh") > col("rolling_avg_kwh") * lit(SPIKE_MULTIPLIER))
    )
    .select(
        col("building_id"),
        col("hour_utc").alias("detected_at"),
        lit("CONSUMPTION_SPIKE").alias("anomaly_type"),
        lit("HIGH").alias("severity"),
        concat(
            lit("Tüketim "),
            spark_round(col("total_consumption_kwh"), 2).cast("string"),
            lit(" kWh — 30 günlük ort. "),
            spark_round(col("rolling_avg_kwh"), 2).cast("string"),
            lit(f" kWh'ın {SPIKE_MULTIPLIER}x üstünde")
        ).alias("description"),
        col("total_consumption_kwh").alias("affected_value"),
        (col("rolling_avg_kwh") * lit(SPIKE_MULTIPLIER)).alias("threshold_value"),
        lit(False).alias("is_resolved"),
    )
)
c = df_spike.count()
log_step(f"KURAL 1 — CONSUMPTION_SPIKE", c, "anomaly")
anomaly_frames.append(df_spike)

# ──────────────────────────────────────────────────────────────
# KURAL 2 — NIGHT_OVERCONSUMPTION
# Gece tüketimi (22:00-06:00) o günün gündüz peak'inin %40'ını geçiyorsa
# HVAC gece boyunca tam güçte çalışıyor olabilir.
# ──────────────────────────────────────────────────────────────

df_day_peak = (
    df_gh
    .filter(~col("is_night_hour"))
    .groupBy("building_id", "date")
    .agg(spark_max("total_consumption_kwh").alias("daytime_peak_kwh"))
)

df_night_anomaly = (
    df_gh
    .filter(col("is_night_hour"))
    .join(df_day_peak, ["building_id", "date"], how="left")
    .filter(
        col("daytime_peak_kwh").isNotNull() &
        (col("daytime_peak_kwh") > 0) &
        (col("total_consumption_kwh") > col("daytime_peak_kwh") * 0.40)
    )
    .select(
        col("building_id"),
        col("hour_utc").alias("detected_at"),
        lit("NIGHT_OVERCONSUMPTION").alias("anomaly_type"),
        lit("MEDIUM").alias("severity"),
        concat(
            lit("Gece tüketimi "),
            spark_round(col("total_consumption_kwh"), 2).cast("string"),
            lit(" kWh — gündüz zirvesinin %40+ üstünde ("),
            spark_round(col("daytime_peak_kwh"), 2).cast("string"),
            lit(" kWh)")
        ).alias("description"),
        col("total_consumption_kwh").alias("affected_value"),
        (col("daytime_peak_kwh") * 0.40).alias("threshold_value"),
        lit(False).alias("is_resolved"),
    )
)
c = df_night_anomaly.count()
log_step(f"KURAL 2 — NIGHT_OVERCONSUMPTION", c, "anomaly")
anomaly_frames.append(df_night_anomaly)

# ──────────────────────────────────────────────────────────────
# KURAL 3 — SOLAR_PR_DROP
# Performance Ratio < 0.65 — panel soiling, arıza, gölgelenme.
# Sadece irradiance > 50 W/m² olan saatlerde kontrol et.
# Beklenen: B001 Ağustos anomalisini yakalamalı.
# ──────────────────────────────────────────────────────────────

df_pr_drop = (
    df_gh
    .filter(
        (col("has_pv") == True) &
        col("solar_performance_ratio").isNotNull() &
        (col("avg_irradiance_wm2") > MIN_IRRADIANCE_WM2) &
        (col("solar_performance_ratio") < lit(MIN_PR_THRESHOLD))
    )
    .select(
        col("building_id"),
        col("hour_utc").alias("detected_at"),
        lit("SOLAR_PR_DROP").alias("anomaly_type"),
        when(col("solar_performance_ratio") < 0.50, lit("CRITICAL"))
        .when(col("solar_performance_ratio") < 0.60, lit("HIGH"))
        .otherwise(lit("MEDIUM")).alias("severity"),
        concat(
            lit("Solar PR = "),
            spark_round(col("solar_performance_ratio"), 3).cast("string"),
            lit(f" (eşik: {MIN_PR_THRESHOLD}) — panel kirliliği veya arıza şüphesi")
        ).alias("description"),
        col("solar_performance_ratio").alias("affected_value"),
        lit(MIN_PR_THRESHOLD).alias("threshold_value"),
        lit(False).alias("is_resolved"),
    )
)
c = df_pr_drop.count()
log_step(f"KURAL 3 — SOLAR_PR_DROP", c, "anomaly")
anomaly_frames.append(df_pr_drop)

# ──────────────────────────────────────────────────────────────
# KURAL 4 — BATTERY_OVERDISCHARGE
# SOC < %10 — LFP batarya için kritik sınır.
# Beklenen: B001 Kasım anomalisini yakalamalı.
# ──────────────────────────────────────────────────────────────

df_overdischarge = (
    df_gh
    .filter(
        (col("has_battery") == True) &
        col("battery_soc_min_pct").isNotNull() &
        (col("battery_soc_min_pct") < lit(SOC_MIN_THRESHOLD))
    )
    .select(
        col("building_id"),
        col("hour_utc").alias("detected_at"),
        lit("BATTERY_OVERDISCHARGE").alias("anomaly_type"),
        when(col("battery_soc_min_pct") < 5.0, lit("CRITICAL"))
        .otherwise(lit("HIGH")).alias("severity"),
        concat(
            lit("Batarya SOC = %"),
            spark_round(col("battery_soc_min_pct"), 1).cast("string"),
            lit(f" — aşırı deşarj (min eşik: %{SOC_MIN_THRESHOLD})")
        ).alias("description"),
        col("battery_soc_min_pct").alias("affected_value"),
        lit(SOC_MIN_THRESHOLD).alias("threshold_value"),
        lit(False).alias("is_resolved"),
    )
)
c = df_overdischarge.count()
log_step(f"KURAL 4 — BATTERY_OVERDISCHARGE", c, "anomaly")
anomaly_frames.append(df_overdischarge)

# ──────────────────────────────────────────────────────────────
# KURAL 5 — BATTERY_OVERCHARGE
# SOC > %98 tekrarlayan — BMS üst sınır sorunu.
# ──────────────────────────────────────────────────────────────

df_overcharge = (
    df_gh
    .filter(
        (col("has_battery") == True) &
        col("battery_soc_max_pct").isNotNull() &
        (col("battery_soc_max_pct") > lit(SOC_MAX_THRESHOLD))
    )
    .select(
        col("building_id"),
        col("hour_utc").alias("detected_at"),
        lit("BATTERY_OVERCHARGE").alias("anomaly_type"),
        lit("MEDIUM").alias("severity"),
        concat(
            lit("Batarya SOC = %"),
            spark_round(col("battery_soc_max_pct"), 1).cast("string"),
            lit(f" — BMS üst sınır kontrolü gerekli (max eşik: %{SOC_MAX_THRESHOLD})")
        ).alias("description"),
        col("battery_soc_max_pct").alias("affected_value"),
        lit(SOC_MAX_THRESHOLD).alias("threshold_value"),
        lit(False).alias("is_resolved"),
    )
)
c = df_overcharge.count()
log_step(f"KURAL 5 — BATTERY_OVERCHARGE", c, "anomaly")
anomaly_frames.append(df_overcharge)

# ──────────────────────────────────────────────────────────────
# KURAL 6 — DATA_QUALITY_GAP
# Silver'da saatlik 4+ MISSING/ANOMALY kayıt = 1 saatlik güvenilmez veri.
# Bu kural Silver verisinden okur (quality flag bilgisi Gold'da yok).
# ──────────────────────────────────────────────────────────────

df_gap = (
    df_energy  # Tüm Silver veri (MISSING/ANOMALY dahil)
    .filter(col("data_quality_flag").isin(["MISSING", "ANOMALY"]))
    .withColumn("hour_utc", date_trunc("hour", col("timestamp_utc")))
    .groupBy("building_id", "hour_utc")
    .agg(count("*").alias("bad_reading_count"))
    .filter(col("bad_reading_count") >= 4)  # 4 okuma = 1 saatlik veri
    .select(
        col("building_id"),
        col("hour_utc").alias("detected_at"),
        lit("DATA_QUALITY_GAP").alias("anomaly_type"),
        lit("LOW").alias("severity"),
        concat(
            col("bad_reading_count").cast("string"),
            lit(" adet MISSING/ANOMALY okuma — 1 saatlik veri güvenilir değil")
        ).alias("description"),
        col("bad_reading_count").cast("double").alias("affected_value"),
        lit(4.0).alias("threshold_value"),
        lit(False).alias("is_resolved"),
    )
)
c = df_gap.count()
log_step(f"KURAL 6 — DATA_QUALITY_GAP", c, "anomaly")
anomaly_frames.append(df_gap)

# ── Tüm anomalileri birleştir ve yaz ──────────────────────────

df_all_anomalies = reduce(DataFrame.unionAll, anomaly_frames)
total_anomalies = df_all_anomalies.count()
log_step("Toplam anomali tespit edildi", total_anomalies, "gold_anomaly_log")

print(f"\n📊 Anomali Dağılımı (tip + ciddiyet):")
df_all_anomalies.groupBy("anomaly_type", "severity") \
    .count() \
    .orderBy("anomaly_type", "severity") \
    .show(truncate=False)

merge_to_gold(
    df_all_anomalies,
    GOLD_PATHS["anomaly_log"],
    merge_keys=["building_id", "anomaly_type", "detected_at"],
    table_name="gold_anomaly_log",
    partition_cols=["building_id"]
)


# =============================================================================
# BÖLÜM 9 — Z-ORDER OPTIMIZE
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 9 — Z-ORDER OPTIMIZE")
print("="*60)

# DP-600: Z-ORDER — Power BI'dan gelen filtrelere göre dosyaları düzenle.
# Power BI tipik sorgusu: WHERE building_id = 'B001' AND date = '2024-08-...'
# Z-ORDER bu kombinasyonu hızlandırır (data skipping).

optimize_gold(GOLD_PATHS["kpi_hourly"],  "gold_kpi_hourly",  ["building_id", "hour_utc"])
optimize_gold(GOLD_PATHS["kpi_daily"],   "gold_kpi_daily",   ["building_id", "date"])
optimize_gold(GOLD_PATHS["kpi_monthly"], "gold_kpi_monthly", ["building_id", "year", "month"])
optimize_gold(GOLD_PATHS["anomaly_log"], "gold_anomaly_log", ["building_id", "detected_at"])


# =============================================================================
# BÖLÜM 10 — VALIDATION RAPORU
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 10 — Validation Raporu")
print("="*60)

df_kpi_h = spark.read.format("delta").load(GOLD_PATHS["kpi_hourly"])
df_kpi_d = spark.read.format("delta").load(GOLD_PATHS["kpi_daily"])
df_kpi_m = spark.read.format("delta").load(GOLD_PATHS["kpi_monthly"])
df_anom  = spark.read.format("delta").load(GOLD_PATHS["anomaly_log"])

print(f"\n{'='*60}")
print("=== GOLD LAYER VALİDASYON RAPORU ===")
print(f"{'='*60}")
print(f"  gold_kpi_hourly:   {df_kpi_h.count():>8,} satır")
print(f"  gold_kpi_daily:    {df_kpi_d.count():>8,} satır")
print(f"  gold_kpi_monthly:  {df_kpi_m.count():>8,} satır")
print(f"  gold_anomaly_log:  {df_anom.count():>8,} satır")

print(f"\n📊 Yıllık Özet (Bina Bazında):")
df_kpi_m.groupBy("building_id") \
    .agg(
        spark_round(spark_sum("total_consumption_kwh"), 0).alias("yillik_tuketim_kwh"),
        spark_round(spark_sum("solar_generated_kwh"), 0).alias("yillik_solar_kwh"),
        spark_round(spark_sum("co2_emissions_kg"), 0).alias("yillik_co2_kg"),
        spark_round(spark_sum("co2_savings_from_solar_kg"), 0).alias("yillik_co2_tasarruf_kg"),
        spark_round(spark_sum("total_cost_eur"), 0).alias("yillik_maliyet_eur"),
        spark_round(spark_sum("total_savings_eur"), 0).alias("yillik_tasarruf_eur"),
    ) \
    .orderBy("building_id") \
    .show(truncate=False)

print(f"\n📊 Anomali Özeti (Bina × Tip):")
df_anom.groupBy("building_id", "anomaly_type", "severity") \
    .count() \
    .orderBy("building_id", "anomaly_type") \
    .show(truncate=False)

print(f"\n📊 Enjekte Edilmiş Anomali Kontrolü:")
print("  B001 Ağustos SOLAR_PR_DROP tespit edildi mi?")
df_anom.filter(
    (col("building_id") == "B001") &
    (col("anomaly_type") == "SOLAR_PR_DROP")
).select("detected_at", "affected_value", "severity") \
    .orderBy("detected_at") \
    .show(5, truncate=False)

print("  B001 Kasım BATTERY_OVERDISCHARGE tespit edildi mi?")
df_anom.filter(
    (col("building_id") == "B001") &
    (col("anomaly_type") == "BATTERY_OVERDISCHARGE")
).select("detected_at", "affected_value", "severity") \
    .orderBy("detected_at") \
    .show(5, truncate=False)

print("  B002 Mart CONSUMPTION_SPIKE tespit edildi mi?")
df_anom.filter(
    (col("building_id") == "B002") &
    (col("anomaly_type") == "CONSUMPTION_SPIKE")
).select("detected_at", "affected_value", "threshold_value") \
    .orderBy("detected_at") \
    .show(5, truncate=False)

print(f"\n{'='*60}")
print("✅ Gold KPI Engine tamamlandı!")
print("   Power BI artık Gold tablolarına bağlanabilir.")
print("   Sonraki adım: Power BI Semantic Model kurulumu")
print(f"{'='*60}")
