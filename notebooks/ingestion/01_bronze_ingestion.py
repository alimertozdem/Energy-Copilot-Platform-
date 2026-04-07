# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 01_bronze_ingestion.py
# Layer: BRONZE — Raw Data Ingestion
# =============================================================================
#
# GÖREV (Purpose):
#   Kaynak verileri olduğu gibi Bronze Lakehouse katmanına yükle.
#   Hiçbir dönüşüm yapma. Veriyi ham halde koru.
#
# KURAL (Rule):
#   Bronze = Append-only. Mevcut veriyi silme veya değiştirme.
#   Hatalı veri bile Bronze'a yazılır — Silver temizler.
#
# DP-600 NOTLARI:
#   - Explicit schema tanımı (schema-on-write)
#   - Partition pruning için year/month partitioning
#   - Shuffle partition optimizasyonu
#   - Delta Lake append modu
#   - OPTIMIZE komutu dosya boyutlarını düzenler
#
# ÇALIŞTIRMA MODU:
#   MODE = "development" → sample-data klasöründen okur (CSV)
#   MODE = "production"  → Eventstream / API'den okur
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================
# DP-600: Shuffle partition sayısı veri boyutuna göre ayarlanmalı.
# Default: 200 → büyük veri için iyi, küçük veri için çok fazla.
# Küçük veri (< 1GB) için 8-16 arası idealdir.
# Fazla partition = fazla task overhead = yavaş çalışma.

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType, TimestampType, BooleanType
)
from pyspark.sql.functions import (
    col, to_timestamp, current_timestamp,
    year, month, dayofmonth, lit
)
from delta.tables import DeltaTable
import logging
from datetime import datetime

# Spark session (Fabric'te otomatik başlar, bu satır local test içindir)
# spark = SparkSession.builder.getOrCreate()

# DP-600: Küçük veri için shuffle partition optimizasyonu
spark.conf.set("spark.sql.shuffle.partitions", "8")

# DP-600: Delta Lake schema evolution — yeni kolon gelirse otomatik kabul et
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")

# Log ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bronze_ingestion")

print("✅ Spark konfigürasyonu tamamlandı")
print(f"   shuffle.partitions = {spark.conf.get('spark.sql.shuffle.partitions')}")


# =============================================================================
# BÖLÜM 2 — KONFİGÜRASYON
# =============================================================================
# Tüm değişken değerler burada tanımlanır.
# Notebook'un geri kalanında hardcoded string kullanılmaz.

# Çalışma modu — sadece bu satırı değiştir
MODE = "development"  # "development" veya "production"

# Lakehouse konfigürasyonu
# Fabric'te Lakehouse adını buraya yaz
LAKEHOUSE_NAME = "energy-copilot-lakehouse"

# DP-600: Fabric'te dosya yolları "abfss://" ile başlar
# Development'ta ise local path kullanırız
if MODE == "development":
    # Fabric notebook'unda sample-data klasörü buraya yüklenmeli
    # (Files bölümünden "Upload folder" ile yükle)
    BASE_DATA_PATH = "Files/sample-data"
    print(f"🔧 MODE: development — {BASE_DATA_PATH} klasöründen okunacak")
else:
    # Production: Eventstream landing path
    BASE_DATA_PATH = f"abfss://...@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_NAME}/Files/landing"
    print(f"🚀 MODE: production — Eventstream landing zone'dan okunacak")

# Bronze tablo yolları
# DP-600: Delta tabloları "Tables/" altında tutulur — SQL endpoint otomatik görür
BRONZE_PATHS = {
    "energy_readings": "Tables/bronze_raw_energy_readings",
    "solar_generation": "Tables/bronze_raw_solar_generation",
    "battery_status":   "Tables/bronze_raw_battery_status",
    "weather_data":     "Tables/bronze_raw_weather_data",
    "building_master":  "Tables/bronze_building_master",
}

