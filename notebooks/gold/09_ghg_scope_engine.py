# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 09_ghg_scope_engine.py
# Layer: GOLD — GHG Scope Emissions Engine
# Updated: 2026-04-16
# ⚠️ FABRIC NOTE: ~34KB → too big for ONE Fabric cell (~33KB paste limit). The LIVE
#    Fabric 09 is the 3-cell split: 09_ghg_FABRIC_cell1_dataprep + cell2_scopecalc +
#    cell3_breakdown_long (newer; cell3 also builds gold_ghg_breakdown_long). Add the
#    bridge BRIDGE_BUILDING_ID param cell + read-filter to the 3-cell version, NOT here.
#    This single file is readable reference only — do not paste it into Fabric as one cell.
# =============================================================================
#
# GÖREV (Purpose):
#   GHG Protokolü kapsamlarına göre bina bazlı sera gazı emisyonlarını hesapla.
#   Çıktı tablosu Power BI'da Sayfa 6 (Sustainability & Compliance) için
#   Scope 1, Scope 2 (Location & Market), Scope 3 ayrımıyla raporlama sağlar.
#
# GHG PROTOKOL TANIMI (GHG Protocol Corporate Standard):
#   Scope 1 — Doğrudan emisyonlar: bina içi yakıt yakımı
#              (doğalgaz kazanı, dizel jeneratör, soğutucu gaz kaçağı)
#   Scope 2 Location — Satın alınan elektriğin şebeke ort. emisyonu
#              (IEA / Eurostat ülke bazlı ızgara faktörü)
#   Scope 2 Market  — Satın alınan elektriğin sözleşmeli/yeşil tarifeli
#              emisyonu (yeşil enerji kontratı yoksa Location ile aynı)
#   Scope 3 — Diğer dolaylı emisyonlar: malzeme, servis, ulaşım (tahmini)
#
# VARSAYIMLAR (Assumptions) — BMAD kuralı gereği açık bildirim (WP1-5 sonrası güncel):
#   A1: Gaz CO₂ faktörü ref_fuel_factors'tan (0.201 kg/kWh, DEFRA). Hardcoded 2.04 kg/m³ kaldırıldı.
#   A2: Dizel faktörü ref_fuel_factors'tan (2.68 kg/litre, DEFRA).
#   A3: Şebeke faktörleri ref_grid_emission_factors'tan, YIL-İNDEKSLİ:
#       DE UBA resmi serisi (2024=0.363) | TR 0.442 | AT/NL/FR/PL/EU EEA-sourced.
#   A4: Scope 3 (WP4) kategori-yapılı: Cat 1 embodied = alan × RICS/LETI benchmark /
#       amortizasyon; Cat 13 leased = gerçek kiracı verisi bekliyor (0). disclosure_grade=False.
#   A5: Refrigerant Scope 1 (WP3) = silver_refrigerant_log × ref_refrigerant_gwp (IPCC GWP,
#       F-Gas logbook); tablo yoksa 0 (uydurma yok). Market-based S2 (WP2) = residual mix
#       fallback (ref_residual_mix, AIB) — location DEĞİL.
#   A6: Doğalgaz tüketimi yoksa ısıtma payı = toplam tüketimin %25'i proxy + kazan verimi %85.
#
# INPUT TABLOLAR:
#   gold_kpi_daily          — günlük elektrik tüketimi, solar üretim
#   silver_building_master  — alan, ülke, doğalgaz bayrağı, bina türü
#   ref_grid_emission_factors (statik referans, bu notebook'ta hardcode)
#
# OUTPUT TABLO:
#   gold_ghg_scope          — aylık, bina bazlı, scope bazlı emisyon tablosu
#
# KOLONLAR (gold_ghg_scope):
#   building_id             STRING NOT NULL
#   year_month              DATE NOT NULL          (ayın ilk günü: YYYY-MM-01)
#   reporting_year          INT NOT NULL
#   reporting_month         INT NOT NULL
#   scope1_gas_tco2         DOUBLE                 Doğalgaz combustion
#   scope1_diesel_tco2      DOUBLE                 Jeneratör (varsa)
#   scope1_total_tco2       DOUBLE                 = gas + diesel
#   scope2_location_tco2    DOUBLE                 Elektrik × ülke faktörü
#   scope2_market_tco2      DOUBLE                 Elektrik × sözleşme faktörü
#   scope3_estimated_tco2   DOUBLE                 Tedarik zinciri tahmini
#   total_ghg_location_tco2 DOUBLE                 Scope1 + Scope2_location + Scope3
#   total_ghg_market_tco2   DOUBLE                 Scope1 + Scope2_market + Scope3
#   emission_factor_grid    DOUBLE                 Kullanılan şebeke faktörü (kgCO2/kWh)
#   data_quality_flag       STRING                 "complete" | "estimated" | "missing_gas"
#   updated_at              TIMESTAMP
#
# DP-600 KONULARI:
#   - date_trunc + GROUP BY (aylık agregasyon)
#   - broadcast join (küçük referans tablosu)
#   - Delta MERGE UPSERT (idempotent çalışma)
#   - Z-ORDER (building_id, year_month) — Power BI filtre hızı
#   - Adaptive Query Execution (shuffle partition optimizasyonu)
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU VE IMPORT'LAR
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, when, coalesce, broadcast,
    date_trunc, to_date, year, month, dayofmonth,
    sum as spark_sum, avg as spark_avg, count,
    round as spark_round,
    current_timestamp, concat,
    add_months, last_day, trunc,
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType,
    DateType, TimestampType
)
from delta.tables import DeltaTable
import re

