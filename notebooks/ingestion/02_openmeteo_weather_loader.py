# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 02_openmeteo_weather_loader.py
# Layer: SILVER — Real Weather (Open-Meteo) → HOURLY silver_weather_clean (+ daily rollup)
# Created: 2026-05-30  (live-data initiative)
# Revised: 2026-05-30  (HOURLY + shortwave_radiation; 03 drop-in silver_weather_clean)
# =============================================================================
#
# GÖREV (Purpose):
#   GERÇEK havayı (Open-Meteo Archive) SAATLİK çek; sıcaklık + güneş radyasyonu
#   (shortwave_radiation, W/m²) → 03_gold_kpi_engine'in beklediği TAM şemada
#   `silver_weather_clean` yaz (drop-in; 03'e dokunmadan). Ayrıca günlük
#   `silver_weather_daily` rollup (doğrulama + günlük tüketiciler).
#   Sentetik bronze hava verisinin yerini alır:
#     - climate_adjusted_eui (B1) → gerçek HDD/CDD (10 bina)
#     - solar PR (Page 2)         → gerçek irradiance
#     - gold_kpi_hourly           → gerçek saatlik sıcaklık/irradiance
#
# ⚠️ ÇALIŞMA SIRASI:
#   02_silver_transformation `silver_weather_clean`'i sentetik yazar. Bu loader
#   onu GERÇEK veriyle OVERWRITE eder → 02_silver_transformation'dan SONRA,
#   03_gold_kpi_engine'den ÖNCE koş. (Kalıcı: 02_silver weather bloğunu kapat.)
#
# DEGREE-DAY (02_silver ile tutarlı integral yöntem):
#   heating_degree_day(saat) = max(0, 15 − T) × (1/24)   → 24h toplamı = günlük HDD
#   cooling_degree_day(saat) = max(0, T − 22) × (1/24)
#
# KAYNAK: Open-Meteo Archive — hourly=temperature_2m,shortwave_radiation; timezone=UTC
#   ⚠️ Free tier = NON-COMMERCIAL (satışta DWD/Open-Meteo commercial).
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from datetime import date
import requests
import time

spark = SparkSession.builder.getOrCreate()

# -----------------------------------------------------------------------------
# KONFİGÜRASYON
# -----------------------------------------------------------------------------
HDD_BASE_C = 15.0
CDD_BASE_C = 22.0
HOUR_FRACTION = 1.0 / 24.0          # saatlik degree-day fraction (02_silver 1/96 ile aynı mantık)
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

START_DATE = "2024-01-01"
END_DATE   = date.today().isoformat()

CITY_COORDS = {
    "B001": (50.1109,  8.6821, "Frankfurt"),   # DE
    "B002": (48.1351, 11.5820, "Munich"),      # DE
    "B003": (48.2082, 16.3738, "Vienna"),      # AT
    "B004": (52.3676,  4.9041, "Amsterdam"),   # NL
    "B005": (52.5200, 13.4050, "Berlin"),      # DE
    "B006": (52.3676,  4.9041, "Amsterdam"),   # NL
    "B007": (55.6761, 12.5683, "Copenhagen"),  # DK
    "B008": (51.3397, 12.3731, "Leipzig"),     # DE
    "B009": (50.1109,  8.6821, "Frankfurt"),   # DE
    "B010": (59.3293, 18.0686, "Stockholm"),   # SE
}

print(f"✅ Open-Meteo HOURLY weather loader — {START_DATE} → {END_DATE}, HDD{HDD_BASE_C}/CDD{CDD_BASE_C}")


# -----------------------------------------------------------------------------
# 1) BİNA KOORDİNATLARI (master öncelik, yoksa fallback)
# -----------------------------------------------------------------------------
try:
    _bm = spark.table("silver_building_master")
    if {"latitude", "longitude"}.issubset(set(_bm.columns)):
        coords = [
            (r["building_id"], float(r["latitude"]), float(r["longitude"]))
            for r in _bm.select("building_id", "latitude", "longitude")
                        .where(F.col("latitude").isNotNull()).collect()
        ]
        print(f"✅ Koordinat kaynağı: silver_building_master ({len(coords)} bina)")
    else:
        coords = [(b, lat, lon) for b, (lat, lon, _c) in CITY_COORDS.items()]
        print(f"⚠️  silver_building_master'da lat/lon yok → CITY_COORDS fallback ({len(coords)} bina)")
except Exception as _e:
    coords = [(b, lat, lon) for b, (lat, lon, _c) in CITY_COORDS.items()]
    print(f"⚠️  silver_building_master okunamadı ({str(_e)[:60]}) → CITY_COORDS fallback")


