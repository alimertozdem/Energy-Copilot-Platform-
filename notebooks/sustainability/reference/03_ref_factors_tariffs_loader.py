# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 03_ref_factors_tariffs_loader.py
# Layer: REFERENCE — Single Source of Truth for Factors, Tariffs & Fuels
# Created: 2026-05-30  (audit fix: A1, A2, A3, F2, F3, H1, I2)
# =============================================================================
#
# GÖREV (Purpose):
#   Tüm motorların (KPI, GHG, compliance, recommendation, battery) okuduğu
#   TEK kanonik referans tablolarını üretir. Daha önce her notebook kendi
#   hardcoded sabitini taşıyordu → aynı ülke için 3-4 farklı emisyon faktörü /
#   elektrik fiyatı dolaşıyordu (TR: 0.430 / 0.442 / 0.450). Bu loader o
#   tutarsızlığı kökten kaldırır.
#
#   ÇIKTI TABLOLARI:
#     ref_grid_emission_factors  — ülke × YIL bazlı şebeke CO₂ faktörü
#     ref_electricity_tariffs    — ülke × yıl: peak/mid/offpeak/demand/feed-in
#     ref_fuel_factors           — yakıt CO₂ faktörleri + EU ETS karbon fiyatı
#
# MİMARİ KARAR — Neden YIL-İNDEKSLİ faktör?
#   Bir binanın 2023 Scope 2 emisyonu, 2023 şebeke faktörüyle hesaplanmalı;
#   2024'ü 2024 faktörüyle. Tek düz faktör kullanılırsa yıl-bazlı karbon trendi
#   "şebeke temizlendi" ile "bina iyileşti"yi birbirine karıştırır.
#   CRREM stranding ve CSRD/ESRS E1-6 raporlama YILINA göre raporlar →
#   denetçi faktörün yılla eşleşmesini bekler. Saklamak aynı maliyet,
#   denetim itirazını ortadan kaldırır.
#
# MİMARİ KARAR — Neden ayrı 'ref_' tablolar (silver/gold değil)?
#   Bu veriler ölçüm değil, dış otoritelerin yayınladığı statik referanslar
#   (UBA, IEA, Eurostat, DEFRA). Yılda ~1 güncellenir. Her satır KAYNAK + URL +
#   güncelleme tarihi taşır → "row-level lineage from raw factor to disclosed
#   kg CO₂" satış vaadini gerçek kılar. 05_compliance / 06_recommendation zaten
#   'ref_' konvansiyonunu kullanıyor (ref_building_type_profiles vb.).
#
# KAYNAKLAR (2026-05-30 doğrulandı):
#   DE grid : Umweltbundesamt (UBA) — "CO₂-Emissionen pro kWh Strom"
#             2022=433, 2023=386, 2024=363 g/kWh
#   TR grid : TEİAŞ — 0.442 kg/kWh (product owner onayı 2026-05-30)
#   AT/NL/FR/PL/EU : IEA Emissions Factors 2025 (build placeholder — yıllık teyit)
#   Tarife  : Eurostat non-household (nrg_pc_205) + ülke ToU yapısı
#   Yakıt   : DEFRA 2023 / IPCC
#   ETS     : EU ETS spot (2024 aralığı €60–80/t)
#
# DP-600 KONULARI:
#   - Statik referans → basit overwrite + saveAsTable (path değil, catalog adı)
#     (CRREM loader'daki hardcoded "Tables/" hatası burada tekrarlanmadı)
#   - Küçük tablolar → downstream notebook'lar broadcast eder
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType, DateType,
)
from datetime import date

spark = SparkSession.builder.getOrCreate()
spark.conf.set("spark.sql.shuffle.partitions", "8")

_TODAY = date.today().isoformat()
print("✅ Reference loader başlatıldı")


