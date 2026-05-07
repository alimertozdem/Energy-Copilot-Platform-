# Page 8 — Power BI Binding Guide
**IoT Real-Time Monitoring & Anomaly Detection**
**DAX version: v44 | File: 53_dax_v44_page8_iot.dax**

---

## ⚠️ IMPORTANT: Two Data Connections on This Page

Page 8 is unique in the report — it uses **two different data sources**:

| Source | Tables | Visual Type | Refresh |
|---|---|---|---|
| KQL Eventhouse (DirectQuery) | `iot_hot_readings`, `iot_anomaly_alerts` | C1-C4 cards | Real-time (seconds) |
| Lakehouse DirectLake | `gold_iot_realtime`, `gold_iot_daily_summary` | V1-V4 visuals | 15 minutes |

You must add **both** connections in Power BI Desktop before binding measures.

---

## Step 0 — Prerequisites

- [ ] EventStream is running (verify in Fabric: status = "Running")
- [ ] Simulator sent batch data: `python iot_device_simulator.py --mode batch`
- [ ] KQL tables have data: run Q1 query from `iot_schema.kql`
- [ ] Notebook 11b ran successfully (gold tables exist)
- [ ] DAX v44 imported into Power BI model

---

## Step 1 — Add KQL Eventhouse Connection

1. Power BI Desktop → **Home** → **Get Data** → **More…** → search "KQL"
2. Select **Kusto (Azure Data Explorer)**
3. **Cluster:** paste your Eventhouse Query URI
   - Found in: Fabric → `iot_eventhouse` → Overview → **Query URI**
   - Looks like: `https://xxxxxxxx.z1.kusto.fabric.microsoft.com`
4. **Database:** `iot_eventhouse`
5. Select tables:
   - ✅ `iot_hot_readings`
   - ✅ `iot_anomaly_alerts`
   - ✅ `iot_sensor_master`
6. **Connectivity mode:** `DirectQuery` ← CRITICAL
7. Click **Load**

---

## Step 2 — Import DAX v44 Measures

1. Open `53_dax_v44_page8_iot.dax` in any text editor
2. In Power BI Desktop → **Modeling** → **New measure**
3. Copy-paste each measure block (between the `//---` separators)
4. Assign to table:
   - Measures starting with `C1_`, `C2_`, `C3_`, `C4_` → assign to `iot_hot_readings`
   - Measures starting with `V1_`, `V2_`, `V3_`, `V4_` → assign to `gold_iot_realtime`
   - Measures starting with `Summary_`, `Filter_` → assign to `gold_iot_realtime`

---

## Step 3 — Page Background

1. Report view → Page 8 → right-click canvas → **Format page**
2. **Page background** → Browse → select `backgrounds/08_iot_monitoring.png`
3. Transparency: **0%**

*(Background will be created separately — use a dark/teal theme matching Pages 1-7)*

---

## Step 4 — Add Slicers

### S1: Building Selector (applies to all visuals)
- Visual type: **Slicer**
- Field: `silver_building_master[building_name]`
- Style: Dropdown
- Position: Top-left corner (consistent with other pages)

### S2: Date Range (applies to V1-V4 only)
- Visual type: **Slicer**
- Field: `gold_iot_realtime[timestamp]`
- Style: Between (date range)
- Default: Last 24 hours

---

## Step 5 — KPI Cards (C1-C4)

Place four **New Card** visuals in the top row.

### C1: HVAC Status
- Visual: **Card (New)**
- **Callout value:** `[C1_HVAC_Status_Text]`
- Reference label: "HVAC Status"
- Font size: 18pt
- Conditional formatting: none (text already includes status)

### C2: Temperature Deviation
- Visual: **Gauge**
- **Value:** `[C2_Temp_Deviation_C]`
- **Min:** -5 | **Max:** 5 | **Target:** 0
- Reference label: "°C vs Setpoint (22°C)"
- Color zones:
  - Green: -1 to +1
  - Yellow: -3 to -1 and +1 to +3
  - Red: below -3 or above +3

