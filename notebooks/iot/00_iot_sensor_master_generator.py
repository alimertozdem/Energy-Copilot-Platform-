# =============================================================================
# ENERGY COPILOT PLATFORM
# Notebook: 00_iot_sensor_master_generator.py
# Layer: GOLD — IoT SEMANTIC REGISTRY (Brick Schema + Project Haystack + ASHRAE 223P)
# Created: 2026-05-31
# =============================================================================
# GÖREV: gold_iot_sensor_master — IoT'nin "anlam katmanı". Her sensör noktası
#   Brick class + Haystack tag + ekipman + konum hiyerarşisi + protokol + birim +
#   setpoint/alarm ile etiketli. Sektörün yönü (Brick+Haystack+ASHRAE 223P
#   harmonizasyonu). bronze_iot_raw generator + 11b + 11c bu registry'den beslenir.
#
# 11b'nin okuduğu ÇEKİRDEK kolonlar (zorunlu, satır 83-89):
#   building_id, sensor_type, sensor_location,
#   setpoint_min, setpoint_max, alert_threshold_low, alert_threshold_high, baseline_value
# Ek SEMANTİK kolonlar (Page 8 + 11c + doküman):
#   sensor_id, floor, zone, equipment_ref, equipment_type, brick_class,
#   haystack_tags, point_group, reading_unit, source_protocol, vendor_model
# =============================================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

spark = SparkSession.builder.getOrCreate()
print("✅ IoT sensor master (Brick/Haystack/223P) generator başladı")

