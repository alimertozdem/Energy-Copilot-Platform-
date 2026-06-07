# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 01_bronze_iot_raw_generator.py
# Layer: BRONZE — IoT STATIC SNAPSHOT GENERATOR (protocol-native raw telemetry)
# Created: 2026-06-01
# =============================================================================
# GÖREV: gold_iot_sensor_master (515 nokta) registry'sinden beslenerek, geçmiş
#   ~N gün boyunca SAATLİK ham telemetri üretir → bronze_iot_raw. Bu, EventStream
#   KAPALIYKEN (trial sonrası) Page 8'i CANLI gösteren STATİK anlık görüntüdür.
#
# NEDEN STATİK SNAPSHOT: 00_iot_adapter_framework + EventStream = canlı yol (aç/kapa,
#   maliyetli). Demo/satış için Page 8'in boş kalmaması gerekir → sensor_master +
#   bu generator + 11b + 11c tüm IoT katmanını compute'suz ayakta tutar. [[page8-eventstream-architecture]]
#
# ŞEMA SÖZLEŞMESİ (11b_iot_processing.py BRONZE_SCHEMA — 18 kolon, BİREBİR):
#   device_id, building_id, sensor_type, sensor_location, reading_value, reading_unit,
#   source_protocol, timestamp(STRING "yyyy-MM-dd'T'HH:mm:ss'Z'"), reading_quality(INT),
#   setpoint_min, setpoint_max, baseline_value, in_setpoint(BOOL), is_anomaly(BOOL),
#   anomaly_type, anomaly_severity, action_recommended, cost_eur_estimate
#   NOT: 11b is_anomaly/severity/in_setpoint/action'ı sensor_master setpoint'lerinden
#   YENİDEN hesaplar; bronze değerleri yalnız EventStream-pariteli self-consistency için.
#   Gerçek anomali oranını VALUE ↔ master-setpoint ilişkisi belirler (aşağıda hedeflendi).
#
# FAULT TAKSONOMİSİ (ASHRAE Guideline 36 AFDD — 11c'nin korele ettiği imzalar):
#   R1 LOW_DELTA_T      : supply≈return (Δ<5°C) HVAC aktifken      → B009 chiller penceresi
#   R2 AFTER_HOURS_HVAC : gece (22–05) hvac_kwh aktif              → B003 2 gece
#   R3 VENTILATION_FAULT: CO2>1000ppm HVAC aktifken                → B001 zon penceresi
#   R4 SETPOINT_NOT_MET : zon HVAC_temp konfor-dışı yüksek yükte   → B005 zon penceresi
#   + tek-sensör eşik anomalileri (11b): boiler_eff<75, chiller_cop<2.5, power_factor<0.85,
#     filter_dp>300, PM2.5>35, pump_pressure<100, CO2>1500.
#   NOT (11c location-correlation): supply/return = ekipman konumu, hvac_kwh = Main-Meter,
#   CO2/HVAC_temp = zon konumu → AYNI sensor_location'da DEĞİLLER. Bu yüzden imzalar
#   BİNA+ZAMAN düzeyinde senkronize üretilir; 11c'yi bina-düzeyi korelasyona genişletmek
#   = A5 adım ③ (bu generator o düzeltmeye veri hazırlar).
#
# PARAMETRELER (spark.conf): gen_days(=7), seed(=42), noise_scale(=1.0)
# ÇIKTI: bronze_iot_raw (overwrite). SONRAKİ: 11b_iot_processing lookback_hours=50 (default 2h GOTCHA!)
# ⚠️ Fabric: bu notebook'a default lakehouse PIN ZORUNLU (saveAsTable bare-isim "No default context").
# =============================================================================

import math
from datetime import datetime, timedelta, timezone
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType, IntegerType, BooleanType
)

spark = SparkSession.builder.getOrCreate()
print("✅ bronze_iot_raw generator (statik IoT snapshot) başladı")

# -----------------------------------------------------------------------------
# Parametreler
# -----------------------------------------------------------------------------
N_DAYS      = int(spark.conf.get("gen_days", "7"))
SEED        = int(spark.conf.get("seed", "42"))
NOISE_SCALE = float(spark.conf.get("noise_scale", "1.0"))
rng = np.random.default_rng(SEED)
print(f"   gen_days={N_DAYS} | seed={SEED} | noise_scale={NOISE_SCALE}")