# =============================================================================
# BÖLÜM 1 — ref_grid_emission_factors  (ülke × YIL)
# =============================================================================
# Birim: kg CO₂ / kWh (location-based, üretim bazlı şebeke ortalaması)
# (ülke, yıl, faktör, kaynak, url, güncelleme)
#
# NOT: DE bir GERÇEK zaman serisidir (UBA yıllık yayını). TR için ulusal seri
# elimizde olmadığından 0.442 son yıllara uygulanır (data_confidence='national_single').
# AT/NL/FR/PL/EU IEA-bazlı placeholder'dır → 'verify_iea_2025' bayrağı taşır.
# =============================================================================

GRID_SCHEMA = StructType([
    StructField("country_code",          StringType(),  False),
    StructField("year",                  IntegerType(), False),
    StructField("emission_factor_kg_kwh", DoubleType(), False),
    StructField("source",                StringType(),  True),
    StructField("source_url",            StringType(),  True),
    StructField("data_confidence",       StringType(),  True),  # official_series | national_single | verify_iea_2025
    StructField("last_updated",          StringType(),  True),
])

_UBA = "Umweltbundesamt (UBA) — CO₂-Emissionen pro kWh Strom"
_UBA_URL = "https://www.umweltbundesamt.de/themen/co2-emissionen-pro-kilowattstunde-strom-2024"
_IEA = "IEA Emissions Factors 2025"
_IEA_URL = "https://www.iea.org/data-and-statistics/data-product/emissions-factors-2025"
_TEIAS = "TEİAŞ (Türkiye Elektrik İletim A.Ş.)"
# EEA — free, official per-country electricity carbon intensity (replaces IEA placeholders)
_EEA = "EEA — GHG emission intensity of electricity generation (country level)"
_EEA_URL = "https://www.eea.europa.eu/en/analysis/indicators/greenhouse-gas-emission-intensity-of-1"

grid_rows = [
    # Germany — official UBA annual series (consumption-based, incl. imports & T&D)
    ("DE", 2022, 0.433, _UBA, _UBA_URL, "official_series", _TODAY),
    ("DE", 2023, 0.386, _UBA, _UBA_URL, "official_series", _TODAY),
    ("DE", 2024, 0.363, _UBA, _UBA_URL, "official_series", _TODAY),
    ("DE", 2025, 0.363, _UBA, _UBA_URL, "official_series_carryforward", _TODAY),  # 2025 final yayımlanana kadar 2024 taşınır
    # Turkey — single national value (product-owner approved 2026-05-30; not in EEA/AIB scope)
    ("TR", 2023, 0.442, _TEIAS, "", "national_single", _TODAY),
    ("TR", 2024, 0.442, _TEIAS, "", "national_single", _TODAY),
    ("TR", 2025, 0.442, _TEIAS, "", "national_single", _TODAY),
    # Other Europe — EEA "GHG emission intensity of electricity generation" (free, official).
    # Web-verified EEA 2023 values (2026-06-08); carried forward until EEA publishes 2024.
    # FR/PL/EU exact; AT/NL approximate (hydro/gas) → confirm the exact EEA cell.
    ("FR", 2024, 0.056, _EEA, _EEA_URL, "eea_2023_basis", _TODAY),   # nuclear/hydro dominant
    ("PL", 2024, 0.662, _EEA, _EEA_URL, "eea_2023_basis", _TODAY),   # coal dominant
    ("EU", 2024, 0.242, _EEA, _EEA_URL, "eea_2023_basis", _TODAY),   # EU-27 average
    ("AT", 2024, 0.158, _EEA, _EEA_URL, "eea_verify",     _TODAY),   # hydro dominant (confirm exact)
    ("NL", 2024, 0.290, _EEA, _EEA_URL, "eea_verify",     _TODAY),   # gas dominant (confirm exact)
]

df_grid = spark.createDataFrame(grid_rows, schema=GRID_SCHEMA)
df_grid.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ref_grid_emission_factors")
print(f"✅ ref_grid_emission_factors yazıldı: {df_grid.count()} satır")
df_grid.orderBy("country_code", "year").show(truncate=False)


