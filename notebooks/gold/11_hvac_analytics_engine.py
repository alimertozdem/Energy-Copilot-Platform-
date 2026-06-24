# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 11_hvac_analytics_engine.py
# Layer: GOLD — HVAC & Building Envelope Analytics Engine
# Updated: 2026-04-17
# =============================================================================
#
# GÖREV (Purpose):
#   Power BI Sayfa 7 (HVAC & Building Envelope) için gerekli tüm KPI'ları hesapla.
#   Isıtma/soğutma/havalandırma enerji ayrıştırması, bina kabuğu analizi,
#   yalıtım skoru, HVAC sistem tipi ve renovasyon önceliği bu notebook'tan üretilir.
#
# MİMARİ KARAR: Neden Ayrı Bir Gold Notebook?
#   HVAC analizi gold_kpi_daily'den (tüketim) + silver_building_master'dan
#   (U-değerleri, sistem bayrakları) + gold_ghg_scope'tan (Scope 1 gaz verisi)
#   beslenir. Bu üç tablonun birleşiminden türetilen 20+ KPI, tek bir tabloda
#   saklanır → Power BI'da her ölçü basit SUM/AVERAGE olur, DAX basit kalır.
#   Bu DP-600 Gold layer prensibine uygundur: "pre-computed, ready-to-consume".
#
# INPUT TABLOLAR:
#   silver_building_master  → U-değerleri, HP specs, sistem bayrakları, bina tipi
#   gold_kpi_daily          → Günlük tüketim, HDD, CDD, COP
#   gold_ghg_scope          → Scope 1 gaz emisyonu (m³ back-calculation için)
#
# OUTPUT TABLO: gold_hvac_analytics
#   Grain: aylık, bina bazlı
#
# KOLONLAR:
#   building_id              STRING
#   year_month               DATE          (YYYY-MM-01)
#   reporting_year           INT
#   reporting_month          INT
#   total_consumption_kwh    DOUBLE        Toplam aylık elektrik tüketimi
#   heating_energy_kwh       DOUBLE        Ayrıştırılmış ısıtma enerjisi
#   cooling_energy_kwh       DOUBLE        Ayrıştırılmış soğutma enerjisi
#   ventilation_kwh          DOUBLE        Havalandırma tahmini (sabit %15)
#   hvac_total_kwh           DOUBLE        Isıtma + soğutma + havalandırma
#   non_hvac_kwh             DOUBLE        Ekipman + aydınlatma (HVAC dışı)
#   hvac_share_pct           DOUBLE        HVAC/toplam × 100
#   heating_share_pct        DOUBLE        Isıtma/toplam × 100
#   cooling_share_pct        DOUBLE        Soğutma/toplam × 100
#   hdd_monthly              DOUBLE        Isıtma Derece Gün (base 15°C)
#   cdd_monthly              DOUBLE        Soğutma Derece Gün (base 22°C)
#   cop_actual_avg           DOUBLE        Isı pompası aylık ortalama COP (NULL = gaz)
#   scop_rolling             DOUBLE        Isı sezonu kümülatif SCOP (Ekim-Nisan)
#   heat_loss_kwh_m2         DOUBLE        Iletim ısı kaybı kWh/m²/ay
#   u_composite              DOUBLE        Ağırlıklı ortalama U-değeri W/m²K
#   insulation_score         DOUBLE        0-100 (100 = pasif ev standardı)
#   hvac_efficiency_score    DOUBLE        0-100 (COP / U-value karşılaştırma)
#   system_type              STRING        heat_pump | gas_boiler | hybrid | district
#   system_label             STRING        ASHP | GSHP | Gas Condensing | VRF | etc.
#   renovation_priority      STRING        High | Medium | Low
#   renovation_reason        STRING        İnsan-okunabilir açıklama
#   updated_at               TIMESTAMP
#
# VARSAYIMLAR:
#   V1: HVAC enerji ayrıştırması — HDD/CDD oransal model (bkz. BÖLÜM 5)
#       Gerçek sub-sayaç verisi olmadığında sektörel standart yaklaşım.
#   V2: Isı kaybı hesabı — EN ISO 13370 basitleştirilmiş yöntemi
#       U_composite × Zarf_alanı × HDD × 24 / 1000
#   V3: Zarf alanı tahmini — Kare planlı, 3 katlı bina varsayımı
#       Gerçek proje: BIM/DWG'den alınmalı
#   V4: GEG 2023 (Almanya) referans U-değerleri yalıtım skoru için kullanıldı
#       TR ve NL binaları için aynı benchmark uygulandı (güvenli taraf)
#   V5: COP verisi yalnızca ısı pompası olan binalarda (B001) anlamlı
#       Diğer binalar için NULL → DAX'ta COALESCE ile ele alınır
#   V6: Sistem tipi tespiti silver_building_master boolean kolonlarından yapılır
#       has_heat_pump, has_hvac_traditional, has_gas_heating kombinasyonu
#
# DP-600 KONULARI:
#   - Window functions (rolling SCOP hesabı)
#   - broadcast join (building_master küçük tablo)
#   - Delta MERGE UPSERT (idempotent)
#   - Z-ORDER (building_id, year_month)
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast, greatest, least,
    date_trunc, year, month, to_date,
    sum as spark_sum, avg as spark_avg, max as spark_max, min as spark_min,
    count, round as spark_round,
    current_timestamp, expr, lag
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType,
    DateType, TimestampType
)
from delta.tables import DeltaTable

spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

print("✅ Spark konfigürasyonu tamamlandı")


# =============================================================================
# BÖLÜM 2 — SABİTLER VE REFERANS DEĞERLER
# =============================================================================

# 2026-05-21: Schema-enabled lakehouse uyumu — dinamik ABFS path resolver
# Hardcoded "Tables/..." schema-enabled lakehouse'ta çalışmaz (gerçek path "Tables/dbo/...")
# Bu pattern catalog query ile actual physical path'i discover eder
import re

def _resolve_tables_prefix() -> tuple[str, str]:
    """Lakehouse'un Tables prefix'ini dinamik tespit eder.
    Schema-enabled (dbo) ve flat lakehouse'ları otomatik destekler."""
    candidate_tables = ["gold_kpi_daily", "silver_building_master", "gold_recommendations"]
    sample_path = None
    for t in candidate_tables:
        try:
            sample_path = spark.table(t).inputFiles()[0]
            break
        except Exception:
            continue
    if not sample_path:
        raise Exception("Referans tablo catalog'da yok — 01_bronze ve 02_silver çalıştı mı?")
    match = re.match(r"(abfss://[^/]+@[^/]+/[^/]+)", sample_path)
    if not match:
        raise Exception(f"ABFS base extract edilemedi: {sample_path}")
    abfss_base = match.group(1)
    if "/Tables/dbo/" in sample_path:
        return (f"{abfss_base}/Tables/dbo", "schema-enabled (dbo)")
    elif "/Tables/" in sample_path:
        return (f"{abfss_base}/Tables", "flat")
    else:
        raise Exception(f"Tables prefix tanınamadı: {sample_path}")

