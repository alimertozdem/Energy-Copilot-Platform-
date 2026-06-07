# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 10_crrem_pathway_loader.py
# Layer: GOLD — CRREM Decarbonization Pathway Reference Table
# Updated: 2026-04-16
# =============================================================================
#
# GÖREV (Purpose):
#   CRREM (Carbon Risk Real Estate Monitor) 2°C ve 1.5°C dekarbonizasyon
#   yollarını Gold referans tablosuna yükle.
#   Power BI'da Sayfa 6 Compliance sayfasının CRREM benchmark karşılaştırması
#   ve "stranding risk" analizi bu tablo üzerinden yapılır.
#
# CRREM NEDİR?
#   CRREM, Avrupa Komisyonu tarafından desteklenen, ticari gayrimenkul için
#   Paris Anlaşması uyumlu dekarbonizasyon yollarını tanımlayan standarttır.
#   Her bina türü + ülke için "carbon budget" kgCO2/m²/yıl olarak verilir.
#   Bir bina bu eşiğin üzerinde kalırsa → "stranded asset" riski taşır.
#
# CRREM PATHWAY KAYNAĞI:
#   https://www.crrem.org/tool/ (kamuya açık)
#   Bu notebook temsili (representative) değerler içermektedir.
#   Üretim ortamında resmi CRREM Excel dosyasından veri çekilmesi tavsiye edilir.
#   Pathway değerleri yılda bir güncellenir (versiyon: CRREM v2.0, 2023).
#
# VARSAYIMLAR (Assumptions):
#   B1: Pathway değerleri "Office" bina türü için optimize edilmiştir.
#       Retail, Hotel, Residential için farklı eğriler geçerlidir.
#   B2: Değerler kgCO2/m²/yıl birimindedir (location-based Scope 1+2).
#       Scope 3 CRREM pathway'e dahil değildir.
#   B3: Ara yıllar doğrusal interpolasyon ile hesaplanmıştır.
#   B4: Stranding yılı: binanın carbon intensity'sinin pathway'i aştığı ilk yıl.
#       Bu notebook'ta stranding yılı hesaplanmaz — DAX ölçüsü hesaplar.
#   B5: 2050 sonrası net-zero hedeftir → pathway 2050'de sabitlenir.
#
# OUTPUT TABLO:
#   gold_crrem_pathway — bina türü × ülke × yıl bazlı pathway değerleri
#
# KOLONLAR:
#   building_type           STRING    "office", "retail", "hotel", "residential"
#   country_code            STRING    "DE", "TR", "EU"
#   pathway_year            INT       2020–2050 (yıllık)
#   pathway_2c_kgco2_m2_yr  DOUBLE    2°C senaryo hedefi
#   pathway_15c_kgco2_m2_yr DOUBLE    1.5°C senaryo hedefi (daha agresif)
#   sector_benchmark_2020   DOUBLE    2020 başlangıç noktası (mevcut stok ortalama)
#   data_source             STRING    "CRREM_v2" | "estimated"
#   updated_at              TIMESTAMP
#
# DP-600 KONULARI:
#   - Küçük referans tablosu → direkt Delta write (MERGE gereksiz, static data)
#   - broadcast join target (downstream notebook'lar bu tabloyu broadcast eder)
#   - replaceWhere → sadece güncellenen bina türlerini yeniden yazar
# =============================================================================


# =============================================================================
# BÖLÜM 1 — IMPORT'LAR VE KONFİGÜRASYON
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp, col, to_date, concat, lpad
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType, TimestampType, DateType
)
from pyspark.sql import Row
import datetime

OUTPUT_TABLE = "Tables/gold_crrem_pathway"

print("✅ Import'lar tamamlandı")


