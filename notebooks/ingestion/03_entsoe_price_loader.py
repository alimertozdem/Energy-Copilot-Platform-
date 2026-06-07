# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 03_entsoe_price_loader.py
# Layer: SILVER/REF — Real Day-Ahead Electricity Prices (ENTSO-E)
# Created: 2026-05-30  (live-data initiative: official EU prices)
# =============================================================================
#
# GÖREV: Resmi AB gün-öncesi (day-ahead) elektrik fiyatlarını ENTSO-E
#   Transparency Platform'dan çek. Operasyonel sayfalar (maliyet, batarya
#   dispatch ROI, forecast) GERÇEK saatlik fiyatla çalışsın.
#
# MİMARİ: API loader → tablo → motorlar (değişmez). Loader saatlik spot fiyatı
#   günlük peak/midpeak/offpeak/avg'e indirip ref_electricity_prices_daily'e yazar.
#   ⚠️ DEMAND-charge ve FEED-IN (regüle, spot değil) ref_electricity_tariffs'te
#      KALIR; bu loader sadece ENERJİ (spot) fiyatını besler.
#   ⚠️ Disclosure Scope-2 faktörü canlı YAPILMAZ — o yıllık-resmi kalır (auditable).
#
# KAYNAK & TOKEN:
#   https://web-api.tp.entsoe.eu/api  (documentType=A44 = day-ahead prices)
#   ÜCRETSİZ token: transparency.entsoe.eu → kayıt ol → "Restful API" iste
#   (e-posta ile gelir). Sonra:
#     Fabric notebook → spark.conf.set("entsoe.token", "<TOKEN>")  VEYA
#     bu hücrede ENTSOE_TOKEN = "<TOKEN>" elle (repo'ya commit etme!).
#
# NOT: Fabric'te çalışır (requests + network). Sandbox web-fetch kısıtlı → burada test edilmedi.
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, DateType, TimestampType
)
from datetime import datetime, timedelta, timezone
import requests
import xml.etree.ElementTree as ET

spark = SparkSession.builder.getOrCreate()

# -----------------------------------------------------------------------------
# TOKEN — spark.conf'tan oku; yoksa buraya elle (commit etme).
# -----------------------------------------------------------------------------
try:
    ENTSOE_TOKEN = spark.conf.get("entsoe.token")
except Exception:
    ENTSOE_TOKEN = ""   # ← Fabric'te kendi token'ını gir, ya da spark.conf.set kullan

if not ENTSOE_TOKEN:
    raise Exception(
        "ENTSO-E token yok. transparency.entsoe.eu'dan ücretsiz al, sonra:\n"
        "  spark.conf.set('entsoe.token', '<TOKEN>')  ya da bu hücrede ENTSOE_TOKEN'ı doldur."
    )

API_URL = "https://web-api.tp.entsoe.eu/api"

# Teklif bölgesi EIC kodları (gün-öncesi fiyat domain'i)
BIDDING_ZONES = {
    "DE": "10Y1001A1001A82H",   # DE-LU
    "AT": "10YAT-APG------L",
    "NL": "10YNL----------L",
    "FR": "10YFR-RTE------C",
    # TR ENTSO-E gözlemci → gün-öncesi genelde yok; EPİAŞ/EXIST kullan (ayrı loader).
}

LOOKBACK_DAYS = 7   # son N gün (production'da günlük cron ile artımlı)
_now = datetime.now(timezone.utc)
PERIOD_START = (_now - timedelta(days=LOOKBACK_DAYS)).strftime("%Y%m%d0000")
PERIOD_END   = _now.strftime("%Y%m%d0000")

print(f"✅ ENTSO-E loader — {PERIOD_START} → {PERIOD_END}, {len(BIDDING_ZONES)} bölge")


# -----------------------------------------------------------------------------
# XML parse — namespace-agnostik (local tag adıyla eşleştir)
# -----------------------------------------------------------------------------
def _local(tag: str) -> str:
    return tag.split("}")[-1]

