# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 00_reference_data_loader.py
# Layer: REFERENCE — Simülasyon ve Öneri Motoru İçin Temel Veriler
# =============================================================================
#
# GÖREV:
#   Simülasyon engine ve öneri motorunun ihtiyaç duyduğu
#   referans tablolarını oluştur. Bu tablolar bina verisinden
#   bağımsız — platform genelinde geçerli sabit bilgilerdir.
#
# OUTPUT TABLOLAR:
#   ref_tariffs                → Ülke bazlı enerji tarifeleri
#   ref_building_type_profiles → 8 bina tipi: benchmark, yük profili, öncelikler
#   ref_technology_catalog     → Isı pompası, batarya, yalıtım ürün kategorileri
#   ref_simulation_inputs      → 3 örnek bina için simülasyon girdi değerleri
#
# NOT: Bu notebook'u pipeline başında (Bronze öncesinde) veya
#      bağımsız olarak çalıştırabilirsin. Veriler inline tanımlıdır —
#      dış dosya veya API gerektirmez.
# =============================================================================


# =============================================================================
# BÖLÜM 1 — SPARK KONFİGÜRASYONU
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType, BooleanType
)
from delta.tables import DeltaTable
from pyspark.sql.functions import current_timestamp, lit

spark.conf.set("spark.sql.shuffle.partitions", "8")
spark.conf.set("spark.sql.adaptive.enabled", "true")

REF_PATHS = {
    "tariffs":               "Tables/ref_tariffs",
    "building_type_profiles":"Tables/ref_building_type_profiles",
    "technology_catalog":    "Tables/ref_technology_catalog",
    "simulation_inputs":     "Tables/ref_simulation_inputs",
}

def write_ref_table(data, schema, path, table_name):
    """Referans tablosunu overwrite ile yaz (her zaman en güncel veri)."""
    df = spark.createDataFrame(data, schema)
    df = df.withColumn("loaded_at", current_timestamp())
    df.write.format("delta").mode("overwrite").save(path)
    print(f"✅ {table_name}: {df.count()} satır yazıldı → {path}")
    return df

print("✅ Referans veri yükleyici başlatıldı")


# =============================================================================
# BÖLÜM 2 — ref_tariffs
# Ülke bazlı enerji fiyatları.
# Üretimde müşteri kendi tarifesini girebilir (ref_simulation_inputs'tan override).
# Kaynaklar: BDEW 2024 (DE), EPDK 2024 (TR), EEG 2024 (feed-in DE)
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 2 — Enerji Tarifeleri")
print("="*60)

tariff_schema = StructType([
    StructField("tariff_id",                StringType(),  False),
    StructField("country_code",             StringType(),  False),
    StructField("tariff_type",              StringType(),  False),  # FLAT/TOU/DEMAND
    StructField("electricity_flat_eur_kwh", DoubleType(),  True),
    StructField("electricity_peak_eur_kwh", DoubleType(),  True),   # TOU pik saati
    StructField("electricity_offpeak_eur_kwh", DoubleType(), True), # TOU pik dışı
    StructField("demand_charge_eur_kw_month", DoubleType(), True),  # Güç bedeli
    StructField("gas_eur_kwh",              DoubleType(),  True),
    StructField("fuel_oil_eur_kwh",         DoubleType(),  True),
    StructField("district_heat_eur_kwh",    DoubleType(),  True),
    StructField("feed_in_tariff_eur_kwh",   DoubleType(),  True),   # Solar ihracat
    StructField("co2_tax_eur_ton",          DoubleType(),  True),   # Karbon vergisi
    StructField("valid_year",               IntegerType(), False),
    StructField("source",                   StringType(),  True),
    StructField("notes",                    StringType(),  True),
])

tariff_data = [
    # Almanya — Ticari bina (orta gerilim, >100 MWh/yıl)
    ("TAR-DE-FLAT", "DE", "FLAT",
     0.30, None, None, None,          # elektrik flat
     0.08, 0.095, 0.12,               # gaz, fuel oil, district heat
     0.082,                            # EEG 2024 feed-in (<10 kWp)
     45.0,                             # EU ETS + Almanya CO₂ fiyatı
     2024, "BDEW/EEG 2024",
     "Almanya ticari ortalama. Ağ ücreti + vergiler dahil."),

    # Almanya — Time-of-Use (akıllı sayaç, büyük ticari)
    ("TAR-DE-TOU", "DE", "TOU",
     None, 0.38, 0.22, 18.0,          # peak/offpeak/demand charge
     0.08, 0.095, 0.12,
     0.082,
     45.0,
     2024, "BDEW 2024 TOU",
     "Pik saatler: 08:00-20:00. Pik dışı: 20:00-08:00 + hafta sonu."),

    # Türkiye — Ticari bina (orta gerilim)
    ("TAR-TR-FLAT", "TR", "FLAT",
     0.12, None, None, None,          # ~4 TL/kWh × 0.031 EUR/TL ≈ 0.12 EUR/kWh
     0.035, 0.075, 0.08,              # Doğalgaz (BOTAŞ), fuel oil, DH
     0.083,                            # YEKA feed-in (≈0.133 USD/kWh)
     8.0,                              # Türkiye henüz ETS'de değil, düşük
     2024, "EPDK 2024",
     "Türkiye ticari ortalama. Döviz dalgalanması nedeniyle EUR eşdeğeri yaklaşık."),

    # Türkiye — TOU
    ("TAR-TR-TOU", "TR", "TOU",
     None, 0.15, 0.08, 8.0,
     0.035, 0.075, 0.08,
     0.083,
     8.0,
     2024, "EPDK 2024 TOU",
     "Pik saatler: 08:00-22:00. TEİAŞ talep tarifesi uygulaması."),
]

