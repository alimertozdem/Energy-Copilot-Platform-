# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 11c_iot_fdd.py  (v3 — FULL AFDD ENGINE)
# Layer: GOLD — IoT Fault Detection & Diagnostics (ASHRAE Guideline 36 + APAR)
# Created: 2026-05-30 · Rewritten: 2026-06-01 (sector-grade full AFDD)
# =============================================================================
# GÖREV: Schneider EcoStruxure / Siemens Desigo / Clockworks-grade AFDD. Tek-sensör
#   eşiğinin ötesinde, AYNI bina+zamandaki sensörleri korele ederek arıza TEŞHİSİ
#   üretir; her teşhise confidence (kesinlik), priority (öncelik) ve probable_cause
#   (olası kök-neden) atar.
#
# v2→v3 DEĞİŞİKLİKLER:
#   1) LOCATION-CORRELATION FIX (kritik): v2 pivot'u sensor_location'a göre korele
#      ediyordu AMA supply/return=ekipman-loc, hvac_kwh=Main-Meter, CO2/HVAC_temp=
#      zon-loc → asla aynı location → R1/R3/R4 hiç fire ETMİYORDU. v3, bina-sayaç
#      sinyallerini (hvac_kwh, building_kwh, power_factor) BİNA+ts düzeyinde broadcast
#      eder; zon ve ekipman kuralları bu bağlamı kullanır. point_group ile granülerlik:
#        - zon kuralları   : groupBy(building, sensor_location, ts)  [iaq_comfort/occupancy]
#        - ekipman kuralları: groupBy(building, equipment_ref, ts)   [hvac_equip]
#        - bina kuralları   : groupBy(building, ts)                  [energy meters]
#   2) ~12 kural (ekipman-bazlı), v2'nin 4'ü yerine. Frozen taxonomy (FAULT_CODES).
#   3) Çıktı = WINDOW değil TEŞHİS düzeyi: (building, scope, fault_code, gün) başına
#      tek satır + occurrence_count(persistence) + first/last_seen + confidence + priority.
#   4) confidence/priority/probable_cause/energy_impact_kwh yeni kolonlar.
#
# DÜRÜSTLÜK (CLAUDE.md "uydurma mühendislik mantığı yok"): economizer-fault ve
#   eşzamanlı-ısıtma/soğutma kuralları KASITLI atlandı — dış-hava sıcaklığı ve ayrık
#   ısıtma/soğutma valfi sensörü mevcut sensör setinde YOK. Phase 2.5'te (OA temp +
#   split-valve) eklenir. Var olmayan veriden teşhis ÜRETİLMEZ.
#
# GERİYE-UYUMLULUK: gold_iot_fdd, DAX v59'un kullandığı kolonları KORUR
#   (fdd_rule, severity, description, recommended_action, cost_eur_estimate, event_date)
#   → mevcut Page 8 ölçüleri çalışmaya devam eder; yeni kolonlar ek (DAX v60 kullanır).
#
# MALİYET (audit H1): ref_electricity_tariffs ülke-bazlı grid fiyatı (hardcoded yok).
#   energy_impact_kwh = power_waste_kw × occurrence_count × READING_INTERVAL_H.
# NATIVE EXPR (audit H3): UDF YOK — when/otherwise + aritmetik (Catalyst-friendly).
#
# INPUT : silver_iot_normalized (11b), gold_iot_sensor_master, ref_electricity_tariffs,
#         silver_building_master
# OUTPUT: gold_iot_fdd (teşhis düzeyi)
# ⚠️ Fabric: default lakehouse PIN zorunlu. Pipeline: 11b → 11c (silver hazır olmalı).
# =============================================================================

from functools import reduce
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()
print("✅ IoT FDD engine v3 (full AFDD: G36 + APAR) başladı")

