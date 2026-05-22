# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 02_silver_transformation.py
# Layer: SILVER — Clean, Normalize, Validate
# =============================================================================
#
# GÖREV (Purpose):
#   Bronze ham verisini temiz, normalize edilmiş ve güvenilir
#   Silver verisine dönüştür.
#
# KURALLAR:
#   1. Bronze veriyi asla değiştirme — sadece oku
#   2. Her dönüşümü açıkça belgele
#   3. Hatalı veriyi silme — flag'le ve sakla
#   4. MERGE ile yaz — duplicate oluşturma
#
# DP-600 KONULARI:
#   - Delta MERGE (upsert) — SCD Type 1
#   - Window Functions (lag/lead) — interpolasyon
#   - Broadcast Join — küçük tablo optimizasyonu
#   - Z-ORDER OPTIMIZE — data skipping
#   - filter push-down — erken filtreleme
#   - Broadcast threshold yönetimi
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType,
    TimestampType, BooleanType
)
from pyspark.sql.functions import (
    col, to_timestamp, current_timestamp,
    year, month, dayofmonth, hour,
    when, lit, coalesce, isnan, isnull,
    lag, lead, greatest, least,
    broadcast, regexp_replace,
    round as spark_round,
    unix_timestamp, from_unixtime,
    min as spark_min, max as spark_max,
    count, sum as spark_sum,
    abs as spark_abs
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# DP-600: Shuffle partition optimizasyonu
spark.conf.set("spark.sql.shuffle.partitions", "8")

# DP-600: Broadcast join threshold — 10MB altındaki tablolar otomatik broadcast
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))

# DP-600: Delta adaptive query execution — sorgu planını runtime'da optimize et
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

print("✅ Spark konfigürasyonu tamamlandı")
print(f"   shuffle.partitions     = {spark.conf.get('spark.sql.shuffle.partitions')}")
print(f"   adaptive.enabled       = {spark.conf.get('spark.sql.adaptive.enabled')}")
print(f"   broadcastJoinThreshold = 10 MB")


# =============================================================================
# BÖLÜM 2 — KONFİGÜRASYON
# =============================================================================

# Bronze kaynak yolları
BRONZE_PATHS = {
    "energy_readings": "Tables/bronze_raw_energy_readings",
    "solar_generation": "Tables/bronze_raw_solar_generation",
    "battery_status":   "Tables/bronze_raw_battery_status",
    "weather_data":     "Tables/bronze_raw_weather_data",
    "building_master":  "Tables/bronze_building_master",
}

# Silver hedef yolları
SILVER_PATHS = {
    "energy_readings": "Tables/silver_energy_readings_clean",
    "solar_generation": "Tables/silver_solar_generation_clean",
    "battery_status":   "Tables/silver_battery_status_clean",
    "weather_data":     "Tables/silver_weather_clean",
    "building_master":  "Tables/silver_building_master",
}

# Veri kalitesi sabitleri
MAX_INTERPOLATION_GAP_HOURS = 2   # 2 saatten uzun boşlukları doldurma
MIN_CONSUMPTION_KWH = 0.0          # Negatif tüketim fiziksel olarak imkânsız
MAX_CONSUMPTION_KWH = 10000.0      # Aşırı yüksek değer — şüpheli
MIN_TEMP_C = -50.0
MAX_TEMP_C = 70.0
MIN_SOC_PCT = 0.0
MAX_SOC_PCT = 100.0

# Ülke bazlı UTC offset'leri (basitleştirilmiş, DST dikkate alınmadı)
# Production'da pytz veya zoneinfo kullanılır
UTC_OFFSETS = {
    "DE": 1,   # CET (kış saati)
    "TR": 3,   # TRT
    "AT": 1,   # CET — Almanya ile aynı zaman dilimi
    "NL": 1,   # CET — Orta Avrupa
    "GB": 0,   # GMT (kış saati)
    "FR": 1,   # CET
    "ES": 1,   # CET
    "IT": 1,   # CET
    "PL": 1,   # CET
    "SE": 1,   # CET
}