### C3: CO₂ Level
- Visual: **Card (New)**
- **Callout value:** `[C3_CO2_Display]`
- Reference label: "Air Quality"
- Conditional text color based on `[C3_CO2_Quality_Label]`:
  - "Good" → green (#00B050)
  - "Fair" → orange (#FFC000)
  - "Poor — Ventilate" → red (#FF0000)

### C4: Active Alerts
- Visual: **Card (New)**
- **Callout value:** `[C4_Active_High_Alerts]`
- Reference label: `[C4_Alert_Count_Label]`
- Conditional background color on `[C4_Alert_Color_Index]`:
  - 1 → #FF0000 (red, high alerts)
  - 2 → #FFC000 (orange, medium)
  - 3 → #00B050 (green, clear)
- Font size callout: 32pt (this is the "alarm bell" card)

---

## Step 6 — Trend Visuals (V1-V4)

### V1: 24h Temperature Trend (Line Chart)
- Visual: **Line Chart**
- **X-axis:** `gold_iot_realtime[timestamp]` (15-min buckets)
- **Y-axis:** `[V1_Avg_HVAC_Temp]`
- **Legend:** `gold_iot_realtime[building_id]` (one line per building)
- Add reference lines:
  - Constant line at 20 (label: "Min setpoint")
  - Constant line at 24 (label: "Max setpoint")
- X-axis range: Last 24 hours
- Y-axis range: 10–35

### V2: Sensor Uptime Matrix
- Visual: **Matrix**
- **Rows:** `gold_iot_realtime[sensor_location]`
- **Columns:** `gold_iot_realtime[sensor_type]`
- **Values:** `[V2_Sensor_Uptime_Pct]`
- Conditional formatting on values:
  - Data bars: green gradient
  - Background color rule: `[V2_Uptime_Color_Index]`
    - 1 → green
    - 2 → yellow
    - 3 → red

### V3: Daily Anomaly Trend (Clustered Column)
- Visual: **Stacked Column Chart**
- **X-axis:** `gold_iot_daily_summary[event_date]`
- **Y-axis (stack 1):** `[V3_Anomaly_Count_High]` — color: #FF0000
- **Y-axis (stack 2):** `[V3_Anomaly_Count_Medium]` — color: #FFC000
- **Legend:** manual (High = red, Medium = orange)
- Title: "Daily Anomalies by Severity"

### V4: Sensor Alert Table
- Visual: **Table**
- Columns (in order):
  1. `gold_iot_realtime[building_id]` — "Building"
  2. `gold_iot_realtime[sensor_location]` — "Location"
  3. `gold_iot_realtime[sensor_type]` — "Sensor"
  4. `gold_iot_realtime[reading_value_avg]` — "Reading (avg)"
  5. `gold_iot_realtime[reading_unit]` — "Unit"
  6. `gold_iot_realtime[anomaly_severity_window]` — "Severity"
  7. `gold_iot_realtime[action_recommended]` — "Action"
- Sort default: `anomaly_severity_window` DESC (High first)
- Conditional format on "Severity" column:
  - "High" → red background
  - "Medium" → orange background
  - "Low" → yellow background

---

## Step 7 — Edit Interactions

Set these interaction rules (Format → Edit interactions):

| Source visual | Target visual | Interaction |
|---|---|---|
| S1 (Building slicer) | All C and V visuals | Filter ✅ |
| S2 (Date slicer) | V1, V2, V3, V4 | Filter ✅ |
| S2 (Date slicer) | C1, C2, C3, C4 | None ❌ (cards show live, not filtered by date) |
| V3 (Anomaly column) | V4 (Table) | Filter ✅ (click a day to see that day's alerts) |
| V3 | V1, V2 | None ❌ |

---

## Step 8 — Validation Checklist

Run through each item after binding:

**Data:**
- [ ] C1 shows "Normal (XX.X°C)" with realistic temperature (20-24°C)
- [ ] C2 gauge needle is near 0 (within setpoint)
- [ ] C3 shows CO2 value in 400-1200 ppm range with "Good" or "Fair" label
- [ ] C4 shows integer count (≥0) — not blank
- [ ] V1 shows 96 data points (24h × 15-min interval per building)
- [ ] V2 matrix has values for all building × sensor_type combinations
- [ ] V3 columns appear for last 7 days
- [ ] V4 table shows anomaly rows with non-blank action text

**Interactivity:**
- [ ] Clicking building in S1 filters all visuals to that building
- [ ] Changing date range in S2 updates V1-V4 but NOT C1-C4
- [ ] Clicking a column in V3 filters V4 to that day's anomalies
- [ ] Sorting V4 by Severity shows High rows first

**Visual:**
- [ ] Background image loaded (dark theme)
- [ ] Card colors: C4 turns red when alerts > 0
- [ ] No "#ERROR" or "BLANK" text in any card

---

## Estimated UI Time: ~90 minutes
(Slicers: 10min | Cards: 20min | Visuals: 40min | Interactions: 10min | Validation: 10min)