# -----------------------------------------------------------------------------
# Eşikler (frozen, sektör-tipik — standart referanslı)
# -----------------------------------------------------------------------------
DELTA_T_MIN_C   = 5.0     # min anlamlı supply-return Δ (ısı transferi)
HVAC_ACTIVE_KW  = 1.0     # bu üstü = HVAC "çalışıyor"
HVAC_HIGH_KW    = 5.0     # "yüksek" yük (setpoint-not-met için)
CO2_HIGH_PPM    = 1000.0  # EN 16798 IDA-2 üstü
COMFORT_MIN_C   = 20.0    # EN 16798 Cat II ısıtma
COMFORT_MAX_C   = 24.0    # EN 16798 Cat II soğutma
SUPPLY_MIN_C    = 12.0    # AHU supply-air bandı (soğutma)
SUPPLY_MAX_C    = 16.0
SUPPLY_FAULT_LO = 10.0    # supply-air FAULT deadband (band 12–16, ±2)
SUPPLY_FAULT_HI = 18.0
CHW_MIN_C       = 6.0     # chilled-water bandı
CHW_MAX_C       = 10.0
FILTER_DP_MAX   = 300.0   # Pa — tıkalı filtre
COP_MIN         = 2.5     # chiller min kabul COP
BOILER_EFF_MIN  = 75.0    # % — verim alt sınırı
PUMP_MIN_KPA    = 150.0
PUMP_MAX_KPA    = 350.0
PF_MIN          = 0.85    # güç faktörü alt sınırı (reaktif ceza)
PM25_MAX        = 35.0    # WELL / EN 16798
PM10_MAX        = 50.0
NIGHT_HOURS     = [22, 23, 0, 1, 2, 3, 4, 5]
# G36 transient bastırma: konfor bandı ≠ FAULT eşiği. Deadband + persistence ile gürültü bastır.
CO2_FAULT_PPM   = 1400.0  # ventilation FAULT (EN 16798 IDA-4 "poor"); 1000 sadece "elevated"
TEMP_FAULT_LO   = COMFORT_MIN_C - 2.0   # 18.0 °C (konfor bandı + 2.0 deadband)
TEMP_FAULT_HI   = COMFORT_MAX_C + 2.0   # 26.0 °C
MIN_OCCURRENCES = 2       # G36 persistence timer analoğu: <2 pencere/gün = transient → teşhis DEĞİL

# PV underperformance (Solar B) — kendine-referansli diurnal-medyan baseline
PV_UNDERPERF_RATIO_HI  = 0.40   # actual/expected bunun altinda -> HIGH (ciddi inverter/string arizasi)
PV_UNDERPERF_RATIO_MED = 0.60   # HI ustu ama bunun altinda -> MEDIUM (kismi soiling/golge)
PV_EXPECTED_MIN_KW     = 5.0    # beklenen bu ustundeyse "gunes saati" (gece/alacakaranlik elenir)
# Skorlama parametreleri
READING_INTERVAL_H   = float(spark.conf.get("reading_interval_h", "1.0"))  # snapshot=saatlik; canlı EventStream=0.25
EXPECTED_DAY_WINDOWS = 8.0   # persistence normalizasyonu: ≥8 pencere/gün = kalıcı arıza

# Granülerlik için sensör sınıfları (gold_iot_sensor_master.point_group)
METER_TYPES = ["hvac_kwh", "building_kwh", "power_factor", "pv_ac_power"]
ZONE_TYPES  = ["HVAC_temp", "humidity", "CO2", "PM2_5", "PM10"]
EQUIP_TYPES = ["HVAC_supply_temp", "HVAC_return_temp", "chilled_water_temp",
               "chiller_cop", "boiler_eff", "pump_pressure", "filter_dp",
               "valve_position", "damper_position", "fan_vfd_speed"]

# -----------------------------------------------------------------------------
# 1) Veri oku + semantik zenginleştir (equipment/point_group sensor_master'dan)
# -----------------------------------------------------------------------------
silver = spark.table("silver_iot_normalized").select(
    "building_id", "ts_bucket", "event_date", "sensor_type", "sensor_location",
    "reading_value", "reading_quality"
)
sm = spark.table("gold_iot_sensor_master").select(
    "building_id", "sensor_type", "sensor_location",
    "equipment_ref", "equipment_type", "point_group"
)
enr = silver.join(F.broadcast(sm), ["building_id", "sensor_type", "sensor_location"], "left") \
            .withColumn("hour", F.hour("ts_bucket"))

# ülke grid fiyatı (audit H1)
try:
    _tar = {r["country_code"]: r["avg_eur_kwh"]
            for r in spark.table("ref_electricity_tariffs").select("country_code", "avg_eur_kwh").collect()}
except Exception:
    _tar = {}