TABLES_PREFIX, _lakehouse_format = _resolve_tables_prefix()
print(f"✅ Lakehouse format: {_lakehouse_format}")
print(f"   Tables prefix: {TABLES_PREFIX}")

# Tablo yolları (dinamik prefix ile)
SILVER_BUILDING  = f"{TABLES_PREFIX}/silver_building_master"
GOLD_KPI_DAILY   = f"{TABLES_PREFIX}/gold_kpi_daily"
GOLD_GHG_SCOPE   = f"{TABLES_PREFIX}/gold_ghg_scope"
OUTPUT_TABLE     = f"{TABLES_PREFIX}/gold_hvac_analytics"
OUTPUT_TABLE_NAME = "gold_hvac_analytics"  # catalog table name (without prefix)

# ─── GEG 2023 Referans U-Değerleri (W/m²K) ────────────────────────────────
# Kaynak: Gebäudeenergiegesetz 2023, §19 — Modernizasyon teknik minimumları
# "Yeni Bina" seviyesi referans olarak kullanıldı (Varsayım V4)
U_BENCHMARK = {
    "wall":   0.24,   # GEG 2023 dış duvar yenileme standardı
    "roof":   0.20,   # Çatı/üst döşeme
    "floor":  0.35,   # Zemin döşemesi (toprağa temas eden)
    "window": 1.30,   # Pencere (çift cam, enerji tasarruflu)
}

# Pasif ev standardı (mükemmel = 100 puan eşiği)
U_PASSIVE = {
    "wall":   0.15,
    "roof":   0.10,
    "floor":  0.20,
    "window": 0.80,
}

# U-değeri ağırlıkları (tipik ticari bina ısı kaybı dağılımı)
# Kaynak: CIBSE Guide A (Environmental Design), Tablo 3.2
U_WEIGHTS = {
    "wall":   0.40,   # Dışduvar — en büyük pay
    "window": 0.30,   # Pencereler — yüksek U-değeri nedeniyle kritik
    "roof":   0.20,   # Çatı
    "floor":  0.10,   # Zemin (toprağa karşı düşük gradyan)
}

# ─── HVAC Enerji Ayrıştırma Katsayıları (bina tipine göre) ────────────────
# Kaynak: ASHRAE Handbook 2021, Bölüm 32 + EN ISO 13790 basitleştirme
#         + Uptime Institute Tier III DC profile (Datacenter)
#         + ASHRAE Lab Design Guide 2.0 (Lab/Research)
# heating_sens: HDD bazlı ısıtma payı katsayısı (yıllık total'ın %'si)
# cooling_sens: CDD bazlı soğutma payı katsayısı (yıllık total'ın %'si)
# ventilation:  Sabit havalandırma payı (toplam tüketimin oranı)
#
# Varsayım V1: Gerçek sub-meter verisi olmadığında HDD/CDD oransal model
# Bu katsayılar sektörel ortalamadır — gerçek binada kalibrasyon gerekir
#
# 2026-05-20: Data_Center ve Lab profilleri eklendi (yeni vertical'lar — B009, B010)
# 2026-05-21: "Datacenter" → "Data_Center" (ref_building_type_profiles uyumu, UPPER = DATA_CENTER)
HVAC_COEFFICIENTS = {
    "Office":      {"heating_sens": 0.35, "cooling_sens": 0.12, "ventilation": 0.15},
    "Retail":      {"heating_sens": 0.28, "cooling_sens": 0.18, "ventilation": 0.15},
    "Logistics":   {"heating_sens": 0.42, "cooling_sens": 0.05, "ventilation": 0.10},
    "Hotel":       {"heating_sens": 0.40, "cooling_sens": 0.12, "ventilation": 0.18},
    "Healthcare":  {"heating_sens": 0.22, "cooling_sens": 0.10, "ventilation": 0.20},
    "Education":   {"heating_sens": 0.48, "cooling_sens": 0.05, "ventilation": 0.15},
    # ── YENİ VERTICAL'LAR (2026-05-20) ───────────────────────────────────
    # Data_Center: Cooling-dominated. IT load dominates total kWh.
    #   Heating minimal (atık ısı yan ürün). Free cooling kış aylarında.
    #   Uptime Institute Tier III: ~65% cooling, ~2% heating, ~10% ventilation, kalan IT load
    "Data_Center": {"heating_sens": 0.02, "cooling_sens": 0.65, "ventilation": 0.10},
    # Lab/Research: Yüksek havalandırma (HEPA + fume hood + 8-12 ACH).
    #   Mixed heating/cooling (precise setpoint). Ventilation enerjinin %35'i.
    #   ASHRAE Lab Design Guide referans
    "Lab":         {"heating_sens": 0.18, "cooling_sens": 0.20, "ventilation": 0.35},
    "DEFAULT":     {"heating_sens": 0.35, "cooling_sens": 0.10, "ventilation": 0.15},
}

# ─── Isı Pompası Teknoloji Karşılaştırması ────────────────────────────────
# Kaynak: IEA Heat Pump Technology Roadmap 2023 + Eurovent Sertifikasyon
HP_TECHNOLOGY_BENCHMARKS = {
    # (min_cop, max_cop, label, description_tr)
    "ASHP_standard":  (2.5, 3.5, "ASHP Standart",      "Hava kaynaklı ısı pompası — sabit kompresör"),
    "ASHP_inverter":  (3.5, 5.0, "ASHP İnverter",       "Hava kaynaklı ısı pompası — değişken hız (en yaygın 2023+)"),
    "GSHP":           (4.0, 6.0, "GSHP",                "Toprak kaynaklı ısı pompası — en yüksek verim, yüksek maliyet"),
    "WSHP":           (4.5, 7.0, "WSHP / Water Loop",   "Su kaynaklı — ısı geri kazanımlı VRF büyük binalar"),
    "VRF_VRV":        (3.0, 5.5, "VRF/VRV Sistemi",     "Değişken soğutucu akışlı — büyük ticari binalarda popüler"),
    "Hybrid_HP_Gas":  (3.0, 4.5, "Hibrit HP + Gaz",     "Isı pompası + gaz kazan yedek — geçiş çözümü"),
    "Gas_Condensing": (None, None, "Gaz Yoğuşmalı Kazan","Verimlilik %90-98, sıfır karbon hedefiyle uyumsuz"),
    "District_Heat":  (None, None, "Bölgesel Isıtma",   "Yenilenebilir bağlantıda sıfır Scope 1 — ideal"),
}

# Isı pompası COP hedefleri (EN 14511, 7°C dış sıcaklık, 35°C besleme)
COP_TARGET_ASHP = 3.0   # Minimum kabul edilebilir (standart koşul)
COP_EXCELLENT_ASHP = 4.5  # Mükemmel inverter ısı pompası

# ─── Yalıtım Skoru Ağırlıkları ────────────────────────────────────────────
INSULATION_WEIGHTS = {
    "wall":   0.35,
    "window": 0.35,
    "roof":   0.20,
    "floor":  0.10,
}

