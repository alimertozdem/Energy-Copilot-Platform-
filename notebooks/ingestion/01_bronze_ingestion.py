# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 01_bronze_ingestion.py
# Layer: BRONZE — Raw Data Ingestion (Incremental Load)
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
# INCREMENTAL LOAD (Watermark Pattern):
#   Her çalışmada tüm CSV yeniden yüklenmez. Sadece watermark'tan
#   sonraki yeni kayıtlar eklenir. Bu şekilde:
#   → Duplicate oluşmaz
#   → Fabric kapasitesi verimli kullanılır
#   → Büyük veri hacimlerinde çalışma süresi sabit kalır
#
#   Watermark = her tablo için MAX(timestamp_utc) değeri
#   Konum     = Tables/bronze_watermarks Delta tablosu
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

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType, TimestampType, BooleanType
)
from pyspark.sql.functions import (
    col, to_timestamp, current_timestamp,
    year, month, dayofmonth, lit, max as spark_max
)
from delta.tables import DeltaTable
import logging
from datetime import datetime, timezone

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

# Çalışma modu — sadece bu satırı değiştir
MODE = "development"  # "development" veya "production"

# Lakehouse konfigürasyonu
LAKEHOUSE_NAME = "energy-copilot-lakehouse"

if MODE == "development":
    BASE_DATA_PATH = "Files/sample-data"
    print(f"🔧 MODE: development — {BASE_DATA_PATH} klasöründen okunacak")
else:
    BASE_DATA_PATH = f"abfss://...@onelake.dfs.fabric.microsoft.com/{LAKEHOUSE_NAME}/Files/landing"
    print(f"🚀 MODE: production — Eventstream landing zone'dan okunacak")

# Bronze tablo yolları
BRONZE_PATHS = {
    "energy_readings": "Tables/bronze_raw_energy_readings",
    "solar_generation": "Tables/bronze_raw_solar_generation",
    "battery_status":   "Tables/bronze_raw_battery_status",
    "weather_data":     "Tables/bronze_raw_weather_data",
    "building_master":  "Tables/bronze_building_master",
}

# Watermark kontrol tablosu — incremental load için
# Her satır: table_name, last_watermark_utc
WATERMARK_TABLE_PATH = "Tables/bronze_watermarks"

# Epoch başlangıcı — tabloda hiç veri yoksa bu tarihten itibaren yükle
# "1970-01-01" kullanmak yerine makul bir başlangıç tarihi kullan
EPOCH_START = "2020-01-01T00:00:00"

print(f"\n📋 Bronze tablo yolları:")
for name, path in BRONZE_PATHS.items():
    print(f"   {name}: {path}")


# =============================================================================
# BÖLÜM 3 — SCHEMA TANIMLARI (Schema-on-Write)
# =============================================================================

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
    StructField("has_pv",                StringType(),   True),
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
    StructField("insulation_year",       DoubleType(),   True),
    StructField("has_thermal_bridge",    StringType(),   True),
    StructField("energy_certificate",    StringType(),   True),
    StructField("energy_certificate_year", DoubleType(), True),
    StructField("regulatory_profile_id", StringType(),  True),
    StructField("iso50001_certified",    StringType(),   True),
])

# Watermark kontrol tablosu şeması
schema_watermark = StructType([
    StructField("table_name",          StringType(),    False),
    StructField("last_watermark_utc",  StringType(),    True),   # ISO 8601 string
    StructField("rows_loaded",         IntegerType(),   True),   # Son çalışmada yüklenen satır sayısı
    StructField("updated_at",          TimestampType(), True),
])

print("✅ Schema tanımları hazır — 5 tablo + 1 watermark tablosu")


# =============================================================================
# BÖLÜM 4 — WATERMARK FONKSİYONLARI
# =============================================================================

def get_watermark(table_key: str) -> str:
    """
    Verilen tablo için son watermark değerini oku.

    Önce bronze_watermarks kontrol tablosuna bakar.
    Tablo yoksa veya kayıt yoksa EPOCH_START değerini döner.

    Returns: ISO 8601 string — örn. "2024-03-15T10:30:00"
    """
    try:
        if not DeltaTable.isDeltaTable(spark, WATERMARK_TABLE_PATH):
            print(f"   ⏱️  Watermark tablosu yok — ilk çalışma, {EPOCH_START}'dan yükleniyor")
            return EPOCH_START

        df_wm = spark.read.format("delta").load(WATERMARK_TABLE_PATH)
        row = df_wm.filter(col("table_name") == table_key).select("last_watermark_utc").first()

        if row is None:
            print(f"   ⏱️  '{table_key}' için kayıt yok — {EPOCH_START}'dan yükleniyor")
            return EPOCH_START

        wm = row["last_watermark_utc"]
        print(f"   ⏱️  Watermark: {wm}")
        return wm

    except Exception as e:
        print(f"   ⚠️  Watermark okunamadı ({str(e)[:60]}) — {EPOCH_START} kullanılıyor")
        return EPOCH_START