_grid_default = _tar.get("EU", 0.19)
df_country = spark.table("silver_building_master").select("building_id", "country_code", "building_type") \
    .withColumn("grid_price",
        F.when(F.col("country_code") == "DE", F.lit(_tar.get("DE", 0.226)))
         .when(F.col("country_code") == "TR", F.lit(_tar.get("TR", 0.085)))
         .when(F.col("country_code") == "AT", F.lit(_tar.get("AT", 0.190)))
         .when(F.col("country_code") == "NL", F.lit(_tar.get("NL", 0.205)))
         .otherwise(F.lit(_grid_default)))
print(f"   grid fiyatları: {_tar if _tar else '(ref yok → varsayılan)'}")

# -----------------------------------------------------------------------------
# 2) Korelasyon çerçeveleri — bina-sayaç bağlamı + zon pivotu + ekipman pivotu
#    (LOCATION-FIX: hvac_kwh/building_kwh BİNA+ts düzeyinde, sonra her scope'a join)
# -----------------------------------------------------------------------------
bm = (enr.filter(F.col("sensor_type").isin(METER_TYPES))
        .groupBy("building_id", "ts_bucket")
        .pivot("sensor_type", METER_TYPES).agg(F.avg("reading_value")))
q = enr.groupBy("building_id", "ts_bucket").agg(F.avg("reading_quality").alias("data_quality"))
bm = (bm.join(q, ["building_id", "ts_bucket"], "left")
        .join(F.broadcast(df_country), "building_id", "left")
        .withColumn("hour", F.hour("ts_bucket"))
        .withColumn("event_date", F.to_date("ts_bucket")))
# after-hours: STATİK building_type ile programlı-vs-24/7 (analiz penceresi hafta-sonuna
# düşse bile bağışık — pencereden türetilen profil kırılgandı). Programlı tipler (Office/
# Retail/Education) gece setback yapar → occupied-level gece çalışması = fault. 24/7 tipler
# (Hotel/Healthcare/Data_Center/Lab/Logistics) elenir; meşru gece çalışması fault DEĞİL.
# Eşik = sensor_master hvac baseline'ı (pencereden bağımsız, statik occupied referansı).
_hvb = (spark.table("gold_iot_sensor_master").filter(F.col("sensor_type") == "hvac_kwh")
          .groupBy("building_id").agg(F.first("baseline_value").alias("hvac_baseline")))
bm = bm.join(F.broadcast(_hvb), "building_id", "left")
SCHEDULED_TYPES = ["office", "retail", "education"]

# her scope'a taşınacak bina bağlamı
ctx = bm.select("building_id", "ts_bucket", "hvac_kwh", "building_kwh",
                "grid_price", "data_quality", "building_type", "hour", "event_date")

# Zon pivotu (iaq_comfort + occupancy)
zp = (enr.filter(F.col("point_group").isin("iaq_comfort", "occupancy"))
        .groupBy("building_id", "sensor_location", "ts_bucket")
        .pivot("sensor_type", ZONE_TYPES).agg(F.avg("reading_value"))
        .join(F.broadcast(ctx), ["building_id", "ts_bucket"], "left"))

# Ekipman pivotu (hvac_equip)
ep = (enr.filter(F.col("point_group") == "hvac_equip")
        .groupBy("building_id", "equipment_ref", "equipment_type", "ts_bucket")
        .pivot("sensor_type", EQUIP_TYPES).agg(F.avg("reading_value"))
        .join(F.broadcast(ctx), ["building_id", "ts_bucket"], "left"))

print(f"   çerçeveler: bina-bağlam={bm.count()} | zon-pencere={zp.count()} | ekipman-pencere={ep.count()}")