# -----------------------------------------------------------------------------
# 1) Sensör registry oku (515 nokta — anlam katmanı)
# -----------------------------------------------------------------------------
sm = spark.table("gold_iot_sensor_master").select(
    "building_id", "sensor_id", "sensor_type", "sensor_location",
    "equipment_ref", "equipment_type", "point_group", "reading_unit",
    "source_protocol", "setpoint_min", "setpoint_max",
    "alert_threshold_low", "alert_threshold_high", "baseline_value",
).collect()
sensors = [r.asDict() for r in sm]
print(f"   sensor_master: {len(sensors)} nokta")

# -----------------------------------------------------------------------------
# 2) Saatlik zaman ekseni — NOW'da biter, geriye N_DAYS
# -----------------------------------------------------------------------------
H = N_DAYS * 24
now_floor = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
ts_dt  = [now_floor - timedelta(hours=(H - 1 - i)) for i in range(H)]
ts_str = [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in ts_dt]
hour    = np.array([t.hour for t in ts_dt])          # 0–23
dow     = np.array([t.weekday() for t in ts_dt])     # 0=Mon … 6=Sun
weekend = dow >= 5
frac    = np.arange(H) / max(H - 1, 1)               # 0→1 (yavaş trend: filtre kirlenmesi vb.)
hours_ago = np.array([(now_floor - t).total_seconds() / 3600.0 for t in ts_dt])  # 0=now
print(f"   zaman ekseni: {ts_str[0]} → {ts_str[-1]} ({H} saat)")

# -----------------------------------------------------------------------------
# 3) Doluluk (occupancy) profilleri — değer modelinin sürücüsü
#    office_day | always_on (sağlık/DC) | hotel. Kimlik/şehir ATAMAZ (audit A4/I1'den kaçınır),
#    yalnızca kullanım ritmi karakteri verir.
# -----------------------------------------------------------------------------
BUILDING_PROFILE = {
    "B001": "office_day", "B002": "office_day", "B003": "hotel",
    "B004": "hotel",      "B005": "always_on", "B006": "office_day",
    "B007": "office_day", "B008": "office_day", "B009": "always_on",
    "B010": "office_day",
}
PV_PEAK_KW = {"B001": 40.0, "B004": 55.0, "B006": 45.0, "B007": 70.0, "B010": 48.0}

def occ_series(profile):
    """Saat-bazlı doluluk faktörü [0,1], profil + hafta içi/sonu."""
    daybump = np.exp(-((hour - 13.0) / 4.5) ** 2)        # iş günü öğle tepeli gauss
    if profile == "office_day":
        o = np.where(weekend, 0.08, np.clip(daybump, 0.0, 1.0))
    elif profile == "always_on":
        o = (0.55 + 0.35 * daybump) - np.where(weekend, 0.05, 0.0)
    else:  # hotel
        morn = np.exp(-((hour - 8.0) / 2.5) ** 2)
        eve  = np.exp(-((hour - 21.0) / 3.0) ** 2)
        o = 0.35 + 0.50 * np.maximum(morn, eve) + np.where(weekend, 0.10, 0.0)
    return np.clip(o, 0.02, 1.0)

OCC = {bid: occ_series(p) for bid, p in BUILDING_PROFILE.items()}

# -----------------------------------------------------------------------------
# 3b) PV diurnal irradiance profile (Solar D baglantisi) — pv_ac_power'i GERCEK
#     havaya baglar. silver_weather_clean'den (son ~60 gun, mevsim-uygun) bina x
#     saat-of-day ortalama irradiance (W/m2). Tam-tarih join YERINE diurnal
#     klimatoloji -> Open-Meteo archive gecikmesine dayanikli. Yoksa fallback sinus.
# -----------------------------------------------------------------------------
PV_PR_INST = 0.82   # anlik performans orani (inverter+sicaklik+kirlilik kayiplari) (0.75-0.85)
try:
    _wx = (spark.table("silver_weather_clean")
              .filter(F.col("timestamp_utc") >= F.date_sub(F.current_date(), 60))
              .withColumn("_hod", F.hour("timestamp_utc"))
              .groupBy("building_id", "_hod")
              .agg(F.avg("solar_irradiance").alias("_irr")))
    PV_IRR_DIURNAL = {}
    for _r in _wx.collect():
        PV_IRR_DIURNAL.setdefault(_r["building_id"], {})[int(_r["_hod"])] = float(_r["_irr"] or 0.0)
    HAS_PV_IRR = sum(len(v) for v in PV_IRR_DIURNAL.values()) > 0
    print(f"   PV irradiance diurnal: {len(PV_IRR_DIURNAL)} bina (gercek hava, son 60g)")