print("✅ Sabitler yüklendi")
print(f"   GEG referans U-duvar : {U_BENCHMARK['wall']} W/m²K")
print(f"   GEG referans U-pencere: {U_BENCHMARK['window']} W/m²K")
print(f"   COP hedef ASHP       : {COP_TARGET_ASHP}")


# =============================================================================
# BÖLÜM 3 — TABLOLARI OKU
# =============================================================================

df_building = spark.read.format("delta").load(SILVER_BUILDING)
df_kpi      = spark.read.format("delta").load(GOLD_KPI_DAILY)

# gold_ghg_scope opsiyonel — ilk çalıştırmada mevcut olmayabilir
try:
    df_ghg = spark.read.format("delta").load(GOLD_GHG_SCOPE)
    HAS_GHG = True
    print(f"✅ gold_ghg_scope mevcut: {df_ghg.count()} satır")
except Exception:
    HAS_GHG = False
    print("⚠️  gold_ghg_scope mevcut değil → gaz tüketimi DAX'tan türetilecek")

print(f"✅ silver_building_master: {df_building.count()} bina")
print(f"✅ gold_kpi_daily: {df_kpi.count():,} satır")


# =============================================================================
# BÖLÜM 4 — BINA BİLGİSİ HAZIRLA
# =============================================================================

_avail = set(df_building.columns)

df_bldg = df_building.select(
    "building_id",
    "building_type",
    "country_code",
    "conditioned_area_m2",
    "gross_floor_area_m2",
    # Isı pompası
    coalesce(col("has_heat_pump"),       lit(False)).alias("has_hp"),
    coalesce(col("heat_pump_cop_rated"), lit(None).cast("double")).alias("cop_rated"),
    coalesce(col("heat_pump_capacity_kw"), lit(None).cast("double")).alias("hp_kw"),
    # Isıtma sistemi — 2026-05-04: bronze schema'ya has_gas_heating eklendi (01_bronze_ingestion.py)
    # has_gas_heating artık silver_building_master'da mevcut.
    # Fallback (eski lakehouse'larda geriye dönük uyumluluk için korundu).
    coalesce(
        col("has_gas_heating").cast("boolean") if "has_gas_heating" in _avail else lit(None).cast("boolean"),
        (coalesce(col("has_hvac_traditional"), lit(False)).cast("boolean") &
         ~coalesce(col("has_heat_pump"), lit(False)).cast("boolean"))
    ).alias("has_gas"),
    # primary_hvac_system — 2026-05-05: DÜZELTME — bu kolon select'e dahil edilmemişti.
    # Bu eksiklik system_type'ın her zaman boolean fallback'e düşmesine yol açıyordu
    # (B001 Berliner = heat_pump, B006 VRF gibi değerler hiç kullanılmıyordu).
    (col("primary_hvac_system") if "primary_hvac_system" in _avail
     else lit(None).cast("string")).alias("primary_hvac_system"),
    # Yalıtım U-değerleri
    coalesce(col("wall_u_value"),   lit(0.50)).alias("u_wall"),
    coalesce(col("roof_u_value"),   lit(0.30)).alias("u_roof"),
    coalesce(col("floor_u_value"),  lit(0.40)).alias("u_floor"),
    coalesce(col("window_u_value"), lit(2.00)).alias("u_window"),
    coalesce(col("window_to_wall_ratio"), lit(0.30)).alias("wwr"),
    coalesce(col("insulation_year"), lit(None).cast("integer")).alias("insulation_year"),
    # 2026-05-20: hava sızdırmazlık + termal köprü flag'i (önceden okunmuyordu)
    coalesce(col("air_tightness_ach"), lit(2.0)).alias("air_tightness_ach"),  # 2.0 = sektör ortalama
    coalesce(col("has_thermal_bridge").cast("boolean"), lit(False)).alias("has_thermal_bridge"),
    # Enerji sertifikası
    coalesce(col("energy_certificate"), lit("Unknown")).alias("energy_cert"),
).distinct()

# U_composite: ağırlıklı ortalama (Varsayım V1 ağırlıkları)
df_bldg = df_bldg.withColumn(
    "u_composite",
    spark_round(
        col("u_wall")   * lit(U_WEIGHTS["wall"])   +
        col("u_window") * lit(U_WEIGHTS["window"]) +
        col("u_roof")   * lit(U_WEIGHTS["roof"])   +
        col("u_floor")  * lit(U_WEIGHTS["floor"]),
        3
    )
)

# Zarf alanı tahmini (Varsayım V3):
# Kare planlı 3 katlı bina → side = sqrt(gross/3), height = 10.5m
df_bldg = df_bldg.withColumn(
    "envelope_area_m2",
    spark_round(
        # Duvar alanı: 4 × (sqrt(gross/3)) × 10.5
        4 * (col("gross_floor_area_m2") / 3).cast("double") ** 0.5 * 10.5 +
        # Çatı: brüt alanın 1/3'ü (üst kat)
        col("gross_floor_area_m2") / 3 +
        # Taban döşemesi: brüt alanın 1/3'ü
        col("gross_floor_area_m2") / 3,
        0
    )
)

# Yalıtım Skoru hesabı (2026-05-20 — 3-PARÇALI LINEER, Passive House diskriminasyonu)
#
# ÖNCEKİ HATA: score = min(100, target/u × 100) → Passive House (U=0.15) ve GEG (U=0.24)
#              her ikisi de 100 puana clipleniyordu → premium binalar ayırt edilemiyordu.
#
# YENI 3-PARÇALI EĞRİ (her U-element için):
#   U ≤ U_passive     → 100 puan (Passive House sınıfı)
#   U_passive..U_geg  → lineer 100→70 (GEG seviyesi = 70 puan)
#   U_geg..2×U_geg    → lineer 70→0  (GEG'in 2 katı = sıfır puan)
#   U > 2×U_geg       → 0 puan
#
# Sonuç: Passive House binası 90-100, GEG-modern bina 65-75, eski bina 20-50 arası
for elem, w in INSULATION_WEIGHTS.items():
    target  = U_BENCHMARK[elem]   # GEG referans (70 puan eşiği)
    passive = U_PASSIVE[elem]     # Passive House (100 puan)
    target_2x = {"wall": 2.0, "roof": 1.5, "floor": 1.2, "window": 5.0}[elem]      # 2× GEG (0 puan)

    u_col = col(f"u_{elem}")

    df_bldg = df_bldg.withColumn(
        f"ins_score_{elem}",
        spark_round(
            when(u_col <= lit(passive), lit(100.0))
            .when(u_col <= lit(target),
                  lit(100.0) - (u_col - lit(passive)) / lit(target - passive) * lit(30.0))
            .when(u_col <= lit(target_2x),
                  lit(70.0) - (u_col - lit(target)) / lit(target_2x - target) * lit(70.0))
            .otherwise(lit(0.0)),
            1
        )
    )