print(f"\n📋 Bronze tablo yolları:")
for name, path in BRONZE_PATHS.items():
    print(f"   {name}: {path}")


# =============================================================================
# BÖLÜM 3 — SCHEMA TANIMLARI (Schema-on-Write)
# =============================================================================
# DP-600 CRITICAL:
#   CSV'yi schema olmadan okursan Spark her kolonu STRING yapar
#   veya yanlış tip tahmin eder. Bu Gold katmanında KPI hesaplama
#   hatalarına yol açar. Her zaman explicit schema kullan.

# Enerji tüketim verisi
schema_energy = StructType([
    StructField("ingestion_id",   StringType(),    True),
    StructField("building_id",    StringType(),    False),  # NotNull
    StructField("source_system",  StringType(),    True),
    StructField("sensor_id",      StringType(),    True),
    StructField("timestamp_utc",  StringType(),    False),  # String olarak alıp sonra cast edeceğiz
    StructField("raw_value",      DoubleType(),    True),
    StructField("raw_unit",       StringType(),    True),
    StructField("ingested_at",    StringType(),    True),
    StructField("tier",           StringType(),    True),
])

# Solar üretim verisi
schema_solar = StructType([
    StructField("ingestion_id",   StringType(),    True),
    StructField("building_id",    StringType(),    False),
    StructField("timestamp_utc",  StringType(),    False),
    StructField("generated_raw",  DoubleType(),    True),
    StructField("exported_raw",   DoubleType(),    True),
    StructField("raw_unit",       StringType(),    True),
    StructField("inverter_id",    StringType(),    True),
    StructField("ingested_at",    StringType(),    True),
])

# Batarya durum verisi
schema_battery = StructType([
    StructField("ingestion_id",          StringType(),  True),
    StructField("building_id",           StringType(),  False),
    StructField("timestamp_utc",         StringType(),  False),
    StructField("soc_raw",               DoubleType(),  True),
    StructField("charge_power_raw",      DoubleType(),  True),
    StructField("discharge_power_raw",   DoubleType(),  True),
    StructField("battery_id",            StringType(),  True),
    StructField("ingested_at",           StringType(),  True),
])

# Hava durumu verisi
schema_weather = StructType([
    StructField("ingestion_id",       StringType(),  True),
    StructField("building_id",        StringType(),  False),
    StructField("timestamp_utc",      StringType(),  False),
    StructField("temperature_raw",    DoubleType(),  True),
    StructField("humidity_raw",       DoubleType(),  True),
    StructField("solar_irradiance",   DoubleType(),  True),
    StructField("wind_speed_raw",     DoubleType(),  True),
    StructField("source_api",         StringType(),  True),
    StructField("ingested_at",        StringType(),  True),
])

# Bina master verisi
schema_building = StructType([
    StructField("building_id",           StringType(),   False),
    StructField("organization_id",       StringType(),   True),
    StructField("building_name",         StringType(),   True),
    StructField("country_code",          StringType(),   True),
    StructField("city",                  StringType(),   True),
    StructField("climate_zone",          StringType(),   True),
    StructField("gross_floor_area_m2",   DoubleType(),   True),
    StructField("conditioned_area_m2",   DoubleType(),   True),
    StructField("year_built",            IntegerType(),  True),
    StructField("building_type",         StringType(),   True),
    StructField("subscription_tier",     StringType(),   True),
    StructField("has_pv",                StringType(),   True),  # CSV'de True/False string
    StructField("pv_capacity_kwp",       DoubleType(),   True),
    StructField("roof_area_m2",          DoubleType(),   True),
    StructField("roof_orientation",      StringType(),   True),
    StructField("roof_tilt_deg",         DoubleType(),   True),
    StructField("has_battery",           StringType(),   True),
    StructField("battery_capacity_kwh",  DoubleType(),   True),
    StructField("battery_technology",    StringType(),   True),
    StructField("battery_strategy",      StringType(),   True),
    StructField("has_heat_pump",         StringType(),   True),
    StructField("heat_pump_cop_rated",   DoubleType(),   True),
    StructField("heat_pump_capacity_kw", DoubleType(),   True),
    StructField("has_hvac_traditional",  StringType(),   True),
    StructField("has_ev_charging",       StringType(),   True),
    StructField("has_led_lighting",      StringType(),   True),
    StructField("wall_u_value",          DoubleType(),   True),
    StructField("roof_u_value",          DoubleType(),   True),
    StructField("floor_u_value",         DoubleType(),   True),
    StructField("window_u_value",        DoubleType(),   True),
    StructField("window_to_wall_ratio",  DoubleType(),   True),
    StructField("air_tightness_ach",     DoubleType(),   True),
    StructField("thermal_mass_level",    StringType(),   True),
    StructField("insulation_year",       DoubleType(),   True),  # nullable
    StructField("has_thermal_bridge",    StringType(),   True),
    StructField("energy_certificate",    StringType(),   True),
    StructField("energy_certificate_year", DoubleType(), True),
    StructField("regulatory_profile_id", StringType(),  True),
    StructField("iso50001_certified",    StringType(),   True),
])