except Exception as _e:
    HAS_PV_IRR = False
    PV_IRR_DIURNAL = {}
    print(f"   PV: silver_weather_clean yok/bos -> fallback sinus ({str(_e)[:50]})")

def _pv_irr_shape(bid):
    """Bina icin saat-bazli irradiance vektoru (H, W/m2). Profil yoksa None -> sinus fallback."""
    prof = PV_IRR_DIURNAL.get(bid)
    if not prof:
        return None
    return np.array([prof.get(int(h), 0.0) for h in hour], dtype=float)
print(f"   doluluk profilleri hazır: {sorted(set(BUILDING_PROFILE.values()))}")

# -----------------------------------------------------------------------------
# 4) DEĞER MODELİ — sensor_type → saatlik ham seri (fault ÖNCESİ)
#    Tasarım ilkesi: sensörler VARSAYILAN olarak [setpoint_min,setpoint_max] içinde
#    kalır; anomaliler (a) gerçekçi gürültü (konfor sapması = Medium) ve (b) enjekte
#    fault'lardan (alarm eşiği aşımı = High) doğar. Doluluksuz dönemde sistematik
#    band-dışı değer ÜRETİLMEZ (örn. gece ışığı standby ≥300lux, gece setback hafif)
#    → sahte anomali yok, semantik dürüst.
# -----------------------------------------------------------------------------
def _noise(sd):
    return rng.normal(0.0, sd, H) * NOISE_SCALE

daylight = np.clip(np.sin(np.pi * (hour - 6.0) / 12.0), 0.0, 1.0)   # 0..1 gün ışığı (PV/ışık)