# Base score: ağırlıklı U-değeri kompoziti
df_bldg = df_bldg.withColumn(
    "_ins_base_score",
    spark_round(
        col("ins_score_wall")   * lit(INSULATION_WEIGHTS["wall"])   +
        col("ins_score_window") * lit(INSULATION_WEIGHTS["window"]) +
        col("ins_score_roof")   * lit(INSULATION_WEIGHTS["roof"])   +
        col("ins_score_floor")  * lit(INSULATION_WEIGHTS["floor"]),
        1
    )
)

# Air tightness cezası (n50 / ACH50 değeri)
# CIBSE TM23: <1.0 mükemmel, 1-3 iyi, 3-7 zayıf, >7 sızıntılı
# Penalty: ACH ≥ 5 → -10 puan, ACH ≥ 3 → -5 puan, ACH < 3 → 0
df_bldg = df_bldg.withColumn(
    "_air_penalty",
    when(col("air_tightness_ach") >= 5.0, lit(-10.0))
    .when(col("air_tightness_ach") >= 3.0, lit(-5.0))
    .otherwise(lit(0.0))
)

# Termal köprü cezası — has_thermal_bridge = True ise -3 puan
df_bldg = df_bldg.withColumn(
    "_tb_penalty",
    when(col("has_thermal_bridge"), lit(-3.0)).otherwise(lit(0.0))
)

df_bldg = df_bldg.withColumn(
    "insulation_score",
    spark_round(
        greatest(lit(0.0), least(lit(100.0),
            col("_ins_base_score") + col("_air_penalty") + col("_tb_penalty")
        )),
        1
    )
)

# ── Sistem tipi belirleme ─────────────────────────────────────────────────
# Öncelik sırası:
#   1. primary_hvac_system (sample-data veya ERP'den gelen doğrudan değer) — en güvenilir
#   2. has_hp / has_gas boolean kombinasyonu — fallback
# Bu yaklaşım yeni HVAC tiplerini (VRF, District, GSHP, Biomass...) destekler.
#
# NOT (2026-05-05 düzeltme): primary_hvac_system artık df_bldg select'ine dahil.
# _phys_avail yerine _avail (df_building.columns) kullanılıyor — daha güvenilir.

# primary_hvac_system NULL değerleri normalize et (boş string → NULL)
df_bldg = df_bldg.withColumn(
    "primary_hvac_system",
    when(
        col("primary_hvac_system").isNotNull() & (col("primary_hvac_system") != lit("")),
        col("primary_hvac_system")
    ).otherwise(lit(None).cast("string"))
)

df_bldg = df_bldg.withColumn(
    "system_type",
    when(
        col("primary_hvac_system").isNotNull(),
        col("primary_hvac_system")      # doğrudan kullan (vrf, district, biomass, electric vb.)
    )
    # Fallback: boolean flag kombinasyonu
    .when(col("has_hp") & col("has_gas"), lit("hybrid"))
    .when(col("has_hp"),                  lit("heat_pump"))
    .when(col("has_gas"),                 lit("gas_boiler"))
    .otherwise(                           lit("other"))
)

# Desteklenen tüm sistem tipleri ve etiketleri
# Genişletmek için buraya yeni when() satırı ekle
# audit G2 fix: system_label İngilizce (web-app/rapor UI tamamen İngilizce kuralı)
df_bldg = df_bldg.withColumn(
    "system_label",
    when(col("system_type") == "heat_pump",
         when(col("cop_rated") >= 4.5, lit("ASHP Inverter (Premium)"))
         .when(col("cop_rated") >= 4.0, lit("ASHP Inverter (High Efficiency)"))
         .when(col("cop_rated") >= 3.0, lit("ASHP Standard"))
         .otherwise(lit("Heat Pump (Air Source)"))
    )
    .when(col("system_type") == "gshp",     lit("GSHP (Ground Source HP)"))
    .when(col("system_type") == "wshp",     lit("WSHP (Water Source HP)"))
    .when(col("system_type") == "hybrid",   lit("Hybrid HP + Gas Boiler"))
    .when(col("system_type") == "gas_boiler", lit("Gas Condensing Boiler"))
    .when(col("system_type") == "vrf",      lit("VRF/VRV System"))
    .when(col("system_type") == "district", lit("District Heating/Cooling"))
    .when(col("system_type") == "biomass",  lit("Biomass Boiler"))
    .when(col("system_type") == "electric", lit("Electric Resistance Heating"))
    .when(col("system_type") == "chiller",  lit("Chiller (Cooling-led)"))
    .otherwise(lit("Unknown / Other"))
)

print(f"✅ Bina bilgisi hazırlandı: {df_bldg.count()} bina")
print("\nSistem tipleri:")
df_bldg.groupBy("system_type", "system_label").count().show(truncate=False)
print("\nYalıtım skorları:")
df_bldg.select("building_id", "u_composite", "insulation_score").show()


# =============================================================================
# BÖLÜM 5 — AYLIK KPI AGREGASYONU
# =============================================================================

# gold_kpi_daily mevcut kolonlarını kontrol et (versiyon farklılıklarına karşı güvenlik)
_kpi_avail = set(df_kpi.columns)
print(f"ℹ️  gold_kpi_daily kolonları: {sorted(_kpi_avail)}")

# ── COP kolonu fiziksel varlık testi ──────────────────────────────────────────
# NEDEN: df_kpi.columns Delta log (şema metadata) okur — fiziksel parquet
# dosyalarını taramaz. Şema güncel değilse kolon schema'da var görünür ama
# Spark plan çözümünde UNRESOLVED_COLUMN hatası verir.
# FIX: Gerçek bir Spark plan tetikleyerek kolonun fiziksel olarak erişilebilir
#      olduğunu doğrula. limit(0) → plan oluşturur ama veri okumaz.
# ─────────────────────────────────────────────────────────────────────────────
def _col_physically_exists(df, col_name: str) -> bool:
    """Delta log şeması yerine Spark plan çözümünü test eder."""
    if col_name not in df.columns:
        return False
    try:
        df.select(col_name).limit(0).write.format("noop").mode("overwrite").save()
        return True
    except Exception as _e:
        print(f"   ⚠️  '{col_name}' schema'da tanımlı ama fiziksel veri yok: {type(_e).__name__}")
        return False

_has_cop_col = _col_physically_exists(df_kpi, "cop_actual_avg")

if _has_cop_col:
    print("✅ cop_actual_avg gold_kpi_daily'de MEVCUT → gerçek COP verisi kullanılacak")
    _cop_expr = spark_avg(coalesce(col("cop_actual_avg"), lit(None).cast("double")))
else:
    print("ℹ️  cop_actual_avg gold_kpi_daily'de YOK → NULL kullanılacak")
    print("   (COP sonraki adımda cop_rated [silver_building_master] ile doldurulacak)")
    _cop_expr = spark_avg(lit(None).cast("double"))

