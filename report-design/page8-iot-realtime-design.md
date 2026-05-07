# PAGE 8: IoT Real-Time Monitoring & Anomaly Detection
**Status:** Design Phase | **Target:** DAX v43-v45 | **Deadline:** 2026-05-17

---

## 📋 OVERVIEW

**Purpose:** Live building data (HVAC, sensors, BACnet/MQTT) → real-time anomaly detection + actionable alerts

**Data Latency:** 15-minute interval (Phase 1) → Real-time streaming (Phase 2 with Eventstream)

**Target Users:**
- Facility Managers (daily operations)
- Energy Operators (shift monitoring)
- Facility Technicians (maintenance alerts)

---

## 🗂️ DATA MODEL (Fabric Gold Layer)

### Table 1: `gold_iot_realtime` (15-min aggregated readings)

```
Column Name              | Type      | Source        | Description
─────────────────────────┼───────────┼───────────────┼──────────────────────
timestamp               | datetime  | sensor        | 15-min interval
building_id             | string    | static        | FK: silver_building_master
sensor_id               | string    | sensor        | unique identifier
sensor_type             | string    | static        | HVAC_temp, humidity, CO2, power
sensor_location         | string    | static        | "Floor 2, Zone A", "AHU Unit 1"
reading_value           | float     | sensor        | actual measurement
reading_unit            | string    | static        | °C, %, ppm, kW
reading_quality         | int       | sensor        | 0-100 (% data completeness)
is_anomaly              | boolean   | calculated    | detected by rule-based logic
anomaly_type            | string    | calculated    | spike, drift, threshold_exceeded
anomaly_severity        | string    | calculated    | Low, Medium, High
action_recommended      | string    | calculated    | "Check HVAC", "Inspect sensor"
is_resolved             | boolean   | manual        | operator mark-as-resolved
resolved_timestamp      | datetime  | manual        | when resolved by operator
```

### Table 2: `gold_iot_sensor_master` (sensor metadata)

```
Column Name              | Type      | Source        | Description
─────────────────────────┼───────────┼───────────────┼──────────────────────
sensor_id               | string    | static        | PK
building_id             | string    | static        | FK: silver_building_master
sensor_type             | string    | static        | HVAC_temp, humidity, CO2, power
sensor_location         | string    | static        | zone/room name
setpoint_min            | float     | config        | normal range min
setpoint_max            | float     | config        | normal range max
alert_threshold_low     | float     | config        | alarm if below
alert_threshold_high    | float     | config        | alarm if above
last_calibration_date   | date      | manual        | maintenance tracking
is_active               | boolean   | static        | sensor currently monitored
install_date            | date      | static        | commissioning date
```

### Table 3: `gold_iot_daily_summary` (aggregated by day)

```
Column Name              | Type      | Source        | Description
─────────────────────────┼───────────┼───────────────┼──────────────────────
date                    | date      | calculated    | daily aggregate
building_id             | string    | static        | FK
sensor_type             | string    | static        | by type
avg_reading_value       | float     | aggregated    | mean
min_reading_value       | float     | aggregated    | minimum
max_reading_value       | float     | aggregated    | maximum
anomaly_count           | int       | count         | # anomalies detected
high_severity_count     | int       | count         | critical alerts
avg_reading_quality     | float     | aggregated    | data quality %
```

---

## 🧮 DAX MEASURES (v43-v45)

### KPI Cards (C1-C4)

**C1: Current HVAC Status (Text)**
```dax
-- v43_C1_HVAC_Status_Text
VAR CurrentTemp = MAXX(
    FILTER(gold_iot_realtime, gold_iot_realtime[sensor_type] = "HVAC_temp"),
    gold_iot_realtime[reading_value]
)
VAR Status = IF(
    AND(CurrentTemp >= 20, CurrentTemp <= 24),
    "Normal",
    IF(CurrentTemp < 20, "Low", "High")
)
RETURN Status & " (" & FORMAT(CurrentTemp, "0.0°C") & ")"
```

**C2: Avg Room Temperature vs Setpoint (Gauge)**
```dax
-- v43_C2_Temp_Variance
VAR AvgTemp = AVERAGEX(
    FILTER(gold_iot_realtime, gold_iot_realtime[sensor_type] = "HVAC_temp"),
    gold_iot_realtime[reading_value]
)
VAR Setpoint = 22
RETURN AvgTemp - Setpoint  -- negative = too cold, positive = too hot
```

**C3: CO₂ Level & Air Quality (Card)**
```dax
-- v43_C3_CO2_Current
MAXX(
    FILTER(gold_iot_realtime, gold_iot_realtime[sensor_type] = "CO2"),
    gold_iot_realtime[reading_value]
)

-- v43_C3_CO2_Quality_Label
VAR CO2 = [v43_C3_CO2_Current]
RETURN IF(CO2 < 1000, "Good", IF(CO2 < 1500, "Fair", "Poor"))
```

**C4: Active High-Severity Alerts (Card)**
```dax
-- v43_C4_Active_Alerts_High
CALCULATE(
    COUNTROWS(gold_iot_realtime),
    gold_iot_realtime[anomaly_severity] = "High",
    gold_iot_realtime[is_resolved] = FALSE()
)
```

### Visuals (V1-V4)

**V1: 24h Temperature Trend (Line Chart)**
```dax
-- v43_V1_Temp_LastDay
CALCULATE(
    AVERAGEX(gold_iot_realtime, gold_iot_realtime[reading_value]),
    gold_iot_realtime[sensor_type] = "HVAC_temp",
    gold_iot_realtime[timestamp] >= TODAY() - 1
)

-- X-axis: timestamp (15-min), Y-axis: reading_value
```