# Ülke bazlı grid emission faktörleri (kg CO₂/kWh)
# Kaynak: EEA/Eurostat 2024 — EU ortalama electricity grid intensity
EMISSION_FACTORS = {
    "DE": 0.380,   # Almanya — yenilenebilir geçişte, kömür hâlâ %25
    "TR": 0.442,   # Türkiye — TEIAŞ 2023 faktörü
    "AT": 0.158,   # Avusturya — %75 hidroelektrik, AB'nin en düşükleri
    "NL": 0.389,   # Hollanda — doğalgaz ağırlıklı, rüzgar artıyor
    "GB": 0.233,   # İngiltere — offshore rüzgar + nükleer katkısı
    "FR": 0.052,   # Fransa — nükleer ağırlıklı, AB'nin en düşüğü
    "ES": 0.195,   # İspanya — güneş + rüzgar hızlı büyüyor
    "IT": 0.372,   # İtalya — doğalgaz ağırlıklı
    "PL": 0.773,   # Polonya — kömür ağırlıklı, AB'nin en yükseklerinden
    "SE": 0.013,   # İsveç — hidroelektrik + nükleer, neredeyse karbon nötr
}

print(f"\n📋 Bronze → Silver dönüşümü başlıyor")
print(f"   Interpolasyon limiti: {MAX_INTERPOLATION_GAP_HOURS} saat")


# =============================================================================
# BÖLÜM 3 — YARDIMCI FONKSİYONLAR
# =============================================================================

def log_step(step, count=None, table=None):
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")
    msg = f"[{ts}] {step}"
    if table: msg += f" | {table}"
    if count is not None: msg += f" | {count:,} satır"
    print(msg)


def table_exists(table_name):
    """
    FIX (2026-05-18): Path-based değil, metastore-based kontrol.
    """
    try:
        return spark.catalog.tableExists(table_name)
    except:
        return False


def merge_to_silver(df_new, target_path, merge_keys, table_name):
    """
    DP-600: Delta MERGE (upsert) operasyonu.

    FIX (2026-05-18):
    - .save(path) → .saveAsTable(name): Fabric metastore'a kayıt zorunlu
    - DeltaTable.forPath → forName: managed table için doğru API
    - table_exists artık name-based
    """
    record_count = df_new.count()

    if not table_exists(table_name):
        # İlk kez yazılıyor — direkt overwrite
        (df_new.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .partitionBy("building_id", "year", "month")
            .saveAsTable(table_name)
        )
        log_step(f"✅ İlk yazma (saveAsTable, metastore kayıtlı)", record_count, table_name)
    else:
        # Tablo var — MERGE ile upsert
        delta_table = DeltaTable.forName(spark, table_name)

        # Merge koşulu oluştur (örn: "target.building_id = source.building_id AND ...")
        merge_condition = " AND ".join(
            [f"target.{k} = source.{k}" for k in merge_keys]
        )

        (delta_table.alias("target")
            .merge(df_new.alias("source"), merge_condition)
            .whenMatchedUpdateAll()    # Tüm kolonları güncelle
            .whenNotMatchedInsertAll() # Yeni kayıtları ekle
            .execute()
        )
        log_step(f"✅ MERGE tamamlandı", record_count, table_name)

    return record_count


def add_quality_flag(df, value_col, min_val, max_val, flag_col="data_quality_flag"):
    """
    Veri kalitesi flag'i ekle.
    NULL veya fiziksel sınır dışı değerler ANOMALY olarak işaretlenir.
    """
    return df.withColumn(
        flag_col,
        when(col(value_col).isNull(), lit("MISSING"))
        .when(
            (col(value_col) < min_val) | (col(value_col) > max_val),
            lit("ANOMALY")
        )
        .otherwise(lit("OK"))
    )


def optimize_silver_table(path, table_name, zorder_cols):
    """
    DP-600: Z-ORDER OPTIMIZE.
    Sık sorgulanan kolonlara göre dosyaları fiziksel olarak düzenler.
    Data skipping etkinleşir — sorgu sadece ilgili dosyaları okur.
    """
    try:
        zorder_str = ", ".join(zorder_cols)
        spark.sql(f"OPTIMIZE delta.`{path}` ZORDER BY ({zorder_str})")
        log_step(f"⚡ Z-ORDER OPTIMIZE", table=f"{table_name} [{zorder_str}]")
    except Exception as e:
        log_step(f"⚠️  OPTIMIZE atlandı: {str(e)[:60]}", table=table_name)