_df_monthly_agg = (
    df_kpi.withColumn(
        "year_month", date_trunc("month", col("date")).cast(DateType())
    ).groupBy("building_id", "year_month").agg(
        spark_sum("total_consumption_kwh").alias("total_consumption_kwh"),
        spark_sum(coalesce(col("hdd_day"), lit(0.0))).alias("hdd_monthly"),
        spark_sum(coalesce(col("cdd_day"), lit(0.0))).alias("cdd_monthly"),
        _cop_expr.alias("cop_actual_avg"),
        spark_sum("net_grid_consumption_kwh").alias("grid_kwh"),
    )
)
df_monthly = (
    _df_monthly_agg
    .withColumn("reporting_year",  year(col("year_month")))
    .withColumn("reporting_month", month(col("year_month")))
)

print(f"✅ Aylık KPI agregasyonu: {df_monthly.count()} satır")


# =============================================================================
# BÖLÜM 6 — BINA BİLGİSİ İLE BİRLEŞTİR
# =============================================================================
#
# JOIN DIRECTION (2026-05-06 fix):
#   ÖNCEKI: df_monthly.join(df_bldg, how="left")
#     → gold_kpi_daily'de kaydı olmayan binalar result'tan düşer
#     → Power BI slicer cross-filter'da sadece enerji verisi olan binalar görünür
#   YENİ: df_bldg.join(df_monthly, how="left")
#     → silver_building_master'daki tüm binalar result'ta her zaman var
#     → Enerji verisi olmayan ay/bina → NULL total_consumption, NULL HVAC metrics
#     → Power BI slicer tüm 6 binayı gösterir
#   DP-600 best practice: dimension-first LEFT JOIN for dimension completeness

df_joined = df_bldg.join(
    df_monthly,
    on="building_id",
    how="left"
)


# =============================================================================
# BÖLÜM 7 — HVAC ENERJİ AYRIŞTIRMASI (Varsayım V1)
# =============================================================================
#
# Yöntem: HDD/CDD Oransal Model (EN ISO 13790 Basitleştirilmiş)
#
# Temel fikir:
#   Isıtma enerjisi HDD ile orantılıdır (soğuk = çok ısıtma)
#   Soğutma enerjisi CDD ile orantılıdır (sıcak = çok soğutma)
#   HDD/CDD yıllık toplamı ile normalize edilir → aylık pay
#
# heating_kwh = toplam × heating_sens × (HDD_ay / HDD_yıl)
# cooling_kwh = toplam × cooling_sens × (CDD_ay / CDD_yıl)
# ventilation  = toplam × 0.15 (sabit)
# non_hvac     = toplam - heating - cooling - ventilation
#
# SINIRLILIK: Gerçek alt-sayaç verisi olmadan bu bir tahmindir.
# Sub-meter verisi geldiğinde bu bölüm gerçek veriyle değiştirilmeli.
# =============================================================================

# Yıllık HDD, CDD ve TOPLAM TÜKETİM (normalize için)
# 2026-05-20 BUG FIX: total_consumption_annual eklendi.
#   ÖNCEKİ HATA: heating/cooling formülü `total_consumption_kwh` (aylık) kullanıyordu
#   → annual heating = total/12 × heating_sens (12× DÜŞÜK!)
#   → HVAC Share %19 (gerçek beklenen %55-65)
#   YENI: heating = total_ANNUAL × heating_sens × hdd_fraction
#   → annual sum doğru: total × heating_sens (heating_sens = annual share)
win_bldg_year = Window.partitionBy("building_id", "reporting_year")

df_with_annual = df_joined.withColumn(
    "total_consumption_annual",
    spark_sum(coalesce(col("total_consumption_kwh"), lit(0.0))).over(win_bldg_year)
).withColumn(
    "hdd_annual", spark_sum("hdd_monthly").over(win_bldg_year)
).withColumn(
    "cdd_annual", spark_sum("cdd_monthly").over(win_bldg_year)
)

# HDD/CDD fraksiyonları (sıfır bölme koruması)
df_with_frac = df_with_annual.withColumn(
    "hdd_fraction",
    when(col("hdd_annual") > 0,
         col("hdd_monthly") / col("hdd_annual")
    ).otherwise(lit(0.0))
).withColumn(
    "cdd_fraction",
    when(col("cdd_annual") > 0,
         col("cdd_monthly") / col("cdd_annual")
    ).otherwise(lit(0.0))
)

# HVAC katsayılarını bina tipine göre uygula
# PySpark'ta UDF kullanmak yerine CASE WHEN (DP-600 best practice)
def add_hvac_coeff(df, coeff_key, col_out):
    """Bina tipine göre HVAC katsayısını ekle.
    2026-05-20: Datacenter ve Lab tipleri de destekleniyor (B009, B010)."""
    c = HVAC_COEFFICIENTS
    return df.withColumn(
        col_out,
        when(col("building_type") == "Office",     lit(c["Office"][coeff_key]))
        .when(col("building_type") == "Retail",    lit(c["Retail"][coeff_key]))
        .when(col("building_type") == "Logistics", lit(c["Logistics"][coeff_key]))
        .when(col("building_type") == "Hotel",     lit(c["Hotel"][coeff_key]))
        .when(col("building_type") == "Healthcare",lit(c["Healthcare"][coeff_key]))
        .when(col("building_type") == "Education", lit(c["Education"][coeff_key]))
        .when(col("building_type") == "Data_Center",lit(c["Data_Center"][coeff_key]))
        .when(col("building_type") == "Lab",        lit(c["Lab"][coeff_key]))
        .otherwise(lit(c["DEFAULT"][coeff_key]))
    )

df_with_frac = add_hvac_coeff(df_with_frac, "heating_sens", "_h_sens")
df_with_frac = add_hvac_coeff(df_with_frac, "cooling_sens", "_c_sens")
df_with_frac = add_hvac_coeff(df_with_frac, "ventilation",  "_vent_share")

# Enerji ayrıştırması (2026-05-20 düzeltildi — total_consumption_annual kullanıyor)
#
# MATEMATİK MANTIK:
#   heating_sens = yıllık tüketimin % kaçı ısıtmadır (Office=35%)
#   hdd_fraction = ay HDD'sinin yıllık HDD'ye oranı (yıl boyu Σ=1.0)
#   heating_monthly = total_ANNUAL × heating_sens × hdd_fraction
#   → Σ heating_monthly over year = total_annual × heating_sens × 1.0 ✅
#
#   Ventilation aylık total ile çarpıma devam ediyor (yıllık toplam doğru çıkıyor):
#   Σ vent = Σ(total_monthly × 0.15) = total_annual × 0.15 ✅
df_disagg = df_with_frac.withColumn(
    "heating_energy_kwh",
    spark_round(
        col("total_consumption_annual") * col("_h_sens") * col("hdd_fraction"),
        2
    )
).withColumn(
    "cooling_energy_kwh",
    spark_round(
        col("total_consumption_annual") * col("_c_sens") * col("cdd_fraction"),
        2
    )
).withColumn(
    "ventilation_kwh",
    spark_round(col("total_consumption_kwh") * col("_vent_share"), 2)
).withColumn(
    "hvac_total_kwh",
    spark_round(
        col("heating_energy_kwh") + col("cooling_energy_kwh") + col("ventilation_kwh"),
        2
    )
).withColumn(
    "non_hvac_kwh",
    spark_round(
        col("total_consumption_kwh") - col("hvac_total_kwh"),
        2
    )
).withColumn(
    "hvac_share_pct",
    spark_round(
        col("hvac_total_kwh") / col("total_consumption_kwh") * 100,
        1
    )
).withColumn(
    "heating_share_pct",
    spark_round(
        col("heating_energy_kwh") / col("total_consumption_kwh") * 100,
        1
    )
).withColumn(
    "cooling_share_pct",
    spark_round(
        col("cooling_energy_kwh") / col("total_consumption_kwh") * 100,
        1
    )
)