# -----------------------------------------------------------------------------
# 3) AFDD KURALLARI — frozen taxonomy. Her kural standart "finding" satırı üretir.
#    FAULT_CODES: SETPOINT_NOT_MET, VENTILATION_FAULT, IAQ_PARTICULATE, LOW_DELTA_T,
#      SUPPLY_AIR_TEMP_FAULT, FILTER_LOADING, COP_DEGRADATION, CHW_TEMP_FAULT,
#      BOILER_EFF_DEGRADATION, PUMP_PRESSURE_FAULT, AFTER_HOURS_HVAC, POWER_FACTOR_LOW
# -----------------------------------------------------------------------------
def finding(df, cond, scope_col, equip_type_col, point_group, fdd_rule, fault_code,
            severity, desc_col, cause, action, waste_col, exceed_col):
    return (df.filter(cond).select(
        "building_id",
        scope_col.alias("scope_key"),
        equip_type_col.alias("equipment_type"),
        F.lit(point_group).alias("point_group"),
        "ts_bucket", "event_date", "hour", "grid_price", "data_quality", "building_type",
        F.lit(fdd_rule).alias("fdd_rule"),
        F.lit(fault_code).alias("fault_code"),
        F.lit(severity).alias("severity"),
        desc_col.alias("description"),
        F.lit(cause).alias("probable_cause"),
        F.lit(action).alias("recommended_action"),
        waste_col.cast("double").alias("power_waste_kw"),
        F.least(F.lit(1.0), F.greatest(F.lit(0.0), exceed_col)).alias("exceed_norm"),
    ))

ZONE = F.col("sensor_location"); ZLAB = F.lit("Zone")
EQ   = F.col("equipment_ref")
BLD  = F.lit("BUILDING");       BLAB = F.lit("Building")
frames = []

# ===== ZON kuralları (zp) =====
frames.append(finding(zp,
    F.col("HVAC_temp").isNotNull() & (F.col("hvac_kwh") > HVAC_HIGH_KW)
      & ((F.col("HVAC_temp") < TEMP_FAULT_LO) | (F.col("HVAC_temp") > TEMP_FAULT_HI)),
    ZONE, ZLAB, "iaq_comfort", "Setpoint Not Met", "SETPOINT_NOT_MET", "Medium",
    F.concat(F.lit("Zone "), F.round("HVAC_temp", 1).cast("string"),
             F.lit("°C beyond comfort deadband (EN 16798 20–24 ±2) while HVAC at high load — cannot meet setpoint")),
    "HVAC capacity/fault, sensor miscalibration, or setpoint misconfiguration",
    "Inspect HVAC unit capacity/fault, sensor calibration, setpoint config",
    F.col("hvac_kwh") * F.lit(0.15),
    F.greatest(COMFORT_MIN_C - F.col("HVAC_temp"), F.col("HVAC_temp") - COMFORT_MAX_C) / F.lit(4.0)))

frames.append(finding(zp,
    F.col("CO2").isNotNull() & (F.col("CO2") > CO2_FAULT_PPM) & (F.col("hvac_kwh") > HVAC_ACTIVE_KW),
    ZONE, ZLAB, "iaq_comfort", "Ventilation Fault", "VENTILATION_FAULT", "High",
    F.concat(F.lit("CO2="), F.round("CO2", 0).cast("string"),
             F.lit("ppm despite HVAC active — insufficient fresh air")),
    "Outdoor-air damper closed/stuck, DCV setpoint too low, or economizer fault",
    "Inspect OA damper, demand-controlled ventilation setpoint, AHU economizer",
    F.lit(2.0), (F.col("CO2") - CO2_HIGH_PPM) / F.lit(1000.0)))

frames.append(finding(zp,
    (F.coalesce(F.col("PM2_5"), F.lit(0.0)) > PM25_MAX) | (F.coalesce(F.col("PM10"), F.lit(0.0)) > PM10_MAX),
    ZONE, ZLAB, "iaq_comfort", "IAQ Particulate", "IAQ_PARTICULATE", "Medium",
    F.concat(F.lit("Particulate high: PM2.5="), F.round(F.coalesce("PM2_5", F.lit(0.0)), 0).cast("string"),
             F.lit(" / PM10="), F.round(F.coalesce("PM10", F.lit(0.0)), 0).cast("string"),
             F.lit(" µg/m³ (WELL/EN 16798)")),
    "Insufficient filtration, outdoor infiltration, or indoor particulate source",
    "Upgrade/replace filtration (MERV), check OA intake, identify indoor source",
    F.lit(0.5),
    F.greatest((F.coalesce(F.col("PM2_5"), F.lit(0.0)) - PM25_MAX) / F.lit(35.0),
               (F.coalesce(F.col("PM10"), F.lit(0.0)) - PM10_MAX) / F.lit(50.0))))

