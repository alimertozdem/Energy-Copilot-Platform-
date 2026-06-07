# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 05_electricitymaps_co2_loader.py
# Layer: SILVER — Live Grid Carbon Intensity (ElectricityMaps)
# Created: 2026-05-30  (live-data initiative: live grid CO2)
# =============================================================================
#
# GÖREV: Canlı/saatlik şebeke karbon yoğunluğunu (gCO2eq/kWh) ElectricityMaps'ten
#   çek. SADECE OPERASYONEL sayfalar için (Page 2 real-time CO₂, Page 8 IoT, batarya
#   dispatch CO₂ tasarrufu). Karbon-bilinçli yük kaydırma (cheap+temiz saatler) anlatısı.
#
# ⚠️ KRİTİK MİMARİ KURAL (auditable Scope 2):
#   Bu CANLI değer DISCLOSURE/raporlama faktörü DEĞİLDİR. CSRD/CRREM Scope-2
#   hesabı ref_grid_emission_factors'taki YILLIK-RESMİ (UBA/TEİAŞ) değerden gelir.
#   Canlı veri dalgalanır → denetçi tekrar-üretilemez sayı istemez. İki katman ayrı.
#
# KAYNAK & TOKEN:
#   https://api.electricitymap.org/v3/carbon-intensity/{latest|history}?zone=DE
#   ÜCRETSİZ token: electricitymaps.com → kayıt (personal/eval). Header: auth-token.
#     Fabric: spark.conf.set("emaps.token", "<TOKEN>")  ya da bu hücrede ELE.
#
# NOT: Fabric'te çalışır. Sandbox web-fetch kısıtlı → burada test edilmedi.
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType
)
from pyspark.sql.window import Window
from datetime import datetime, timezone
import requests

spark = SparkSession.builder.getOrCreate()

try:
    EMAPS_TOKEN = spark.conf.get("emaps.token")
except Exception:
    EMAPS_TOKEN = ""   # ← Fabric'te kendi token'ını gir

if not EMAPS_TOKEN:
    raise Exception(
        "ElectricityMaps token yok. electricitymaps.com'dan ücretsiz al, sonra:\n"
        "  spark.conf.set('emaps.token', '<TOKEN>')  ya da EMAPS_TOKEN'ı doldur."
    )

BASE = "https://api.electricitymap.org/v3"
HEADERS = {"auth-token": EMAPS_TOKEN}

# ElectricityMaps zone kodları (TR DESTEKLENİR — ENTSO-E'nin aksine)
ZONES = {"DE": "DE", "AT": "AT", "NL": "NL", "FR": "FR", "TR": "TR"}

print(f"✅ ElectricityMaps CO₂ loader — {len(ZONES)} bölge (canlı/son 24h)")


def fetch_history(country: str, zone: str) -> list:
    """Son 24 saatlik karbon yoğunluğu → [(country, ts_utc, gco2_kwh)]."""
    r = requests.get(f"{BASE}/carbon-intensity/history",
                     params={"zone": zone}, headers=HEADERS, timeout=45)
    r.raise_for_status()
    data = r.json().get("history", [])
    rows = []
    for h in data:
        ci = h.get("carbonIntensity")
        dt = h.get("datetime")
        if ci is None or dt is None:
            continue
        ts = datetime.fromisoformat(dt.replace("Z", "+00:00")).astimezone(timezone.utc)
        rows.append((country, ts.replace(tzinfo=None), float(ci)))
    return rows


all_rows = []
for country, zone in ZONES.items():
    try:
        rows = fetch_history(country, zone)
        all_rows.extend(rows)
        print(f"   {country}: {len(rows)} saatlik CO₂ noktası")
    except Exception as _e:
        print(f"   ⚠️  {country} CO₂ çekilemedi: {str(_e)[:90]}")

if not all_rows:
    raise Exception("Hiç canlı CO₂ çekilemedi — token / network / zone kodlarını kontrol et.")

SCHEMA = StructType([
    StructField("country_code", StringType(), False),
    StructField("timestamp_utc", TimestampType(), False),
    StructField("grid_co2_g_per_kwh", DoubleType(), True),
])
df = (spark.createDataFrame(all_rows, schema=SCHEMA)
      .withColumn("date", F.to_date("timestamp_utc"))
      .withColumn("source", F.lit("electricitymaps_live"))
      .withColumn("fetched_at", F.current_timestamp()))

# OPERASYONEL canlı tablo — disclosure DEĞİL
(df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .partitionBy("country_code").saveAsTable("silver_grid_co2_live"))
print(f"✅ silver_grid_co2_live: {df.count()} satır (OPERASYONEL — disclosure değil)")

print("\n📊 Ülke × son değer (canlı grid CO₂ gCO2/kWh):")
(df.withColumn("_rk", F.row_number().over(
        Window.partitionBy("country_code").orderBy(F.col("timestamp_utc").desc())))
   .filter(F.col("_rk") == 1)
   .select("country_code", "timestamp_utc", "grid_co2_g_per_kwh").show(truncate=False))

print("""
📋 ENTEGRASYON (sadece operasyonel):
   - Page 2/8: real-time CO₂ kartı → silver_grid_co2_live son değer.
   - Batarya dispatch: "temiz saatte şarj" anlatısı için canlı eğri.
   - ⚠️ CSRD/CRREM Scope-2 = ref_grid_emission_factors (YILLIK-resmi) — CANLI DEĞİL.
""")
print("✅ 05_electricitymaps_co2_loader tamamlandı.")