df_tariffs = write_ref_table(tariff_data, tariff_schema, REF_PATHS["tariffs"], "ref_tariffs")


# =============================================================================
# BÖLÜM 3 — ref_building_type_profiles
# 8 bina tipi için: EUI benchmark, çalışma saatleri, yük profili,
# öncelik ağırlıkları, teknoloji uygunluğu, anomali eşikleri.
# Bu tablo Gold anomali tespitini ve öneri motorunu akıllı hale getirir.
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 3 — Bina Tipi Profilleri")
print("="*60)

btp_schema = StructType([
    StructField("building_type",              StringType(),  False),
    StructField("display_name_de",            StringType(),  True),
    StructField("display_name_tr",            StringType(),  True),
    # EUI Benchmark (kWh/m²/yıl) — AB/EN 15232 ve BPIE veritabanından
    StructField("eui_excellent_kwh_m2",       DoubleType(),  True),  # A/A+ sınıfı
    StructField("eui_good_kwh_m2",            DoubleType(),  True),  # B sınıfı
    StructField("eui_average_kwh_m2",         DoubleType(),  True),  # C/D sınıfı
    StructField("eui_poor_kwh_m2",            DoubleType(),  True),  # E/F sınıfı
    StructField("eui_nzeb_target_kwh_m2",     DoubleType(),  True),  # nZEB hedef
    # Çalışma Profili
    StructField("typical_operating_hours",    StringType(),  True),
    StructField("operating_days",             StringType(),  True),
    StructField("night_base_load_pct",        DoubleType(),  True),  # Peak'in yüzdesi
    StructField("weekend_load_pct",           DoubleType(),  True),
    StructField("summer_load_factor",         DoubleType(),  True),  # 1.0 = yıllık ort.
    StructField("winter_load_factor",         DoubleType(),  True),
    # Tüketim Dağılımı (tahmini)
    StructField("hvac_share_pct",             DoubleType(),  True),
    StructField("lighting_share_pct",         DoubleType(),  True),
    StructField("equipment_share_pct",        DoubleType(),  True),
    StructField("hot_water_share_pct",        DoubleType(),  True),
    # Öncelik Ağırlıkları (toplam = 1.0)
    StructField("priority_cost",              DoubleType(),  True),
    StructField("priority_comfort",           DoubleType(),  True),
    StructField("priority_sustainability",    DoubleType(),  True),
    StructField("priority_reliability",       DoubleType(),  True),
    # Teknoloji Uygunluğu
    StructField("heat_pump_feasibility",      StringType(),  True),  # HIGH/MEDIUM/LOW
    StructField("solar_feasibility",          StringType(),  True),
    StructField("battery_feasibility",        StringType(),  True),
    StructField("insulation_feasibility",     StringType(),  True),
    # Akıllı Anomali Eşikleri (Gold 03'te kullanılacak — Phase 2)
    StructField("night_overconsumption_threshold_pct", DoubleType(), True),
    StructField("consumption_spike_multiplier",        DoubleType(), True),
    # Regülasyon
    StructField("primary_regulation_de",      StringType(),  True),
    StructField("primary_regulation_tr",      StringType(),  True),
    StructField("notes",                      StringType(),  True),
])