# DP-600: GHG tablo çıktısı küçük (bina × ay) → 8 partition yeterli
spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

print("✅ Spark konfigürasyonu tamamlandı")


# =============================================================================
# CELL 0 — PARAMETERS  (mark this cell as "Toggle parameter cell" in Fabric)
# -----------------------------------------------------------------------------
# Self-serve bridge: when the orchestrator runs this notebook for ONE freshly
# bridged building it passes BRIDGE_BUILDING_ID (the fabric_building_id, e.g.
# "B012"). The reference reads below are then filtered to that building and the
# Delta MERGE touches only its rows — every other building's gold_ghg_scope is
# left untouched. Left EMPTY (the default) the notebook runs the FULL batch
# exactly as before, so the daily pipeline is unaffected.
# =============================================================================
BRIDGE_BUILDING_ID = ""   # e.g. "B012" → single-building bridge; "" → full batch
print(f"📋 BRIDGE_BUILDING_ID = {BRIDGE_BUILDING_ID!r} "
      f"({'single-building bridge' if BRIDGE_BUILDING_ID else 'full batch'})")


# =============================================================================
# BÖLÜM 2 — KONFİGÜRASYON VE SABİTLER
# =============================================================================

# -----------------------------------------------------------------------------
# Lakehouse Tables/ prefix'ini dinamik tespit et.
# Schema-enabled lakehouse (Tables/dbo/) ve flat lakehouse (Tables/) ikisini de destekler.
# Pattern referansı: 07_consumption_forecast.py — feedback_fabric_schema_lakehouse.md
# -----------------------------------------------------------------------------
def _resolve_tables_prefix() -> tuple[str, str]:
    """
    Lakehouse'un Tables/ veya Tables/dbo/ prefix'ini catalog üzerinden tespit eder.
    Returns: (tables_prefix, lakehouse_format_label)
    """
    candidate_tables = ["gold_kpi_daily", "silver_building_master", "gold_recommendations"]
    sample_path = None
    for t in candidate_tables:
        try:
            sample_path = spark.table(t).inputFiles()[0]
            break
        except Exception:
            continue
    if not sample_path:
        raise Exception(
            "Hiçbir referans tablo (gold_kpi_daily, silver_building_master, "
            "gold_recommendations) catalog'da bulunamadı. Lakehouse attached mı? "
            "Önce 03_gold_kpi_engine veya bronze→silver pipeline'ı çalıştır."
        )

    abfss_match = re.match(r"(abfss://[^/]+@[^/]+/[^/]+)", sample_path)
    if not abfss_match:
        raise Exception(f"ABFS base extract edilemedi: {sample_path}")
    abfss_base = abfss_match.group(1)

    if "/Tables/dbo/" in sample_path:
        return (f"{abfss_base}/Tables/dbo", "schema-enabled (dbo)")
    elif "/Tables/" in sample_path:
        return (f"{abfss_base}/Tables", "flat")
    else:
        raise Exception(f"Tables prefix tanınamadı: {sample_path}")


TABLES_PREFIX, _lakehouse_format = _resolve_tables_prefix()
print(f"✅ Lakehouse formatı tespit edildi: {_lakehouse_format}")
print(f"   Tables prefix: {TABLES_PREFIX[:90]}{'...' if len(TABLES_PREFIX) > 90 else ''}")

# Tablo yolları (dinamik prefix üzerinden — schema-enabled & flat lakehouse uyumlu)
GOLD_KPI_DAILY        = f"{TABLES_PREFIX}/gold_kpi_daily"
SILVER_BUILDING       = f"{TABLES_PREFIX}/silver_building_master"
OUTPUT_TABLE          = f"{TABLES_PREFIX}/gold_ghg_scope"