# =============================================================================
# BÖLÜM 2 — ref_electricity_tariffs  (ülke × yıl)
# =============================================================================
# Birim: €/kWh (non-household, vergi-hariç). avg = Eurostat blended; ToU peak/mid/
# offpeak ülke yapısı; demand €/kW/ay; feed_in €/kWh (PV ihracı).
# Kaynak: Eurostat nrg_pc_205 (blended) + ülke ToU yapısı (battery nb 12 ile birleştirildi)
# =============================================================================

TARIFF_SCHEMA = StructType([
    StructField("country_code",            StringType(), False),
    StructField("year",                    IntegerType(), False),
    StructField("avg_eur_kwh",             DoubleType(), True),   # Eurostat blended non-household
    StructField("peak_eur_kwh",            DoubleType(), True),
    StructField("mid_eur_kwh",             DoubleType(), True),
    StructField("offpeak_eur_kwh",         DoubleType(), True),
    StructField("demand_charge_eur_kw_month", DoubleType(), True),
    StructField("feed_in_eur_kwh",         DoubleType(), True),
    StructField("source",                  StringType(), True),
    StructField("source_url",              StringType(), True),
    StructField("last_updated",            StringType(), True),
])

_EUROSTAT = "Eurostat nrg_pc_205 (non-household, ex-recoverable tax) + country ToU structure"
_EUROSTAT_URL = "https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205/default/table"

tariff_rows = [
    # country, year, avg, peak, mid, offpeak, demand, feed_in
    ("DE", 2025, 0.226, 0.285, 0.182, 0.062, 13.50, 0.082, _EUROSTAT, _EUROSTAT_URL, _TODAY),
    ("AT", 2025, 0.190, 0.248, 0.165, 0.055, 11.20, 0.075, _EUROSTAT, _EUROSTAT_URL, _TODAY),
    ("NL", 2025, 0.205, 0.302, 0.195, 0.071, 14.80, 0.095, _EUROSTAT, _EUROSTAT_URL, _TODAY),
    ("TR", 2025, 0.085, 0.120, 0.085, 0.040,  8.50, 0.045, "EPDK / EXIST (approx)", "", _TODAY),
    ("EU", 2025, 0.190, 0.255, 0.170, 0.060, 12.50, 0.080, _EUROSTAT, _EUROSTAT_URL, _TODAY),
]

df_tariff = spark.createDataFrame(tariff_rows, schema=TARIFF_SCHEMA)
df_tariff.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ref_electricity_tariffs")
print(f"✅ ref_electricity_tariffs yazıldı: {df_tariff.count()} satır")
df_tariff.orderBy("country_code").show(truncate=False)


# =============================================================================
# BÖLÜM 3 — ref_fuel_factors  (yakıt CO₂ faktörleri + EU ETS karbon fiyatı)
# =============================================================================
# Doğalgaz TEK baz: kg CO₂/kWh. m³ gereken yerde 10.55 kWh/m³ ile türetilir
# (09_ghg_scope'taki 2.04 kg/m³ ≈ 0.201 × 10.55 ile uyumlu). Böylece gaz karbonu
# her sayfada AYNI çıkar (audit F2 fix).
# =============================================================================

FUEL_SCHEMA = StructType([
    StructField("factor_key",   StringType(), False),
    StructField("value",        DoubleType(), False),
    StructField("unit",         StringType(), True),
    StructField("basis",        StringType(), True),   # HHV / LHV / n.a.
    StructField("source",       StringType(), True),
    StructField("source_url",   StringType(), True),
    StructField("last_updated", StringType(), True),
])

_DEFRA = "DEFRA 2023 GHG conversion factors"
_DEFRA_URL = "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023"

fuel_rows = [
    ("natural_gas_kg_per_kwh",  0.201, "kg CO2/kWh", "HHV", _DEFRA, _DEFRA_URL, _TODAY),
    ("natural_gas_kwh_per_m3", 10.55, "kWh/m3",     "n.a.", "IPCC / typical EU NG", "", _TODAY),
    ("diesel_kg_per_litre",     2.68,  "kg CO2/L",   "n.a.", _DEFRA, _DEFRA_URL, _TODAY),
    ("eu_ets_price_eur_per_t",  70.0,  "EUR/tCO2",   "n.a.", "EU ETS spot (2024 range 60-80)", "", _TODAY),
]