# -----------------------------------------------------------------------------
# SENSOR CATALOG — sensor_type -> (brick_class, haystack_tags, unit, protocol,
#   setpoint_min, setpoint_max, alert_low, alert_high, baseline, equip_type, group)
# brick_class = Brick Schema point class; haystack = Project Haystack marker tags.
# Setpoint/alarm aralıkları: ASHRAE 55 (konfor), ASHRAE 62.1 (IAQ/CO2), WELL (PM/VOC),
# EN 16798, ASHRAE G36 (HVAC ekipman) referansları.
# None = sınırsız (güç/sayaç sensörleri).
# -----------------------------------------------------------------------------
C = {
 # ---- IAQ / comfort ----
 "HVAC_temp":        ("Zone_Air_Temperature_Sensor",     "zone air temp sensor",        "degC",      "BACnet/IP",  20.0, 24.0, 18.0, 27.0, 22.0, "VAV",         "iaq_comfort"),
 "humidity":         ("Zone_Air_Humidity_Sensor",        "zone air humidity sensor",    "percentRH", "BACnet/IP",  30.0, 60.0, 25.0, 70.0, 45.0, "VAV",         "iaq_comfort"),
 "CO2":              ("CO2_Sensor",                       "zone air co2 sensor",         "ppm",       "LoRaWAN",   400.0,1000.0,400.0,1500.0,650.0,"Zone",        "iaq_comfort"),
 "VOC":              ("TVOC_Sensor",                      "zone air voc sensor",         "ppb",       "Zigbee",      0.0, 400.0,  0.0,1000.0,180.0,"Zone",        "iaq_comfort"),
 "PM2_5":            ("PM2.5_Sensor",                     "zone air pm25 sensor",        "ug/m3",     "Zigbee",      0.0,  15.0,  0.0,  35.0,  8.0,"Zone",        "iaq_comfort"),
 "PM10":             ("PM10_Sensor",                      "zone air pm10 sensor",        "ug/m3",     "Zigbee",      0.0,  45.0,  0.0,  50.0, 18.0,"Zone",        "iaq_comfort"),
 "CO":               ("CO_Sensor",                        "zone air co sensor",          "ppm",       "LoRaWAN",     0.0,   9.0,  0.0,  35.0,  1.0,"Zone",        "iaq_comfort"),
 "illuminance":      ("Illuminance_Sensor",               "zone illuminance sensor",     "lux",       "KNX",       300.0, 750.0,200.0,1500.0,500.0,"Lighting",    "iaq_comfort"),
 "sound_level":      ("Sound_Level_Sensor",               "zone sound sensor",           "dBA",       "Zigbee",     30.0,  45.0,  0.0,  60.0, 38.0,"Zone",        "iaq_comfort"),
 # ---- occupancy ----
 "occupancy_pir":    ("Occupancy_Sensor",                 "zone occupancy sensor",       "bool",      "Zigbee",      0.0,   1.0,  0.0,   1.0,  0.0,"Zone",        "occupancy"),
 "people_count":     ("Occupancy_Count_Sensor",           "zone occupancy count sensor", "count",     "MQTT",        0.0,  50.0,  0.0,  80.0, 12.0,"Zone",        "occupancy"),
 # ---- energy / power (sub-metering) ----
 "building_kwh":     ("Building_Electrical_Meter",        "elec meter power sensor",     "kW",        "Modbus/TCP",  0.0, None,  0.0, None,120.0,"Meter",       "energy"),
 "hvac_kwh":         ("HVAC_Electrical_Meter",            "hvac elec meter power sensor","kW",        "Modbus/TCP",  0.0, None,  0.0, None, 45.0,"Meter",       "energy"),
 "lighting_kwh":     ("Lighting_Electrical_Meter",        "lighting elec power sensor",  "kW",        "Modbus/TCP",  0.0, None,  0.0, None, 15.0,"Meter",       "energy"),
 "plug_load_kwh":    ("Plug_Load_Electrical_Meter",       "plugload elec power sensor",  "kW",        "Modbus/TCP",  0.0, None,  0.0, None, 20.0,"Meter",       "energy"),
 "power_factor":     ("Power_Factor_Sensor",              "elec pf sensor",              "ratio",     "Modbus/TCP",  0.9,  1.0, 0.85,  1.0, 0.96,"Meter",       "energy"),
 # ---- HVAC equipment telemetry (ASHRAE G36) ----
 "HVAC_supply_temp": ("Supply_Air_Temperature_Sensor",   "supply air temp sensor",      "degC",      "BACnet/IP",  12.0, 16.0, 10.0, 20.0, 14.0,"AHU",         "hvac_equip"),
 "HVAC_return_temp": ("Return_Air_Temperature_Sensor",   "return air temp sensor",      "degC",      "BACnet/IP",  22.0, 26.0, 20.0, 28.0, 24.0,"AHU",         "hvac_equip"),
 "chilled_water_temp":("Chilled_Water_Supply_Temperature_Sensor","chilled water supply temp sensor","degC","BACnet/IP",6.0,8.0,5.0,10.0,7.0,"Chiller","hvac_equip"),
 "valve_position":   ("Valve_Position_Sensor",           "valve position sensor",       "percent",   "BACnet/IP",   0.0,100.0,  0.0,100.0, 45.0,"AHU",         "hvac_equip"),
 "damper_position":  ("Damper_Position_Sensor",          "damper position sensor",      "percent",   "BACnet/IP",   0.0,100.0,  0.0,100.0, 30.0,"AHU",         "hvac_equip"),
 "filter_dp":        ("Filter_Differential_Pressure_Sensor","filter air pressure sensor","Pa",       "BACnet/IP",  50.0,250.0,  0.0,300.0,120.0,"AHU",         "hvac_equip"),
 "fan_vfd_speed":    ("Fan_VFD_Speed_Sensor",             "fan vfd speed sensor",        "percent",   "OPC-UA",      0.0,100.0,  0.0,100.0, 60.0,"AHU",         "hvac_equip"),
 "chiller_cop":      ("Coefficient_Of_Performance_Sensor","chiller efficiency cop sensor","ratio",    "OPC-UA",      3.5,  7.0,  2.5,  8.0,  4.5,"Chiller",     "hvac_equip"),
 "boiler_eff":       ("Efficiency_Sensor",                "boiler efficiency sensor",    "percent",   "Modbus/TCP", 85.0, 98.0, 75.0,100.0, 90.0,"Boiler",      "hvac_equip"),
 "pump_pressure":    ("Water_Differential_Pressure_Sensor","pump water pressure sensor", "kPa",       "Modbus/TCP",150.0,350.0,100.0,400.0,250.0,"Pump",        "hvac_equip"),
 # ---- water ----
 "water_flow":       ("Water_Flow_Sensor",                "water flow sensor",           "m3/h",      "M-Bus",       0.0, None,  0.0, None,  2.5,"Meter",       "water"),
 "water_leak":       ("Leak_Detection_Sensor",            "water leak sensor",           "bool",      "LoRaWAN",     0.0,  0.0,  0.0,   1.0,  0.0,"Zone",        "water"),
 # ---- renewables / EV ----
 "pv_ac_power":      ("PV_Generation_Power_Sensor",       "pv ac power sensor",          "kW",        "MQTT",        0.0, None,  0.0, None,  0.0,"PV_Inverter", "renewable_ev"),
 "battery_soc":      ("Battery_State_Of_Charge_Sensor",   "battery soc sensor",          "percent",   "MQTT",       10.0, 95.0,  5.0,100.0, 55.0,"Battery",     "renewable_ev"),
 "ev_charger_power": ("EV_Charger_Power_Sensor",          "evse power sensor",           "kW",        "OCPP/MQTT",   0.0, None,  0.0, None,  0.0,"EVSE",        "renewable_ev"),
}