btp_data = [
    # ── OFİS ──────────────────────────────────────────────────────────────────
    ("OFFICE", "Bürogebäude", "Ofis Binası",
     70.0, 100.0, 150.0, 220.0, 50.0,
     "08:00-18:00", "MON-FRI",
     0.10, 0.05, 0.75, 1.25,             # gece %10, hft sonu %5, yaz 0.75x, kış 1.25x
     0.45, 0.25, 0.25, 0.05,             # HVAC %45, aydınlatma %25, ekipman %25, sıcak su %5
     0.40, 0.25, 0.25, 0.10,             # öncelik: maliyet en yüksek
     "HIGH", "HIGH", "MEDIUM", "HIGH",
     0.40, 2.5,                           # gece anomali %40, spike 2.5x
     "EnEfG + GEG 2024", "BEP-TR",
     "Hafta sonu çok düşük tüketim. Aydınlatma ve HVAC baskın. "
     "Solar ile yüksek self-consumption potansiyeli (08-18 örtüşme)."),

    # ── PERAKENDe / AVM ───────────────────────────────────────────────────────
    ("RETAIL", "Einzelhandel/EKZ", "Perakende/AVM",
     120.0, 180.0, 250.0, 380.0, 70.0,
     "09:00-22:00", "MON-SUN",
     0.15, 0.80, 1.10, 0.90,             # hafta sonu yüksek, yaz biraz düşük
     0.35, 0.40, 0.20, 0.05,
     0.45, 0.35, 0.15, 0.05,
     "MEDIUM", "HIGH", "HIGH", "MEDIUM",
     0.60, 3.0,                           # gece güvenlik+soğutma normal, spike 3x
     "EnEfG + GEG 2024", "BEP-TR",
     "Aydınlatma baskın. Müşteri konforu kritik. 7 gün açık. "
     "Peak shaving için batarya ideal (akşam kapanış + sabah açılış)."),

    # ── LOJİSTİK / DEPO ───────────────────────────────────────────────────────
    ("LOGISTICS", "Logistik/Lager", "Lojistik/Depo",
     40.0, 65.0, 100.0, 160.0, 35.0,
     "06:00-22:00", "MON-SAT",
     0.08, 0.30, 0.85, 1.15,
     0.40, 0.20, 0.30, 0.10,             # soğutma/ısıtma + ekipman (forklift şarj)
     0.50, 0.15, 0.20, 0.15,
     "MEDIUM", "HIGH", "HIGH", "MEDIUM",
     0.35, 2.5,
     "EnEfG + GEG 2024", "BEP-TR",
     "Geniş çatı alanı = yüksek solar potansiyeli. "
     "Forklift şarj yükü peak shaving için önemli. Soğuk depo varsa ek analiz gerekir."),

    # ── HASTANE / SAĞLIK ──────────────────────────────────────────────────────
    ("HOSPITAL", "Krankenhaus/Klinik", "Hastane/Klinik",
     300.0, 380.0, 480.0, 600.0, 150.0,
     "00:00-24:00", "MON-SUN",
     0.75, 1.00, 1.05, 0.95,             # 7/24, gece bazı birimler tam aktif
     0.40, 0.20, 0.30, 0.10,             # sterilizasyon, tıbbi ekipman, aydınlatma
     0.15, 0.45, 0.20, 0.20,             # güvenilirlik en kritik öncelik
     "LOW", "MEDIUM", "LOW", "MEDIUM",   # ısı pompası kesinti riski
     0.90, 4.0,                           # gece tüketim normal (yüksek eşik), spike 4x
     "EnEfG + Krankenhausfinanzierungsgesetz", "Sağlık Bakanlığı Yönetmelikleri",
     "GÜVENİLİRLİK KRİTİK — ısı pompası yedekli sistem olmadan önerilmez. "
     "UPS ve yedek jeneratör önce sağlanmalı. CHP (kojenerasyon) ideal çözüm."),

    # ── OKUL / ÜNİVERSİTE ────────────────────────────────────────────────────
    ("SCHOOL", "Schule/Universität", "Okul/Üniversite",
     60.0, 90.0, 130.0, 190.0, 45.0,
     "07:00-17:00", "MON-FRI",
     0.05, 0.10, 0.70, 1.30,             # yaz tatili düşük, kış yüksek
     0.50, 0.20, 0.20, 0.10,             # HVAC dominant, tatil döneminde dip
     0.50, 0.20, 0.20, 0.10,
     "HIGH", "HIGH", "MEDIUM", "HIGH",   # solar ile çalışma saati örtüşüyor
     0.20, 2.0,                           # gece çok düşük beklenti
     "EnEfG + GEG 2024 + Bundesländer Schulbaurichtlinien", "MEB Yönetmelikleri",
     "Solar ideal: üretim saatleri (09-15) tüketimle örtüşüyor. "
     "Yaz tatilinde fazla solar üretimi → batarya veya feed-in. "
     "Örnek bina olma (eğitim amaçlı) sürdürülebilirlik önceliğini artırır."),

    # ── OTEL / KONAKLAMA ─────────────────────────────────────────────────────
    ("HOTEL", "Hotel/Beherbergung", "Otel/Konaklama",
     150.0, 220.0, 300.0, 420.0, 100.0,
     "00:00-24:00", "MON-SUN",
     0.60, 0.95, 1.20, 0.80,             # yaz yüksek (soğutma + turist), kış orta
     0.35, 0.15, 0.25, 0.25,             # sıcak su %25 (yüksek — duş, yemek)
     0.30, 0.40, 0.15, 0.15,
     "HIGH", "MEDIUM", "MEDIUM", "HIGH",
     0.70, 3.0,
     "EnEfG + GEG 2024 + Beherbergungsverordnung", "Turizm Bakanlığı Yönetmelikleri",
     "Sıcak su büyük enerji kalemi — ısı pompası + güneş kollektörü ideal. "
     "Konfor kritik: ısıtma/soğutma kesintisi müşteri şikayetine yol açar."),

    # ── VERİ MERKEZİ ─────────────────────────────────────────────────────────
    ("DATA_CENTER", "Rechenzentrum", "Veri Merkezi",
     500.0, 800.0, 1200.0, 2000.0, 300.0,
     "00:00-24:00", "MON-SUN",
     1.00, 1.00, 1.00, 1.00,             # tamamen sabit yük (PUE karakteristiği)
     0.40, 0.05, 0.50, 0.05,             # BT ekipmanı + soğutma dominant
     0.10, 0.60, 0.10, 0.20,             # güvenilirlik+maliyet kritik
     "LOW", "LOW", "LOW", "HIGH",        # solar/batarya güç kalitesini etkiler
     1.00, 5.0,                           # gece tüketim aynı (sabit yük)
     "EnEfG + ISO/IEC 30134 (PUE) + BSI IT-Grundschutz", "BTK + ISO 27001",
     "Ana metrik: PUE (Power Usage Effectiveness) = toplam / BT enerjisi. "
     "Hedef PUE < 1.4. Soğutma verimliliği (free cooling, adiabatik) öncelik. "
     "Kesintisiz güç → UPS + yedek güç zorunlu. Solar önerilmez (güç kalitesi)."),

    # ── KONUT (ÇOK KATLI) ────────────────────────────────────────────────────
    ("RESIDENTIAL_MF", "Mehrfamilienhaus", "Çok Katlı Konut",
     50.0, 80.0, 120.0, 180.0, 40.0,
     "06:00-23:00", "MON-SUN",
     0.30, 0.90, 0.80, 1.20,             # akşam peak (18-21 arası), hafta sonu benzer
     0.50, 0.15, 0.15, 0.20,             # ısıtma dominant, sıcak su önemli
     0.55, 0.10, 0.15, 0.20,
     "HIGH", "MEDIUM", "LOW", "HIGH",
     0.60, 2.5,
     "GEG 2024 + WEG (Wohnungseigentumsgesetz)", "Binalarda Enerji Performansı Yönetmeliği",
     "Isıtma ve sıcak su baskın. Birden fazla kiracı → ortak alan sayacı ayrımı önemli. "
     "Isı pompası en yüksek ROI potansiyeli (gaz → elektrik geçişi). "
     "BAFA/KfW teşvikleri bu tip için en avantajlı."),
]