df_fuel = spark.createDataFrame(fuel_rows, schema=FUEL_SCHEMA)
df_fuel.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ref_fuel_factors")
print(f"✅ ref_fuel_factors yazıldı: {df_fuel.count()} satır")
df_fuel.show(truncate=False)


# =============================================================================
# BÖLÜM 4 — ref_residual_mix  (market-based Scope 2 — no-instrument fallback)
# =============================================================================
# GHG Protocol Scope 2 Guidance: bir tüketicinin sözleşmeli enstrümanı (GoO/PPA)
# YOKSA, market-based emisyon LOCATION ortalamasıyla DEĞİL, RESIDUAL MIX faktörüyle
# hesaplanmalı — çünkü yeşil nitelikler GoO olarak satıldığında kalan ("residual")
# miks daha kirlidir. Örn: DE 2024 residual mix = 0.725 kg/kWh, location = 0.363
# → ~2× fark. 09_ghg_scope bu tabloyu enstrümansız binalar için kullanır.
#
# Kaynak: AIB European Residual Mixes 2024 (issuance-based method), Table 2.
#   Atıf zorunlu (AIB). NOT: AIB'nin ALTTAKİ base teknoloji faktörleri türev araçta
#   yeniden dağıtılamaz; burada YALNIZCA yayımlanmış ülke residual-mix CO₂ değerini
#   (gCO₂/kWh) referans alıyoruz — bu izinli kullanımdır.
# AT/NL/CH: "full consumption disclosure" → residual mix YOK → location kullanılır.
# =============================================================================

RESIDUAL_SCHEMA = StructType([
    StructField("country_code",        StringType(),  False),
    StructField("year",                IntegerType(), False),
    StructField("residual_mix_kg_kwh", DoubleType(),  True),   # NULL → full disclosure / use location
    StructField("applicable",          StringType(),  True),   # yes | full_disclosure_use_location | not_in_aib
    StructField("source",              StringType(),  True),
    StructField("source_url",          StringType(),  True),
    StructField("data_confidence",     StringType(),  True),
    StructField("last_updated",        StringType(),  True),
])

_AIB = "AIB European Residual Mixes 2024 (Table 2, issuance-based)"
_AIB_URL = "https://www.aib-net.org/facts/european-residual-mix/2024"

residual_rows = [
    # country, year, residual_kg_kwh, applicable, source, url, confidence, updated
    ("DE", 2023, 0.72456, "yes", _AIB, _AIB_URL, "aib_2024_carryback_verify", _TODAY),
    ("DE", 2024, 0.72456, "yes", _AIB, _AIB_URL, "aib_2024_official",         _TODAY),  # Table 2: 724.56 gCO₂/kWh
    ("DE", 2025, 0.72456, "yes", _AIB, _AIB_URL, "aib_2024_carryforward",     _TODAY),
    ("AT", 2024, None, "full_disclosure_use_location", _AIB, _AIB_URL, "aib_2024_official", _TODAY),
    ("NL", 2024, None, "full_disclosure_use_location", _AIB, _AIB_URL, "aib_2024_official", _TODAY),
    ("FR", 2024, None, "verify_aib_2024", _AIB, _AIB_URL, "verify",     _TODAY),
    ("PL", 2024, None, "verify_aib_2024", _AIB, _AIB_URL, "verify",     _TODAY),
    ("TR", 2024, None, "not_in_aib",      _TEIAS, "",     "use_location", _TODAY),
]

df_residual = spark.createDataFrame(residual_rows, schema=RESIDUAL_SCHEMA)
df_residual.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ref_residual_mix")
print(f"✅ ref_residual_mix yazıldı: {df_residual.count()} satır "
      f"(DE 2024 = 0.725 kg/kWh ≈ location'ın 2×'i)")
df_residual.orderBy("country_code", "year").show(truncate=False)