# ===== AHU / ekipman kuralları (ep) =====
frames.append(finding(ep,
    F.col("HVAC_supply_temp").isNotNull() & F.col("HVAC_return_temp").isNotNull()
      & (F.col("hvac_kwh") > HVAC_ACTIVE_KW)
      & (F.abs(F.col("HVAC_supply_temp") - F.col("HVAC_return_temp")) < DELTA_T_MIN_C),
    EQ, F.col("equipment_type"), "hvac_equip", "Low Delta-T", "LOW_DELTA_T", "Medium",
    F.concat(F.lit("Low ΔT: |supply−return|="),
             F.round(F.abs(F.col("HVAC_supply_temp") - F.col("HVAC_return_temp")), 1).cast("string"),
             F.lit("°C while HVAC active — poor heat transfer")),
    "Control valve stuck, hydronic flow imbalance, or coil fouling/oversizing",
    "Check control valve, balance hydronic flow, verify pump/coil sizing",
    F.col("hvac_kwh") * F.lit(0.15),
    (DELTA_T_MIN_C - F.abs(F.col("HVAC_supply_temp") - F.col("HVAC_return_temp"))) / F.lit(DELTA_T_MIN_C)))

frames.append(finding(ep,
    F.col("HVAC_supply_temp").isNotNull() & (F.coalesce(F.col("fan_vfd_speed"), F.lit(0.0)) > 0)
      & ((F.col("HVAC_supply_temp") < SUPPLY_FAULT_LO) | (F.col("HVAC_supply_temp") > SUPPLY_FAULT_HI)),
    EQ, F.col("equipment_type"), "hvac_equip", "Supply-Air Temp Fault", "SUPPLY_AIR_TEMP_FAULT", "Medium",
    F.concat(F.lit("Supply-air "), F.round("HVAC_supply_temp", 1).cast("string"),
             F.lit("°C outside band (12–16 ±2) while AHU running — SAT not maintained")),
    "Cooling-coil/valve fault, chilled-water supply issue, or sensor drift",
    "Inspect cooling coil, control valve, chilled-water temp, sensor calibration",
    F.coalesce(F.col("hvac_kwh"), F.lit(0.0)) * F.lit(0.12),
    F.greatest(SUPPLY_MIN_C - F.col("HVAC_supply_temp"), F.col("HVAC_supply_temp") - SUPPLY_MAX_C) / F.lit(4.0)))

frames.append(finding(ep,
    F.col("filter_dp").isNotNull() & (F.col("filter_dp") > FILTER_DP_MAX),
    EQ, F.col("equipment_type"), "hvac_equip", "Filter Loading", "FILTER_LOADING", "Medium",
    F.concat(F.lit("Filter ΔP="), F.round("filter_dp", 0).cast("string"),
             F.lit("Pa (>300) — clogged filter increasing fan energy")),
    "Air filter loaded/clogged past replacement threshold",
    "Replace air filter; review filter-change schedule",
    F.lit(1.5), (F.col("filter_dp") - FILTER_DP_MAX) / F.lit(150.0)))

frames.append(finding(ep,
    F.col("chiller_cop").isNotNull() & (F.col("chiller_cop") < COP_MIN),
    EQ, F.col("equipment_type"), "hvac_equip", "Chiller COP Degradation", "COP_DEGRADATION", "High",
    F.concat(F.lit("Chiller COP="), F.round("chiller_cop", 1).cast("string"),
             F.lit(" (<2.5) — efficiency degraded")),
    "Low refrigerant charge, condenser/evaporator fouling, or compressor wear",
    "Check refrigerant charge, clean heat exchangers, inspect compressor",
    F.lit(3.0), (COP_MIN - F.col("chiller_cop")) / F.lit(COP_MIN)))

frames.append(finding(ep,
    F.col("chilled_water_temp").isNotNull()
      & ((F.col("chilled_water_temp") < CHW_MIN_C) | (F.col("chilled_water_temp") > CHW_MAX_C)),
    EQ, F.col("equipment_type"), "hvac_equip", "Chilled-Water Temp Fault", "CHW_TEMP_FAULT", "Medium",
    F.concat(F.lit("Chilled-water "), F.round("chilled_water_temp", 1).cast("string"),
             F.lit("°C outside band (6–10) — CHW reset/control fault")),
    "CHW setpoint/reset misconfiguration, valve fault, or sensor drift",
    "Verify CHW setpoint/reset schedule, valve operation, sensor calibration",
    F.lit(1.5),
    F.greatest(CHW_MIN_C - F.col("chilled_water_temp"), F.col("chilled_water_temp") - CHW_MAX_C) / F.lit(4.0)))