def build_base(s):
    st  = s["sensor_type"]; bid = s["building_id"]
    occ = OCC.get(bid, OCC["B001"])
    base = float(s["baseline_value"]) if s["baseline_value"] is not None else 0.0

    if   st == "HVAC_temp":         v = 22.0 + 1.4*np.sin(2*np.pi*(hour-15)/24.0) + _noise(1.7)
    elif st == "humidity":          v = 45.0 + 10.0*occ - 5.0*daylight + _noise(11.5)
    elif st == "CO2":               v = 420.0 + 820.0*occ + _noise(62.0)            # occ-tepe ~1040 → bazen >1000 (Medium)
    elif st == "VOC":               v = 70.0 + 240.0*occ + _noise(65.0)
    elif st == "PM2_5":             v = 7.5 + 5.0*occ + _noise(3.6)
    elif st == "PM10":              v = 16.0 + 11.0*occ + _noise(8.0)
    elif st == "CO":                v = 0.8 + 0.6*occ + _noise(0.3)
    elif st == "illuminance":       v = np.where(occ > 0.3, 500.0 + _noise(55.0), 330.0 + _noise(20.0))  # gece standby ≥300lux
    elif st == "sound_level":       v = 33.0 + 11.0*occ + _noise(4.3)
    elif st == "occupancy_pir":     v = (occ + _noise(0.12) > 0.30).astype(float)
    elif st == "people_count":      v = np.round(40.0*occ + _noise(2.5))
    elif st == "water_leak":        v = np.zeros(H)
    elif st == "building_kwh":      v = 0.33*base + 0.90*base*occ + _noise(0.04*base)
    elif st == "hvac_kwh":          v = 0.18*base + 0.80*base*occ + 0.15*base*np.sin(2*np.pi*frac) + _noise(0.05*base)
    elif st == "lighting_kwh":      v = 0.10*base + 1.05*base*occ + _noise(0.05*base)
    elif st == "plug_load_kwh":     v = 0.40*base + 0.70*base*occ + _noise(0.05*base)
    elif st == "power_factor":      v = 0.955 + _noise(0.02)
    elif st == "HVAC_supply_temp":  v = 14.0 + _noise(1.4)
    elif st == "HVAC_return_temp":  v = 24.0 + _noise(1.4)
    elif st == "chilled_water_temp":v = 7.0 + _noise(0.5)
    elif st == "valve_position":    v = 15.0 + 70.0*occ + _noise(8.0)
    elif st == "damper_position":   v = 25.0 + 45.0*occ + _noise(8.0)
    elif st == "filter_dp":         v = 110.0 + 80.0*frac + _noise(12.0)            # haftalık kirlenme trendi
    elif st == "fan_vfd_speed":     v = 45.0 + 40.0*occ + _noise(6.0)
    elif st == "chiller_cop":       v = 4.4 + 0.3*np.sin(2*np.pi*(hour-15)/24.0) + _noise(0.2)
    elif st == "boiler_eff":        v = 90.0 + _noise(1.5)
    elif st == "pump_pressure":     v = 250.0 + _noise(22.0)
    elif st == "water_flow":        v = 0.3*base + base*occ + _noise(0.1*base)
    elif st == "pv_ac_power":
        _peak = PV_PEAK_KW.get(bid, 35.0)
        _irr  = _pv_irr_shape(bid)
        if _irr is not None:
            v = _peak * np.clip(_irr / 1000.0, 0.0, 1.1) * PV_PR_INST * (1.0 + 0.08 * rng.standard_normal(H) * NOISE_SCALE)
        else:
            v = _peak * daylight * (0.6 + 0.4 * rng.random(H))   # fallback: jenerik gunes sinusu
    elif st == "battery_soc":
        chg = 30.0 + 60.0*np.clip((hour-9.0)/6.0, 0, 1)
        dis = 90.0 - 55.0*np.clip((hour-15.0)/7.0, 0, 1)
        v = np.where(hour < 15, chg, dis) + _noise(2.0)
    elif st == "ev_charger_power":
        sess = (rng.random(H) < 0.12) & (hour >= 8) & (hour <= 18)
        v = np.where(sess, rng.choice([11.0, 22.0], size=H), 0.0)
    else:
        v = np.full(H, base) + _noise(1.0)

    # Fiziksel alt/üst sınırlar (negatif güç/ppm vb. olmaz)
    NONNEG = {"building_kwh","hvac_kwh","lighting_kwh","plug_load_kwh","water_flow","pv_ac_power",
              "people_count","VOC","PM2_5","PM10","CO","valve_position","damper_position",
              "fan_vfd_speed","ev_charger_power","sound_level","filter_dp","pump_pressure"}
    if st in NONNEG:      v = np.clip(v, 0.0, None)
    if st == "CO2":       v = np.clip(v, 400.0, None)
    if st == "power_factor": v = np.clip(v, 0.0, 1.0)
    if st in ("valve_position","damper_position","fan_vfd_speed"): v = np.clip(v, 0.0, 100.0)
    if st == "battery_soc": v = np.clip(v, 5.0, 100.0)
    return v.astype(float)

# -----------------------------------------------------------------------------
# 5) FAULT KATALOĞU — ASHRAE G36 imzaları + tek-sensör eşik anomalileri
#    Pencereler hours_ago (0=now) ile; çoğu son 48s içinde → lookback=50 yakalar.
#    Değer override'ı VALUE'yu eşik dışına iter; severity sonra setpoint'ten türetilir.
# -----------------------------------------------------------------------------
INCIDENTS = [
    # --- AFDD korelasyon imzaları (11c, bina+zaman düzeyi) ---
    {"name":"R1_low_deltaT",      "building":"B009","sensor_type":"HVAC_supply_temp","equip_type":"AHU",  "when":"any",    "k":8, "max_ago":48,"val":20.0,  "sd":0.4},
    {"name":"R2_afterhours",      "building":"B001","sensor_type":"hvac_kwh",                              "when":"night",  "k":6, "max_ago":72,"val":28.0,  "sd":0.8},
    {"name":"R3_ventilation",     "building":"B001","sensor_type":"CO2","loc_contains":"Floor-1",          "when":"daytime","k":6, "max_ago":48,"val":1650.0,"sd":60.0},
    {"name":"R4_setpoint_notmet", "building":"B005","sensor_type":"HVAC_temp","loc_contains":"Floor-1",    "when":"daytime","k":6, "max_ago":48,"val":26.5, "sd":0.3},
    # --- tek-sensör eşik anomalileri (11b) ---
    {"name":"boiler_degraded",    "building":"B008","sensor_type":"boiler_eff",                            "when":"any",    "k":48,"max_ago":48,"val":72.0, "sd":1.0},
    {"name":"chiller_cop_low",    "building":"B009","sensor_type":"chiller_cop","equip_type":"Chiller",    "when":"any",    "k":18,"max_ago":36,"val":2.3,  "sd":0.15},
    {"name":"chw_temp_fault",     "building":"B009","sensor_type":"chilled_water_temp","equip_type":"Chiller","when":"any",    "k":8, "max_ago":30,"val":12.0, "sd":0.4},
    {"name":"low_power_factor",   "building":"B004","sensor_type":"power_factor",                          "when":"any",    "k":12,"max_ago":24,"val":0.82, "sd":0.01},
    {"name":"filter_clogged",     "building":"B001","sensor_type":"filter_dp","equip_type":"AHU",          "when":"any",    "k":24,"max_ago":24,"val":320.0,"sd":10.0},
    {"name":"pm25_spike",         "building":"B002","sensor_type":"PM2_5","loc_contains":"Floor-1",        "when":"daytime","k":6, "max_ago":24,"val":40.0, "sd":3.0},
    {"name":"pump_low_pressure",  "building":"B003","sensor_type":"pump_pressure","equip_type":"Pump",     "when":"any",    "k":16,"max_ago":36,"val":90.0, "sd":6.0},
    {"name":"water_leak_event",   "building":"B005","sensor_type":"water_leak","loc_contains":"Floor-2",   "when":"any",    "k":6, "max_ago":12,"val":1.0,  "sd":0.0},
    {"name":"pv_inverter_derate", "building":"B007","sensor_type":"pv_ac_power",                            "when":"daytime","k":18,"max_ago":72,"val":5.0,  "sd":1.0},
]
NIGHT   = np.isin(hour, [22, 23, 0, 1, 2, 3, 4, 5])
DAYTIME = (hour >= 10) & (hour <= 16)

