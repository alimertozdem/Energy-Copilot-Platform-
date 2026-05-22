# PAGE 8: IoT Real-Time Monitoring & Anomaly Detection
**Status:** Implementation Ready | **DAX:** v44 (revised) | **Deadline:** 2026-05-14
**Last revised:** 2026-05-07 — full design review, sensor architecture expanded

---

## 📋 OVERVIEW

**Purpose:** Live building sensor data → real-time operational awareness + anomaly detection + energy waste estimation

**Users:**
- **Facility Manager** — "Is the building running OK right now? Any alerts to act on?"
- **Energy Manager** — "How much power am I consuming vs baseline? Is HVAC efficient?"

**Data Latency:**
- C1-C4 KPI cards: near real-time via KQL DirectQuery (seconds latency)
- V1-V4 visuals: 15-minute aggregated via DirectLake (gold Delta tables)

---

## 🗂️ SENSOR ARCHITECTURE (Dynamic — NOT hardcoded)

`sensor_type` is a dimension. Each building exposes only its connected sensor types.
Visuals adapt automatically — no code change needed when a new sensor type is added.

### Minimum Sensor Set (all buildings must have)

| sensor_type | unit | normal_range | alert_threshold |
|---|---|---|---|
| `HVAC_temp` | °C | 20–24 | <18 or >26 |
| `humidity` | % | 40–60 | <30 or >70 |
| `CO2` | ppm | 400–1000 | >1500 |
| `building_kwh` | kW | building-specific | >120% baseline |
| `hvac_kwh` | kW | building-specific | >110% of building_kwh share |

### Extended Sensor Set (full BMS buildings)

| sensor_type | unit | description |
|---|---|---|
| `HVAC_supply_temp` | °C | Supply air temp (pre-zone) |
| `HVAC_return_temp` | °C | Return air temp — delta-T = efficiency indicator |
| `lighting_kwh` | kW | Lighting sub-meter |
| `plug_load_kwh` | kW | Plug loads / equipment |
| `chiller_cop` | ratio | Chiller coefficient of performance |
| `boiler_eff` | % | Boiler combustion efficiency |
| `pump_pressure` | bar | Hydronic loop pressure |
| `fan_rpm` | RPM | AHU fan speed |

---

## 🗂️ DATA MODEL (Fabric Gold Layer)

### Table 1: `gold_iot_realtime` (15-min aggregated readings)

```
Column Name                  | Type      | Source        | Description
─────────────────────────────┼───────────┼───────────────┼──────────────────────────────
timestamp                    | datetime  | sensor        | 15-min interval bucket start
building_id                  | string    | static        | FK: silver_building_master
sensor_id                    | string    | sensor        | unique sensor identifier
sensor_type                  | string    | dimension     | dynamic (see sensor set above)
sensor_location              | string    | static        | "Floor 2, Zone A" / "AHU Unit 1"
reading_value                | float     | sensor        | actual measurement
reading_value_avg            | float     | calculated    | 15-min window average
reading_unit                 | string    | static        | °C, %, ppm, kW
reading_quality              | int       | sensor        | 0-100 (data completeness %)
setpoint_min                 | float     | config        | lower comfort/operation bound
setpoint_max                 | float     | config        | upper comfort/operation bound
in_setpoint                  | boolean   | calculated    | reading within setpoint range
is_anomaly                   | boolean   | calculated    | rule-based anomaly flag
anomaly_type                 | string    | calculated    | spike / drift / threshold_exceeded
anomaly_severity             | string    | calculated    | Low / Medium / High
anomaly_severity_window      | string    | calculated    | worst severity in 15-min window
duration_anomaly_minutes     | float     | calculated    | consecutive anomaly duration
cost_eur_estimate            | float     | calculated    | estimated € waste (see logic below)
action_recommended           | string    | calculated    | "Check HVAC Unit 2 — Floor 3"
is_resolved                  | boolean   | manual        | operator mark-as-resolved
```

### Table 2: `gold_iot_sensor_master` (sensor metadata — static config)

```
Column Name              | Type      | Description
─────────────────────────┼───────────┼──────────────────────────────
sensor_id                | string    | PK
building_id              | string    | FK: silver_building_master
sensor_type              | string    | dynamic type label
sensor_location          | string    | zone/room/equipment name
setpoint_min             | float     | configured normal range min
setpoint_max             | float     | configured normal range max
alert_threshold_low      | float     | alarm trigger low
alert_threshold_high     | float     | alarm trigger high
last_calibration_date    | date      | maintenance record
is_active                | boolean   | sensor currently monitored
install_date             | date      | commissioning date
baseline_value           | float     | 30-day rolling average (for deviation calc)
```