# Sensör grupları (her zon / her bina / her ekipman hangi sensörleri taşır)
ZONE_SENSORS     = ["HVAC_temp","humidity","CO2","VOC","PM2_5","PM10","CO","illuminance","sound_level","occupancy_pir","people_count","water_leak"]
BUILDING_SENSORS = ["building_kwh","hvac_kwh","lighting_kwh","plug_load_kwh","power_factor","water_flow"]
EQUIP_SENSORS = {
    "AHU":     ["HVAC_supply_temp","HVAC_return_temp","valve_position","damper_position","filter_dp","fan_vfd_speed"],
    "Chiller": ["chilled_water_temp","chiller_cop","pump_pressure"],
    "Boiler":  ["boiler_eff"],
    "Pump":    ["pump_pressure"],
    "PV":      ["pv_ac_power"],
    "Battery": ["battery_soc"],
    "EVSE":    ["ev_charger_power"],
}

# Bina profilleri: building_id -> (n_zone, [ekipman örnekleri]). Gerçekçi dağılım.
BUILDINGS = {
    "B001": (3, ["AHU-1","AHU-2","Boiler-1","PV-1","EVSE-1"]),                 # DE Office
    "B002": (2, ["AHU-1","Boiler-1"]),                                        # TR Retail
    "B003": (3, ["AHU-1","AHU-2","Chiller-1","Pump-1"]),                      # AT/DE Hotel/Logistics
    "B004": (2, ["AHU-1","Boiler-1","PV-1"]),                                 # NL Hotel
    "B005": (4, ["AHU-1","AHU-2","Chiller-1","Boiler-1","Pump-1","Battery-1"]),# DE Healthcare (full BMS)
    "B006": (2, ["AHU-1","PV-1"]),                                            # NL Education
    "B007": (3, ["AHU-1","Chiller-1","PV-1","Battery-1","EVSE-1"]),           # DK Copenhagen Net-Plus
    "B008": (2, ["AHU-1","Boiler-1"]),                                        # DE Leipzig
    "B009": (4, ["AHU-1","AHU-2","Chiller-1","Chiller-2","Pump-1"]),          # DE Frankfurt Data Center (cooling-led)
    "B010": (3, ["AHU-1","Chiller-1","PV-1"]),                                # SE Stockholm Lab
}