# =============================================================================
# BÖLÜM 5 — ref_refrigerant_gwp  (Scope 1 fugitive — refrigerant kaçağı)
# =============================================================================
# Scope 1 fugitive emisyon = yıllık dolum (kg) × GWP-100. 09_ghg_scope bu tabloyu
# silver_refrigerant_log ile JOIN eder (F-Gas logbook'tan; EU 2024/573 zorunlu).
# Legacy blend'ler için EU F-Gas Reg Annex (AR4-temelli) değerleri yaygın kullanılır;
# GHG Protocol/ESRS en güncel IPCC'yi (AR6) önerir → ipcc_basis kolonu hangisini
# kullandığımızı taşır (müşterinin raporlama standardına göre değiştirilebilir).
# =============================================================================

GWP_SCHEMA = StructType([
    StructField("refrigerant",  StringType(),  False),
    StructField("gwp_100",      DoubleType(),  False),
    StructField("ipcc_basis",   StringType(),  True),
    StructField("note",         StringType(),  True),
    StructField("source",       StringType(),  True),
    StructField("last_updated", StringType(),  True),
])

_FGAS = "EU F-Gas Reg (EU) 2024/573 Annex I / IPCC"
gwp_rows = [
    ("R-410A",   2088.0, "AR4_blend", "common AC / heat-pump (R-32+R-125)", _FGAS, _TODAY),
    ("R-32",      675.0, "AR4",       "modern AC / heat-pump (lower GWP)",  _FGAS, _TODAY),
    ("R-134a",   1430.0, "AR4",       "chillers, mobile AC",                _FGAS, _TODAY),
    ("R-407C",   1774.0, "AR4_blend", "AC retrofit blend",                  _FGAS, _TODAY),
    ("R-404A",   3922.0, "AR4_blend", "commercial refrigeration",           _FGAS, _TODAY),
    ("R-1234yf",    1.0, "AR5",       "HFO, very low GWP",                  _FGAS, _TODAY),
    ("R-290",       3.0, "AR5",       "propane (natural refrigerant)",      _FGAS, _TODAY),
    ("R-744",       1.0, "AR5",       "CO₂ (natural refrigerant)",          _FGAS, _TODAY),
    ("R-717",       0.0, "AR5",       "ammonia (natural refrigerant)",      _FGAS, _TODAY),
]
df_gwp = spark.createDataFrame(gwp_rows, schema=GWP_SCHEMA)
df_gwp.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ref_refrigerant_gwp")
print(f"✅ ref_refrigerant_gwp yazıldı: {df_gwp.count()} soğutucu gaz")
df_gwp.show(truncate=False)


# =============================================================================
# BÖLÜM 6 — ref_embodied_carbon  (Scope 3 Cat 1 — gömülü/upfront karbon benchmark)
# =============================================================================
# Bina malzemelerinin gömülü karbonu (A1-A5), bina tipine göre kgCO₂e/m². 09_ghg_scope
# (WP4) bunu alan × yoğunluk / amortization_years ile YILLIK Cat 1 tahmini yapar.
# Bu bir BENCHMARK tahminidir (gerçek malzeme/EPD verisi DEĞİL) → scope3 disclosure_grade
# False kalır. Kaynak: RICS WLCA / LETI / DGNB tipik aralıkları. Amortizasyon: 60 yıl.
# =============================================================================

EMBODIED_SCHEMA = StructType([
    StructField("building_type",      StringType(),  False),
    StructField("embodied_kgco2e_m2", DoubleType(),  False),   # upfront A1-A5, whole building
    StructField("amortization_years", IntegerType(), False),
    StructField("source",             StringType(),  True),
    StructField("data_confidence",    StringType(),  True),
    StructField("last_updated",       StringType(),  True),
])