### Table 3: `gold_iot_daily_summary` (aggregated by day)

```
Column Name              | Type      | Description
─────────────────────────┼───────────┼──────────────────────────────
event_date               | date      | daily aggregate
building_id              | string    | FK
sensor_type              | string    | by type
avg_reading_value        | float     | mean reading
min_reading_value        | float     | minimum
max_reading_value        | float     | maximum
anomaly_count            | int       | total anomalies detected
high_severity_count      | int       | critical alerts only
avg_reading_quality      | float     | data quality %
total_cost_eur_estimate  | float     | total estimated € waste that day
compliance_pct           | float     | % of readings within setpoint
```

---

## 💸 ANOMALY COST ESTIMATION LOGIC

**Always shown as "Est. €XX" — never presented as exact.**

```python
# Cost per anomaly row in gold_iot_realtime
def estimate_cost(sensor_type, deviation, duration_hours, country):
    grid_price = {"DE": 0.20, "TR": 0.14, "EU": 0.18}.get(country, 0.18)

    if sensor_type == "HVAC_temp":
        # Each °C deviation from setpoint = 2-5 kW extra HVAC load
        power_waste_kw = abs(deviation) * 3.5  # midpoint estimate
    elif sensor_type == "CO2" and deviation > 500:  # >1500ppm
        # Extra ventilation needed: 1-3 kW
        power_waste_kw = 2.0
    elif sensor_type == "building_kwh":
        # Direct: actual excess kW visible
        power_waste_kw = max(0, deviation)
    else:
        power_waste_kw = 1.0  # default small estimate

    return round(duration_hours * power_waste_kw * grid_price, 2)
```

**Energy logic basis:**
- HVAC over/under-temperature rule: standard EN 15232 building automation standard
- CO2 ventilation: EN 13779 (indoor air quality) — extra fan power to dilute CO2
- Grid prices: German commercial tariff 2026 (not residential)

---

## 🧮 DAX MEASURES (v44 revised)

### KPI Cards

**C1: Real-time Building Power (kW)**
```dax
C1_Building_kW =
VAR LatestReading =
    CALCULATE(
        MAXX(gold_iot_realtime, gold_iot_realtime[timestamp]),
        gold_iot_realtime[sensor_type] = "building_kwh"
    )
VAR CurrentkW =
    CALCULATE(
        AVERAGE(gold_iot_realtime[reading_value]),
        gold_iot_realtime[sensor_type] = "building_kwh",
        gold_iot_realtime[timestamp] = LatestReading
    )
RETURN FORMAT(CurrentkW, "0.0") & " kW"

-- Color: green if <100% baseline, amber 100-120%, red >120%
C1_Building_kW_Color =
VAR CurrentkW = [C1_Building_kW_Raw]  -- raw numeric version
VAR Baseline =
    CALCULATE(
        AVERAGE(gold_iot_realtime[reading_value]),
        gold_iot_realtime[sensor_type] = "building_kwh",
        DATESINPERIOD(gold_iot_realtime[timestamp], NOW(), -30, DAY)
    )
VAR Ratio = DIVIDE(CurrentkW, Baseline, 1)
RETURN IF(Ratio > 1.2, "#FF0000", IF(Ratio > 1.0, "#FFC000", "#00B050"))
```

**C2: Zone Comfort Compliance %**
```dax
C2_Zone_Compliance_Pct =
VAR TotalReadings =
    CALCULATE(
        COUNTROWS(gold_iot_realtime),
        gold_iot_realtime[sensor_type] IN {"HVAC_temp", "humidity", "CO2"},
        gold_iot_realtime[timestamp] >= NOW() - 1  -- last 24h
    )
VAR InSetpointReadings =
    CALCULATE(
        COUNTROWS(gold_iot_realtime),
        gold_iot_realtime[sensor_type] IN {"HVAC_temp", "humidity", "CO2"},
        gold_iot_realtime[timestamp] >= NOW() - 1,
        gold_iot_realtime[in_setpoint] = TRUE()
    )
RETURN FORMAT(DIVIDE(InSetpointReadings, TotalReadings, 0) * 100, "0") & "% zones OK"
```

**C3: CO₂ Display**
```dax
C3_CO2_Display =
VAR MaxCO2 =
    CALCULATE(
        MAX(gold_iot_realtime[reading_value]),
        gold_iot_realtime[sensor_type] = "CO2"
    )
VAR Label =
    IF(MaxCO2 < 1000, "Good",
    IF(MaxCO2 < 1500, "Fair",
    "Poor — Ventilate"))
RETURN FORMAT(MaxCO2, "0") & " ppm — " & Label
```