# =============================================================================
# BÖLÜM 4 — BUILDING MASTER DÖNÜŞÜMÜ (önce yap, join için lazım)
# =============================================================================

print("\n" + "="*60)
print("ADIM 1/5 — Building Master Dönüşümü")
print("="*60)

df_bld_bronze = spark.read.format("delta").load(BRONZE_PATHS["building_master"])
log_step("Bronze okundu", df_bld_bronze.count(), "bronze_building_master")

# Boolean string'leri gerçek boolean'a çevir
# CSV'den "True"/"False" string olarak geldi
bool_cols = [
    "has_pv", "has_battery", "has_heat_pump", "has_hvac_traditional",
    "has_gas_heating", "has_diesel_generator",
    # primary_hvac_system STRING olarak kalır — boolean değil
    "has_ev_charging", "has_led_lighting", "has_thermal_bridge",
    "iso50001_certified"
]

df_bld_silver = df_bld_bronze
for c in bool_cols:
    if c in df_bld_bronze.columns:
        df_bld_silver = df_bld_silver.withColumn(
            c,
            when(col(c) == "True", lit(True))
            .when(col(c) == "False", lit(False))
            .otherwise(lit(None).cast(BooleanType()))
        )

# Emission faktörü ve UTC offset ekle (ülke bazlı)
# Tüm desteklenen ülkeler için dinamik mapping — yeni ülke eklemek için
# sadece EMISSION_FACTORS ve UTC_OFFSETS dict'lerine satır eklemek yeterli.
_ef_expr = lit(None).cast("double")
_tz_expr = lit(0).cast("integer")
for _cc, _ef in EMISSION_FACTORS.items():
    _ef_expr = when(col("country_code") == _cc, lit(_ef)).otherwise(_ef_expr)
for _cc, _tz in UTC_OFFSETS.items():
    _tz_expr = when(col("country_code") == _cc, lit(_tz)).otherwise(_tz_expr)

df_bld_silver = (df_bld_silver
    .withColumn("emission_factor_kg_kwh", _ef_expr)
    .withColumn("utc_offset_hours", _tz_expr)
    .withColumn("updated_at", current_timestamp())
)

# Silver'a yaz (referans tablosu — tam overwrite)
# FIX (2026-05-18): .save(path) → .saveAsTable(name) — Fabric metastore kaydı zorunlu
(df_bld_silver.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("silver_building_master")
)

log_step("✅ Silver building_master yazıldı", df_bld_silver.count())

# Broadcast için cache'le — tüm join'lerde kullanacağız
# DP-600: Küçük tabloyu cache + broadcast → shuffle yok
# FIX (2026-05-18): path → spark.table() (saveAsTable yazılan managed table için)
df_building_lookup = spark.table("silver_building_master")
df_building_lookup.cache()
log_step("📌 Building lookup cache'lendi (broadcast join için)")


# =============================================================================
# BÖLÜM 5 — ENERGY READINGS DÖNÜŞÜMÜ
# =============================================================================

print("\n" + "="*60)
print("ADIM 2/5 — Energy Readings Dönüşümü")
print("="*60)

df_energy_bronze = spark.read.format("delta").load(BRONZE_PATHS["energy_readings"])
log_step("Bronze okundu", df_energy_bronze.count(), "bronze_raw_energy_readings")

# ── Adım 1: Timestamp dönüşümü ──────────────────────────────────────────────
df_energy = df_energy_bronze.withColumn(
    "timestamp_utc",
    to_timestamp(col("timestamp_utc"), "yyyy-MM-dd HH:mm:ss")
)

# ── Adım 2: Birim normalizasyonu ─────────────────────────────────────────────
# DP-600: when/otherwise ile koşullu dönüşüm — UDF kullanmak yerine
# native Spark fonksiyonları her zaman daha hızlı
df_energy = df_energy.withColumn(
    "consumption_kwh",
    when(col("raw_unit") == "Wh",  col("raw_value") / 1000.0)
    .when(col("raw_unit") == "MWh", col("raw_value") * 1000.0)
    .when(col("raw_unit") == "W",   col("raw_value") / 1000.0 * (15.0/60.0))
    .otherwise(col("raw_value"))  # Zaten kWh
).withColumn(
    "demand_kw",
    when(col("raw_unit") == "W",   col("raw_value") / 1000.0)
    .when(col("raw_unit") == "kW",  col("raw_value"))
    .when(col("raw_unit") == "kWh", col("raw_value") * (60.0/15.0))
    .otherwise(col("raw_value") * (60.0/15.0))
)