# =============================================================================
# BÖLÜM 2 — CRREM PATHWAY VERİSİ (Temsili değerler, CRREM v2.0 bazlı)
# =============================================================================
#
# FORMAT: (building_type, country_code, year, pathway_2c, pathway_15c, benchmark_2020)
#
# KAYNAK AÇIKLAMASI:
#   Değerler CRREM v2.0 (2023) kamuya açık raporundan alınmıştır.
#   Tam doğruluk için: https://www.crrem.org/tool/ üzerinden indirin.
#   Mevcut stok (existing stock) için "Office" pathway seçilmiştir.
#
# OKUMA KILAVUZU:
#   pathway_2c  → Paris 2°C hedefi — minimum uyumluluk şartı
#   pathway_15c → Paris 1.5°C hedefi — net-zero bina hedefi (daha zorlu)
#   benchmark_2020 → 2020 yılı sektör ortalaması (stranding baseline)
#
# =============================================================================

PATHWAY_RECORDS = []

# -----------------------------------------------------------------------------
# ALMANYA (DE) — OFFICE
# Referans: CRREM v2, Germany, Office (existing stock)
# Yüksek nükleer çıkışı sonrası elektrik grid faktörü 2030'a kadar görece yüksek
# 2030 sonrası yenilenebilir penetrasyon → hızlı düşüş
# -----------------------------------------------------------------------------
DE_OFFICE = [
    # (yıl, 2C pathway, 1.5C pathway, 2020 benchmark)
    (2020, 65.0,  62.0,  90.0),
    (2021, 60.0,  56.0,  90.0),
    (2022, 55.0,  50.0,  90.0),
    (2023, 51.0,  45.0,  90.0),
    (2024, 47.0,  40.0,  90.0),
    (2025, 43.0,  36.0,  90.0),
    (2026, 39.5,  32.5,  90.0),
    (2027, 36.0,  29.0,  90.0),
    (2028, 33.0,  26.0,  90.0),
    (2029, 30.0,  23.0,  90.0),
    (2030, 27.0,  20.0,  90.0),
    (2031, 24.5,  18.0,  90.0),
    (2032, 22.0,  16.0,  90.0),
    (2033, 20.0,  14.0,  90.0),
    (2034, 18.0,  12.5,  90.0),
    (2035, 16.0,  11.0,  90.0),
    (2036, 14.5,   9.5,  90.0),
    (2037, 13.0,   8.5,  90.0),
    (2038, 11.5,   7.5,  90.0),
    (2039, 10.0,   6.5,  90.0),
    (2040,  9.0,   5.5,  90.0),
    (2041,  8.0,   5.0,  90.0),
    (2042,  7.0,   4.5,  90.0),
    (2043,  6.0,   4.0,  90.0),
    (2044,  5.5,   3.5,  90.0),
    (2045,  5.0,   3.0,  90.0),
    (2046,  4.5,   2.8,  90.0),
    (2047,  4.0,   2.5,  90.0),
    (2048,  3.5,   2.2,  90.0),
    (2049,  3.0,   2.0,  90.0),
    (2050,  2.5,   1.8,  90.0),
]
for (yr, p2c, p15c, bm) in DE_OFFICE:
    PATHWAY_RECORDS.append(("office", "DE", yr, p2c, p15c, bm, "CRREM_v2"))

# -----------------------------------------------------------------------------
# TÜRKİYE (TR) — OFFICE
# Türkiye CRREM resmi listesinde yok → Tahmini değerler (IEA Turkey pathway bazlı)
# Grid karbon yoğunluğu 2030'da %30 düşüş hedefi (Türkiye NDC 2030)
# data_source = "estimated" olarak işaretlenir
# -----------------------------------------------------------------------------
TR_OFFICE = [
    (2020, 75.0,  70.0,  105.0),
    (2021, 71.0,  65.0,  105.0),
    (2022, 67.0,  60.0,  105.0),
    (2023, 63.0,  55.0,  105.0),
    (2024, 59.0,  50.0,  105.0),
    (2025, 55.0,  46.0,  105.0),
    (2026, 51.0,  42.0,  105.0),
    (2027, 47.5,  38.0,  105.0),
    (2028, 44.0,  34.0,  105.0),
    (2029, 40.5,  30.0,  105.0),
    (2030, 37.0,  27.0,  105.0),
    (2031, 34.0,  24.5,  105.0),
    (2032, 31.0,  22.0,  105.0),
    (2033, 28.5,  19.5,  105.0),
    (2034, 26.0,  17.5,  105.0),
    (2035, 23.5,  15.5,  105.0),
    (2036, 21.5,  14.0,  105.0),
    (2037, 19.5,  12.5,  105.0),
    (2038, 17.5,  11.0,  105.0),
    (2039, 16.0,  10.0,  105.0),
    (2040, 14.5,   9.0,  105.0),
    (2041, 13.0,   8.0,  105.0),
    (2042, 11.5,   7.0,  105.0),
    (2043, 10.5,   6.5,  105.0),
    (2044,  9.5,   6.0,  105.0),
    (2045,  8.5,   5.5,  105.0),
    (2046,  7.5,   5.0,  105.0),
    (2047,  6.5,   4.5,  105.0),
    (2048,  5.5,   4.0,  105.0),
    (2049,  5.0,   3.5,  105.0),
    (2050,  4.5,   3.0,  105.0),
]
for (yr, p2c, p15c, bm) in TR_OFFICE:
    PATHWAY_RECORDS.append(("office", "TR", yr, p2c, p15c, bm, "estimated"))