**C4: Active Alerts + Estimated Cost**
```dax
C4_Active_High_Alerts =
CALCULATE(
    COUNTROWS(gold_iot_realtime),
    gold_iot_realtime[anomaly_severity] = "High",
    gold_iot_realtime[is_resolved] = FALSE()
)

C4_Alert_Cost_Today_EUR =
CALCULATE(
    SUM(gold_iot_realtime[cost_eur_estimate]),
    gold_iot_realtime[is_anomaly] = TRUE(),
    gold_iot_realtime[timestamp] >= TODAY()
)

C4_Alert_Label =
VAR Alerts = [C4_Active_High_Alerts]
VAR Cost = [C4_Alert_Cost_Today_EUR]
RETURN
    IF(Alerts = 0, "All Clear",
    FORMAT(Alerts, "0") & " High Alerts — Est. €" & FORMAT(Cost, "0"))
```

### Visual Measures

**V1: Power Trend (building + HVAC split)**
```dax
V1_Building_kW =
CALCULATE(
    AVERAGE(gold_iot_realtime[reading_value]),
    gold_iot_realtime[sensor_type] = "building_kwh"
)

V1_HVAC_kW =
CALCULATE(
    AVERAGE(gold_iot_realtime[reading_value]),
    gold_iot_realtime[sensor_type] = "hvac_kwh"
)

V1_Baseline_kW =
CALCULATE(
    AVERAGE(gold_iot_realtime[reading_value]),
    gold_iot_realtime[sensor_type] = "building_kwh",
    DATESINPERIOD(gold_iot_realtime[timestamp], MAX(gold_iot_realtime[timestamp]), -30, DAY)
)
-- Note: baseline used as constant reference line on chart
```

**V2: Sensor Uptime %**
```dax
V2_Sensor_Uptime_Pct =
DIVIDE(
    CALCULATE(
        COUNTROWS(gold_iot_realtime),
        gold_iot_realtime[reading_quality] > 80
    ),
    COUNTROWS(gold_iot_realtime),
    0
) * 100
```

**V3: Zone Setpoint Compliance**
```dax
V3_Zone_Compliance_Pct =
VAR ZoneReadings = COUNTROWS(gold_iot_realtime)
VAR InSetpoint =
    CALCULATE(
        COUNTROWS(gold_iot_realtime),
        gold_iot_realtime[in_setpoint] = TRUE()
    )
RETURN DIVIDE(InSetpoint, ZoneReadings, 0) * 100

V3_Zone_Out_Of_Range_Hours =
CALCULATE(
    SUMX(gold_iot_realtime, gold_iot_realtime[duration_anomaly_minutes]) / 60,
    gold_iot_realtime[in_setpoint] = FALSE()
)
```

**V4: Alert Table cost column**
```dax
V4_Cost_Per_Anomaly =
IF(
    gold_iot_realtime[is_anomaly] = TRUE(),
    gold_iot_realtime[cost_eur_estimate],
    BLANK()
)
```

---

## 🎨 LAYOUT (Revised)

```
┌─────────────────────────────────────────────────────────────────────┐
│  S1: Building ▾    S2: Date range [last 24h ▾]   S3: Sensor ▾      │
├──────────────┬──────────────┬──────────────┬──────────────────────  │
│     C1       │     C2       │     C3       │        C4              │
│  Building kW │ Zone OK %    │  CO₂ Level   │  3 Alerts — Est. €47  │
│   142 kW ↑  │  87% zones  │ 1,240 Fair   │  (red background)      │
├──────────────┴──────────────┴──────────────┴───────────────────────┤
│ V1: 24h Power Trend (kW)                                            │
│  — building_kwh (blue)   — hvac_kwh (teal)   ··· baseline (grey)  │
│  160 ┤                          ▲                                   │
│  140 ┤────────────────────▲▲────  ──────────                       │
│  120 ┤ ·····················  ·········· baseline                   │
│       00:00   04:00   08:00   12:00   16:00   20:00   24:00        │
├──────────────────────────────┬──────────────────────────────────────┤
│ V2: Sensor Uptime Matrix     │ V3: Zone Setpoint Compliance         │
│ [rows: zone, cols: type]     │ [rows: zone, cols: sensor_type]      │
│ Floor1/ZoneA: 99% 97% 100%   │ Floor1/ZoneA: HVAC ✅  CO2 ⚠️       │
│ Floor2/ZoneB: 95% 88%  92%   │ Floor2/ZoneB: HVAC ❌  CO2 ✅       │
│ Roof/AHU-1:  100%  -   98%   │ Roof/AHU-1:  HVAC ✅  CO2 ✅       │
├──────────────────────────────┴──────────────────────────────────────┤
│ V4: Active Anomaly Alert Table                                       │
├──────────┬────────┬──────┬──────┬───────────┬────────┬─────────────┤
│ Building │Location│Sensor│Value │Anomaly    │Severity│Action & Est.│
├──────────┼────────┼──────┼──────┼───────────┼────────┼─────────────┤
│ B002     │Fl2 AHU │HVAC  │18°C  │Threshold↓ │ HIGH   │Check AHU-2  │
│          │        │temp  │      │           │        │Est. €12/day │
├──────────┼────────┼──────┼──────┼───────────┼────────┼─────────────┤
│ B001     │Fl1 ZnB │CO2   │1800  │Threshold↑ │MEDIUM  │Ventilate B  │
│          │        │      │ ppm  │           │        │Est. €7/day  │
└──────────┴────────┴──────┴──────┴───────────┴────────┴─────────────┘
```