def _recent_mask(when, k, max_ago):
    """En yeni K eşleşen saati seç → notebook hangi gün/saatte koşarsa koşsun imza GARANTİ
    (sabit hours_ago penceresi hafta sonu/geceye düşüp boş kalabiliyordu)."""
    pred = NIGHT if when == "night" else (DAYTIME if when == "daytime" else np.ones(H, bool))
    cand = sorted((i for i in range(H) if pred[i] and hours_ago[i] <= max_ago),
                  key=lambda i: hours_ago[i])
    m = np.zeros(H, bool)
    for i in cand[:k]:
        m[i] = True
    return m

def apply_faults(s, v):
    bid = s["building_id"]; st = s["sensor_type"]; loc = s["sensor_location"] or ""; eq = s["equipment_type"]
    for inc in INCIDENTS:
        if inc["building"] != bid or inc["sensor_type"] != st:                  continue
        if inc.get("loc_contains") and inc["loc_contains"] not in loc:          continue
        if inc.get("equip_type") and inc["equip_type"] != eq:                   continue
        m = _recent_mask(inc["when"], inc["k"], inc["max_ago"])
        if not m.any():                                                          continue
        v = np.where(m, inc["val"] + _noise(inc.get("sd", 0.3)), v)
    return v.astype(float)

# -----------------------------------------------------------------------------
# 6) Anomali türetme — 11b severity_from_setpoints ile BİREBİR (master eşikleri)
# -----------------------------------------------------------------------------
WASTE_KW = {"HVAC_temp":3.0,"CO2":2.0,"boiler_eff":3.0,"chiller_cop":3.0,"power_factor":1.0,
            "filter_dp":1.5,"PM2_5":0.5,"pump_pressure":1.5,"HVAC_supply_temp":2.0,
            "HVAC_return_temp":2.0,"humidity":0.5,"hvac_kwh":3.0}
GRID_PLACEHOLDER = 0.20   # €/kWh — KABA placeholder; gerçek ülke-bazlı maliyet = 11c (ref_electricity_tariffs, audit H1)

def derive_anomaly(v, smin, smax, alo, ahi, st):
    hi  = np.zeros(H, bool); med = np.zeros(H, bool); above = np.zeros(H, bool)
    if ahi is not None:  hi  |= v > ahi
    if alo is not None:  hi  |= v < alo
    if smax is not None: med |= v > smax; above |= v > smax
    if smin is not None: med |= v < smin
    if ahi is not None:  above |= v > ahi
    med = med & ~hi
    sev = np.full(H, None, dtype=object); sev[hi] = "High"; sev[med] = "Medium"
    atype = np.full(H, None, dtype=object)
    atype[hi] = "threshold_exceeded"
    atype[med & above] = "spike"
    atype[med & ~above] = "drift"
    insp = np.ones(H, bool)
    if smin is not None: insp &= v >= smin
    if smax is not None: insp &= v <= smax
    is_anom = hi | med
    cost = np.where(is_anom, round(WASTE_KW.get(st, 1.0) * GRID_PLACEHOLDER, 2), 0.0)
    return sev, atype, insp, is_anom, cost.astype(float)