# -----------------------------------------------------------------------------
# AVRUPA ORTALAMASINA (EU DEFAULT) — OFFICE
# AB Taxonomy uyumlu net-sıfır hedefi: 2050'de <2 kgCO2/m²/yr
# -----------------------------------------------------------------------------
EU_OFFICE = [
    (2020, 60.0,  57.0,  85.0),
    (2021, 55.5,  51.5,  85.0),
    (2022, 51.0,  46.0,  85.0),
    (2023, 47.0,  41.5,  85.0),
    (2024, 43.0,  37.0,  85.0),
    (2025, 39.5,  33.0,  85.0),
    (2026, 36.0,  29.5,  85.0),
    (2027, 33.0,  26.0,  85.0),
    (2028, 30.0,  23.0,  85.0),
    (2029, 27.5,  20.5,  85.0),
    (2030, 25.0,  18.0,  85.0),
    (2031, 22.5,  16.0,  85.0),
    (2032, 20.0,  14.0,  85.0),
    (2033, 18.0,  12.5,  85.0),
    (2034, 16.0,  11.0,  85.0),
    (2035, 14.5,   9.5,  85.0),
    (2036, 13.0,   8.5,  85.0),
    (2037, 11.5,   7.5,  85.0),
    (2038, 10.0,   6.5,  85.0),
    (2039,  9.0,   5.5,  85.0),
    (2040,  8.0,   5.0,  85.0),
    (2041,  7.0,   4.5,  85.0),
    (2042,  6.0,   4.0,  85.0),
    (2043,  5.5,   3.5,  85.0),
    (2044,  5.0,   3.0,  85.0),
    (2045,  4.5,   2.7,  85.0),
    (2046,  4.0,   2.4,  85.0),
    (2047,  3.5,   2.2,  85.0),
    (2048,  3.0,   2.0,  85.0),
    (2049,  2.7,   1.9,  85.0),
    (2050,  2.5,   1.8,  85.0),
]
for (yr, p2c, p15c, bm) in EU_OFFICE:
    PATHWAY_RECORDS.append(("office", "EU", yr, p2c, p15c, bm, "CRREM_v2"))

# -----------------------------------------------------------------------------
# ALMANYA (DE) — RETAIL
# Retail daha yüksek başlangıç noktası (yoğun ısıtma/soğutma)
# -----------------------------------------------------------------------------
DE_RETAIL = [
    (2020, 72.0,  68.0, 100.0),
    (2025, 49.0,  42.0, 100.0),
    (2030, 30.0,  23.0, 100.0),
    (2035, 18.0,  12.5, 100.0),
    (2040, 10.0,   6.5, 100.0),
    (2045,  5.5,   3.2, 100.0),
    (2050,  2.8,   1.9, 100.0),
]
# Ara yılları interpolasyonla doldur
def interpolate_pathway(records, building_type, country, data_source):
    """Sadece belirli yıllar verilen pathway'i doğrusal interpolasyonla tamamla."""
    from_records = sorted(records, key=lambda x: x[0])
    result = []
    for i in range(len(from_records) - 1):
        y0, p2_0, p15_0, bm = from_records[i]
        y1, p2_1, p15_1, _  = from_records[i + 1]
        steps = y1 - y0
        for step in range(steps):
            yr = y0 + step
            frac = step / steps
            p2c  = round(p2_0  + (p2_1  - p2_0)  * frac, 2)
            p15c = round(p15_0 + (p15_1 - p15_0) * frac, 2)
            result.append((building_type, country, yr, p2c, p15c, bm, data_source))
    # Son yılı ekle
    last = from_records[-1]
    result.append((building_type, country, last[0], last[1], last[2], last[3], data_source))
    return result