frames.append(finding(ep,
    F.col("boiler_eff").isNotNull() & (F.col("boiler_eff") < BOILER_EFF_MIN),
    EQ, F.col("equipment_type"), "hvac_equip", "Boiler Efficiency Degradation", "BOILER_EFF_DEGRADATION", "High",
    F.concat(F.lit("Boiler efficiency "), F.round("boiler_eff", 0).cast("string"),
             F.lit("% (<75) — combustion degraded")),
    "Burner fouling, poor combustion tuning, or heat-exchanger scaling",
    "Schedule boiler service: combustion tuning, clean heat exchanger",
    F.lit(3.0), (BOILER_EFF_MIN - F.col("boiler_eff")) / F.lit(BOILER_EFF_MIN)))

frames.append(finding(ep,
    F.col("pump_pressure").isNotNull()
      & ((F.col("pump_pressure") < PUMP_MIN_KPA) | (F.col("pump_pressure") > PUMP_MAX_KPA)),
    EQ, F.col("equipment_type"), "hvac_equip", "Pump Pressure Fault", "PUMP_PRESSURE_FAULT", "Medium",
    F.concat(F.lit("Pump ΔP "), F.round("pump_pressure", 0).cast("string"),
             F.lit("kPa outside band (150–350)")),
    "Low: leak/cavitation/valve-open; High: blockage/closed-valve/strainer",
    "Inspect for leaks/blockage, check expansion vessel and isolation valves",
    F.lit(1.5),
    F.greatest(PUMP_MIN_KPA - F.col("pump_pressure"), F.col("pump_pressure") - PUMP_MAX_KPA) / F.lit(100.0)))

# ===== BİNA kuralları (bm) =====
frames.append(finding(bm,
    F.col("hvac_kwh").isNotNull() & (F.col("hour").isin(NIGHT_HOURS))
      & (F.lower(F.col("building_type")).isin(SCHEDULED_TYPES))             # programlı bina (statik tip)
      & (F.col("hvac_kwh") > F.lit(0.5) * F.coalesce(F.col("hvac_baseline"), F.lit(45.0))),  # occupied-level gece spike'ı
    BLD, BLAB, "energy", "After-Hours HVAC", "AFTER_HOURS_HVAC", "High",
    F.concat(F.lit("HVAC running at "), F.col("hour").cast("string"),
             F.lit(":00 (off-hours) — schedule deviation")),
    "BMS time-schedule error or manual override left active",
    "Review BMS time schedule / occupancy override; enable night setback",
    F.col("hvac_kwh"), F.col("hvac_kwh") / F.lit(HVAC_HIGH_KW)))

frames.append(finding(bm,
    F.col("power_factor").isNotNull() & (F.col("power_factor") < PF_MIN),
    BLD, BLAB, "energy", "Low Power Factor", "POWER_FACTOR_LOW", "Medium",
    F.concat(F.lit("Power factor "), F.round("power_factor", 2).cast("string"),
             F.lit(" (<0.85) — reactive-power penalty risk")),
    "Inductive load (motors) without correction, or lightly-loaded oversized equipment",
    "Add/verify power-factor correction (capacitor bank); review motor loading",
    F.coalesce(F.col("building_kwh"), F.lit(0.0)) * F.lit(0.05),
    (PF_MIN - F.col("power_factor")) / F.lit(PF_MIN)))

# ===== RENEWABLE: PV daytime underperformance (Solar B) =====
# Beklenen = pv_ac_power'in bina x saat-of-day MEDYANI (kendine-referansli). Arizali
# saatler azinlikta kaldigindan medyan saglikli kalir -> bulutlu-gun yanlis-pozitif YOK.
pv_base = (bm.filter(F.col("pv_ac_power").isNotNull())
             .groupBy("building_id", "hour")
             .agg(F.expr("percentile_approx(pv_ac_power, 0.5)").alias("pv_expected")))
pvf = (bm.filter(F.col("pv_ac_power").isNotNull())
         .join(F.broadcast(pv_base), ["building_id", "hour"], "left")
         .withColumn("pv_ratio",
             F.when(F.col("pv_expected") > 0, F.col("pv_ac_power") / F.col("pv_expected"))
              .otherwise(F.lit(1.0))))