# =============================================================================
# BÖLÜM 2b — Motor-içi sabit (faktörler ARTIK referans katmanından gelir — WP5 temizlik)
# -----------------------------------------------------------------------------
# Eski hardcoded GRID_EMISSION_FACTORS dict + gaz/dizel sabitleri + SCOPE3_RATIO
# KALDIRILDI (ölü koddu, çelişkili değerler taşıyordu). Artık hepsi referans katmanı:
#   şebeke   → ref_grid_emission_factors   (DE UBA 0.363/2024, diğerleri EEA)
#   gaz/dizel→ ref_fuel_factors            (gaz 0.201 kg/kWh, DEFRA)
#   residual → ref_residual_mix            (market-based fallback, AIB)
#   refrig.  → ref_refrigerant_gwp         (Scope 1 fugitive, IPCC GWP)
#   embodied → ref_embodied_carbon         (Scope 3 Cat 1, RICS/LETI)
# (hepsi BÖLÜM 3b'de yüklenir.) Burada SADECE bir motor parametresi kalır:
# =============================================================================
GAS_BOILER_EFFICIENCY = 0.85   # kazan verimi (yakıt→ısı); model parametresi, faktör değil (Varsayım A6)
print(f"✅ Motor parametresi: kazan verimi {GAS_BOILER_EFFICIENCY}. "
      f"Tüm emisyon faktörleri referans katmanından okunur (BÖLÜM 3b).")


# =============================================================================
# BÖLÜM 3 — REFERANS TABLOLARI OKU
# =============================================================================

df_kpi = spark.read.format("delta").load(GOLD_KPI_DAILY)
df_building = spark.read.format("delta").load(SILVER_BUILDING)

# --- Bridge scoping: filter sources to ONE building when BRIDGE_BUILDING_ID set.
#     fabric_building_id is platform-minted ("B0NN"), so the literal is safe. ---
if BRIDGE_BUILDING_ID:
    df_kpi = df_kpi.filter(f"building_id = '{BRIDGE_BUILDING_ID}'")
    df_building = df_building.filter(f"building_id = '{BRIDGE_BUILDING_ID}'")
    if df_building.count() == 0:
        raise ValueError(
            f"Bridge: building '{BRIDGE_BUILDING_ID}' not in silver_building_master — "
            "run 40_bridge_baseline first."
        )
    print(f"🔗 BRIDGE MODE: scoped to building_id={BRIDGE_BUILDING_ID}")

print(f"✅ gold_kpi_daily: {df_kpi.count():,} satır okundu")
print(f"✅ silver_building_master: {df_building.count()} satır okundu")

# silver_building_master'dan ihtiyaç duyulan kolonlar
# Beklenen kolonlar:
#   building_id, country_code, building_type,
#   conditioned_area_m2, has_gas_heating, has_diesel_generator
# =============================================================================
# KOLON UYUMLULUK KATMANI
# silver_building_master şeması versiyona göre farklı kolonlar içerebilir.
# Bu blok mevcut kolonları kontrol edip eksikleri proxy ile türetir.
# =============================================================================

_avail = set(df_building.columns)

# has_gas_heating: doğrudan varsa kullan; yoksa proxy:
#   geleneksel HVAC (has_hvac_traditional=True) VE ısı pompası yoksa (has_heat_pump=False)
#   → büyük olasılıkla gaz kazan veya fuel-oil ısıtma var (Avrupa bina stoku varsayımı)
if "has_gas_heating" in _avail:
    _gas_expr = col("has_gas_heating").cast("boolean")
else:
    _gas_expr = (
        coalesce(col("has_hvac_traditional"), lit(False)).cast("boolean") &
        ~coalesce(col("has_heat_pump"), lit(False)).cast("boolean")
    )
    print("⚠️  has_gas_heating kolonu yok → has_hvac_traditional & !has_heat_pump proxy kullanılıyor")

# has_diesel_generator: varsa kullan; yoksa False (şema güncellenince kaldırılır)
if "has_diesel_generator" in _avail:
    _diesel_expr = col("has_diesel_generator").cast("boolean")
else:
    _diesel_expr = lit(False)
    print("⚠️  has_diesel_generator kolonu yok → False sabit değeri kullanılıyor (Scope 1 etki: minimal)")

df_building_slim = df_building.select(
    "building_id",
    col("country_code").alias("country_code"),
    col("conditioned_area_m2").alias("area_m2"),
    _gas_expr.alias("has_gas"),
    _diesel_expr.alias("has_diesel"),
    # audit D2: market-based Scope 2 için sözleşme (supplier) faktörü — varsa kullan
    (col("green_supplier_ef_kg_kwh") if "green_supplier_ef_kg_kwh" in _avail
     else lit(None).cast("double")).alias("supplier_ef"),
    # WP4: Scope 3 Cat 1 (embodied) için bina tipi; Cat 13 için kiraya verilen alan (varsa)
    (col("building_type") if "building_type" in _avail
     else lit("DEFAULT")).alias("building_type"),
    (col("leased_area_m2") if "leased_area_m2" in _avail
     else lit(None).cast("double")).alias("leased_area_m2"),
).distinct()