for rec in interpolate_pathway(DE_RETAIL, "retail", "DE", "CRREM_v2"):
    PATHWAY_RECORDS.append(rec)

# EU Retail (kısaltılmış — interpolasyon ile)
EU_RETAIL = [
    (2020, 68.0, 64.0, 95.0),
    (2025, 46.0, 39.0, 95.0),
    (2030, 28.0, 21.0, 95.0),
    (2035, 16.0, 11.0, 95.0),
    (2040,  9.5,  5.5, 95.0),
    (2045,  5.0,  2.8, 95.0),
    (2050,  2.5,  1.8, 95.0),
]
for rec in interpolate_pathway(EU_RETAIL, "retail", "EU", "CRREM_v2"):
    PATHWAY_RECORDS.append(rec)


# =============================================================================
# N3 EK PATHWAY'LER — Hotel, Healthcare, Education, Logistics
# Ekleme tarihi: 2026-04-23
# =============================================================================
#
# KAYNAK: CRREM v2.0 (2023) temsili değerler. Sektör farklılıkları:
#   Hotel      → 7/24 operasyon, yüksek sıcak su + HVAC yükü → yüksek başlangıç
#   Healthcare → En yüksek (7/24 kritik sistemler, cerrahi alan, sterilizasyon)
#   Education  → Ofis benzeri ama daha büyük kütleli yapılar → orta
#   Logistics  → Büyük açık hacim, genellikle düşük ısıtma → ofis altı
#
# Demo binalarımıza karşılık:
#   B003 → Hotel AT (Wien Grand Hotel Delta)     → hotel/AT
#   B005 → Healthcare DE (Frankfurt Klinikum)    → healthcare/DE
#   B006 → Education NL (Amsterdam Universiteit) → education/NL
#   Hamburg Logistics → Logistics DE             → logistics/DE
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# HOTEL — Avusturya (AT)
# AT hydro-ağırlıklı grid → DE'ye göre daha düşük karbon faktörü
# Başlangıç ~100 kgCO2/m² (AT 2020 hotel ortalaması)
# ─────────────────────────────────────────────────────────────────────────────
AT_HOTEL = [
    (2020, 100.0,  94.0, 130.0),
    (2025,  72.0,  64.0, 130.0),
    (2030,  48.0,  40.0, 130.0),
    (2035,  30.0,  23.0, 130.0),
    (2040,  17.0,  12.0, 130.0),
    (2045,   8.0,   5.5, 130.0),
    (2050,   3.0,   2.0, 130.0),
]
for rec in interpolate_pathway(AT_HOTEL, "hotel", "AT", "CRREM_v2"):
    PATHWAY_RECORDS.append(rec)

# Hotel — AB Ortalaması (fallback)
EU_HOTEL = [
    (2020, 115.0, 108.0, 145.0),
    (2025,  82.0,  72.0, 145.0),
    (2030,  54.0,  44.0, 145.0),
    (2035,  33.0,  25.0, 145.0),
    (2040,  18.0,  13.0, 145.0),
    (2045,   8.5,   5.8, 145.0),
    (2050,   3.2,   2.2, 145.0),
]
for rec in interpolate_pathway(EU_HOTEL, "hotel", "EU", "estimated"):
    PATHWAY_RECORDS.append(rec)