# -----------------------------------------------------------------------------
# 2) OPEN-METEO SAATLİK FETCH (retry + exponential backoff)
# -----------------------------------------------------------------------------
def fetch_hourly_weather(building_id: str, lat: float, lon: float, max_retries: int = 4) -> list:
    """Open-Meteo archive HOURLY → [building_id, ts, temp, irradiance, hdd_h, cdd_h, flag].
    Geçici timeout / free-tier rate-limit için retry + backoff."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "temperature_2m,shortwave_radiation",
        "timezone": "UTC",
    }
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(ARCHIVE_URL, params=params, timeout=120)
            r.raise_for_status()
            h = r.json()["hourly"]
            times = h["time"]
            temps = h["temperature_2m"]
            rads  = h.get("shortwave_radiation", [None] * len(times))
            rows = []
            for i, ts in enumerate(times):
                t = temps[i]
                if t is None:
                    continue
                irr = rads[i] if rads[i] is not None else 0.0
                hdd = max(0.0, HDD_BASE_C - t) * HOUR_FRACTION
                cdd = max(0.0, t - CDD_BASE_C) * HOUR_FRACTION
                rows.append((building_id, ts, float(t), float(irr),
                             round(hdd, 5), round(cdd, 5), "OK"))
            return rows
        except Exception as _e:
            last_err = _e
            if attempt < max_retries:
                backoff = 8 * attempt   # 8s → 16s → 24s
                print(f"   … {building_id} deneme {attempt}/{max_retries} başarısız "
                      f"({str(_e)[:50]}) → {backoff}s bekleyip yeniden")
                time.sleep(backoff)
    raise last_err


all_rows = []
for (bid, lat, lon) in coords:
    try:
        rows = fetch_hourly_weather(bid, lat, lon)
        all_rows.extend(rows)
        print(f"   {bid}: {len(rows)} saat ({lat:.2f},{lon:.2f})")
        time.sleep(2.0)   # free-tier throttle için geniş aralık
    except Exception as _e:
        print(f"   ⚠️  {bid} hava çekilemedi: {str(_e)[:80]}")

print(f"✅ Toplam {len(all_rows)} saatlik hava satırı çekildi")

if not all_rows:
    raise Exception("Hiç hava verisi çekilemedi — network / Open-Meteo erişimini kontrol et.")


# -----------------------------------------------------------------------------
# 3) silver_weather_clean (HOURLY — 03 drop-in şema)
# -----------------------------------------------------------------------------
SCHEMA = StructType([
    StructField("building_id",        StringType(), False),
    StructField("ts_str",             StringType(), False),
    StructField("temperature_c",      DoubleType(), True),
    StructField("solar_irradiance",   DoubleType(), True),
    StructField("heating_degree_day", DoubleType(), True),
    StructField("cooling_degree_day", DoubleType(), True),
    StructField("data_quality_flag",  StringType(), True),
])

df_h = (
    spark.createDataFrame(all_rows, schema=SCHEMA)
    .withColumn("timestamp_utc", F.to_timestamp("ts_str", "yyyy-MM-dd'T'HH:mm"))
    .drop("ts_str")
    .withColumn("irradiance_quality",
                F.when(F.col("solar_irradiance") < 0, F.lit("ANOMALY"))
                 .when(F.col("solar_irradiance") > 1500, F.lit("ANOMALY"))
                 .otherwise(F.lit("OK")))
    .withColumn("source", F.lit("open-meteo"))
    .withColumn("fetched_at", F.current_timestamp())
)

(df_h.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
   .partitionBy("building_id").saveAsTable("silver_weather_clean"))
print(f"✅ silver_weather_clean (saatlik) yazıldı: {df_h.count()} satır")


# -----------------------------------------------------------------------------
# 4) silver_weather_daily (günlük rollup — doğrulama + günlük tüketiciler)
# -----------------------------------------------------------------------------
df_d = (
    df_h.withColumn("date", F.to_date("timestamp_utc"))
    .groupBy("building_id", "date")
    .agg(
        F.round(F.avg("temperature_c"), 2).alias("t_mean_c"),
        F.round(F.min("temperature_c"), 2).alias("t_min_c"),
        F.round(F.max("temperature_c"), 2).alias("t_max_c"),
        F.round(F.sum("heating_degree_day"), 3).alias("hdd_day"),
        F.round(F.sum("cooling_degree_day"), 3).alias("cdd_day"),
        F.round(F.avg("solar_irradiance"), 1).alias("avg_irradiance_wm2"),
    )
    .withColumn("source", F.lit("open-meteo"))
    .withColumn("fetched_at", F.current_timestamp())
)

(df_d.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
   .partitionBy("building_id").saveAsTable("silver_weather_daily"))
print(f"✅ silver_weather_daily (günlük rollup) yazıldı: {df_d.count()} satır")


# -----------------------------------------------------------------------------
# 5) DOĞRULAMA
# -----------------------------------------------------------------------------
print("\n📊 Bina bazında (gerçek hava, saatlikten türetildi):")
(df_d.groupBy("building_id")
   .agg(F.round(F.sum("hdd_day"), 0).alias("toplam_HDD"),
        F.round(F.sum("cdd_day"), 0).alias("toplam_CDD"),
        F.round(F.avg("t_mean_c"), 1).alias("ort_C"),
        F.round(F.avg("avg_irradiance_wm2"), 0).alias("ort_irr_wm2"))
   .orderBy("building_id").show(truncate=False))

print("""
📋 SONRAKI ADIM:
   silver_weather_clean artık GERÇEK saatlik veri (10 bina, temp + irradiance).
   Sıra: bu loader → 03_gold_kpi_engine (climate_adjusted_eui gerçek iklimle).
   ⚠️ 02_silver_transformation tekrar koşulursa weather'ı sentetiğe döndürür —
      bu loader'ı ondan SONRA çalıştır (ya da 02_silver weather bloğunu kapat).
""")
print("✅ 02_openmeteo_weather_loader (HOURLY) tamamlandı.")