print("✅ HVAC enerji ayrıştırması tamamlandı")


# =============================================================================
# BÖLÜM 8 — ISI KAYBI HESABI (Varsayım V2, V3)
# =============================================================================
#
# Formül (EN ISO 13370 basitleştirilmiş iletim ısı kaybı):
#   Q_transmission [kWh/ay] = U_composite [W/m²K]
#                           × Zarf_alanı [m²]
#                           × HDD_aylık [K·gün]
#                           × 24 [saat/gün]
#                           / 1000 [W → kW]
#
# Zarf alanı = duvar + çatı + taban (Varsayım V3: kare plan, 3 kat)
# Isı köprüsü katsayısı (Δu) = 0.10 W/m²K eklendi (EN ISO 14683 default)
# =============================================================================

# EN ISO 14683 — Isı köprüsü katsayısı (default vs poor-detailing)
# 2026-05-20: has_thermal_bridge flag'i artık kullanılıyor
#   has_thermal_bridge = True  → 0.10 W/m²K (eski detaylandırma, yüksek kayıp)
#   has_thermal_bridge = False → 0.05 W/m²K (modern detaylandırma, EN ISO 14683 best practice)
THERMAL_BRIDGE_FACTOR_GOOD = 0.05
THERMAL_BRIDGE_FACTOR_POOR = 0.10

df_heat_loss = df_disagg.withColumn(
    "_tb_factor",
    when(col("has_thermal_bridge"), lit(THERMAL_BRIDGE_FACTOR_POOR))
    .otherwise(lit(THERMAL_BRIDGE_FACTOR_GOOD))
).withColumn(
    "heat_loss_kwh",
    spark_round(
        (col("u_composite") + col("_tb_factor"))            # toplam U + köprü (dinamik)
        * col("envelope_area_m2")                           # m²
        * col("hdd_monthly")                                # K·gün
        * 24                                                # saat/gün
        / 1000,                                             # W → kW
        1
    )
).withColumn(
    # kWh/m²/ay → normalize (koşullandırılmış alan ile)
    "heat_loss_kwh_m2",
    spark_round(
        col("heat_loss_kwh") / col("conditioned_area_m2"),
        3
    )
)

print("✅ Isı kaybı hesaplandı")


# =============================================================================
# BÖLÜM 9 — MEVSIMSEL COP (SCOP) — ROLLING WINDOW
# =============================================================================
#
# SCOP (Seasonal Coefficient of Performance):
#   Isı sezonunun tamamında (Ekim–Nisan) oluşan kümülatif COP
#   SCOP = Σ(ısıtma enerjisi) / Σ(elektrik tüketimi) — ısıtma sezonu boyunca
#
# Basitleştirme: 3 aylık rolling average COP
# (Gerçek SCOP = yıllık ısıtma enerjisi / yıllık ısıtma için harcanan elektrik)
# =============================================================================

win_rolling = (Window.partitionBy("building_id").orderBy("year_month")
                    .rowsBetween(-2, 0))  # 3 aylık rolling

# 2026-05-20 BUG FIX: GSHP ve WSHP de heat pump ailesinde → SCOP hesabına dahil
# G1 (2026-06-21): COP rated-proxy. Actual COP unmeasured (BMS=Phase 2) -> cop_actual_avg
# was NULL -> "HVAC Avg COP" card blank. Fill from rated spec for the heat-pump family so
# the COP card + SCOP populate (labelled "rated" in the report). Gas/district/chiller stay NULL.
df_heat_loss = df_heat_loss.withColumn(
    "cop_actual_avg",
    when(col("system_type").isin("heat_pump", "gshp", "wshp"),
         coalesce(col("cop_actual_avg"), col("cop_rated")))
    .otherwise(col("cop_actual_avg"))
)

df_with_scop = df_heat_loss.withColumn(
    "scop_rolling",
    when(
        col("system_type").isin("heat_pump", "gshp", "wshp"),
        spark_round(spark_avg("cop_actual_avg").over(win_rolling), 2)
    ).otherwise(lit(None).cast("double"))
)

print("✅ SCOP rolling window hesaplandı")


# =============================================================================
# BÖLÜM 10 — HVAC VERİMLİLİK SKORU (0-100)
# =============================================================================
#
# Isı pompası binaları: COP actual / COP_excellent × 100 (maks 100)
# Gaz kazan binaları  : (1 - U_composite/U_poor) × 100 × gaz_etkisizlik_cezası
#   Gaz kazanı enerji açısından en iyi %90-98 verimlidir ama
#   karbon açısından ısı pompasına göre ~3× kötüdür.
#   Bu skor "COP eşdeğeri" değil — renovasyon önceliği skoru olarak okuyun.
#
# Yorumlama:
#   80-100: Mükemmel (ısı pompası + iyi yalıtım)
#    60-80: İyi (ısı pompası veya iyi yalıtım)
#    40-60: Orta (gaz + kısmi yenileme)
#    20-40: Zayıf (gaz + kötü yalıtım)
#      <20: Kritik (çok eski sistem + hiç yalıtım yok)
# =============================================================================

U_POOR = 1.50   # Kötü yalıtım eşiği W/m²K