df_btp = write_ref_table(btp_data, btp_schema, REF_PATHS["building_type_profiles"], "ref_building_type_profiles")


# =============================================================================
# BÖLÜM 4 — ref_technology_catalog
# Isı pompası, batarya, yalıtım kategorileri — temsili ürünler ve fiyatlar.
# Platform belirli bir marka önermez; müşteriye karşılaştırma sunar.
# Kaynaklar: üretici katalogları, VDI 2067, IEA Heat Pump report 2023
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 4 — Teknoloji Kataloğu")
print("="*60)

cat_schema = StructType([
    StructField("product_id",              StringType(),  False),
    StructField("category",                StringType(),  False),
    # HEAT_PUMP_ASHP / HEAT_PUMP_GSHP / HEAT_PUMP_EXHAUST /
    # BATTERY_LFP / BATTERY_NMC /
    # INSULATION_EPS / INSULATION_MW / INSULATION_PIR / INSULATION_AEROGEL /
    # SOLAR_INVERTER / SOLAR_PANEL
    StructField("subcategory",             StringType(),  True),
    StructField("brand",                   StringType(),  True),
    StructField("model_range",             StringType(),  True),
    StructField("country_applicable",      StringType(),  True),  # DE / TR / BOTH
    StructField("capacity_min",            DoubleType(),  True),
    StructField("capacity_max",            DoubleType(),  True),
    StructField("capacity_unit",           StringType(),  True),  # kW / kWh / kWp / m²
    # Performans
    StructField("cop_a7w35",               DoubleType(),  True),  # Isı pompası COP (7°C hava, 35°C su)
    StructField("cop_a_minus7w35",         DoubleType(),  True),  # Soğuk iklim COP
    StructField("cop_a2w35",               DoubleType(),  True),  # Orta iklim COP
    StructField("cycle_life",              IntegerType(), True),  # Batarya döngü ömrü
    StructField("warranty_years",          IntegerType(), True),
    StructField("thermal_conductivity",    DoubleType(),  True),  # W/mK — yalıtım
    # Maliyet (EUR)
    StructField("capex_per_unit_min_eur",  DoubleType(),  True),  # Birim başına min maliyet
    StructField("capex_per_unit_max_eur",  DoubleType(),  True),
    StructField("capex_unit",              StringType(),  True),  # EUR/kW, EUR/kWh, EUR/m²
    StructField("install_cost_pct",        DoubleType(),  True),  # Kurulum maliyeti (capex'in yüzdesi)
    StructField("opex_annual_pct",         DoubleType(),  True),  # Yıllık bakım (capex'in yüzdesi)
    StructField("lifetime_years",          IntegerType(), True),
    # Teşvik Uygunluğu
    StructField("kfw_eligible",            BooleanType(), True),
    StructField("bafa_eligible",           BooleanType(), True),
    StructField("yeka_eligible",           BooleanType(), True),
    # Bina Tipi Uygunluğu
    StructField("suitable_for",            StringType(),  True),  # virgülle ayrılmış bina tipleri
    StructField("not_suitable_for",        StringType(),  True),
    # Karşılaştırma Gerekçesi
    StructField("key_advantage",           StringType(),  True),
    StructField("key_disadvantage",        StringType(),  True),
    StructField("when_to_prefer",          StringType(),  True),
    StructField("when_not_to_prefer",      StringType(),  True),
])