**V2: Sensor Network Status (Heatmap Grid)**
```dax
-- v43_V2_Sensor_Uptime_Pct
DIVIDE(
    CALCULATE(
        COUNTA(gold_iot_realtime[reading_value]),
        gold_iot_realtime[reading_quality] > 80
    ),
    COUNTA(gold_iot_realtime[reading_value])
) * 100

-- Rows: sensor_location, Columns: sensor_type, Values: uptime %
```

**V3: Temperature vs Humidity Scatter (by zone)**
```dax
-- v43_V3_Scatter_Temp_Humidity
-- X: avg temperature by location, Y: avg humidity by location
-- Size: anomaly count, Color: severity (red=high)
```

**V4: Real-time Sensor Readings (Table)**
```
Columns: sensor_location | sensor_type | reading_value | unit | anomaly_type | severity | action_recommended
Data: last 96 readings (24h @ 15-min interval)
Sorting: severity DESC, timestamp DESC
```

---

## 🎨 LAYOUT (Power BI Canvas)

```
┌────────────────────────────────────────────────────────────────────┐
│ 🔴 PAGE 8: IoT Real-Time Monitoring & Anomaly Detection           │
└────────────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│      C1         │  │      C2         │  │      C3         │  │      C4         │
│  HVAC Status    │  │  Temp Variance  │  │  CO₂ Level      │  │  Active Alerts  │
│  Normal (22°C)  │  │    +2°C         │  │  Fair (1200ppm) │  │      3 High     │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ V1: 24h Temperature Trend                                            │
│ [Line chart: 20°C→22.5°C→21°C trend over last 24 hours]             │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐
│ V2: Sensor Network Status           │  │ V3: Temperature vs Humidity         │
│ [Heatmap Grid: zones × sensor types]│  │ [Scatter: temp/humidity by zone]    │
│ Floor 1, Zone A: Temp 98%, CO2 95%  │  │ Zone A (22°C, 45%)                  │
│ Floor 1, Zone B: Temp 92%, CO2 88%  │  │ Zone B (20°C, 48%)                  │
│ Floor 2, Zone A: Temp 100%, CO2 100%│  │ Zone C (24°C, 42%)                  │
└─────────────────────────────────────┘  └─────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ V4: Real-time Sensor Readings (Last 24h)                                     │
├────────────┬──────────────┬──────┬──────┬──────────────┬────────┬───────────┤
│ Location   │ Sensor Type  │Value │Unit │ Anomaly Type │Severity│Action     │
├────────────┼──────────────┼──────┼──────┼──────────────┼────────┼───────────┤
│Floor 2, AHU│ HVAC Temp    │ 18°C │ °C  │ Threshold Low│ HIGH   │Check HVAC │
│Floor 1, Z B│ CO2          │1800  │ ppm │ Threshold Hi │ MEDIUM │Ventilate  │
│Floor 1, Z A│ Humidity     │ 52%  │ %   │ Drift High   │ LOW    │Monitor    │
└────────────┴──────────────┴──────┴──────┴──────────────┴────────┴───────────┘
```

---

## 🧪 DATA GENERATION (Trial Period)

**File:** `sample-data/iot_sensor_generator.py`

```python
# Generate dummy IoT data for 6 buildings
buildings = ['B001', 'B002', 'B003', 'B004', 'B005', 'B006']
sensors_per_building = [
    ('HVAC_temp', 20-24°C, normal_range),
    ('humidity', 40-60%, normal_range),
    ('CO2', 400-1200ppm, alert_1500ppm),
    ('power', building-dependent, normal_range)
]

# Generate 96 readings per sensor (24h @ 15-min)
# Inject 10% anomalies (spikes, drifts, threshold violations)
# Output: CSV → bronze_iot_raw.csv
```

---

## 🔧 PIPELINE CHANGES (Fabric Notebook)

### New Notebook: `11b_iot_ingestion_and_agg.py`

```
INPUT:  bronze_iot_raw (raw sensor readings)
        gold_iot_sensor_master (sensor config)

PROCESS:
1. Parse timestamps, validate readings
2. Calculate anomalies (rule-based):
   - Spike: abs(current - avg_last_48h) > 3*stdev
   - Drift: rolling avg differs > 5% from baseline
   - Threshold: reading < min OR reading > max
3. Assign severity: Low/Medium/High
4. Generate action text (domain logic)

OUTPUT: gold_iot_realtime
        gold_iot_daily_summary
```

---

## ✅ VALIDATION CHECKLIST

- [ ] gold_iot_realtime has 6 buildings × 4 sensors = 24 sensor streams
- [ ] 96 readings per stream (24h @ 15-min) = 2304 rows minimum
- [ ] Anomalies detected: ~230 rows (10% injection rate)
- [ ] High severity count (C4) > 0 (verify alert logic)
- [ ] Sensor uptime % (V2) 85-100% range
- [ ] Temp variance (C2) -3 to +3°C realistic
- [ ] V4 table shows action_recommended text correctly
- [ ] Filter by building, sensor_type, date range works
- [ ] Page 8 measures don't reference Page 1-7 tables (isolated)

---

## 🚀 ROLLOUT TIMELINE

| Task | Duration | Owner |
|---|---|---|
| Data model finalize | 2h | Mert (approval) |
| Python generator script | 3h | Claude (code) |
| Notebook 11b (Fabric) | 2h | Claude (code) |
| DAX measures (v43-v45) | 3h | Claude (code) |
| Power BI UI binding | 2h | Claude (UI) |
| Validation & testing | 2h | Mert (QA) |
| **TOTAL** | **~14h** | |

**Target completion:** 2026-05-12 (by day 6 of trial)