_RICS = "RICS WLCA / LETI / DGNB typical embodied-carbon benchmarks"
embodied_rows = [
    ("Office",      750.0, 60, _RICS, "benchmark_estimate", _TODAY),
    ("Retail",      600.0, 60, _RICS, "benchmark_estimate", _TODAY),
    ("Hotel",       850.0, 60, _RICS, "benchmark_estimate", _TODAY),
    ("Logistics",   450.0, 60, _RICS, "benchmark_estimate", _TODAY),
    ("Healthcare",  950.0, 60, _RICS, "benchmark_estimate", _TODAY),
    ("Lab",        1100.0, 60, _RICS, "benchmark_estimate", _TODAY),
    ("DataCenter", 1400.0, 60, _RICS, "benchmark_estimate", _TODAY),
    ("DEFAULT",     700.0, 60, _RICS, "benchmark_estimate", _TODAY),
]
df_embodied = spark.createDataFrame(embodied_rows, schema=EMBODIED_SCHEMA)
df_embodied.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
    .saveAsTable("ref_embodied_carbon")
print(f"✅ ref_embodied_carbon yazıldı: {df_embodied.count()} bina tipi")
df_embodied.show(truncate=False)


# =============================================================================
# BÖLÜM 7 — DOĞRULAMA
# =============================================================================
print("\n" + "=" * 60)
print("VALIDATION — referans katmanı")
print("=" * 60)

# Her ülke için tam bir yıl serisi var mı?
print("\nGrid faktör — ülke × yıl matrisi:")
df_grid.groupBy("country_code").agg(
    F.min("year").alias("from_year"),
    F.max("year").alias("to_year"),
    F.count("*").alias("n_years"),
    F.round(F.avg("emission_factor_kg_kwh"), 3).alias("avg_factor"),
).orderBy("country_code").show(truncate=False)

# Kritik kontrol: tek bir kanonik değer akıyor mu? (TR artık SADECE 0.442)
_tr_vals = [r["emission_factor_kg_kwh"] for r in
            df_grid.filter(F.col("country_code") == "TR").select("emission_factor_kg_kwh").distinct().collect()]
assert _tr_vals == [0.442], f"❌ TR faktörü tek değer olmalı (0.442), bulundu: {_tr_vals}"
print(f"\n✅ TR grid faktörü tek kanonik değer: {_tr_vals[0]} (artık 0.430/0.450 yok)")

# Residual mix anahtar kontrol: DE enstrümansız market-based, location'dan ~2× kirli olmalı
_de_loc = [r["emission_factor_kg_kwh"] for r in
           df_grid.filter((F.col("country_code") == "DE") & (F.col("year") == 2024)).collect()]
_de_res = [r["residual_mix_kg_kwh"] for r in
           df_residual.filter((F.col("country_code") == "DE") & (F.col("year") == 2024)).collect()]
if _de_loc and _de_res and _de_res[0]:
    _ratio = round(_de_res[0] / _de_loc[0], 2)
    print(f"\n✅ DE 2024 market-based kontrolü: residual {_de_res[0]} / location {_de_loc[0]} = {_ratio}× "
          f"(beklenen >1 — GoO'lar yeşili çekince residual kirlenir)")
    assert _de_res[0] > _de_loc[0], "❌ Residual mix location'dan büyük olmalı (GHG Protocol mantığı)"

print("""
📋 SONRAKI ADIM (WP1 → WP2/3/4 wiring):
   Yeni referans tabloları (bu loader):
     ref_grid_emission_factors  → location-based Scope 2 (DE UBA, diğerleri EEA-sourced)
     ref_residual_mix           → market-based Scope 2 no-instrument fallback (AIB)
     ref_refrigerant_gwp        → Scope 1 fugitive (IPCC GWP × F-Gas logbook)
     ref_embodied_carbon        → Scope 3 Cat 1 (RICS/LETI benchmark × alan)
   Motor bağlantıları:
     09_ghg_scope (WP2) → market = residual mix JOIN (location yerine)
     09_ghg_scope (WP3) → scope1_refrigerant = silver_refrigerant_log × ref_refrigerant_gwp
     09_ghg_scope (WP4) → scope3 kategori = ref_embodied_carbon (Cat 1) + leased (Cat 13)
""")
print("✅ Notebook 03_ref_factors_tariffs_loader tamamlandı (WP1).")