cat_data = [
    # ── ISIL POMPALAR — ASHP (Hava-Su) ───────────────────────────────────────

    ("HP-ASHP-VIESSMANN", "HEAT_PUMP_ASHP", "Hava-Su Isı Pompası",
     "Viessmann", "Vitocal 200-A / 222-A",
     "DE", 8.0, 25.0, "kW",
     4.3, 2.8, 3.7,                      # COP A7/W35, A-7/W35, A2/W35
     None, 10, None,
     700.0, 1000.0, "EUR/kW", 0.30, 0.015, 20,
     True, True, False,
     "OFFICE,SCHOOL,RESIDENTIAL_MF,HOTEL,RETAIL",
     "DATA_CENTER,HOSPITAL",
     "Almanya pazarında en yaygın. Servis ağı geniş. KfW + BAFA uyumlu. "
     "Vitocal 222-A entegre sıcak su deposuyla gelir (kompakt kurulum).",
     "İlk yatırım maliyeti gaz kazanından yüksek. "
     "Çok soğuk günlerde (< -10°C) COP düşer, yedek ısıtıcı devreye girebilir.",
     "Mevcut gaz kazanını değiştirirken. Iyi yalıtımlı binalarda. "
     "KfW/BAFA teşviki alınmak istendiğinde — bu markalar onaylı listede.",
     "Eski yüksek sıcaklık radyatör sistemi varsa (>60°C). Hastanelerde tek başına."),

    ("HP-ASHP-DAIKIN", "HEAT_PUMP_ASHP", "Hava-Su Isı Pompası",
     "Daikin", "Altherma 3 H HT",
     "BOTH", 4.0, 16.0, "kW",
     5.1, 3.2, 4.2,                      # Yüksek sıcaklık versiyonu (65°C su)
     None, 12, None,
     750.0, 1100.0, "EUR/kW", 0.25, 0.012, 20,
     True, True, False,
     "OFFICE,SCHOOL,RESIDENTIAL_MF,HOTEL,RETAIL",
     "DATA_CENTER",
     "65°C'ye kadar su sıcaklığı sağlar — eski radyatör sistemi olan binalara uygun. "
     "Türkiye'de yaygın servis ağı. R-32 soğutucu (düşük GWP).",
     "Küçük kapasiteler için fiyat/performans daha düşük.",
     "Eski radyatör sistemi varken (HT versiyonu). Türkiye projelerinde. "
     "Her iki ülkede de yaygın servis ağı gerektiğinde.",
     "Çok büyük ticari tesisler (>500 kW) — bu kapasite aralığı yetmez."),

    ("HP-ASHP-VAILLANT", "HEAT_PUMP_ASHP", "Hava-Su Isı Pompası",
     "Vaillant", "aroTHERM plus",
     "DE", 5.0, 17.0, "kW",
     5.6, 3.5, 4.8,
     None, 10, None,
     680.0, 980.0, "EUR/kW", 0.28, 0.013, 20,
     True, True, False,
     "OFFICE,SCHOOL,RESIDENTIAL_MF,HOTEL",
     "DATA_CENTER,HOSPITAL",
     "En yüksek A7/W35 COP değerlerinden biri (%5.6). "
     "Çok gürültüsüz çalışma (42 dB). Şehir merkezi binalara uygun. "
     "Mevcut Vaillant gaz kazanı sistemiyle tam entegrasyon.",
     "Türkiye'de servis ağı sınırlı. Sadece DE pazarına odaklı.",
     "Gürültü hassasiyeti olan binalarda (ofis, konut). "
     "Mevcut Vaillant sistemi varken yükseltme için.",
     "Türkiye projeleri için."),

    # ── ISIL POMPALAR — GSHP (Yer Kaynaklı) ──────────────────────────────────

    ("HP-GSHP-VIESSMANN", "HEAT_PUMP_GSHP", "Yer Kaynaklı Isı Pompası",
     "Viessmann", "Vitocal 300-G Pro",
     "DE", 10.0, 100.0, "kW",
     5.5, 4.8, 5.2,                      # Toprak sıcaklığı sabit (~10°C) — COP sabit
     None, 12, None,
     1200.0, 1800.0, "EUR/kW", 0.60, 0.010, 25,  # %60 kurulum = sondaj maliyeti
     True, True, False,
     "OFFICE,HOSPITAL,HOTEL,SCHOOL",
     "RETAIL,LOGISTICS",
     "En yüksek yıllık COP (SCOP ~5.0+). Gürültüsüz. "
     "Dış hava sıcaklığından bağımsız (toprak 10°C sabit). "
     "Hastane ve otel gibi 7/24 güvenilirlik gerektiren binalar için ideal.",
     "Çok yüksek ilk yatırım (sondaj = toplam maliyetin %40-60'ı). "
     "Arazi veya park alanı gerektiriyor. İzin süreci uzun.",
     "Büyük ticari binalar. 15+ yıl işletme planı olanlar. "
     "Hastaneler (güvenilirlik + uzun dönem maliyet). Tarihî bina çevrelerinde.",
     "Küçük binalar (<200 m²). Sondaj yapılamayan arsa koşulları. Kısa vadeli projeler."),

    # ── BATARYALAR — LFP ──────────────────────────────────────────────────────

    ("BAT-LFP-BYD", "BATTERY_LFP", "LFP Batarya Sistemi",
     "BYD", "Battery-Box Premium LFP",
     "BOTH", 5.0, 66.0, "kWh",
     None, None, None,
     4000, 10, None,
     500.0, 750.0, "EUR/kWh", 0.10, 0.005, 15,
     False, False, True,
     "OFFICE,RETAIL,LOGISTICS,SCHOOL,HOTEL",
     "DATA_CENTER",
     "Modüler tasarım: 5 kWh'lık birimler gerektiğinde genişletilebilir. "
     "LFP kimyası — termal kaçma riski yok (güvenli). 4000 döngü. "
     "Türkiye YEKA projeleri için uygun. Küresel en geniş kurulu kapasite.",
     "Büyük ticari tesisler için daha büyük kapasiteli sistemler gerekebilir. "
     "Almanya KfW kapsamında değil (bireysel bazda).",
     "Solar self-consumption optimize etmek için. Peak shaving. "
     "Türkiye YEKA teşvik programında. Ölçeklenebilirlik gerektiğinde.",
     "Kritik yük koruması (UPS seviyesi güvenilirlik) gereken yerlerde."),

    ("BAT-LFP-HUAWEI", "BATTERY_LFP", "LFP Batarya Sistemi",
     "Huawei", "LUNA2000 Commercial",
     "BOTH", 30.0, 1000.0, "kWh",
     None, None, None,
     6000, 10, None,
     420.0, 650.0, "EUR/kWh", 0.08, 0.004, 15,
     False, False, True,
     "OFFICE,RETAIL,LOGISTICS,HOTEL,SCHOOL",
     "DATA_CENTER,HOSPITAL",
     "Büyük ticari ölçek için (30 kWh+). En düşük EUR/kWh maliyet aralığı. "
     "Huawei inverter sistemiyle tam entegrasyon. 6000 döngü ömrü.",
     "Küçük binalar için fazla kapasiteli. Tedarik zinciri riski (jeopolitik).",
     "Büyük endüstriyel ve ticari tesisler. Solar + batarya kombine sistemlerde. "
     "Uzun dönem maliyet optimizasyonu öncelikli projelerde.",
     "Küçük ofis veya konut ölçeği (<30 kWh). Politik risk duyarlı projeler."),

    # ── YALITIM ───────────────────────────────────────────────────────────────

    ("INS-EPS", "INSULATION_EPS", "EPS Mantolama",
     "Genel (BASF/Knauf)", "EPS 032 / EPS 035",
     "BOTH", 0.0, None, "m²",
     None, None, None,
     None, None, 0.032,
     15.0, 30.0, "EUR/m²", 0.40, 0.0, 30,
     False, False, False,
     "OFFICE,RETAIL,LOGISTICS,SCHOOL,RESIDENTIAL_MF",
     "DATA_CENTER",
     "En yaygın ve en ekonomik yalıtım malzemesi. "
     "Uygulama kolaylığı. Geniş tedarikçi ağı. Geri dönüştürülebilir.",
     "Yangın dayanımı sınırlı (hastane/otel için B sınıfı yangın sertifikası gerekli). "
     "PIR'e göre daha kalın uygulama gerekir.",
     "Standart dış cephe mantolama. Bütçe odaklı projeler. "
     "GEG uyumu için yeterli — U-value < 0.24 W/m²K hedeflendiğinde.",
     "Yangın sertifikası gerektiren binalar. Çok ince boşluklarda."),

    ("INS-MW", "INSULATION_MW", "Mineral Yün Yalıtım",
     "Genel (Rockwool/Isover)", "Mineral Wool A1",
     "BOTH", 0.0, None, "m²",
     None, None, None,
     None, None, 0.035,
     20.0, 40.0, "EUR/m²", 0.35, 0.0, 40,
     False, False, False,
     "OFFICE,RETAIL,HOSPITAL,HOTEL,SCHOOL,RESIDENTIAL_MF",
     "DATA_CENTER",
     "A1 yangın sınıfı — hastane, otel için zorunlu. "
     "Ses yalıtımı da sağlar. Uzun ömür (40 yıl+).",
     "EPS'e göre daha pahalı. Nem yönetimi kritik (nem bariyeri şart).",
     "Yangın güvenliği öncelikli binalar. Hem ses hem ısı yalıtımı gerektiğinde. "
     "Hastane, otel, okul için varsayılan öneri.",
     "Sıkı bütçe kısıtlaması varsa (EPS daha ucuz)."),

    ("INS-PIR", "INSULATION_PIR", "PIR / PUR Yalıtım Levhası",
     "Genel (Kingspan/Recticel)", "Kooltherm / Eurothane",
     "BOTH", 0.0, None, "m²",
     None, None, None,
     None, None, 0.022,
     35.0, 70.0, "EUR/m²", 0.30, 0.0, 35,
     True, False, False,              # KfW yüksek performans bina teşviki kapsamında
     "OFFICE,RETAIL,LOGISTICS,SCHOOL,RESIDENTIAL_MF",
     "HOSPITAL",
     "En yüksek termal direnç (λ=0.022 W/mK). İnce uygulama. "
     "Sınırlı alan varken maksimum yalıtım için ideal. "
     "nZEB hedefi için gereken U-value değerlerine en hızlı ulaşım.",
     "EPS/MW'ye göre 2-3x daha pahalı. B2 yangın sınıfı — bazı binalar için yetersiz.",
     "Sınırlı dış cephe derinliği olduğunda. nZEB veya KfW 40 hedefi için. "
     "Çatı yalıtımı (ince profil kritik olduğunda).",
     "Bütçe kısıtlamalı projeler. A1 yangın sınıfı zorunlu binalar."),
]