# ── Adım 3: Veri kalitesi flag'i ─────────────────────────────────────────────
df_energy = add_quality_flag(
    df_energy, "consumption_kwh",
    MIN_CONSUMPTION_KWH, MAX_CONSUMPTION_KWH
)

# ── Adım 4: Window Function — interpolasyon ──────────────────────────────────
# DP-600: Window function tanımı
# partitionBy → aynı bina + sensör içinde bağımsız pencere
# orderBy → zamana göre sıralı
window_spec = (Window
    .partitionBy("building_id", "sensor_id")
    .orderBy("timestamp_utc")
)

# Önceki ve sonraki geçerli değeri getir
df_energy = (df_energy
    .withColumn("prev_value", lag("consumption_kwh", 1).over(window_spec))
    .withColumn("next_value", lead("consumption_kwh", 1).over(window_spec))
    .withColumn("prev_ts",    lag("timestamp_utc", 1).over(window_spec))
    .withColumn("next_ts",    lead("timestamp_utc", 1).over(window_spec))
)

# Boşluk boyutunu hesapla (saat cinsinden)
df_energy = df_energy.withColumn(
    "gap_hours",
    when(
        col("data_quality_flag") == "MISSING",
        (unix_timestamp("next_ts") - unix_timestamp("prev_ts")) / 3600.0
    ).otherwise(lit(0.0))
)

# İnterpolasyon uygula — sadece 2 saatten kısa boşluklara
df_energy = df_energy.withColumn(
    "consumption_kwh",
    when(
        (col("data_quality_flag") == "MISSING") &
        (col("gap_hours") <= MAX_INTERPOLATION_GAP_HOURS) &
        col("prev_value").isNotNull() & col("next_value").isNotNull(),
        spark_round((col("prev_value") + col("next_value")) / 2.0, 4)
    ).otherwise(col("consumption_kwh"))
).withColumn(
    "data_quality_flag",
    when(
        (col("data_quality_flag") == "MISSING") &
        (col("gap_hours") <= MAX_INTERPOLATION_GAP_HOURS) &
        col("prev_value").isNotNull() & col("next_value").isNotNull(),
        lit("INTERPOLATED")
    ).otherwise(col("data_quality_flag"))
).withColumn(
    "interpolated",
    col("data_quality_flag") == "INTERPOLATED"
)

# ── Adım 5: Yerel saat ekle ──────────────────────────────────────────────────
# DP-600: Building lookup ile broadcast join
# Building master küçük (3 satır) → broadcast ile shuffle yok
df_energy = (df_energy
    .join(
        broadcast(df_building_lookup.select(
            "building_id", "country_code", "utc_offset_hours",
            "conditioned_area_m2", "building_type", "subscription_tier",
            "has_pv", "has_battery", "has_heat_pump"
        )),
        on="building_id",
        how="left"
    )
    .withColumn(
        "timestamp_local",
        from_unixtime(
            unix_timestamp("timestamp_utc") + col("utc_offset_hours") * 3600
        ).cast(TimestampType())
    )
)

# ── Adım 6: Partition kolonları ve temizlik ───────────────────────────────────
df_energy_silver = (df_energy
    .withColumn("year",  year(col("timestamp_utc")))
    .withColumn("month", month(col("timestamp_utc")))
    .withColumn("processed_at", current_timestamp())
    .drop("prev_value", "next_value", "prev_ts", "next_ts",
          "gap_hours", "raw_value", "raw_unit", "load_timestamp",
          "utc_offset_hours")
    .dropDuplicates(["building_id", "sensor_id", "timestamp_utc"])
)

# Flag dağılımı — kalite raporu
print("\n📊 Energy Readings — Veri Kalitesi Dağılımı:")
df_energy_silver.groupBy("data_quality_flag").count().show()

# Silver'a yaz
energy_count = merge_to_silver(
    df_energy_silver,
    SILVER_PATHS["energy_readings"],
    merge_keys=["building_id", "sensor_id", "timestamp_utc"],
    table_name="silver_energy_readings_clean"
)