df_with_eff = df_with_scop.withColumn(
    "hvac_efficiency_score",
    spark_round(
        when(
            col("system_type").isin("heat_pump", "gshp", "wshp"),
            # Isı pompası skoru (0-100): COP actual veya rated / excellent
            least(
                lit(100.0),
                coalesce(col("cop_actual_avg"), col("cop_rated"), lit(COP_TARGET_ASHP))
                / lit(COP_EXCELLENT_ASHP) * 100
            )
        ).when(
            col("system_type") == "vrf",
            # VRF: tipik COP 3.5-5.0, zoning avantajı var → 60-80 puan
            least(lit(80.0), col("insulation_score") * 0.70 + lit(20.0))
        ).when(
            col("system_type") == "district",
            # Bölgesel: kaynak tarafındaki verim bilinmiyor, yalıtım kritik → 50-75
            least(lit(75.0), col("insulation_score") * 0.65 + lit(15.0))
        ).when(
            col("system_type") == "hybrid",
            # Hibrit: COP katkısı var ama gaz yedek cezası → maks 70
            least(
                lit(70.0),
                coalesce(col("cop_actual_avg"), lit(3.0)) / lit(COP_EXCELLENT_ASHP) * 100 * 0.80
            )
        ).when(
            col("system_type") == "biomass",
            # Biyokütle: karbon-nötr ama verimlilik orta → 45-65
            least(lit(65.0), col("insulation_score") * 0.55 + lit(10.0))
        ).when(
            col("system_type") == "electric",
            # Elektrikli direnç: COP=1, yüksek karbon riski → 10-30
            least(lit(30.0), col("insulation_score") * 0.25 + lit(5.0))
        ).when(
            col("system_type") == "chiller",
            # Chiller (cooling-led datacenter): PUE odaklı verim, refrigerant COP 3-5
            # Modern free-cooling + heat recovery → 55-85 puan
            least(lit(85.0), col("insulation_score") * 0.30 + lit(50.0))
        ).otherwise(
            # Gaz kazan + other: yalıtıma göre 10-50, karbon dezavantajı
            least(lit(50.0), col("insulation_score") * 0.45)
        ),
        1
    )
)

print("✅ HVAC verimlilik skoru hesaplandı")


# =============================================================================
# BÖLÜM 11 — RENOVASYON ÖNCELİĞİ VE AÇIKLAMA
# =============================================================================
#
# Karar matrisi (3×2: yalıtım × sistem):
#
#                    Yalıtım İYİ    Yalıtım ORTA    Yalıtım KÖTÜ
# Isı Pompası        Low            Low/Medium       Medium
# Gaz/Hibrit         Medium         High             High (Kritik)
#
# Eşikler: insulation_score ≥ 70 → iyi, ≥ 45 → orta, < 45 → kötü
# =============================================================================

# 2026-05-20 ALIGNMENT: _ins_band eşikleri DAX EPC sınırlarıyla hizalandı
#   DAX Insulation Label v43 eşikleri: 35 / 50 / 65 / 80
#   Yeni: poor < 50 (EPC E/F/G), medium 50-65 (EPC D), good ≥ 65 (EPC A/B/C)
#   Bu sayede notebook karar (renovation_priority) ile DAX etiketi (EPC) tutarlı
df_with_reno = df_with_eff.withColumn(
    "_ins_band",
    when(col("insulation_score") >= 65, lit("good"))     # EPC A/B/C
    .when(col("insulation_score") >= 50, lit("medium"))  # EPC D
    .otherwise(lit("poor"))                              # EPC E/F/G
).withColumn(
    "renovation_priority",
    when(col("system_type").isin("heat_pump","gshp","wshp"),
         when(col("_ins_band") == "poor",   lit("Medium"))
         .otherwise(                         lit("Low"))
    ).when(col("system_type") == "vrf",
         when(col("_ins_band") == "poor",   lit("Medium"))   # VRF + kötü yalıtım → orta
         .otherwise(                         lit("Low"))
    ).when(col("system_type") == "district",
         when(col("_ins_band") == "poor",   lit("Medium"))   # Bölgesel ısı + kötü yalıtım
         .otherwise(                         lit("Low"))
    ).when(col("system_type") == "biomass",
         when(col("_ins_band") == "poor",   lit("High"))     # Biyokütle + kötü yalıtım
         .otherwise(                         lit("Medium"))
    ).when(col("system_type") == "electric",
         lit("High")                                          # Elektrikli direnç daima yüksek
    ).when(col("system_type") == "hybrid",
         when(col("_ins_band") == "poor",   lit("High"))
         .otherwise(                         lit("Medium"))
    ).when(col("system_type") == "chiller",
         # Chiller (DC cooling): envelope iyi → Low, kötü → Medium
         when(col("_ins_band") == "poor",   lit("Medium"))
         .otherwise(                         lit("Low"))
    ).otherwise(  # gas_boiler / other
         when(col("_ins_band") == "good",   lit("Medium"))
         .otherwise(                         lit("High"))
    )
).withColumn(
    "renovation_reason",
    when(
        (col("system_type") == "gas_boiler") & (col("_ins_band") == "poor"),
        lit("Gas heating + poor insulation: prioritise ASHP switch + envelope upgrade (CSRD Scope 1 risk)")
    ).when(
        (col("system_type") == "gas_boiler") & (col("_ins_band") == "medium"),
        lit("Gas heating: plan heat-pump transition (EU directive before 2030)")
    ).when(
        (col("system_type") == "gas_boiler") & (col("_ins_band") == "good"),
        lit("Insulation adequate — good window for gas to HP switch, low retrofit risk")
    ).when(
        col("system_type").isin("heat_pump","gshp","wshp"),
        when(col("_ins_band") == "poor",
             lit("Heat pump present: improving insulation raises SCOP by 15-25%")
        ).otherwise(
             lit("Good performance: annual COP tracking + filter/compressor maintenance")
        )
    ).when(col("system_type") == "vrf",
        when(col("_ins_band") == "poor",
             lit("VRF system: weak insulation, high zone losses — envelope first")
        ).otherwise(
             lit("VRF: refrigerant leak checks + zone balancing optimisation")
        )
    ).when(col("system_type") == "district",
        when(col("_ins_band") == "poor",
             lit("District heat: improve insulation to optimise network connection capacity")
        ).otherwise(
             lit("District heat: monitor internal distribution losses, heat exchanger maintenance")
        )
    ).when(col("system_type") == "hybrid",
        lit("Hybrid: reduce gas share, increase HP runtime — 2030 target is pure HP")
    ).when(col("system_type") == "biomass",
        when(col("_ins_band") == "poor",
             lit("Biomass + poor insulation: envelope first, fuel efficiency is low")
        ).otherwise(
             lit("Biomass: fuel supply security + emissions monitoring (PM2.5)")
        )
    ).when(col("system_type") == "electric",
        lit("Electric resistance: COP=1.0, switching to ASHP cuts energy by ~65%")
    ).when(col("system_type") == "chiller",
        when(col("_ins_band") == "poor",
            lit("Data centre envelope retrofit: reduce thermal infiltration, increase free-cooling hours")
        ).otherwise(
            lit("Data centre chiller: F-Gas refrigerant audit, maximise free-cooling, waste-heat recovery")
        )
    ).otherwise(
        lit("System type unclear: energy audit and HVAC inventory recommended")
    )
)

print("✅ Renovasyon önceliği hesaplandı")


# =============================================================================
# BÖLÜM 12 — ÇIKTI TABLOSU HAZIRLA
# =============================================================================

FINAL_COLS = [
    "building_id", "year_month", "reporting_year", "reporting_month",
    "total_consumption_kwh",
    "heating_energy_kwh", "cooling_energy_kwh", "ventilation_kwh",
    "hvac_total_kwh", "non_hvac_kwh",
    "hvac_share_pct", "heating_share_pct", "cooling_share_pct",
    "hdd_monthly", "cdd_monthly",
    "cop_actual_avg", "scop_rolling",
    "heat_loss_kwh", "heat_loss_kwh_m2",
    "u_composite", "insulation_score", "hvac_efficiency_score",
    "system_type", "system_label",
    "renovation_priority", "renovation_reason",
]