print(f"✅ Bina master proxy katmanı uygulandı: {df_building_slim.count()} bina")

# =============================================================================
# BÖLÜM 3b — REFERANS KATMANI (tek-doğru-kaynak — audit A1/A2/F2 fix)
# -----------------------------------------------------------------------------
# Hardcoded GRID_EMISSION_FACTORS dict + gaz/dizel sabitleri ARTIK kullanılmıyor.
# Değerler ref_grid_emission_factors / ref_fuel_factors tablolarından gelir
# (03_ref_factors_tariffs_loader.py önce çalışmalı). Böylece TR faktörü 0.442
# tek kanonik değer olarak HER sayfaya akar — 0.430/0.450 çeşitlemesi biter.
# =============================================================================
df_ref_grid = (
    spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_grid_emission_factors")
    .select(
        col("country_code").alias("ref_country"),
        col("year").alias("ref_year"),
        col("emission_factor_kg_kwh").alias("ref_ef"),
    )
)
_eu_rows = (df_ref_grid.filter(col("ref_country") == "EU")
            .orderBy(col("ref_year").desc()).limit(1).collect())
EU_EF_FALLBACK = float(_eu_rows[0]["ref_ef"]) if _eu_rows else 0.23

_fuel = {r["factor_key"]: r["value"]
         for r in spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_fuel_factors").collect()}
GAS_EF_KG_PER_KWH      = _fuel.get("natural_gas_kg_per_kwh", 0.201)
DIESEL_EF_KG_PER_LITRE = _fuel.get("diesel_kg_per_litre", 2.68)
print(f"✅ Referans katmanı yüklendi: ref_grid {df_ref_grid.count()} satır, "
      f"gaz {GAS_EF_KG_PER_KWH} kg/kWh, EU fallback {EU_EF_FALLBACK}")

# -----------------------------------------------------------------------------
# WP2: ref_residual_mix — market-based Scope 2 no-instrument fallback (AIB).
# GHG Protocol Scope 2 Guidance: sözleşmeli enstrüman (GoO) YOKSA market-based,
# location ortalaması DEĞİL, RESIDUAL MIX faktörüyle hesaplanır. Tablo yoksa
# (03 WP1 henüz koşmadıysa) zarifçe location'a düşülür — sessiz hata yok.
# -----------------------------------------------------------------------------
try:
    df_ref_residual = (
        spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_residual_mix")
        .select(
            col("country_code").alias("res_country"),
            col("year").alias("res_year"),
            col("residual_mix_kg_kwh").alias("res_ef"),
        )
    )
    _has_residual = True
    print(f"✅ ref_residual_mix yüklendi: {df_ref_residual.count()} satır (market-based fallback)")
except Exception as _res_ex:
    df_ref_residual = None
    _has_residual = False
    print(f"ℹ️  ref_residual_mix yok ({type(_res_ex).__name__}) → market-based location'a düşer. "
          f"Önce 03_ref_factors_tariffs_loader (WP1) çalıştır.")

# -----------------------------------------------------------------------------
# WP3: Refrigerant Scope 1 (fugitive) prep.
# silver_refrigerant_log BEKLENEN ŞEMA (pilot F-Gas logbook'tan doldurulacak —
# EU 2024/573 zorunlu kılıyor):
#     building_id  STRING
#     event_date   DATE        (servis/dolum tarihi)
#     refrigerant  STRING      (ör. "R-410A", "R-32")
#     topup_kg     DOUBLE      (eklenen = sızan miktar)
# Fugitive tCO2e = topup_kg × GWP-100 / 1000  (ref_refrigerant_gwp'den).
# Tablo yoksa refrigerant Scope 1 = 0 (uydurmuyoruz — sadece yapı hazır).
# -----------------------------------------------------------------------------
try:
    df_refrig_log = spark.read.format("delta").load(f"{TABLES_PREFIX}/silver_refrigerant_log")
    df_gwp_ref = (
        spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_refrigerant_gwp")
        .select(col("refrigerant").alias("gwp_refrigerant"), col("gwp_100"))
    )
    df_refrig_monthly = (
        df_refrig_log
        .withColumn("year_month", date_trunc("month", col("event_date")).cast(DateType()))
        .join(broadcast(df_gwp_ref), col("refrigerant") == col("gwp_refrigerant"), "left")
        .withColumn(
            "refrig_tco2",
            spark_round(col("topup_kg") * coalesce(col("gwp_100"), lit(0.0)) / 1000, 4),
        )
        .groupBy("building_id", "year_month")
        .agg(spark_sum("refrig_tco2").alias("scope1_refrigerant_tco2"))
    )
    _has_refrig = True
    print(f"✅ silver_refrigerant_log işlendi: {df_refrig_monthly.count()} bina-ay (refrigerant Scope 1)")
except Exception as _refrig_ex:
    df_refrig_monthly = None
    _has_refrig = False
    print(f"ℹ️  silver_refrigerant_log yok ({type(_refrig_ex).__name__}) → refrigerant Scope 1 = 0. "
          f"Pilot F-Gas logbook gelince doldur (building_id, event_date, refrigerant, topup_kg).")

# -----------------------------------------------------------------------------
# WP4: ref_embodied_carbon — Scope 3 Cat 1 (gömülü karbon) benchmark.
# bina tipi → kgCO2e/m² (upfront A1-A5) + amortizasyon yılı. Tablo yoksa default'a düşer.
# -----------------------------------------------------------------------------
try:
    df_embodied = (
        spark.read.format("delta").load(f"{TABLES_PREFIX}/ref_embodied_carbon")
        .select(
            col("building_type").alias("emb_type"),
            col("embodied_kgco2e_m2"),
            col("amortization_years"),
        )
    )
    _has_embodied = True
    print(f"✅ ref_embodied_carbon yüklendi: {df_embodied.count()} bina tipi (Scope 3 Cat 1)")
except Exception as _emb_ex:
    df_embodied = None
    _has_embodied = False
    print(f"ℹ️  ref_embodied_carbon yok ({type(_emb_ex).__name__}) → Cat 1 default benchmark (700 kgCO2e/m²).")


# =============================================================================
# BÖLÜM 4 — AYLIK ELEKTRİK TÜKETİMİ HESAPLA (Scope 2 tabanı)
# =============================================================================

# DP-600: date_trunc → aylık granülarite
df_monthly = df_kpi.withColumn(
    "year_month", date_trunc("month", col("date")).cast(DateType())
).groupBy("building_id", "year_month").agg(
    spark_sum("total_consumption_kwh").alias("monthly_consumption_kwh"),
    spark_sum("net_grid_consumption_kwh").alias("monthly_grid_kwh"),
    spark_sum("co2_emissions_kg").alias("existing_co2_kg"),   # mevcut hesaplanan değer (referans)
).withColumn("reporting_year",  year(col("year_month"))) \
 .withColumn("reporting_month", month(col("year_month")))

print(f"✅ Aylık KPI agregasyonu: {df_monthly.count()} satır")


# =============================================================================
# BÖLÜM 5 — BİNA BİLGİSİ İLE BİRLEŞTİR
# =============================================================================

# DP-600: building_master küçük tablo → broadcast join
df_joined = df_monthly.join(
    broadcast(df_building_slim),
    on="building_id",
    how="left"
)

# audit A1/A2 fix: yıl-indeksli ref_grid_emission_factors JOIN (hardcoded dict yerine).
# (country_code, reporting_year) → ref_ef. Eşleşme yoksa EU son-yıl fallback.
# DP-600: küçük referans tablosu → broadcast join, shuffle yok.
df_with_ef = (
    df_joined
    .join(
        broadcast(df_ref_grid),
        (col("country_code") == col("ref_country")) & (col("reporting_year") == col("ref_year")),
        "left",
    )
    .withColumn("emission_factor_grid", coalesce(col("ref_ef"), lit(EU_EF_FALLBACK)))
    .withColumn(
        "emission_factor_source",
        when(col("ref_ef").isNotNull(), lit("ref_grid_emission_factors"))
        .otherwise(lit("EU_fallback")),
    )
    .drop("ref_country", "ref_year", "ref_ef")
)

# WP2: residual mix JOIN (country_code, reporting_year) → res_ef.
# Eşleşme yoksa (AT/NL full-disclosure, TR not-in-AIB, veya tablo yok) res_ef = NULL
# → market-based location'a düşer (doğru davranış).
if _has_residual:
    df_with_ef = (
        df_with_ef
        .join(
            broadcast(df_ref_residual),
            (col("country_code") == col("res_country")) & (col("reporting_year") == col("res_year")),
            "left",
        )
        .drop("res_country", "res_year")
    )
else:
    df_with_ef = df_with_ef.withColumn("res_ef", lit(None).cast("double"))

# WP3: refrigerant Scope 1 JOIN (building_id, year_month). Yoksa 0.
if _has_refrig:
    df_with_ef = df_with_ef.join(df_refrig_monthly, on=["building_id", "year_month"], how="left")
else:
    df_with_ef = df_with_ef.withColumn("scope1_refrigerant_tco2", lit(None).cast("double"))
df_with_ef = df_with_ef.withColumn(
    "scope1_refrigerant_tco2", coalesce(col("scope1_refrigerant_tco2"), lit(0.0))
)

# WP4: embodied benchmark JOIN (building_type). Eşleşme yoksa calc'ta default'a düşer.
if _has_embodied:
    df_with_ef = (
        df_with_ef
        .join(broadcast(df_embodied), col("building_type") == col("emb_type"), "left")
        .drop("emb_type")
    )
else:
    df_with_ef = (
        df_with_ef
        .withColumn("embodied_kgco2e_m2", lit(None).cast("double"))
        .withColumn("amortization_years", lit(None).cast("int"))
    )


# =============================================================================
# BÖLÜM 6 — SCOPE HESAPLAMALARI
# =============================================================================

df_scoped = df_with_ef.withColumn(
    # -----------------------------------------------------------------
    # SCOPE 1 — Doğalgaz yakımı
    # Varsayım A6: doğalgaz tüketimi mevcut değil →
    # heating_energy = toplam tüketimin %25'i (iklimsel ortalama)
    # Sonra m³'e çevir: kWh / 10.55 (doğalgazın ısıl değeri) / verimlilik
    # Gerçek veri varsa: silver_gas_meter[monthly_m3] tablosunu kullan
    # -----------------------------------------------------------------
    "scope1_gas_tco2",
    when(
        col("has_gas").cast("boolean"),
        # audit F2 fix: TEK kanonik gaz faktörü (ref_fuel_factors, kg CO2/kWh).
        # heat_kwh = tüketim×0.25 (ısıtma payı proxy, A6); fuel_kwh = heat/verim.
        # m³ ara dönüşümü kaldırıldı → compliance (05) ile aynı baz, sayfa-arası tutarlı.
        spark_round(
            col("monthly_consumption_kwh") * 0.25      # ısıtma payı tahmini (A6)
            / GAS_BOILER_EFFICIENCY                     # kazan verimi → yakıt girdisi
            * lit(GAS_EF_KG_PER_KWH)                    # kg CO2/kWh (ref_fuel_factors)
            / 1000,                                     # kg → tonne
            4
        )
    ).otherwise(lit(0.0))
).withColumn(
    # Scope 1 — Dizel jeneratör (küçük katkı, has_diesel varsa)
    "scope1_diesel_tco2",
    when(
        col("has_diesel").cast("boolean"),
        # Bekleme modu: toplam tüketimin %1'i dizel kabul (seçim kesintisi)
        spark_round(
            col("monthly_consumption_kwh") * 0.01
            / 10.0          # kWh/litre dizel yaklaşık ısıl değeri
            * DIESEL_EF_KG_PER_LITRE
            / 1000,
            4
        )
    ).otherwise(lit(0.0))
).withColumn(
    # WP3: Scope 1 toplam artık refrigerant fugitive'i de içerir
    # (gaz + dizel + soğutucu gaz kaçağı). Pilot logbook'u yoksa refrigerant=0.
    "scope1_total_tco2",
    spark_round(
        col("scope1_gas_tco2") + col("scope1_diesel_tco2") + col("scope1_refrigerant_tco2"),
        4,
    )

).withColumn(
    # -----------------------------------------------------------------
    # SCOPE 2 — Location-based (şebeke ort. faktörü)
    # Formül: net şebeke tüketimi × şebeke emisyon faktörü
    # -----------------------------------------------------------------
    "scope2_location_tco2",
    spark_round(
        coalesce(col("monthly_grid_kwh"), col("monthly_consumption_kwh"))
        * col("emission_factor_grid")
        / 1000,   # kg → tonne
        4
    )
).withColumn(
    # WP2: market-based Scope 2 — GHG Protocol Scope 2 Guidance faktör hiyerarşisi:
    #   1) supplier_ef   — sözleşmeli enstrüman (GoO/PPA/yeşil tarife), en spesifik
    #   2) res_ef        — residual mix (enstrüman YOKSA; location DEĞİL, çünkü GoO'lar
    #                      yeşil nitelikleri çekince kalan miks daha kirlidir — AIB)
    #   3) location      — residual da yoksa (AT/NL full-disclosure veya tablo yok)
    # Böylece location ile market GERÇEKTEN ayrışır (ESRS E1-6 çift-metot disclosure).
    "scope2_market_tco2",
    spark_round(
        coalesce(col("monthly_grid_kwh"), col("monthly_consumption_kwh"))
        * coalesce(col("supplier_ef"), col("res_ef"), col("emission_factor_grid"))
        / 1000,
        4,
    )
).withColumn(
    "scope2_market_factor",
    coalesce(col("supplier_ef"), col("res_ef"), col("emission_factor_grid"))
).withColumn(
    "scope2_method",
    when(col("supplier_ef").isNotNull(), lit("market_based_contract"))
    .when(col("res_ef").isNotNull(), lit("residual_mix_no_instrument"))
    .otherwise(lit("location_fallback_full_disclosure"))

).withColumn(
    # -----------------------------------------------------------------
    # WP4: SCOPE 3 — kategori-yapılı (eski düz %8 yerine), ESRS-E1 eşlenebilir.
    # Cat 1 (embodied/upfront): AYLIK = alan × kgCO2e/m² / amortizasyon / 12 / 1000.
    # Benchmark tahmini (RICS/LETI) → disclosure_grade=False. Default 700 / 60 yıl.
    # -----------------------------------------------------------------
    "scope3_cat1_embodied_tco2",
    spark_round(
        coalesce(col("area_m2"), lit(0.0))
        * coalesce(col("embodied_kgco2e_m2"), lit(700.0))
        / coalesce(col("amortization_years"), lit(60))
        / 12.0 / 1000.0,
        4,
    )
).withColumn(
    # Cat 13 (downstream leased — kiracı enerjisi): GERÇEK kiracı verisi gelene kadar 0.
    # Uydurmuyoruz; leased_area_m2 + tenant tüketimi gelince alan-oranlı tahmin eklenir.
    "scope3_cat13_leased_tco2",
    lit(0.0)
).withColumn(
    # Scope 3 toplam = Cat 1 + Cat 13 (hâlâ TARAMA/tahmin → disclosure_grade=False)
    "scope3_estimated_tco2",
    spark_round(col("scope3_cat1_embodied_tco2") + col("scope3_cat13_leased_tco2"), 4)

).withColumn(
    "total_ghg_location_tco2",
    spark_round(
        col("scope1_total_tco2")
        + col("scope2_location_tco2")
        + col("scope3_estimated_tco2"),
        4
    )
).withColumn(
    "total_ghg_market_tco2",
    spark_round(
        col("scope1_total_tco2")
        + col("scope2_market_tco2")
        + col("scope3_estimated_tco2"),
        4
    )
).withColumn(
    # WP4: Scope 3 artık kategori-yapılı ama hâlâ TAHMİN (Cat 1 benchmark, Cat 13 bekliyor).
    # ESRS-disclosure-grade DEĞİL → görsel "estimated, not disclosure-grade" etiketi taşır.
    "scope3_method", lit("cat1_embodied_benchmark+cat13_leased_pending")
).withColumn(
    "scope3_disclosure_grade", lit(False)
).withColumn(
    # Veri kalitesi bayrağı
    "data_quality_flag",
    when(
        col("has_gas").cast("boolean") & col("monthly_grid_kwh").isNotNull(),
        lit("complete")
    ).when(
        col("has_gas").cast("boolean") & col("monthly_grid_kwh").isNull(),
        lit("estimated")
    ).otherwise(
        lit("missing_gas")   # has_gas=False → Scope 1 hesabı yapılmadı
    )
).withColumn("updated_at", current_timestamp())

print("✅ Scope 1 / 2 / 3 hesaplamaları tamamlandı")


# =============================================================================
# BÖLÜM 7 — ÇIKTI TABLOSUNU HAZIRLA
# =============================================================================

FINAL_COLS = [
    "building_id",
    "year_month",
    "reporting_year",
    "reporting_month",
    "scope1_gas_tco2",
    "scope1_diesel_tco2",
    "scope1_refrigerant_tco2",   # WP3
    "scope1_total_tco2",
    "scope2_location_tco2",
    "scope2_market_tco2",
    "scope2_market_factor",      # WP2
    "scope2_method",
    "scope3_cat1_embodied_tco2", # WP4
    "scope3_cat13_leased_tco2",  # WP4
    "scope3_estimated_tco2",
    "scope3_method",
    "scope3_disclosure_grade",
    "total_ghg_location_tco2",
    "total_ghg_market_tco2",
    "emission_factor_grid",
    "emission_factor_source",
    "data_quality_flag",
    "updated_at",
]

df_final = df_scoped.select(FINAL_COLS)

# Doğrulama
print("\n📊 Çıktı özeti (portföy toplamı):")
df_final.agg(
    spark_sum("scope1_total_tco2").alias("Scope1_tCO2"),
    spark_sum("scope2_location_tco2").alias("Scope2_Location_tCO2"),
    spark_sum("scope3_estimated_tco2").alias("Scope3_tCO2"),
    spark_sum("total_ghg_location_tco2").alias("Total_GHG_tCO2"),
).show()

print("\n📋 Veri kalitesi dağılımı:")
df_final.groupBy("data_quality_flag").count().show()


# =============================================================================
# BÖLÜM 8 — DELTA MERGE UPSERT (idempotent)
# =============================================================================

# DP-600: MERGE → yeniden çalıştırıldığında duplicate oluşturmaz
try:
    gold_table = DeltaTable.forPath(spark, OUTPUT_TABLE)

    gold_table.alias("tgt").merge(
        df_final.alias("src"),
        "tgt.building_id = src.building_id AND tgt.year_month = src.year_month"
    ).whenMatchedUpdateAll() \
     .whenNotMatchedInsertAll() \
     .execute()

    print(f"✅ Delta MERGE tamamlandı: {OUTPUT_TABLE}")

except Exception as _merge_ex:
    # Beklenen durum: tablo henüz yok (AnalysisException / DeltaTableNotFoundException).
    # Beklenmeyen durum: schema mismatch, permission, vb. → log'da görünür kalsın.
    # (feedback_fabric_notebooks.md: silent except yasak)
    _ex_type = type(_merge_ex).__name__
    _ex_msg  = str(_merge_ex)[:200]
    print(f"ℹ️  MERGE atlandı ({_ex_type}): {_ex_msg}")
    print("   Tablo ilk kez oluşturuluyor (saveAsTable fallback)...")

    # saveAsTable: hem Tables/ klasörüne yazar hem Lakehouse kataloğuna kaydeder.
    # Path'in son segmentini al — abfss://.../Tables/[dbo/]gold_ghg_scope → "gold_ghg_scope"
    # Schema-enabled lakehouse'ta default schema "dbo" olduğu için saveAsTable("gold_ghg_scope")
    # otomatik dbo.gold_ghg_scope olarak yazılır.
    _tbl_name_init = OUTPUT_TABLE.rstrip("/").split("/")[-1]
    df_final.write \
        .format("delta") \
        .partitionBy("reporting_year") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(_tbl_name_init)

    print(f"✅ Delta tablo ilk kez oluşturuldu ve kataloğa kaydedildi: {_tbl_name_init}")


# =============================================================================
# BÖLÜM 9 — Z-ORDER OPTIMIZE (DP-600)
# =============================================================================

# OPTIMIZE — tablo yeni oluştuysa veya ABFS commit henüz finalize olmadıysa
# fail edebilir. Aynı koruma occupancy notebook'unda da gerekti.
# (memory: occupancy_notebook_bug.md)
try:
    spark.sql(f"""
        OPTIMIZE delta.`{OUTPUT_TABLE}`
        ZORDER BY (building_id, year_month)
    """)
    print("✅ Z-ORDER OPTIMIZE tamamlandı")
except Exception as _opt_ex:
    print(f"⚠️  OPTIMIZE atlandı (tablo yeni oluştuysa normal): {type(_opt_ex).__name__}: {str(_opt_ex)[:120]}")
    print("   Bir sonraki çalıştırmada otomatik OPTIMIZE olur.")


# =============================================================================
# BÖLÜM 9b — LAKEHOUSE KATALOG SYNC (Direct Lake için)
# =============================================================================
# Fabric'te CREATE TABLE ... LOCATION relative path KABUL ETMEZ (absolute ABFS lazım).
# Bunun yerine: tablo katalogda varsa cache'i temizle, yoksa Fabric otomatik keşfeder.

# Path'in son segmentini al — dinamik prefix (abfss://.../Tables/[dbo/]gold_ghg_scope) ile uyumlu
_tbl_name = OUTPUT_TABLE.rstrip("/").split("/")[-1]

try:
    spark.catalog.refreshTable(_tbl_name)
    print(f"✅ Katalog cache temizlendi: {_tbl_name}")
except Exception as _ex:
    print(f"ℹ️  '{_tbl_name}' katalogda henüz yok — Fabric otomatik keşfeder (1-2 dk beklenir)")
    print(f"   Semantic model hata verirse: Lakehouse → Tables → ⟳ Refresh → Model → Refresh now")


# =============================================================================
# BÖLÜM 10 — SON DOĞRULAMA
# =============================================================================

df_check = spark.read.format("delta").load(OUTPUT_TABLE)

print(f"\n📊 gold_ghg_scope istatistikleri:")
print(f"   Toplam satır        : {df_check.count():,}")
print(f"   Benzersiz bina      : {df_check.select('building_id').distinct().count()}")
print(f"   Yıl aralığı        : {df_check.agg({'reporting_year': 'min'}).collect()[0][0]} – {df_check.agg({'reporting_year': 'max'}).collect()[0][0]}")

df_check.agg(
    spark_sum("total_ghg_location_tco2").alias("Toplam_GHG_tCO2")
).show()

print("""
📋 SONRAKI ADIMLAR:
   1. Power BI Semantic Model'e gold_ghg_scope tablosunu ekle
   2. building_id üzerinden silver_building_master ile ilişki kur
   3. year_month üzerinden Date tablosuyla ilişki kur
   4. 12_dax_v7_ghg_crrem.dax dosyasındaki ölçüleri ekle
   5. Scope 3 verisini gelecekte silver_scope3_inventory tablosuyla güçlendir
   6. Faktörler artık ref_grid_emission_factors / ref_fuel_factors'tan gelir (audit A1/A2/F2 fix)
""")