# =============================================================================
# BÖLÜM 6 — SOLAR GENERATION DÖNÜŞÜMÜ
# =============================================================================

print("\n" + "="*60)
print("ADIM 3/5 — Solar Generation Dönüşümü")
print("="*60)

df_solar_bronze = spark.read.format("delta").load(BRONZE_PATHS["solar_generation"])
log_step("Bronze okundu", df_solar_bronze.count(), "bronze_raw_solar_generation")

df_solar = df_solar_bronze.withColumn(
    "timestamp_utc", to_timestamp(col("timestamp_utc"), "yyyy-MM-dd HH:mm:ss")
)

# Birim normalizasyonu
df_solar = (df_solar
    .withColumn("generated_kwh",
        when(col("raw_unit") == "Wh", col("generated_raw") / 1000.0)
        .otherwise(col("generated_raw"))
    )
    .withColumn("exported_kwh",
        when(col("raw_unit") == "Wh", col("exported_raw") / 1000.0)
        .otherwise(col("exported_raw"))
    )
)

# Self-consumed hesabı: üretilen - şebekeye verilen
# DP-600: greatest/least ile negatif değer önleme
df_solar = df_solar.withColumn(
    "self_consumed_kwh",
    greatest(
        col("generated_kwh") - col("exported_kwh"),
        lit(0.0)
    )
)

# Kalite kontrolü
df_solar = add_quality_flag(df_solar, "generated_kwh", 0.0, 5000.0)

# Building join
df_solar = (df_solar
    .join(
        broadcast(df_building_lookup.select(
            "building_id", "utc_offset_hours"
        )),
        on="building_id", how="left"
    )
    .withColumn(
        "timestamp_local",
        from_unixtime(
            unix_timestamp("timestamp_utc") + col("utc_offset_hours") * 3600
        ).cast(TimestampType())
    )
)

df_solar_silver = (df_solar
    .withColumn("year",  year(col("timestamp_utc")))
    .withColumn("month", month(col("timestamp_utc")))
    .withColumn("processed_at", current_timestamp())
    .drop("generated_raw", "exported_raw", "raw_unit",
          "load_timestamp", "utc_offset_hours")
    .dropDuplicates(["building_id", "inverter_id", "timestamp_utc"])
)

solar_count = merge_to_silver(
    df_solar_silver,
    SILVER_PATHS["solar_generation"],
    merge_keys=["building_id", "inverter_id", "timestamp_utc"],
    table_name="silver_solar_generation_clean"
)


# =============================================================================
# BÖLÜM 7 — BATTERY STATUS DÖNÜŞÜMÜ
# =============================================================================

print("\n" + "="*60)
print("ADIM 4/5 — Battery Status Dönüşümü")
print("="*60)

df_battery_bronze = spark.read.format("delta").load(BRONZE_PATHS["battery_status"])
log_step("Bronze okundu", df_battery_bronze.count(), "bronze_raw_battery_status")

df_battery = df_battery_bronze.withColumn(
    "timestamp_utc", to_timestamp(col("timestamp_utc"), "yyyy-MM-dd HH:mm:ss")
)

# Net güç hesabı: pozitif = şarj, negatif = deşarj
df_battery = df_battery.withColumn(
    "net_power_kw",
    col("charge_power_raw") - col("discharge_power_raw")
)

# SoC kalite kontrolü
df_battery = add_quality_flag(df_battery, "soc_raw", MIN_SOC_PCT, MAX_SOC_PCT)

# SoC sütununu temiz isimle ekle
df_battery = df_battery.withColumn(
    "soc_pct",
    when(col("data_quality_flag") == "OK", col("soc_raw"))
    .otherwise(lit(None))
)

# Window function ile cycle count hesapla
# Bir tam döngü: şarj → deşarj → şarj geçişi
window_batt = (Window
    .partitionBy("building_id", "battery_id")
    .orderBy("timestamp_utc")
    .rowsBetween(Window.unboundedPreceding, 0)
)

# Kümülatif şarj enerjisi (kWh) — cycle count proxy
df_battery = df_battery.withColumn(
    "cumulative_charge_kwh",
    spark_sum(
        when(col("charge_power_raw") > 0,
             col("charge_power_raw") * lit(15.0/60.0))
        .otherwise(lit(0.0))
    ).over(window_batt)
)