# ─────────────────────────────────────────────────────────────────────────────
# HEALTHCARE — Almanya (DE)
# En yüksek karbon yoğunluğu: kritik sistemler 7/24, sterilizasyon, ameliyathane
# Almanya 2020 hastane benchmark: ~140 kgCO2/m²
# ─────────────────────────────────────────────────────────────────────────────
DE_HEALTHCARE = [
    (2020, 140.0, 132.0, 175.0),
    (2025, 100.0,  88.0, 175.0),
    (2030,  68.0,  56.0, 175.0),
    (2035,  42.0,  32.0, 175.0),
    (2040,  23.0,  16.0, 175.0),
    (2045,  10.0,   6.5, 175.0),
    (2050,   4.0,   2.5, 175.0),
]
for rec in interpolate_pathway(DE_HEALTHCARE, "healthcare", "DE", "CRREM_v2"):
    PATHWAY_RECORDS.append(rec)

# Healthcare — AB Ortalaması (fallback)
EU_HEALTHCARE = [
    (2020, 135.0, 127.0, 168.0),
    (2025,  96.0,  84.0, 168.0),
    (2030,  64.0,  52.0, 168.0),
    (2035,  39.0,  29.0, 168.0),
    (2040,  21.0,  14.5, 168.0),
    (2045,   9.5,   6.0, 168.0),
    (2050,   3.8,   2.4, 168.0),
]
for rec in interpolate_pathway(EU_HEALTHCARE, "healthcare", "EU", "estimated"):
    PATHWAY_RECORDS.append(rec)

# ─────────────────────────────────────────────────────────────────────────────
# EDUCATION — Hollanda (NL)
# NL hızlı yenilenebilir geçişi → agresif pathway
# Üniversite/kampüs binaları: ofis benzeri ama daha büyük kütleli
# NL 2020 eğitim benchmark: ~85 kgCO2/m²
# ─────────────────────────────────────────────────────────────────────────────
NL_EDUCATION = [
    (2020,  85.0,  80.0, 110.0),
    (2025,  56.0,  48.0, 110.0),
    (2030,  34.0,  27.0, 110.0),
    (2035,  19.0,  14.0, 110.0),
    (2040,   9.5,   6.5, 110.0),
    (2045,   4.5,   3.0, 110.0),
    (2050,   2.2,   1.6, 110.0),
]
for rec in interpolate_pathway(NL_EDUCATION, "education", "NL", "CRREM_v2"):
    PATHWAY_RECORDS.append(rec)

# Education — AB Ortalaması (fallback)
EU_EDUCATION = [
    (2020,  90.0,  84.0, 115.0),
    (2025,  62.0,  53.0, 115.0),
    (2030,  39.0,  31.0, 115.0),
    (2035,  22.0,  16.0, 115.0),
    (2040,  11.0,   7.5, 115.0),
    (2045,   5.2,   3.4, 115.0),
    (2050,   2.5,   1.8, 115.0),
]
for rec in interpolate_pathway(EU_EDUCATION, "education", "EU", "estimated"):
    PATHWAY_RECORDS.append(rec)

# ─────────────────────────────────────────────────────────────────────────────
# LOGISTICS / INDUSTRIAL — Almanya (DE)
# Büyük hacimli yapılar, genellikle düşük ısıtma ama yüksek elektrik tüketimi
# Soğuk depo, üretim: daha yüksek başlangıç
# DE logistics benchmark 2020: ~90 kgCO2/m²
# ─────────────────────────────────────────────────────────────────────────────
DE_LOGISTICS = [
    (2020,  90.0,  84.0, 120.0),
    (2025,  63.0,  54.0, 120.0),
    (2030,  41.0,  33.0, 120.0),
    (2035,  25.0,  18.5, 120.0),
    (2040,  13.5,   9.0, 120.0),
    (2045,   6.0,   3.8, 120.0),
    (2050,   2.8,   1.9, 120.0),
]
for rec in interpolate_pathway(DE_LOGISTICS, "logistics", "DE", "CRREM_v2"):
    PATHWAY_RECORDS.append(rec)