print("✅ Schema tanımları hazır — 5 tablo")


# =============================================================================
# BÖLÜM 4 — YARDIMCI FONKSİYONLAR
# =============================================================================

def log_step(step_name, record_count=None, table_name=None):
    """Adım loglaması — ne yapıldı, kaç satır işlendi."""
    ts = datetime.now().strftime("%H:%M:%S")
    msg = f"[{ts}] {step_name}"
    if table_name:
        msg += f" | tablo: {table_name}"
    if record_count is not None:
        msg += f" | {record_count:,} satır"
    print(msg)


def table_exists(table_path):
    """Delta tablo var mı kontrol et."""
    try:
        DeltaTable.forPath(spark, table_path)
        return True
    except Exception:
        return False


def write_bronze_table(df, table_path, partition_cols, table_name):
    """
    Bronze katmanına Delta formatında yaz.

    DP-600 NOTLARI:
    - mode("append"): Bronze append-only olmalı
    - partitionBy: Sorgu hızı için kritik
      → year/month ile partition yapınca
        sadece ilgili ay okunur, tüm tablo değil
    - Küçük dosya sorunu: çok fazla partition = çok küçük dosyalar
      Bu yüzden OPTIMIZE komutu sonunda çalıştırılır
    """
    record_count = df.count()

    (df.write
       .format("delta")
       .mode("append")
       .partitionBy(partition_cols)
       .option("mergeSchema", "true")  # Yeni kolon gelirse kabul et
       .save(table_path)
    )

    log_step(f"✅ Bronze yazma tamamlandı", record_count, table_name)
    return record_count


def optimize_table(table_path, table_name):
    """
    DP-600: OPTIMIZE komutu küçük Delta dosyalarını birleştirir.
    Çok sayıda küçük dosya = yavaş okuma = kötü performans.
    Bronze'da genellikle çok sayıda küçük dosya oluşur.
    OPTIMIZE bunu düzeltir.
    """
    try:
        spark.sql(f"OPTIMIZE delta.`{table_path}`")
        log_step(f"⚡ OPTIMIZE tamamlandı", table_name=table_name)
    except Exception as e:
        log_step(f"⚠️  OPTIMIZE atlandı ({str(e)[:50]})", table_name=table_name)


# =============================================================================
# BÖLÜM 5 — ENERGY READINGS YÜKLEME
# =============================================================================

print("\n" + "="*60)
print("ADIM 1/5 — Energy Readings (Tüketim Verisi)")
print("="*60)

# CSV oku — explicit schema ile
df_energy_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")          # Boş string'i null olarak işle
    .option("emptyValue", "")
    .schema(schema_energy)
    .load(f"{BASE_DATA_PATH}/raw_energy_readings.csv")
)

log_step("CSV okundu", df_energy_raw.count(), "raw_energy_readings")