---

## 🧪 DATA GENERATION (Trial Period)

**File:** `sample-data/iot_device_simulator.py` (to be updated)

**Minimum sensor profile (all 6 buildings):**
- 5 sensor types minimum: HVAC_temp, humidity, CO2, building_kwh, hvac_kwh
- 96 readings per sensor per day (15-min intervals)
- 6 buildings × 5 sensors × 96 readings = 2,880 rows/day minimum
- Inject ~10% anomalies with realistic cost estimates

**Building-specific profiles (for realism):**

| Building | Extra Sensors | Country | Baseline kW |
|---|---|---|---|
| B001 (Berliner) | HVAC_supply_temp, HVAC_return_temp | DE | 85 kW |
| B002 (Amsterdam) | lighting_kwh, plug_load_kwh | EU | 120 kW |
| B003 (Hamburg) | chiller_cop | DE | 95 kW |
| B004 (Munich) | boiler_eff, pump_pressure | DE | 110 kW |
| B005 (Frankfurt) | HVAC_supply_temp | DE | 130 kW |
| B006 (Istanbul) | — (minimum set only) | TR | 200 kW |

---

## 🔧 PIPELINE (Notebook 11b — to be updated)

```
INPUT:
  bronze_iot_raw          (raw readings from EventStream)
  gold_iot_sensor_master  (sensor config: setpoints, baselines)

PROCESS:
1. Parse timestamps, validate sensor readings
2. Join with sensor_master to get setpoint_min/max, baseline_value
3. Compute in_setpoint boolean
4. Anomaly detection:
   - Threshold: reading < alert_threshold_low OR > alert_threshold_high
   - Spike: abs(reading - baseline) > 3 × rolling_stdev (15-min window)
   - Drift: 6h rolling avg deviates >5% from 30-day baseline
5. Assign severity: High (threshold exceeded) / Medium (spike) / Low (drift)
6. Calculate duration_anomaly_minutes (consecutive flagged readings)
7. Estimate cost_eur_estimate using anomaly cost logic
8. Generate action_recommended text (rule-based, sensor_type + severity)

OUTPUT:
  gold_iot_realtime        (15-min rows, all columns above)
  gold_iot_daily_summary   (daily aggregates per building + sensor_type)
```

---

## ✅ VALIDATION CHECKLIST

**Data completeness:**
- [ ] gold_iot_realtime: 6 buildings × 5+ sensors × 96 readings = 2,880+ rows/day
- [ ] building_kwh and hvac_kwh present for all buildings
- [ ] cost_eur_estimate > 0 for anomaly rows
- [ ] in_setpoint boolean correct (not all TRUE or all FALSE)

**KPI cards:**
- [ ] C1 building kW realistic (50-250 kW range per building size)
- [ ] C2 zone compliance 70-95% typical (not 100% — some anomalies always present)
- [ ] C3 CO2 400-1800 ppm range, label correct
- [ ] C4 shows integer alerts + €cost estimate ("3 High Alerts — Est. €47")

**Visuals:**
- [ ] V1 shows two lines (building + HVAC) — HVAC ~40-60% of building total
- [ ] V1 baseline line visible as dotted reference
- [ ] V2 matrix: no building × sensor_type combination is blank
- [ ] V3 shows at least one zone out of compliance (red/amber)
- [ ] V4 table has Est. €cost column with values > 0 for anomaly rows

**Interaction:**
- [ ] S1 (building) filters all visuals
- [ ] S2 (date) filters V1-V4 only, NOT C1-C4 (live cards unaffected)
- [ ] S3 (sensor type) filters V1, V2, V3, V4 — not C cards
- [ ] V3 click → V4 drills to that zone's alerts