# Building join — aktif stratejiyi ekle
df_battery = (df_battery
    .join(
        broadcast(df_building_lookup.select(
            "building_id", "battery_strategy",
            "battery_capacity_kwh", "utc_offset_hours"
        )),
        on="building_id", how="left"
    )
    .withColumnRenamed("battery_strategy", "active_strategy")
    .withColumn(
        "timestamp_local",
        from_unixtime(
            unix_timestamp("timestamp_utc") + col("utc_offset_hours") * 3600
        ).cast(TimestampType())
    )
)

df_battery_silver = (df_battery
    .withColumn("year",  year(col("timestamp_utc")))
    .withColumn("month", month(col("timestamp_utc")))
    .withColumn("charge_kw",    col("charge_power_raw"))
    .withColumn("discharge_kw", col("discharge_power_raw"))
    .withColumn("processed_at", current_timestamp())
    .drop("soc_raw", "charge_power_raw", "discharge_power_raw",
          "load_timestamp", "utc_offset_hours")
    .dropDuplicates(["building_id", "battery_id", "timestamp_utc"])
)

battery_count = merge_to_silver(
    df_battery_silver,
    SILVER_PATHS["battery_status"],
    merge_keys=["building_id", "battery_id", "timestamp_utc"],
    table_name="silver_battery_status_clean"
)


# =============================================================================
# BÖLÜM 8 — WEATHER DÖNÜŞÜMÜ (HDD / CDD DAHİL)
# =============================================================================

print("\n" + "="*60)
print("ADIM 5/5 — Weather Dönüşümü (HDD / CDD Hesaplama)")
print("="*60)

df_weather_bronze = spark.read.format("delta").load(BRONZE_PATHS["weather_data"])
log_step("Bronze okundu", df_weather_bronze.count(), "bronze_raw_weather_data")

df_weather = df_weather_bronze.withColumn(
    "timestamp_utc", to_timestamp(col("timestamp_utc"), "yyyy-MM-dd HH:mm:ss")
)

# Birim normalizasyonu
df_weather = (df_weather
    .withColumnRenamed("temperature_raw", "temperature_c")
    .withColumnRenamed("humidity_raw",    "humidity_pct")
    .withColumnRenamed("wind_speed_raw",  "wind_speed_ms")
)

# Sıcaklık kalite kontrolü
df_weather = add_quality_flag(df_weather, "temperature_c", MIN_TEMP_C, MAX_TEMP_C)

# ── HDD / CDD Hesaplama ──────────────────────────────────────────────────────
# HDD (Heating Degree Day): Isıtma ihtiyacını ölçer
#   Base: 15°C → 15°C altında ısıtma gerekir
#   15 dakikalık interval → günlük değeri elde etmek için 96'ya böleceğiz
#
# CDD (Cooling Degree Day): Soğutma ihtiyacını ölçer
#   Base: 22°C → 22°C üzerinde soğutma gerekir
#
# DP-600: greatest(x, 0) → negatif değer oluşmasını önler
#          (15°C üzerindeki günler için HDD = 0 olmalı)

INTERVAL_FRACTION = 15.0 / (60.0 * 24.0)  # 15 dakika / 1 gün

df_weather = (df_weather
    .withColumn(
        "heating_degree_day",
        spark_round(
            greatest(lit(15.0) - col("temperature_c"), lit(0.0)) * lit(INTERVAL_FRACTION),
            4
        )
    )
    .withColumn(
        "cooling_degree_day",
        spark_round(
            greatest(col("temperature_c") - lit(22.0), lit(0.0)) * lit(INTERVAL_FRACTION),
            4
        )
    )
)

# Irradiance kalite kontrolü
df_weather = df_weather.withColumn(
    "irradiance_quality",
    when(col("solar_irradiance") < 0, lit("ANOMALY"))
    .when(col("solar_irradiance") > 1500, lit("ANOMALY"))  # Fiziksel maksimum ~1361 W/m²
    .otherwise(lit("OK"))
)