# Partition kolonları ekle (yıl ve ay)
# DP-600: Partition kolonları sorguda WHERE ile kullanılır
# → "WHERE year=2024 AND month=3" sadece o klasörü okur
df_energy = (
    df_energy_raw
    .withColumn("year",  year(to_timestamp(col("timestamp_utc"))))
    .withColumn("month", month(to_timestamp(col("timestamp_utc"))))
    .withColumn("load_timestamp", current_timestamp())  # Ne zaman yüklendi
)

# Temel veri kalitesi kontrolü — Bronze'da sadece loglarız, silmeyiz
null_building = df_energy.filter(col("building_id").isNull()).count()
null_value    = df_energy.filter(col("raw_value").isNull()).count()
if null_building > 0:
    print(f"⚠️  NULL building_id: {null_building} satır — yükleniyor (Bronze kuralı)")
if null_value > 0:
    print(f"⚠️  NULL raw_value: {null_value} satır — yükleniyor (Bronze kuralı)")

# Bronze'a yaz
energy_count = write_bronze_table(
    df_energy,
    BRONZE_PATHS["energy_readings"],
    partition_cols=["building_id", "year", "month"],
    table_name="bronze_raw_energy_readings"
)

# Küçük dosyaları birleştir
optimize_table(BRONZE_PATHS["energy_readings"], "bronze_raw_energy_readings")


# =============================================================================
# BÖLÜM 6 — SOLAR GENERATION YÜKLEME
# =============================================================================

print("\n" + "="*60)
print("ADIM 2/5 — Solar Generation (PV Üretim Verisi)")
print("="*60)

df_solar_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .schema(schema_solar)
    .load(f"{BASE_DATA_PATH}/raw_solar_generation.csv")
)

log_step("CSV okundu", df_solar_raw.count(), "raw_solar_generation")

df_solar = (
    df_solar_raw
    .withColumn("year",           year(to_timestamp(col("timestamp_utc"))))
    .withColumn("month",          month(to_timestamp(col("timestamp_utc"))))
    .withColumn("load_timestamp", current_timestamp())
)

solar_count = write_bronze_table(
    df_solar,
    BRONZE_PATHS["solar_generation"],
    partition_cols=["building_id", "year", "month"],
    table_name="bronze_raw_solar_generation"
)

optimize_table(BRONZE_PATHS["solar_generation"], "bronze_raw_solar_generation")


# =============================================================================
# BÖLÜM 7 — BATTERY STATUS YÜKLEME
# =============================================================================

print("\n" + "="*60)
print("ADIM 3/5 — Battery Status (Batarya Durum Verisi)")
print("="*60)

df_battery_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .schema(schema_battery)
    .load(f"{BASE_DATA_PATH}/raw_battery_status.csv")
)

log_step("CSV okundu", df_battery_raw.count(), "raw_battery_status")

df_battery = (
    df_battery_raw
    .withColumn("year",           year(to_timestamp(col("timestamp_utc"))))
    .withColumn("month",          month(to_timestamp(col("timestamp_utc"))))
    .withColumn("load_timestamp", current_timestamp())
)

battery_count = write_bronze_table(
    df_battery,
    BRONZE_PATHS["battery_status"],
    partition_cols=["building_id", "year", "month"],
    table_name="bronze_raw_battery_status"
)

optimize_table(BRONZE_PATHS["battery_status"], "bronze_raw_battery_status")


# =============================================================================
# BÖLÜM 8 — WEATHER DATA YÜKLEME
# =============================================================================

print("\n" + "="*60)
print("ADIM 4/5 — Weather Data (Hava Durumu Verisi)")
print("="*60)

df_weather_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .schema(schema_weather)
    .load(f"{BASE_DATA_PATH}/raw_weather_data.csv")
)

log_step("CSV okundu", df_weather_raw.count(), "raw_weather_data")