df_cat = write_ref_table(cat_data, cat_schema, REF_PATHS["technology_catalog"], "ref_technology_catalog")


# =============================================================================
# BÖLÜM 5 — ref_simulation_inputs
# 3 örnek bina için simülasyon girdileri.
# Üretimde: müşteri bu verileri UI üzerinden girer veya API'den çekilir.
# Eksik veriler için ülke/bina tipi bazlı defaults kullanılır.
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 5 — Simülasyon Girdi Değerleri (3 Bina)")
print("="*60)

sim_schema = StructType([
    StructField("building_id",              StringType(),  False),
    # Tarife — ref_tariffs'ten override veya custom
    StructField("tariff_id",                StringType(),  True),   # ref_tariffs FK
    StructField("electricity_tariff_eur_kwh", DoubleType(), True),  # override
    StructField("gas_price_eur_kwh",        DoubleType(),  True),
    StructField("feed_in_tariff_eur_kwh",   DoubleType(),  True),
    StructField("demand_charge_eur_kw_month", DoubleType(), True),
    # Mevcut Isıtma Sistemi
    StructField("heating_fuel_type",        StringType(),  True),   # GAS/OIL/ELECTRIC/DISTRICT/NONE
    StructField("heating_system_age_years", IntegerType(), True),
    StructField("heat_distribution_type",   StringType(),  True),   # UNDERFLOOR/RADIATOR_LT/RADIATOR_HT/AIR
    StructField("design_supply_temp_c",     DoubleType(),  True),   # Mevcut sistemin su sıcaklığı
    # Bina Geometrisi (yalıtım hesabı için)
    StructField("num_floors",               IntegerType(), True),
    StructField("floor_height_m",           DoubleType(),  True),   # Kat yüksekliği
    StructField("building_height_m",        DoubleType(),  True),   # Toplam yükseklik
    StructField("building_perimeter_m",     DoubleType(),  True),   # Bina çevresi
    # Şebeke
    StructField("grid_connection_kw",       DoubleType(),  True),   # Max şebeke bağlantı gücü
    StructField("max_solar_export_kw",      DoubleType(),  True),   # Max ihracat gücü
    # Simülasyon Senaryoları — Hedefler
    StructField("target_hp_capacity_kw",    DoubleType(),  True),   # Önerilen ısı pompası kapasitesi
    StructField("target_battery_kwh",       DoubleType(),  True),   # Önerilen ek batarya kapasitesi
    StructField("target_wall_u_value",      DoubleType(),  True),   # Hedef duvar U-değeri
    StructField("target_window_u_value",    DoubleType(),  True),   # Hedef pencere U-değeri
    StructField("target_roof_u_value",      DoubleType(),  True),   # Hedef çatı U-değeri
    # Finansal Parametreler
    StructField("discount_rate_pct",        DoubleType(),  True),   # NPV hesabı için iskonto oranı
    StructField("energy_price_escalation_pct", DoubleType(), True), # Yıllık enerji fiyat artışı
    StructField("project_lifetime_years",   IntegerType(), True),
    StructField("data_source",              StringType(),  True),   # MANUAL/ESTIMATED/API
    StructField("notes",                    StringType(),  True),
])