def fetch_prices(country: str, eic: str) -> list:
    """ENTSO-E day-ahead → [(country, timestamp_utc, price_eur_kwh)] saatlik."""
    params = {
        "securityToken": ENTSOE_TOKEN,
        "documentType": "A44",          # day-ahead prices
        "in_Domain": eic,
        "out_Domain": eic,
        "periodStart": PERIOD_START,
        "periodEnd": PERIOD_END,
    }
    r = requests.get(API_URL, params=params, timeout=60)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    rows = []
    for ts in root.iter():
        if _local(ts.tag) != "TimeSeries":
            continue
        for period in ts:
            if _local(period.tag) != "Period":
                continue
            start_str, resolution = None, "PT60M"
            for child in period:
                lt = _local(child.tag)
                if lt == "timeInterval":
                    for ti in child:
                        if _local(ti.tag) == "start":
                            start_str = ti.text
                elif lt == "resolution":
                    resolution = child.text
            if not start_str:
                continue
            start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
            step_min = 60 if resolution == "PT60M" else (15 if resolution == "PT15M" else 60)
            for pt in period:
                if _local(pt.tag) != "Point":
                    continue
                pos, amount = None, None
                for p in pt:
                    if _local(p.tag) == "position":
                        pos = int(p.text)
                    elif _local(p.tag) == "price.amount":
                        amount = float(p.text)
                if pos is None or amount is None:
                    continue
                ts_utc = start_dt + timedelta(minutes=step_min * (pos - 1))
                rows.append((country, ts_utc.replace(tzinfo=None), round(amount / 1000.0, 6)))  # €/MWh → €/kWh
    return rows


all_rows = []
for country, eic in BIDDING_ZONES.items():
    try:
        rows = fetch_prices(country, eic)
        all_rows.extend(rows)
        print(f"   {country}: {len(rows)} saatlik fiyat")
    except Exception as _e:
        print(f"   ⚠️  {country} fiyat çekilemedi: {str(_e)[:90]}")

if not all_rows:
    raise Exception("Hiç fiyat çekilemedi — token / network / EIC kodlarını kontrol et.")


# -----------------------------------------------------------------------------
# SILVER: saatlik spot fiyat + REF: günlük peak/midpeak/offpeak/avg
# -----------------------------------------------------------------------------
HSCHEMA = StructType([
    StructField("country_code", StringType(), False),
    StructField("timestamp_utc", TimestampType(), False),
    StructField("price_eur_kwh", DoubleType(), True),
])
df_h = (spark.createDataFrame(all_rows, schema=HSCHEMA)
        .withColumn("date", F.to_date("timestamp_utc"))
        .withColumn("source", F.lit("entsoe_day_ahead")))

(df_h.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .partitionBy("country_code").saveAsTable("silver_electricity_prices_hourly"))
print(f"✅ silver_electricity_prices_hourly: {df_h.count()} satır")

# Günlük peak (en pahalı 8 saat ort.), offpeak (en ucuz 8 saat ort.), avg
from pyspark.sql.window import Window
_w = Window.partitionBy("country_code", "date").orderBy(F.col("price_eur_kwh").desc())
_wa = Window.partitionBy("country_code", "date").orderBy(F.col("price_eur_kwh").asc())
df_ranked = (df_h
    .withColumn("_rk_desc", F.row_number().over(_w))
    .withColumn("_rk_asc", F.row_number().over(_wa)))

df_daily = (df_ranked.groupBy("country_code", "date").agg(
        F.round(F.avg("price_eur_kwh"), 5).alias("avg_eur_kwh"),
        F.round(F.avg(F.when(F.col("_rk_desc") <= 8, F.col("price_eur_kwh"))), 5).alias("peak_eur_kwh"),
        F.round(F.avg(F.when(F.col("_rk_asc")  <= 8, F.col("price_eur_kwh"))), 5).alias("offpeak_eur_kwh"),
    )
    .withColumn("source", F.lit("entsoe_day_ahead"))
    .withColumn("fetched_at", F.current_timestamp()))

(df_daily.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .partitionBy("country_code").saveAsTable("ref_electricity_prices_daily"))
print(f"✅ ref_electricity_prices_daily: {df_daily.count()} satır")

print("\n📊 Bina yok — ülke × gün gerçek fiyat (örnek):")
df_daily.orderBy(F.col("date").desc()).show(8, truncate=False)

print("""
📋 ENTEGRASYON:
   - 12_battery / 06_recommendation: ülke-gün fiyatı ref_electricity_prices_daily'den
     al (spot enerji). demand_charge/feed_in ref_electricity_tariffs'te kalır.
   - TR: ENTSO-E'de gün-öncesi yok → EPİAŞ/EXIST için ayrı loader (04_exist_price_loader).
   - Disclosure Scope-2 faktörü CANLI DEĞİL — ref_grid_emission_factors yıllık-resmi.
""")
print("✅ 03_entsoe_price_loader tamamlandı.")