# Logistics — AB Ortalaması (fallback)
EU_LOGISTICS = [
    (2020,  88.0,  82.0, 115.0),
    (2025,  61.0,  52.0, 115.0),
    (2030,  39.0,  31.0, 115.0),
    (2035,  24.0,  17.5, 115.0),
    (2040,  13.0,   8.5, 115.0),
    (2045,   5.8,   3.6, 115.0),
    (2050,   2.7,   1.8, 115.0),
]
for rec in interpolate_pathway(EU_LOGISTICS, "logistics", "EU", "estimated"):
    PATHWAY_RECORDS.append(rec)


# ─────────────────────────────────────────────────────────────────────────────
# DATA CENTER — EU representative (ESTIMATED, not an official CRREM sector)
# CRREM does not publish a data-centre pathway: DC intensity is process-driven
# (IT load + cooling), not floor-area-driven, so kgCO2/m² is a weak proxy and a
# dense facility will read "stranded now" by construction. We still provide a
# representative decarbonisation curve so the asset is benchmarked rather than
# blank — read DC stranding together with a PUE / per-kWh-IT caveat in the report.
# EU whole-building DC benchmark 2020 ≈ 340 kgCO2/m² (typical colo, not hyperscale).
# ─────────────────────────────────────────────────────────────────────────────
EU_DATA_CENTER = [
    (2020, 340.0, 320.0, 400.0),
    (2025, 250.0, 220.0, 400.0),
    (2030, 165.0, 135.0, 400.0),
    (2035, 100.0,  75.0, 400.0),
    (2040,  55.0,  38.0, 400.0),
    (2045,  25.0,  16.0, 400.0),
    (2050,  11.0,   7.0, 400.0),
]
for rec in interpolate_pathway(EU_DATA_CENTER, "data_center", "EU", "estimated"):
    PATHWAY_RECORDS.append(rec)

# ─────────────────────────────────────────────────────────────────────────────
# LAB / RESEARCH — EU representative (ESTIMATED, not an official CRREM sector)
# Wet/dry labs run high air-change rates (fume hoods, once-through air) plus 24/7
# equipment, so intensity sits above office but well below a data centre. No
# official CRREM lab pathway exists; this is a sector-representative estimate.
# EU lab benchmark 2020 ≈ 210 kgCO2/m².
# ─────────────────────────────────────────────────────────────────────────────
EU_LAB = [
    (2020, 175.0, 165.0, 210.0),
    (2025, 128.0, 112.0, 210.0),
    (2030,  84.0,  68.0, 210.0),
    (2035,  51.0,  38.0, 210.0),
    (2040,  28.0,  19.0, 210.0),
    (2045,  13.0,   8.0, 210.0),
    (2050,   7.0,   4.0, 210.0),
]
for rec in interpolate_pathway(EU_LAB, "lab", "EU", "estimated"):
    PATHWAY_RECORDS.append(rec)


print(f"✅ Toplam pathway kaydı hazırlandı: {len(PATHWAY_RECORDS)}")


# =============================================================================
# BÖLÜM 3 — SPARK DATAFRAME OLUŞTUR
# =============================================================================

SCHEMA = StructType([
    StructField("building_type",             StringType(),  False),
    StructField("country_code",              StringType(),  False),
    StructField("pathway_year",              IntegerType(), False),
    StructField("pathway_2c_kgco2_m2_yr",    DoubleType(),  True),
    StructField("pathway_15c_kgco2_m2_yr",   DoubleType(),  True),
    StructField("sector_benchmark_2020",     DoubleType(),  True),
    StructField("data_source",               StringType(),  True),
])
# NOT: year_month DATE kolonu aşağıda withColumn ile türetilir (Row'a girmez)

rows = [Row(
    building_type=r[0],
    country_code=r[1],
    pathway_year=r[2],
    pathway_2c_kgco2_m2_yr=float(r[3]),
    pathway_15c_kgco2_m2_yr=float(r[4]),
    sector_benchmark_2020=float(r[5]),
    data_source=r[6],
) for r in PATHWAY_RECORDS]