df_final = df_with_reno.select(FINAL_COLS).withColumn("updated_at", current_timestamp()).filter(col("reporting_year") >= 2024)  # G3 (2026-06-21): 2023 has no HDD/CDD -> drop sham rows

# Doğrulama özeti
print("\n📊 Çıktı özeti:")
df_final.groupBy("building_id").agg(
    spark_avg("hvac_share_pct").alias("Avg_HVAC_Share_%"),
    spark_avg("insulation_score").alias("Avg_Insulation_Score"),
    spark_avg("hvac_efficiency_score").alias("Avg_Efficiency_Score"),
    spark_avg("heating_energy_kwh").alias("Avg_Monthly_Heating_kWh"),
).orderBy("building_id").show(truncate=False)

print("\n📊 Renovasyon öncelikleri:")
(df_final.groupBy("building_id", "system_label", "renovation_priority").count()
    .orderBy("building_id").show(truncate=False))


# =============================================================================
# BÖLÜM 13 — DELTA WRITE (Schema-Aware)
# =============================================================================
#
# NEDEN BU DEĞİŞİKLİK?
#   Tablo daha önce year_month STRING olarak oluşturulduysa, MERGE işlemi
#   şemayı değiştirmez — Power BI ilişkisi kurulamaz.
#   Bu blok mevcut şemayı kontrol eder:
#     • year_month DATE ise → normal MERGE (incremental, veri kaybı yok)
#     • year_month STRING veya tablo yok → overwriteSchema=true ile yeniden yaz
#
# SONUÇ: gold_hvac_analytics[year_month] her zaman DATE tipinde çıkar.
#        Power BI → Date[Date] ilişkisi doğrudan kurulabilir.
# =============================================================================

_tbl_name = OUTPUT_TABLE_NAME  # catalog adı (sadece "gold_hvac_analytics")
_needs_overwrite = False

try:
    _existing_schema = spark.read.format("delta").load(OUTPUT_TABLE).schema
    _ym_type = str(_existing_schema["year_month"].dataType)
    if "DateType" not in _ym_type:
        print(f"⚠️  year_month tipi '{_ym_type}' tespit edildi — DATE değil.")
        print("   overwriteSchema=true ile yeniden yazılıyor...")
        _needs_overwrite = True
    else:
        print(f"✅ year_month tipi doğru (DateType) — MERGE kullanılacak.")
except Exception:
    print("ℹ️  Tablo henüz mevcut değil — ilk kez oluşturulacak.")
    _needs_overwrite = True

if _needs_overwrite:
    (df_final.write
        .format("delta")
        .partitionBy("reporting_year")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(_tbl_name))
    print(f"\n✅ Delta tablo oluşturuldu / schema fix edildi: {_tbl_name}")
    print("   year_month → DATE  ✓")
else:
    gold_table = DeltaTable.forPath(spark, OUTPUT_TABLE)
    (gold_table.alias("tgt").merge(
        df_final.alias("src"),
        "tgt.building_id = src.building_id AND tgt.year_month = src.year_month"
    ).whenMatchedUpdateAll()
     .whenNotMatchedInsertAll()
     .execute())
    print(f"\n✅ Delta MERGE tamamlandı: {OUTPUT_TABLE}")


# =============================================================================
# BÖLÜM 14 — Z-ORDER OPTIMIZE
# =============================================================================

# =============================================================================
# BOLUM 13b - G3 (2026-06-21): purge pre-2024 rows (2023 has no HDD/CDD -> split=0)
# MERGE does NOT delete source-absent rows, so df_final's >=2024 filter leaves stale
# 2023 rows in gold. Delete them explicitly. Idempotent (every run sweeps pre-2024).
# =============================================================================
DeltaTable.forPath(spark, OUTPUT_TABLE).delete("reporting_year < 2024")
print("G3: reporting_year < 2024 rows purged (2023 = no weather data)")


spark.sql(f"""
    OPTIMIZE delta.`{OUTPUT_TABLE}`
    ZORDER BY (building_id, year_month)
""")

print("✅ Z-ORDER OPTIMIZE tamamlandı")


# =============================================================================
# BÖLÜM 14b — LAKEHOUSE KATALOG SYNC (Direct Lake için)
# =============================================================================
# Fabric'te CREATE TABLE ... LOCATION relative path KABUL ETMEZ (absolute ABFS lazım).
# Bunun yerine: tablo katalogda varsa cache'i temizle, yoksa Fabric otomatik keşfeder.

_tbl_name = OUTPUT_TABLE_NAME  # catalog adı (ABFS path'ten ayrı)

try:
    spark.catalog.refreshTable(_tbl_name)
    print(f"✅ Katalog cache temizlendi: {_tbl_name}")
except Exception as _ex:
    print(f"ℹ️  '{_tbl_name}' katalogda henüz yok — Fabric otomatik keşfeder (1-2 dk beklenir)")
    print(f"   Semantic model hata verirse: Lakehouse → Tables → ⟳ Refresh → Model → Refresh now")


# =============================================================================
# BÖLÜM 15 — SONRAKI ADIMLAR
# =============================================================================

print("""
📋 SONRAKI ADIMLAR:
   1. Power BI Semantic Model'e gold_hvac_analytics tablosunu ekle
   2. İlişki kur: gold_hvac_analytics[building_id] → silver_building_master[building_id]
   3. İlişki kur: gold_hvac_analytics[year_month]  → Date[Date]
   4. 13_dax_v8_hvac_envelope.dax dosyasındaki ölçüleri ekle
   5. Sayfa 7 (HVAC & Building Envelope) görsellerini oluştur

📌 ÖNEMLİ VARSAYIM HATIRLATICI:
   - Isıtma/soğutma ayrıştırması: HDD/CDD oransal model (gerçek değil, tahmin)
   - Isı kaybı: Kare plan + 3 kat varsayımı (BIM verisiyle kesinleştirin)
   - COP: Yalnızca B001 (ısı pompası) için gerçek veri, diğerleri NULL
   - Tüm "yüksek renovasyon önceliği" binaları için ilk adım: enerji denetimi

🌡️ ISI POMPASI TEKNOLOJİ NOTU (2026 Sektör Durumu):
   - ASHP İnverter: COP 4.0-5.5 — en yaygın retrofit çözümü
   - GSHP: COP 4.5-6.0 — yeni binalar için ideal, yüksek yatırım
   - VRF/VRV: COP 3.5-5.5 — büyük ticari binalarda giderek yaygınlaşıyor
   - Hibrit HP+Gaz: Geçiş çözümü — 2030 sonrası tek başına gaz yasak (AB)
""")

print("\n✅ Notebook 11 tamamlandı.")
print("=" * 60)
print("gold_hvac_analytics tablosu başarıyla oluşturuldu.")
print("=" * 60)