def update_watermark(table_key: str, new_watermark: str, rows_loaded: int):
    """
    Bronze_watermarks tablosunu güncelle (MERGE — upsert).

    Tablo yoksa oluşturur.
    Varsa ilgili table_name satırını günceller.

    DP-600: MERGE = idempotent update. Aynı notebook iki kez çalışsa
    bile watermark doğru değerde kalır.
    """
    if new_watermark is None:
        print(f"   ⚠️  Yeni watermark None — güncelleme atlanıyor")
        return

    from pyspark.sql import Row

    new_row = spark.createDataFrame([
        Row(
            table_name=table_key,
            last_watermark_utc=new_watermark,
            rows_loaded=rows_loaded,
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
    ], schema=schema_watermark)

    if DeltaTable.isDeltaTable(spark, WATERMARK_TABLE_PATH):
        # MERGE — upsert: kayıt varsa güncelle, yoksa ekle
        dt_wm = DeltaTable.forPath(spark, WATERMARK_TABLE_PATH)
        (dt_wm.alias("existing")
            .merge(
                new_row.alias("updates"),
                "existing.table_name = updates.table_name"
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        # İlk kez oluştur
        (new_row.write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .save(WATERMARK_TABLE_PATH)
        )

    print(f"   ✅ Watermark güncellendi: {table_key} → {new_watermark} ({rows_loaded:,} satır)")


def compute_new_watermark(df_new, timestamp_col: str = "timestamp_utc") -> str:
    """
    Yüklenen yeni verinin MAX(timestamp_utc) değerini hesapla.
    Bu değer bir sonraki çalışmada watermark olarak kullanılacak.
    """
    max_row = df_new.agg(spark_max(to_timestamp(col(timestamp_col))).alias("max_ts")).first()
    if max_row and max_row["max_ts"]:
        return max_row["max_ts"].strftime("%Y-%m-%dT%H:%M:%S")
    return None


# =============================================================================
# BÖLÜM 5 — YARDIMCI FONKSİYONLAR
# =============================================================================

def log_step(step_name, record_count=None, table_name=None):
    ts = datetime.now().strftime("%H:%M:%S")
    msg = f"[{ts}] {step_name}"
    if table_name:
        msg += f" | tablo: {table_name}"
    if record_count is not None:
        msg += f" | {record_count:,} satır"
    print(msg)


def table_exists(table_path):
    try:
        DeltaTable.forPath(spark, table_path)
        return True
    except Exception:
        return False


def filter_new_records(df, watermark_str: str, timestamp_col: str = "timestamp_utc"):
    """
    Watermark'tan sonraki kayıtları filtrele.

    DP-600: to_timestamp() ile karşılaştırma yapıyoruz çünkü
    kaynak CSV'de timestamp_utc STRING tipinde. String karşılaştırması
    ISO 8601 formatında doğru çalışır ama explicit cast daha güvenli.

    Sınır dahil değil (>) — watermark anındaki kayıt zaten yüklenmiş.
    """
    return df.filter(
        to_timestamp(col(timestamp_col)) > to_timestamp(lit(watermark_str))
    )


def write_bronze_table(df, table_path, partition_cols, table_name):
    """
    Bronze katmanına Delta formatında yaz (append-only).
    """
    record_count = df.count()

    if record_count == 0:
        print(f"   ℹ️  Yeni kayıt yok — {table_name} yazma atlandı")
        return 0

    (df.write
       .format("delta")
       .mode("append")
       .partitionBy(partition_cols)
       .option("mergeSchema", "true")
       .save(table_path)
    )

    log_step(f"✅ Bronze yazma tamamlandı", record_count, table_name)
    return record_count


def optimize_table(table_path, table_name, z_order_cols=None):
    """
    OPTIMIZE + isteğe bağlı ZORDER.

    Z-ORDER: Çok sık sorgulanan kolonlara göre dosyaları fiziksel olarak sıralar.
    Bronze için sadece OPTIMIZE (dosya birleştirme) yeterlidir.
    ZORDER daha çok Gold katmanı içindir.

    DP-600 NOT: Partition kolonlarına ZORDER yapılamaz.
    """
    try:
        if z_order_cols:
            z_cols = ", ".join(z_order_cols)
            spark.sql(f"OPTIMIZE delta.`{table_path}` ZORDER BY ({z_cols})")
            log_step(f"⚡ OPTIMIZE + ZORDER({z_cols}) tamamlandı", table_name=table_name)
        else:
            spark.sql(f"OPTIMIZE delta.`{table_path}`")
            log_step(f"⚡ OPTIMIZE tamamlandı", table_name=table_name)
    except Exception as e:
        log_step(f"⚠️  OPTIMIZE atlandı ({str(e)[:60]})", table_name=table_name)


# =============================================================================
# BÖLÜM 6 — ENERGY READINGS YÜKLEME (Incremental)
# =============================================================================

print("\n" + "="*60)
print("ADIM 1/5 — Energy Readings (Tüketim Verisi)")
print("="*60)

# Watermark oku
wm_energy = get_watermark("bronze_raw_energy_readings")

# CSV oku — explicit schema ile
df_energy_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .option("emptyValue", "")
    .schema(schema_energy)
    .load(f"{BASE_DATA_PATH}/raw_energy_readings.csv")
)

total_energy = df_energy_raw.count()
log_step("CSV okundu (toplam)", total_energy, "raw_energy_readings")

# Sadece watermark'tan sonraki kayıtları al
df_energy_new = filter_new_records(df_energy_raw, wm_energy)
new_energy_count = df_energy_new.count()
print(f"   → Watermark sonrası yeni kayıt: {new_energy_count:,} / {total_energy:,}")

# Partition kolonları ekle
df_energy = (
    df_energy_new
    .withColumn("year",  year(to_timestamp(col("timestamp_utc"))))
    .withColumn("month", month(to_timestamp(col("timestamp_utc"))))
    .withColumn("load_timestamp", current_timestamp())
)

# Temel kalite kontrolü — Bronze'da sadece loglarız
null_building = df_energy.filter(col("building_id").isNull()).count()
null_value    = df_energy.filter(col("raw_value").isNull()).count()
if null_building > 0:
    print(f"   ⚠️  NULL building_id: {null_building} satır — yükleniyor (Bronze kuralı)")
if null_value > 0:
    print(f"   ⚠️  NULL raw_value: {null_value} satır — yükleniyor (Bronze kuralı)")

# Bronze'a yaz
energy_count = write_bronze_table(
    df_energy,
    BRONZE_PATHS["energy_readings"],
    partition_cols=["building_id", "year", "month"],
    table_name="bronze_raw_energy_readings"
)

# Watermark güncelle
if energy_count > 0:
    new_wm_energy = compute_new_watermark(df_energy)
    update_watermark("bronze_raw_energy_readings", new_wm_energy, energy_count)

optimize_table(BRONZE_PATHS["energy_readings"], "bronze_raw_energy_readings")


# =============================================================================
# BÖLÜM 7 — SOLAR GENERATION YÜKLEME (Incremental)
# =============================================================================

print("\n" + "="*60)
print("ADIM 2/5 — Solar Generation (PV Üretim Verisi)")
print("="*60)

wm_solar = get_watermark("bronze_raw_solar_generation")

df_solar_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .schema(schema_solar)
    .load(f"{BASE_DATA_PATH}/raw_solar_generation.csv")
)

total_solar = df_solar_raw.count()
df_solar_new = filter_new_records(df_solar_raw, wm_solar)
new_solar_count = df_solar_new.count()
print(f"   → Watermark sonrası yeni kayıt: {new_solar_count:,} / {total_solar:,}")

df_solar = (
    df_solar_new
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

if solar_count > 0:
    new_wm_solar = compute_new_watermark(df_solar)
    update_watermark("bronze_raw_solar_generation", new_wm_solar, solar_count)

optimize_table(BRONZE_PATHS["solar_generation"], "bronze_raw_solar_generation")


# =============================================================================
# BÖLÜM 8 — BATTERY STATUS YÜKLEME (Incremental)
# =============================================================================

print("\n" + "="*60)
print("ADIM 3/5 — Battery Status (Batarya Durum Verisi)")
print("="*60)

wm_battery = get_watermark("bronze_raw_battery_status")

df_battery_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .schema(schema_battery)
    .load(f"{BASE_DATA_PATH}/raw_battery_status.csv")
)

total_battery = df_battery_raw.count()
df_battery_new = filter_new_records(df_battery_raw, wm_battery)
new_battery_count = df_battery_new.count()
print(f"   → Watermark sonrası yeni kayıt: {new_battery_count:,} / {total_battery:,}")

df_battery = (
    df_battery_new
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

if battery_count > 0:
    new_wm_battery = compute_new_watermark(df_battery)
    update_watermark("bronze_raw_battery_status", new_wm_battery, battery_count)

optimize_table(BRONZE_PATHS["battery_status"], "bronze_raw_battery_status")


# =============================================================================
# BÖLÜM 9 — WEATHER DATA YÜKLEME (Incremental)
# =============================================================================

print("\n" + "="*60)
print("ADIM 4/5 — Weather Data (Hava Durumu Verisi)")
print("="*60)

wm_weather = get_watermark("bronze_raw_weather_data")

df_weather_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("nullValue", "")
    .schema(schema_weather)
    .load(f"{BASE_DATA_PATH}/raw_weather_data.csv")
)

total_weather = df_weather_raw.count()
df_weather_new = filter_new_records(df_weather_raw, wm_weather)
new_weather_count = df_weather_new.count()
print(f"   → Watermark sonrası yeni kayıt: {new_weather_count:,} / {total_weather:,}")

df_weather = (
    df_weather_new
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

if weather_count > 0:
    new_wm_weather = compute_new_watermark(df_weather)
    update_watermark("bronze_raw_weather_data", new_wm_weather, weather_count)

optimize_table(BRONZE_PATHS["weather_data"], "bronze_raw_weather_data")


# =============================================================================
# BÖLÜM 10 — BUILDING MASTER YÜKLEME
# =============================================================================
# Building master farklı: zaman serisi değil, referans tablosu.
# Incremental load uygulanmaz — her çalışmada overwrite edilir.
# Değişiklikleri takip etmek için load_timestamp kullanılır.

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
(df_building.write
    .format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(BRONZE_PATHS["building_master"])
)

building_count = df_building.count()
log_step("✅ Building master yazıldı (overwrite)", building_count, "bronze_building_master")


# =============================================================================
# BÖLÜM 11 — WATERMARK DURUMU RAPORU
# =============================================================================

print("\n" + "="*60)
print("WATERMARK DURUMU")
print("="*60)

try:
    df_wm_report = spark.read.format("delta").load(WATERMARK_TABLE_PATH)
    df_wm_report.orderBy("table_name").show(truncate=False)
except Exception as e:
    print(f"⚠️  Watermark raporu okunamadı: {str(e)[:80]}")


# =============================================================================
# BÖLÜM 12 — DOĞRULAMA VE ÖZET RAPOR
# =============================================================================

print("\n" + "="*60)
print("DOĞRULAMA RAPORU")
print("="*60)

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

        building_dist = (df_check
            .groupBy("building_id")
            .count()
            .orderBy("building_id")
        )

        print(f"\n📊 {table_name}")
        print(f"   Toplam satır (kümülatif): {count:,}")
        building_dist.show(truncate=False)

    except Exception as e:
        print(f"❌ {table_name}: Okuma hatası — {str(e)}")

# Timestamp aralığı kontrolü
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
print("\n📁 Partition Yapısı (Energy Readings — ilk 5 partition):")
(df_ts_check
    .select("building_id", "year", "month")
    .distinct()
    .orderBy("building_id", "year", "month")
    .show(5)
)

print("\n" + "="*60)
print("BRONZE INGESTION TAMAMLANDI")
print("="*60)
print(f"✅ Toplam kümülatif kayıt: {total_records:,}")
print(f"✅ Bu çalışmada eklenen: energy={energy_count:,} | solar={solar_count:,} | battery={battery_count:,} | weather={weather_count:,}")
print(f"✅ Partition stratejisi: building_id / year / month")
print(f"✅ Format: Delta Lake")
print(f"✅ Mod: {MODE}")
print(f"✅ Watermark: Tables/bronze_watermarks")
print("\n➡️  Sonraki adım: 02_silver_transformation.py")