df_weather_silver = (df_weather
    .withColumn("year",  year(col("timestamp_utc")))
    .withColumn("month", month(col("timestamp_utc")))
    .withColumn("processed_at", current_timestamp())
    .drop("load_timestamp")
    .dropDuplicates(["building_id", "timestamp_utc"])
)

print("\n📊 Weather — HDD/CDD Örnek (ilk 5 satır):")
(df_weather_silver
    .filter(col("building_id") == "B001")
    .select("timestamp_utc", "temperature_c",
            "heating_degree_day", "cooling_degree_day")
    .orderBy("timestamp_utc")
    .show(5)
)

weather_count = merge_to_silver(
    df_weather_silver,
    SILVER_PATHS["weather_data"],
    merge_keys=["building_id", "timestamp_utc"],
    table_name="silver_weather_clean"
)


# =============================================================================
# BÖLÜM 9 — Z-ORDER OPTIMIZE
# =============================================================================
# DP-600: Z-ORDER en sık kullanılan sorgulara göre seçilir.
# Tipik sorgu: "B001 binasının 2024 Mart ayı saatlik verisi"
# → building_id + timestamp_utc üzerinde Z-ORDER optimal

print("\n" + "="*60)
print("Z-ORDER OPTIMIZE")
print("="*60)

optimize_silver_table(
    SILVER_PATHS["energy_readings"],
    "silver_energy_readings_clean",
    zorder_cols=["building_id", "timestamp_utc"]
)

optimize_silver_table(
    SILVER_PATHS["solar_generation"],
    "silver_solar_generation_clean",
    zorder_cols=["building_id", "timestamp_utc"]
)

optimize_silver_table(
    SILVER_PATHS["battery_status"],
    "silver_battery_status_clean",
    zorder_cols=["building_id", "timestamp_utc"]
)

optimize_silver_table(
    SILVER_PATHS["weather_data"],
    "silver_weather_clean",
    zorder_cols=["building_id", "timestamp_utc"]
)

# Cache temizle
df_building_lookup.unpersist()
log_step("🧹 Building lookup cache temizlendi")


# =============================================================================
# BÖLÜM 10 — DOĞRULAMA RAPORU
# =============================================================================

print("\n" + "="*60)
print("DOĞRULAMA RAPORU")
print("="*60)

tables_to_check = [
    ("silver_energy_readings_clean", SILVER_PATHS["energy_readings"]),
    ("silver_solar_generation_clean", SILVER_PATHS["solar_generation"]),
    ("silver_battery_status_clean",   SILVER_PATHS["battery_status"]),
    ("silver_weather_clean",          SILVER_PATHS["weather_data"]),
    ("silver_building_master",        SILVER_PATHS["building_master"]),
]

total = 0
for name, path in tables_to_check:
    try:
        # FIX (2026-05-18): path → spark.table() (managed table için)
        df_check = spark.table(name)
        cnt = df_check.count()
        total += cnt
        print(f"\n📊 {name}: {cnt:,} satır")

        if "data_quality_flag" in df_check.columns:
            df_check.groupBy("data_quality_flag").count().orderBy("data_quality_flag").show()

    except Exception as e:
        print(f"❌ {name}: {str(e)[:80]}")

# HDD/CDD yıllık özet — iklim düzeltmesi için referans
print("\n🌡️  HDD / CDD Yıllık Özet (iklim düzeltmesi referansı):")
# FIX (2026-05-18): path → spark.table() (managed table için)
df_hdd = spark.table("silver_weather_clean")
(df_hdd
    .groupBy("building_id")
    .agg(
        spark_round(spark_sum("heating_degree_day"), 1).alias("annual_HDD"),
        spark_round(spark_sum("cooling_degree_day"), 1).alias("annual_CDD")
    )
    .orderBy("building_id")
    .show()
)

print("\n" + "="*60)
print("SILVER TRANSFORMATION TAMAMLANDI")
print("="*60)
print(f"✅ Toplam Silver kayıt: {total:,}")
print(f"✅ MERGE ile duplicate önleme: aktif")
print(f"✅ Z-ORDER OPTIMIZE: tüm tablolarda uygulandı")
print(f"✅ HDD/CDD: weather tablosuna eklendi")
print(f"✅ Broadcast join: building lookup optimize edildi")
print(f"\n➡️  Sonraki adım: 03_gold_kpi_engine.py")