_pv_desc = F.concat(
    F.lit("PV output "), F.round(F.col("pv_ratio") * 100.0, 0).cast("int").cast("string"),
    F.lit("% of expected ("), F.round("pv_ac_power", 1).cast("string"),
    F.lit(" vs "), F.round("pv_expected", 1).cast("string"),
    F.lit(" kW) — daytime underperformance"))
_pv_solar  = F.col("pv_expected") > F.lit(PV_EXPECTED_MIN_KW)
_pv_waste  = F.greatest(F.lit(0.0), F.col("pv_expected") - F.col("pv_ac_power"))
_pv_exceed = F.lit(1.0) - F.col("pv_ratio")
frames.append(finding(pvf,
    _pv_solar & (F.col("pv_ratio") < F.lit(PV_UNDERPERF_RATIO_HI)),
    BLD, F.lit("PV_Inverter"), "renewable_ev", "PV Daytime Underperformance", "PV_UNDERPERFORMANCE", "High",
    _pv_desc,
    "Inverter/string fault, heavy soiling, or new shading reducing PV yield",
    "Inspect inverter & DC strings; clean modules; check for new shading/obstruction",
    _pv_waste, _pv_exceed))
frames.append(finding(pvf,
    _pv_solar & (F.col("pv_ratio") >= F.lit(PV_UNDERPERF_RATIO_HI)) & (F.col("pv_ratio") < F.lit(PV_UNDERPERF_RATIO_MED)),
    BLD, F.lit("PV_Inverter"), "renewable_ev", "PV Daytime Underperformance", "PV_UNDERPERFORMANCE", "Medium",
    _pv_desc,
    "Partial soiling, minor shading, or early-stage inverter degradation",
    "Schedule module cleaning & inverter check; monitor output trend",
    _pv_waste, _pv_exceed))

df_find = reduce(DataFrame.unionByName, frames)
print(f"   ham bulgu (pencere düzeyi): {df_find.count()}")

# -----------------------------------------------------------------------------
# 4) TEŞHİS DÜZEYİ — pencere bulgularını (building, scope, fault, gün) başına indir;
#    occurrence_count = persistence (kalıcılık). confidence/priority/energy/cost skorla.
# -----------------------------------------------------------------------------
diag = (df_find.groupBy("building_id", "scope_key", "equipment_type", "point_group",
                        "fdd_rule", "fault_code", "severity", "event_date")
    .agg(
        F.count(F.lit(1)).alias("occurrence_count"),
        F.min("ts_bucket").alias("first_seen"),
        F.max("ts_bucket").alias("last_seen"),
        F.round(F.avg("power_waste_kw"), 3).alias("power_waste_kw"),
        F.avg(F.coalesce("data_quality", F.lit(90.0))).alias("_q"),
        F.first("probable_cause").alias("probable_cause"),
        F.first("recommended_action").alias("recommended_action"),
        F.first("building_type").alias("building_type"),
        F.first("grid_price").alias("grid_price"),
        F.max(F.struct("exceed_norm", "description")).alias("_worst"),
    )
    .withColumn("description", F.col("_worst.description"))
    .withColumn("max_exceed", F.col("_worst.exceed_norm"))
    .drop("_worst"))