df_pathway = spark.createDataFrame(rows, schema=SCHEMA) \
    .withColumn(
        # year_month: pathway_year'ı DATE'e çevir (YYYY-01-01 formatı)
        # Amaç: Power BI'da Date[Date] tablosuyla doğrudan ilişki kurulabilsin.
        # İlişki: gold_crrem_pathway[year_month] → Date[Date] (Many-to-One)
        # DAX'ta YEAR() ile karşılaştır: yıllık pathway vs aylık bina emisyonu.
        "year_month",
        to_date(concat(col("pathway_year").cast("string"), lit("-01-01")), "yyyy-MM-dd")
    ) \
    .withColumn("updated_at", current_timestamp())

print(f"✅ DataFrame oluşturuldu: {df_pathway.count()} satır")
print("   year_month kolonu eklendi (DATE, YYYY-01-01 formatı) ✓")

# Önizleme
print("\n📊 Pathway önizleme (DE Office):")
df_pathway.filter(
    (col("building_type") == "office") & (col("country_code") == "DE")
).filter(col("pathway_year").isin([2024, 2025, 2030, 2035, 2040, 2050])) \
 .select("pathway_year", "pathway_2c_kgco2_m2_yr", "pathway_15c_kgco2_m2_yr") \
 .orderBy("pathway_year") \
 .show()


# =============================================================================
# BÖLÜM 4 — DELTA WRITE
# =============================================================================

# Statik referans tablo → basit overwrite yeterli (MERGE gereksiz)
# saveAsTable: hem Tables/ klasörüne yazar hem Lakehouse kataloğuna kaydeder
_tbl_name_init = OUTPUT_TABLE.replace("Tables/", "")
df_pathway.write \
    .format("delta") \
    .partitionBy("country_code") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(_tbl_name_init)

print(f"✅ gold_crrem_pathway tablo yazıldı ve kataloğa kaydedildi: {_tbl_name_init}")


# =============================================================================
# BÖLÜM 4b — LAKEHOUSE KATALOG SYNC (Direct Lake için)
# =============================================================================
# Fabric'te CREATE TABLE ... LOCATION relative path KABUL ETMEZ (absolute ABFS lazım).
# Bunun yerine: tablo katalogda varsa cache'i temizle, yoksa Fabric otomatik keşfeder.

_tbl_name = OUTPUT_TABLE.replace("Tables/", "")

try:
    spark.catalog.refreshTable(_tbl_name)
    print(f"✅ Katalog cache temizlendi: {_tbl_name}")
except Exception as _ex:
    print(f"ℹ️  '{_tbl_name}' katalogda henüz yok — Fabric otomatik keşfeder (1-2 dk beklenir)")
    print(f"   Semantic model hata verirse: Lakehouse → Tables → ⟳ Refresh → Model → Refresh now")


# =============================================================================
# BÖLÜM 5 — DOĞRULAMA
# =============================================================================

_tbl_check = OUTPUT_TABLE.replace("Tables/", "")
df_check = spark.read.table(_tbl_check)

print(f"\n📊 gold_crrem_pathway istatistikleri:")
print(f"   Toplam satır             : {df_check.count()}")
print(f"   Benzersiz bina türleri   : {df_check.select('building_type').distinct().count()}")
print(f"   Benzersiz ülkeler        : {df_check.select('country_code').distinct().count()}")

df_check.groupBy("building_type", "country_code", "data_source") \
    .count() \
    .orderBy("building_type", "country_code") \
    .show()

print("""
📋 SONRAKI ADIMLAR:
   1. Power BI Semantic Model'e gold_crrem_pathway tablosunu ekle
   2. building_type + country_code üzerinden silver_building_master ile ilişki kur
      (DAX'ta LOOKUPVALUE kullanılacak — doğrudan relationship gerekli değil)
   3. 12_dax_v7_ghg_crrem.dax'taki CRREM ölçülerini ekle:
      [CRREM Pathway 2C kgCO2 m2 yr]
      [CRREM Pathway Target tCO2 Yr]
      [CRREM Stranding Gap kgCO2 m2 yr]
   4. Gerçek CRREM Excel dosyasından veri çekmek için:
      https://www.crrem.org/tool/ → "Download pathway data"
      → bu notebook'un BÖLÜM 2'sini Excel okumayla değiştir
""")