# -----------------------------------------------------------------------------
# 7) Satır üretimi — her sensör × her saat. reading_quality protokole bağlı;
#    kablosuz sensörlerde küçük dropout (V2 uptime matrisi <100% görünsün).
#    NOT (ölçek): 515 nokta × ~168s ≈ 86k satır driver'da numpy-vektörel üretilir
#    (tek-seferlik snapshot için ideal). Fabric-ölçek alternatifi: time-spine DF ×
#    sensor DF cross-join + native expr (canlı EventStream zaten o yolu kullanır).
# -----------------------------------------------------------------------------
WIRELESS = {"LoRaWAN", "Zigbee", "MQTT", "OCPP/MQTT"}
rows = []
for s in sensors:
    v = apply_faults(s, build_base(s))
    smin, smax = s["setpoint_min"], s["setpoint_max"]
    alo, ahi   = s["alert_threshold_low"], s["alert_threshold_high"]
    sev, atype, insp, is_anom, cost = derive_anomaly(v, smin, smax, alo, ahi, s["sensor_type"])

    proto = s["source_protocol"]
    if proto in WIRELESS: q = 90.0 + 8.0 * rng.random(H); pdrop = 0.015
    else:                 q = 96.0 + 4.0 * rng.random(H); pdrop = 0.003
    keep = rng.random(H) > pdrop

    dev, bid, st, loc, unit = s["sensor_id"], s["building_id"], s["sensor_type"], s["sensor_location"], s["reading_unit"]
    base_val = float(s["baseline_value"]) if s["baseline_value"] is not None else None
    smin_f = float(smin) if smin is not None else None
    smax_f = float(smax) if smax is not None else None

    for i in range(H):
        if not keep[i]:
            continue
        rows.append((
            dev, bid, st, loc,
            float(round(v[i], 3)), unit, proto, ts_str[i], int(round(q[i])),
            smin_f, smax_f, base_val,
            bool(insp[i]), bool(is_anom[i]),
            (atype[i] if atype[i] is not None else None),
            (sev[i] if sev[i] is not None else None),
            None,                       # action_recommended → 11b action_udf doldurur (bronze fallback boş)
            float(cost[i]),
        ))

print(f"✅ {len(rows):,} ham telemetri satırı üretildi")

# -----------------------------------------------------------------------------
# 8) ŞEMA — 11b_iot_processing BRONZE_SCHEMA ile BİREBİR (18 kolon, sıra/tip aynı)
# -----------------------------------------------------------------------------
BRONZE_SCHEMA = StructType([
    StructField("device_id",          StringType(),  True),
    StructField("building_id",        StringType(),  True),
    StructField("sensor_type",        StringType(),  True),
    StructField("sensor_location",    StringType(),  True),
    StructField("reading_value",      FloatType(),   True),
    StructField("reading_unit",       StringType(),  True),
    StructField("source_protocol",    StringType(),  True),
    StructField("timestamp",          StringType(),  True),
    StructField("reading_quality",    IntegerType(), True),
    StructField("setpoint_min",       FloatType(),   True),
    StructField("setpoint_max",       FloatType(),   True),
    StructField("baseline_value",     FloatType(),   True),
    StructField("in_setpoint",        BooleanType(), True),
    StructField("is_anomaly",         BooleanType(), True),
    StructField("anomaly_type",       StringType(),  True),
    StructField("anomaly_severity",   StringType(),  True),
    StructField("action_recommended", StringType(),  True),
    StructField("cost_eur_estimate",  FloatType(),   True),
])

df = spark.createDataFrame(rows, schema=BRONZE_SCHEMA)
(df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
   .partitionBy("building_id").saveAsTable("bronze_iot_raw"))
print(f"✅ bronze_iot_raw yazıldı: {df.count():,} satır ({H} saat, biter {ts_str[-1]})")

# -----------------------------------------------------------------------------
# 9) DOĞRULAMA — şema, anomali oranı, FDD imza varlığı, protokol dağılımı
# -----------------------------------------------------------------------------
print("\n" + "=" * 64)
print("DOĞRULAMA")
print("=" * 64)