sim_data = [
    # ── B001: Berlin Ofis — Monitor Tier ──────────────────────────────────────
    # Mevcut: Gaz kazanı + geleneksel HVAC. Isı pompası + yalıtım iyileştirmesi potansiyeli.
    ("B001",
     "TAR-DE-TOU",                         # TOU tarife (akıllı bina)
     0.30, 0.08, 0.082, 18.0,             # elektrik, gaz, feed-in, demand charge
     "GAS", 12, "RADIATOR_LT", 55.0,      # gaz, 12 yıllık, düşük sıcaklık radyatör, 55°C
     5, 3.5, 17.5, 72.0,                  # 5 kat, 3.5m, 17.5m yükseklik, 72m çevre
     500.0, 100.0,                          # şebeke 500kW, max ihracat 100kW
     45.0, 0.0, 0.18, 1.0, 0.12,          # HP 45kW, ek batarya yok, duvar→0.18, pencere→1.0, çatı→0.12
     0.06, 0.03, 15,                        # %6 iskonto, %3 enerji fiyat artışı, 15 yıl proje
     "ESTIMATED",
     "Radyatör sistemi LT uyumlu (55°C) — Daikin Altherma 3 HT veya Viessmann Vitocal ideal. "
     "Mevcut yalıtım: duvar 0.35 W/m²K → hedef 0.18 (KfW 55 standardı). "
     "TOU tarife: peak shaving ile demand charge tasarrufu mümkün."),

    # ── B002: İstanbul Perakende — Insight Tier ───────────────────────────────
    # Mevcut: Geleneksel split klima (elektrik). Solar + batarya yüksek potansiyel.
    ("B002",
     "TAR-TR-TOU",
     0.12, 0.035, 0.083, 8.0,
     "ELECTRIC", 8, "AIR", 0.0,           # Split klima (hava), elektrikli, mevcut su sistemi yok
     3, 4.0, 12.0, 140.0,                  # 3 kat, 4m (AVM yükseklik), 12m, 140m çevre (büyük bina)
     800.0, 150.0,
     0.0, 200.0, 0.25, 1.2, 0.15,         # HP yok (klima sistemi farklı), 200kWh batarya ekle
     0.08, 0.05, 15,
     "ESTIMATED",
     "Mevcut elektrikli klima sistemi — ısı pompası değişimi değil, "
     "mevcut sistemin COP optimizasyonu ve solar+batarya eklenmesi öncelikli. "
     "İstanbul güneşlenme süresi yüksek (1750+ saat/yıl) — yüksek solar potansiyeli. "
     "YEKA teşviki araştırılmalı. Batarya: peak shaving için akşam yoğunluğunu azalt."),

    # ── B003: Hamburg Lojistik — Copilot Tier ────────────────────────────────
    # Mevcut: Gaz + mevcut solar+batarya. Batarya kapasitesi artırımı + yalıtım.
    ("B003",
     "TAR-DE-TOU",
     0.30, 0.08, 0.082, 18.0,
     "GAS", 6, "AIR", 0.0,                # Depo ısıtma (hava üflemeli), gaz
     2, 8.0, 16.0, 360.0,                  # 2 kat (yüksek tavan depolar), 8m/kat, 360m çevre (büyük)
     1200.0, 300.0,                         # Büyük endüstriyel şebeke
     80.0, 200.0, 0.20, 1.1, 0.10,         # HP 80kW, +200kWh batarya, yalıtım iyileştirme
     0.06, 0.03, 20,                        # 20 yıl proje (lojistik bina uzun dönem)
     "ESTIMATED",
     "Büyük çatı alanı → solar kapasitesi artırımı potansiyeli. "
     "Mevcut batarya + ek 200kWh → peak shaving ve self-consumption optimize. "
     "Forklift şarj istasyonları yakında eklenecekse: ani peak yükleri için batarya kritik. "
     "Hamburg iklimi: HDD yüksek → yalıtım iyileştirmesi yüksek ROI. "
     "Büyük depo alanı nedeniyle bina zarfı (çatı yalıtımı) en büyük ısı kaybı kalemi."),
]