diag = (diag
    # enerji + maliyet (audit H1: ülke grid fiyatı; READING_INTERVAL_H ile saatlik snapshot)
    .withColumn("energy_impact_kwh", F.round(F.col("power_waste_kw") * F.col("occurrence_count") * F.lit(READING_INTERVAL_H), 2))
    .withColumn("cost_eur_estimate", F.round(F.col("energy_impact_kwh") * F.col("grid_price"), 2))
    # confidence = 0.4·persistence + 0.4·magnitude + 0.2·data_quality  (taban 0.3)
    .withColumn("_persist", F.least(F.lit(1.0), F.col("occurrence_count") / F.lit(EXPECTED_DAY_WINDOWS)))
    .withColumn("_qn", F.col("_q") / F.lit(100.0))
    .withColumn("confidence", F.round(F.greatest(F.lit(0.3),
        F.lit(0.4) * F.col("_persist") + F.lit(0.4) * F.col("max_exceed") + F.lit(0.2) * F.col("_qn")), 2))
    # priority_score (0–100) = 100·sev·confidence·(0.5 + 0.5·cost_norm)
    .withColumn("_sevw", F.when(F.col("severity") == "High", 1.0).when(F.col("severity") == "Medium", 0.6).otherwise(0.3))
    .withColumn("_costn", F.least(F.lit(1.0), F.col("cost_eur_estimate") / F.lit(50.0)))
    .withColumn("priority_score",
        F.round(F.lit(100.0) * F.col("_sevw") * F.col("confidence") * (F.lit(0.5) + F.lit(0.5) * F.col("_costn")), 0).cast("int"))
    .withColumn("equipment", F.col("scope_key"))
    .withColumn("timestamp", F.col("last_seen"))           # geriye-uyum: bazı görseller son-görülme ister
    .withColumn("detected_at", F.current_timestamp())
    .drop("_q", "_persist", "_qn", "_sevw", "_costn", "max_exceed", "scope_key"))

df_fdd = diag.select(
    "building_id", "equipment", "equipment_type", "point_group",
    "fdd_rule", "fault_code", "severity", "confidence", "priority_score",
    "description", "probable_cause", "recommended_action",
    "occurrence_count", "first_seen", "last_seen", "timestamp",
    "power_waste_kw", "energy_impact_kwh", "cost_eur_estimate",
    "grid_price", "building_type", "event_date", "detected_at",
)

# G36 persistence: transient tek-pencere bulgularını teşhisten düşür (gürültü bastırma)
df_fdd = df_fdd.filter(F.col("occurrence_count") >= MIN_OCCURRENCES)

# schema-evolution (gotcha): önce DROP → overwriteSchema temiz şema
spark.sql("DROP TABLE IF EXISTS gold_iot_fdd")
(df_fdd.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
    .partitionBy("building_id").saveAsTable("gold_iot_fdd"))
print(f"✅ gold_iot_fdd yazıldı: {df_fdd.count()} TEŞHİS satırı")

# -----------------------------------------------------------------------------
# 5) Doğrulama
# -----------------------------------------------------------------------------
print("\n📊 Fault kodu × ciddiyet (teşhis sayısı + ort. confidence + toplam €):")
df_fdd.groupBy("fault_code", "severity").agg(
    F.count("*").alias("teshis"),
    F.round(F.avg("confidence"), 2).alias("avg_conf"),
    F.round(F.sum("cost_eur_estimate"), 1).alias("toplam_eur"),
).orderBy(F.desc("teshis")).show(30, truncate=False)

print("📊 En yüksek öncelikli 10 teşhis (facility manager kuyruğu):")
df_fdd.orderBy(F.desc("priority_score")).select(
    "building_id", "equipment", "fault_code", "severity",
    "priority_score", "confidence", "occurrence_count", "cost_eur_estimate").show(10, truncate=False)

_codes = [r[0] for r in df_fdd.select("fault_code").distinct().collect()]
print(f"📋 Aktif fault kodları ({len(_codes)}): {sorted(_codes)}")
_cf = df_fdd.select(F.min("confidence").alias("min"), F.max("confidence").alias("max"), F.avg("confidence").alias("avg")).first()
print(f"📋 confidence aralığı: min={_cf['min']:.2f} max={_cf['max']:.2f} avg={_cf['avg']:.2f}")

print("""
📋 ENTEGRASYON (Page 8):
   - gold_iot_fdd KOLONLARI: v59 DAX'in kullandıkları KORUNDU (fdd_rule, severity,
     description, recommended_action, cost_eur_estimate, event_date) → mevcut ölçüler çalışır.
   - YENİ kolonlar (DAX v60 için): fault_code, equipment, equipment_type, confidence,
     priority_score, probable_cause, occurrence_count, energy_impact_kwh, first/last_seen.
   - V5 'FDD Findings' tablosu: priority_score DESC sırala; equipment + fault_code +
     confidence% + Est.€ göster. C4 kartı: IoT FDD High Today + Cost (v59 ölçüleri aynen).
   - Pipeline: 11b_iot_processing → 11c_iot_fdd (silver_iot_normalized hazır olmalı).
""")
print("✅ 11c_iot_fdd v3 (full AFDD) tamamlandı.")