df_weather = (
    df_weather_raw
    .withColumn("year",           year(to_timestamp(col("timestamp_utc"))))
    .withColumn("month",          month(to_timestamp(col("timestamp_utc"))))
    .withColumn("load_timestamp", current_timestamp())
)

weather_count = write_bronze_table(
    df_weather,
    BRONZE_PATHS["weather_data"],
    partition_cols=["building_id", "year", "month"],
    table_name="bronze_raw_weather_data"
)

optimize_table(BRONZE_PATHS["weather_data"], "bronze_raw_weather_data")


# =============================================================================
# BÖLÜM 9 — BUILDING MASTER YÜKLEME
# =============================================================================
# Building master farklı: partition yok (küçük referans tablosu)
# overwrite modu — her çalışmada güncel master yüklenir

print("\n" + "="*60)
print("ADIM 5/5 — Building Master (Bina Referans Verisi)")
print("="*60)

df_building_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .schema(schema_building)
    .load(f"{BASE_DATA_PATH}/building_master.csv")
)

log_step("CSV okundu", df_building_raw.count(), "building_master")

df_building = (
    df_building_raw
    .withColumn("load_timestamp", current_timestamp())
)

# Building master: overwrite (her zaman güncel olmalı)
# DP-600: overwrite + replaceWhere pattern — tüm tabloyu sil değil,
# sadece ilgili partition'ı değiştir (büyük tablolarda kullanılır)
# Küçük referans tablolarında tam overwrite uygundur
(df_building.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(BRONZE_PATHS["building_master"])
)

building_count = df_building.count()
log_step("✅ Building master yazıldı", building_count, "bronze_building_master")


# =============================================================================
# BÖLÜM 10 — DOĞRULAMA VE ÖZET RAPOR
# =============================================================================

print("\n" + "="*60)
print("DOĞRULAMA RAPORU")
print("="*60)

# Her tablodan kayıt sayısı ve bina dağılımı
tables_to_validate = [
    ("bronze_raw_energy_readings", BRONZE_PATHS["energy_readings"]),
    ("bronze_raw_solar_generation", BRONZE_PATHS["solar_generation"]),
    ("bronze_raw_battery_status",   BRONZE_PATHS["battery_status"]),
    ("bronze_raw_weather_data",     BRONZE_PATHS["weather_data"]),
    ("bronze_building_master",      BRONZE_PATHS["building_master"]),
]

total_records = 0
for table_name, table_path in tables_to_validate:
    try:
        df_check = spark.read.format("delta").load(table_path)
        count = df_check.count()
        total_records += count

        # Bina dağılımı
        building_dist = (df_check
            .groupBy("building_id")
            .count()
            .orderBy("building_id")
        )

        print(f"\n📊 {table_name}")
        print(f"   Toplam satır: {count:,}")
        building_dist.show(truncate=False)

    except Exception as e:
        print(f"❌ {table_name}: Okuma hatası — {str(e)}")

# Timestamp kontrolü — energy readings için
print("\n📅 Energy Readings — Tarih Aralığı Kontrolü")
df_ts_check = spark.read.format("delta").load(BRONZE_PATHS["energy_readings"])
(df_ts_check
    .groupBy("building_id")
    .agg(
        {"timestamp_utc": "min", "timestamp_utc": "max"}
    )
    .show(truncate=False)
)

# Partition kontrolü
print("\n📁 Partition Yapısı (Energy Readings — ilk 5):")
(df_ts_check
    .select("building_id", "year", "month")
    .distinct()
    .orderBy("building_id", "year", "month")
    .show(5)
)

print("\n" + "="*60)
print("BRONZE INGESTION TAMAMLANDI")
print("="*60)
print(f"✅ Toplam yüklenen kayıt: {total_records:,}")
print(f"✅ Oluşturulan tablo sayısı: {len(tables_to_validate)}")
print(f"✅ Partition stratejisi: building_id / year / month")
print(f"✅ Format: Delta Lake")
print(f"✅ Mod: {MODE}")
print("\n➡️  Sonraki adım: 02_silver_transformation.py")