n      = df.count()
n_type = df.select("sensor_type").distinct().count()
n_bldg = df.select("building_id").distinct().count()
n_anom = df.filter(F.col("is_anomaly")).count()
rate   = n_anom / n * 100 if n else 0.0
print(f"Satır: {n:,} | sensor_type: {n_type} | bina: {n_bldg}")
print(f"Anomali oranı: {rate:.1f}%  (11b doğrulama hedefi 5–30%)")
if rate < 5:    print("  ⚠️ DÜŞÜK → noise_scale'i ARTIR (ör. 1.3) ve yeniden koş")
elif rate > 30: print("  ⚠️ YÜKSEK → noise_scale'i AZALT (ör. 0.8) ve yeniden koş")
else:           print("  ✅ aralıkta")

print("\nSeverity dağılımı:")
df.groupBy("anomaly_severity").count().orderBy(F.desc("count")).show(truncate=False)

# FDD/eşik imza varlığı (snapshot'ın canlı görünmesi için her biri >0 olmalı)
dfc = df.withColumn("hh", F.substring("timestamp", 12, 2).cast("int"))
NIGHT_H = [22, 23, 0, 1, 2, 3, 4, 5]
def sig(label, cond):
    c = dfc.filter(cond).count()
    print(f"  {'OK ' if c > 0 else 'YOK'} {label}: {c}")
print("\nAFDD korelasyon imzaları (11c için):")
sig("R1 LOW_DELTA_T   B009 supply→~20°C (Δ<5)",
    (F.col("building_id")=="B009") & (F.col("sensor_type")=="HVAC_supply_temp") & (F.col("reading_value")>18))
sig("R2 AFTER_HOURS   B003 hvac_kwh>5 @gece",
    (F.col("building_id")=="B003") & (F.col("sensor_type")=="hvac_kwh") & (F.col("reading_value")>5) & (F.col("hh").isin(NIGHT_H)))
sig("R3 VENTILATION   B001 CO2>1500",
    (F.col("building_id")=="B001") & (F.col("sensor_type")=="CO2") & (F.col("reading_value")>1500))
sig("R4 SETPOINT_NM   B005 HVAC_temp>24",
    (F.col("building_id")=="B005") & (F.col("sensor_type")=="HVAC_temp") & (F.col("reading_value")>24))
print("Tek-sensör eşik anomalileri (11b için):")
sig("boiler_eff<75   B008", (F.col("building_id")=="B008") & (F.col("sensor_type")=="boiler_eff") & (F.col("reading_value")<75))
sig("chiller_cop<2.5 B009", (F.col("building_id")=="B009") & (F.col("sensor_type")=="chiller_cop") & (F.col("reading_value")<2.5))
sig("power_factor<.85 B004",(F.col("building_id")=="B004") & (F.col("sensor_type")=="power_factor") & (F.col("reading_value")<0.85))
sig("filter_dp>300   B001", (F.col("building_id")=="B001") & (F.col("sensor_type")=="filter_dp") & (F.col("reading_value")>300))
sig("PM2.5>35        B002", (F.col("building_id")=="B002") & (F.col("sensor_type")=="PM2_5") & (F.col("reading_value")>35))
sig("pump_press<100  B003", (F.col("building_id")=="B003") & (F.col("sensor_type")=="pump_pressure") & (F.col("reading_value")<100))
sig("water_leak=1    B005", (F.col("building_id")=="B005") & (F.col("sensor_type")=="water_leak") & (F.col("reading_value")>0))

print("\nProtokol dağılımı (interoperability):")
df.groupBy("source_protocol").count().orderBy(F.desc("count")).show(truncate=False)

print("Şema (18 kolon — 11b BRONZE_SCHEMA ile birebir olmalı):")
for i, (cn, ct) in enumerate(df.dtypes, 1):
    print(f"  {i:2d}. {cn:<20} {ct}")

print("\nÖrnek anomali satırları:")
df.filter(F.col("is_anomaly")).select(
    "building_id","sensor_type","sensor_location","reading_value","reading_unit",
    "anomaly_severity","anomaly_type","timestamp").show(10, truncate=False)

print("✅ 01_bronze_iot_raw_generator tamamlandı.")
print("➡️  SONRAKİ: 11b_iot_processing  (spark.conf lookback_hours=50 — default 2h GOTCHA!)")