df_sim = write_ref_table(sim_data, sim_schema, REF_PATHS["simulation_inputs"], "ref_simulation_inputs")


# =============================================================================
# BÖLÜM 6 — OPTIMIZE
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 6 — OPTIMIZE")
print("="*60)

for table_name, path in REF_PATHS.items():
    try:
        spark.sql(f"OPTIMIZE delta.`{path}`")
        print(f"⚡ OPTIMIZE: {table_name}")
    except Exception as e:
        print(f"⚠️  OPTIMIZE atlandı ({table_name}): {str(e)[:60]}")


# =============================================================================
# BÖLÜM 7 — VALIDATION RAPORU
# =============================================================================

print("\n" + "="*60)
print("BÖLÜM 7 — Validation Raporu")
print("="*60)

df_t = spark.read.format("delta").load(REF_PATHS["tariffs"])
df_b = spark.read.format("delta").load(REF_PATHS["building_type_profiles"])
df_c = spark.read.format("delta").load(REF_PATHS["technology_catalog"])
df_s = spark.read.format("delta").load(REF_PATHS["simulation_inputs"])

print(f"\n{'='*60}")
print("=== REFERANS VERİ DOĞRULAMA ===")
print(f"{'='*60}")
print(f"  ref_tariffs:                {df_t.count():>4} satır")
print(f"  ref_building_type_profiles: {df_b.count():>4} satır")
print(f"  ref_technology_catalog:     {df_c.count():>4} satır")
print(f"  ref_simulation_inputs:      {df_s.count():>4} satır")

print(f"\n📊 Tarife Özeti:")
df_t.select("country_code", "tariff_type",
            "electricity_flat_eur_kwh", "gas_eur_kwh", "feed_in_tariff_eur_kwh") \
    .show(truncate=False)

print(f"\n📊 Bina Tipi EUI Benchmark Özeti:")
df_b.select("building_type", "eui_excellent_kwh_m2", "eui_average_kwh_m2",
            "heat_pump_feasibility", "solar_feasibility", "priority_cost") \
    .orderBy("eui_average_kwh_m2") \
    .show(truncate=False)

print(f"\n📊 Teknoloji Kataloğu Özeti:")
df_c.select("product_id", "category", "brand", "capex_per_unit_min_eur",
            "capex_unit", "kfw_eligible", "cop_a7w35") \
    .show(truncate=False)

print(f"\n📊 Simülasyon Girdileri Özeti:")
df_s.select("building_id", "heating_fuel_type", "heat_distribution_type",
            "target_hp_capacity_kw", "target_battery_kwh",
            "electricity_tariff_eur_kwh", "gas_price_eur_kwh") \
    .show(truncate=False)

print(f"\n{'='*60}")
print("✅ Referans veri yüklendi!")
print("   Simülasyon engine artık bu tablolardan okuyabilir.")
print("   Sonraki adım: 04_simulation_engine.py")
print(f"{'='*60}")