# -----------------------------------------------------------------------------
# REGISTRY ÜRET
# -----------------------------------------------------------------------------
def make_row(bid, st, location, floor, zone, equip_ref, equip_type, sid):
    (brick, hay, unit, proto, smin, smax, alo, ahi, base, _eq, group) = C[st]
    sensor_id = f"{bid}-{st}-{location}".replace(" ", "")
    haystack = f"{hay} {group.replace('_',' ')}"
    vendor = {"BACnet/IP":"Siemens Desigo","BACnet/SC":"Siemens Desigo","Modbus/TCP":"Schneider PM","KNX":"ABB i-bus",
              "MQTT":"Generic MQTT","LoRaWAN":"Milesight AM319","Zigbee":"Aqara","OPC-UA":"Beckhoff","M-Bus":"Kamstrup","OCPP/MQTT":"ABB Terra"}.get(proto,"Generic")
    return (bid, sensor_id, st, location, floor, zone, equip_ref, equip_type,
            brick, haystack, group, unit, proto,
            smin, smax, alo, ahi, base, vendor)

rows = []
sid = 0
for bid, (nz, equips) in BUILDINGS.items():
    # Zon bazlı konfor/IAQ/doluluk sensörleri
    for z in range(1, nz + 1):
        floor = f"F{z}"
        zone  = f"Z{z}A"
        location = f"Floor-{z}-ZoneA"
        for st in ZONE_SENSORS:
            sid += 1
            rows.append(make_row(bid, st, location, floor, zone, f"VAV-{z}", "VAV", sid))
    # Bina geneli sayaçlar (sub-metering)
    for st in BUILDING_SENSORS:
        sid += 1
        rows.append(make_row(bid, st, "Main-Meter", "F0", "Main", "Main-Meter", "Meter", sid))
    # Ekipman telemetrisi
    for eq in equips:
        etype = eq.split("-")[0]          # "AHU-1" -> "AHU"
        for st in EQUIP_SENSORS.get(etype, []):
            sid += 1
            rows.append(make_row(bid, st, eq, "Plant", "Plant", eq, etype, sid))

print(f"✅ {len(rows)} sensör noktası üretildi ({len(BUILDINGS)} bina)")

SCHEMA = StructType([
    StructField("building_id",          StringType(), False),
    StructField("sensor_id",            StringType(), False),
    StructField("sensor_type",          StringType(), False),
    StructField("sensor_location",      StringType(), True),
    StructField("floor",                StringType(), True),
    StructField("zone",                 StringType(), True),
    StructField("equipment_ref",        StringType(), True),
    StructField("equipment_type",       StringType(), True),
    StructField("brick_class",          StringType(), True),
    StructField("haystack_tags",        StringType(), True),
    StructField("point_group",          StringType(), True),
    StructField("reading_unit",         StringType(), True),
    StructField("source_protocol",      StringType(), True),
    StructField("setpoint_min",         DoubleType(), True),
    StructField("setpoint_max",         DoubleType(), True),
    StructField("alert_threshold_low",  DoubleType(), True),
    StructField("alert_threshold_high", DoubleType(), True),
    StructField("baseline_value",       DoubleType(), True),
    StructField("vendor_model",         StringType(), True),
])

df = spark.createDataFrame(rows, schema=SCHEMA).withColumn("updated_at", F.current_timestamp())
(df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
   .partitionBy("building_id").saveAsTable("gold_iot_sensor_master"))
print(f"✅ gold_iot_sensor_master yazıldı: {df.count()} satır")

# -----------------------------------------------------------------------------
# DOĞRULAMA
# -----------------------------------------------------------------------------
print("\n📊 Protokol dağılımı (interoperability):")
df.groupBy("source_protocol").count().orderBy(F.desc("count")).show(truncate=False)
print("📊 Sensör grubu × bina:")
df.groupBy("point_group").agg(F.countDistinct("sensor_type").alias("sensor_tipi"), F.count("*").alias("nokta")).orderBy("point_group").show(truncate=False)
print("📊 Örnek (Brick/Haystack etiketli):")
df.select("building_id","sensor_type","sensor_location","brick_class","haystack_tags","source_protocol","reading_unit","setpoint_min","setpoint_max").show(8, truncate=False)
print("✅ 00_iot_sensor_master_generator tamamlandı.")
