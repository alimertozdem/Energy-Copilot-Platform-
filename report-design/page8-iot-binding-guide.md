# Page 8 — Power BI Binding Guide
**IoT Real-Time Monitoring & Anomaly Detection**
**DAX version: v44 (REVISED 2026-05-07) | File: 53_dax_v44_page8_iot.dax**

---

## ⚠️ IMPORTANT: Two Data Connections on This Page

Page 8 is unique in the report — it uses **two different data sources**:

| Source | Tables | Visual Type | Refresh |
|---|---|---|---|
| KQL Eventhouse (DirectQuery) | `iot_hot_readings`, `iot_sensor_master` | C1–C4 cards | Real-time (seconds) |
| Lakehouse DirectLake | `gold_iot_realtime`, `gold_iot_daily_summary` | V1–V4 visuals | 15 minutes |

> ⚠️ `iot_anomaly_alerts` is **NOT used** in v44 measures. Do not connect it. Anomaly data flows through `gold_iot_realtime` instead (processed by Notebook 11b).

You must add **both** connections in Power BI Desktop before binding measures.

---

## User Roles on This Page

Page 8 serves **two personas simultaneously**:

| Role | What they look at | Frequency |
|---|---|---|
| **Facility Manager** | C1 (power), C2 (zone comfort), C3 (CO₂), C4 (active alerts), V4 (alert table) | Multiple times per day |
| **Energy Manager** | V1 (24h power trend with HVAC split), V2 (sensor uptime), V3 (zone compliance over time) | Daily review |

Design the layout with cards (C1–C4) at top for Facility Manager quick-glance, and trend visuals (V1–V4) below for Energy Manager deep-dive.

---

## Step 0 — Prerequisites

- [ ] EventStream is running (verify in Fabric: status = "Running")
- [ ] Simulator sent data: `python iot_device_simulator.py --mode batch`
- [ ] KQL tables have data: run `SELECT * FROM iot_hot_readings | limit 10` in KQL editor
- [ ] Notebook 11b ran successfully — confirm `gold_iot_realtime` and `gold_iot_daily_summary` exist in Lakehouse
- [ ] DAX v44 file is ready: `semantic-model/53_dax_v44_page8_iot.dax`

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
   - ✅ `iot_sensor_master`
   - ❌ Do NOT add `iot_anomaly_alerts` (not used in v44)
6. **Connectivity mode:** `DirectQuery` ← CRITICAL — must be DirectQuery, not Import
7. Click **Load**

---

## Step 2 — Add DirectLake Connection (Lakehouse)

If not already in the model from Pages 1–7:

1. Power BI Desktop → **Home** → **Get Data** → **Microsoft Fabric** → **Lakehouse**
2. Select your workspace and lakehouse
3. Select tables:
   - ✅ `gold_iot_realtime`
   - ✅ `gold_iot_daily_summary`
   - ✅ `silver_building_master` (needed for country → grid price in cost measures)
4. **Connectivity mode:** `DirectLake`
5. Click **Load**

---

## Step 3 — Import DAX v44 Measures

1. Open `53_dax_v44_page8_iot.dax` in any text editor
2. In Power BI Desktop → **Modeling** → **New measure**
3. Copy-paste each measure block (between the `// ───` separators)
4. Assign to the correct home table:

| Measure prefix | Home table | Why |
|---|---|---|
| `C1_`, `C2_`, `C3_`, `C4_` | `iot_hot_readings` | Live DirectQuery — cards need real-time context |
| `V1_`, `V2_`, `V3_`, `V4_` | `gold_iot_realtime` | DirectLake — trend visuals |
| `Summary_`, `Daily_` | `gold_iot_daily_summary` | Daily aggregates |
| `Filter_` | `gold_iot_realtime` | Slicer helpers |

> Note: `C2_Zone_Compliance_Pct_Raw` reads from `gold_iot_realtime` internally (last-24h compliance window), even though its home table is `iot_hot_readings`. This is intentional — the card is "live" but the compliance window is 24h, not instantaneous.

---

## Step 4 — Page Background

1. Report view → Page 8 → right-click canvas → **Format page**
2. **Page background** → Browse → select `backgrounds/08_iot_monitoring.png`
3. Transparency: **0%**

*(Background will be created separately — use a dark/teal theme matching Pages 1–7)*

---

## Step 5 — Add Slicers

### S1: Building Selector (applies to ALL visuals)
- Visual type: **Slicer**
- Field: `silver_building_master[building_name]`
- Style: Dropdown
- Position: Top-left corner (consistent with other pages)

### S2: Date Range (applies to V1–V4 only, NOT C1–C4)
- Visual type: **Slicer**
- Field: `gold_iot_realtime[timestamp]`
- Style: Between (date range)
- Default: Last 24 hours

### S3: Sensor Type Filter (applies to V1–V4 only, NOT C1–C4)
- Visual type: **Slicer**
- Field: `gold_iot_realtime[sensor_type]`
- Style: List (multi-select)
- Position: Right panel or below S2
- **Purpose:** Lets Energy Manager drill into a specific sensor category (e.g., show only power sensors in V1, or only comfort sensors in V3)
- ⚠️ Edit interactions — see Step 7 — this slicer must NOT filter C1–C4

> **Dynamic sensor behavior:** sensor_type values in S3 will vary by building. B001 may show HVAC_supply/return_temp; B005 (minimum set) shows only the 5 base sensor types. The slicer adapts automatically — no hardcoding required.

---

## Step 6 — KPI Cards (C1–C4)

Place four **New Card** visuals in the top row.

### C1: Real-Time Building Power
- Visual: **Card (New)**
- **Callout value:** `[C1_Building_kW_Display]`
  - Returns: `"87.3 kW"` or `"-- kW"` if no data
- Reference label: "Building Power (Live)"
- Conditional background or font color: `[C1_Building_kW_Color]`
  - `#2ECC40` (green) — power ≤ 100% of baseline (normal)
  - `#FF851B` (orange) — 100–120% of baseline (above normal)
  - `#FF4136` (red) — >120% of baseline (spike)
- Font size callout: 24pt

### C2: Zone Comfort Compliance
- Visual: **Card (New)**
- **Callout value:** `[C2_Zone_Compliance_Display]`
  - Returns: `"94% zones OK"` or `"-- %"` if no data
- Reference label: "Zone Compliance (24h)"
- Conditional font color: `[C2_Zone_Compliance_Color]`
  - `#2ECC40` (green) — ≥90% compliant
  - `#FF851B` (orange) — 75–89%
  - `#FF4136` (red) — <75%
- Font size callout: 24pt

> **What this measures:** % of 15-min windows where HVAC_temp, humidity, and CO₂ readings were all within their configured setpoints. 90%+ = building is performing well.

### C3: CO₂ Level
- Visual: **Card (New)**
- **Callout value:** `[C3_CO2_Display]`
  - Returns: `"842 ppm — Good"` or `"1620 ppm — Poor — Ventilate"`
- Reference label: "Air Quality"
- Conditional font color: `[C3_CO2_Color]`
  - `#2ECC40` — Good (<1000 ppm)
  - `#FF851B` — Fair (1000–1499 ppm)
  - `#FF4136` — Poor — Ventilate (≥1500 ppm)
- Font size callout: 20pt

### C4: Active High Alerts + Estimated Daily Cost
- Visual: **Card (New)**
- **Callout value:** `[C4_Active_High_Alerts]`
  - Returns: integer count of current High-severity anomalies
- Reference label: `[C4_Alert_Label]`
  - Returns: `"All Clear"` or `"3 High Alerts — Est. €47"`
- Conditional background color: `[C4_Alert_Color]`
  - `#2ECC40` — 0 alerts (green)
  - `#FF851B` — 1–2 alerts (amber)
  - `#FF4136` — 3+ alerts (red)
- Font size callout: 32pt (this is the "alarm bell" card — make it large)

> **Cost estimate note:** the €cost figure shown in C4 is labeled "Est." — it is an engineering estimate based on `duration_hours × power_waste_kw × grid_price_eur_per_kwh`. It is always shown as approximate. See anomaly cost logic in `page8-iot-realtime-design.md`.

---

## Step 7 — Trend Visuals (V1–V4)

### V1: 24h Power Trend (Dual-Series Line Chart)
- Visual: **Line Chart**
- **X-axis:** `gold_iot_realtime[timestamp]` (15-min buckets, last 24h)
- **Y-axis — Line 1:** `[V1_Building_kW]` — label: "Total Building kW" — color: blue
- **Y-axis — Line 2:** `[V1_HVAC_kW]` — label: "HVAC kW" — color: teal
- **Y-axis — Line 3:** `[V1_Baseline_kW]` — label: "Baseline" — color: grey, style: dashed
- Legend: show (three series)
- X-axis range: Last 24 hours
- Y-axis range: auto (or 0–250 for typical commercial building)
- Title: "Building & HVAC Power — Last 24 Hours"

> **Why two power series?** HVAC typically consumes 40–60% of total building power. Showing them separately lets the Energy Manager immediately see if a spike is HVAC-driven or from other loads (lighting, plug load). The baseline reference makes over-consumption visually obvious.

### V2: Sensor Uptime Matrix
- Visual: **Matrix**
- **Rows:** `gold_iot_realtime[sensor_location]` (zone names: "Zone A", "Floor 2", etc.)
- **Columns:** `gold_iot_realtime[sensor_type]`
- **Values:** `[V2_Sensor_Uptime_Pct]`
  - Returns: % of expected readings received in the selected time window
- Conditional formatting on values — background color rule: `[V2_Uptime_Color_Index]`
  - 1 → `#2ECC40` (green, ≥95% uptime)
  - 2 → `#FFC000` (yellow, 80–94%)
  - 3 → `#FF4136` (red, <80%)
- Show data bars: off (color cells are clearer than bars for a matrix)
- Title: "Sensor Uptime by Zone & Type"

> **Dynamic columns:** Because sensor_type is a dimension, columns will vary by building. A building with only the minimum 5 sensor types shows 5 columns; a full-BMS building shows up to 12. The matrix adapts automatically.

### V3: Zone Setpoint Compliance (Matrix)
- Visual: **Matrix**
- **Rows:** `gold_iot_realtime[sensor_location]` (zones)
- **Columns:** `gold_iot_realtime[sensor_type]` (filtered to comfort sensors: HVAC_temp, humidity, CO2)
- **Values:** `[V3_Zone_Compliance_Pct]`
  - Returns: % of 15-min windows where this zone × sensor_type was in setpoint
- Conditional formatting on values — background color: `[V3_Zone_Compliance_Color]`
  - `#2ECC40` — ≥90%
  - `#FF851B` — 75–89%
  - `#FF4136` — <75%
- Secondary column (optional): `[V3_Zone_Out_Of_Range_Hours]` — show as tooltip or second measure column
- Title: "Zone Comfort Compliance — Last 24 Hours"

> **Why this replaced the old V3 (scatter plot)?** A scatter plot of temp vs. humidity is technically interesting but gives facility managers no actionable answer. This matrix shows immediately: "Zone C has been out of CO₂ setpoint for 6 hours today" — that is an actionable finding.

### V4: Alert Table with Cost Estimate
- Visual: **Table**
- Columns (in order):

| Column | Source | Display Name |
|---|---|---|
| `gold_iot_realtime[building_id]` | direct | Building |
| `gold_iot_realtime[sensor_location]` | direct | Location |
| `gold_iot_realtime[sensor_type]` | direct | Sensor |
| `gold_iot_realtime[reading_value_avg]` | direct | Reading |
| `gold_iot_realtime[reading_unit]` | direct | Unit |
| `gold_iot_realtime[anomaly_severity_window]` | direct | Severity |
| `gold_iot_realtime[action_recommended]` | direct | Recommended Action |
| `[V4_Cost_Label]` | measure | Est. Cost |

- Sort default: `[V4_Severity_Sort]` ASC (High=1 first, then Medium=2, Low=3)
- Conditional format on "Severity" column — background:
  - "High" → `#FF4136`
  - "Medium" → `#FF851B`
  - "Low" → `#FFC000`
- Conditional format on "Est. Cost" column — font color:
  - >€20 → `#FF4136`
  - €5–€20 → `#FF851B`
  - ≤€5 → default
- Title: "Active Anomaly Alerts"
- Filter (visual-level): `anomaly_severity_window` IN {"High", "Medium"} — hide Low to reduce noise

---

## Step 8 — Edit Interactions

Set these interaction rules (Format → Edit interactions):

| Source visual | Target visual | Interaction |
|---|---|---|
| S1 (Building slicer) | All C and V visuals | Filter ✅ |
| S2 (Date slicer) | V1, V2, V3, V4 | Filter ✅ |
| S2 (Date slicer) | C1, C2, C3, C4 | None ❌ (cards show live, not date-filtered) |
| S3 (Sensor type slicer) | V1, V2, V3, V4 | Filter ✅ |
| S3 (Sensor type slicer) | C1, C2, C3, C4 | None ❌ (cards show fixed sensor types — do not filter by S3) |
| V4 (Alert table) | V1 | Filter ✅ (click a row to highlight that sensor's power trend) |
| V4 (Alert table) | V2, V3 | None ❌ |

> **Why S3 must not filter C cards:** C1 always shows `building_kwh`, C2 always uses comfort sensor set, C3 always shows CO₂. If S3 were to filter these cards, selecting "HVAC only" in the slicer would blank out C3 (no CO₂ in filter). The cards represent fixed KPIs, not exploratory views.

---

## Step 9 — Validation Checklist

Run through each item after binding:

**Data integrity:**
- [ ] C1 shows a realistic kW value (50–300 kW for commercial building) — not blank
- [ ] C1 color is green in normal hours, turns amber/red if simulator injected power spike
- [ ] C2 shows a % between 70–100% — "95% zones OK" format
- [ ] C3 shows CO₂ ppm value (400–1600 typical range) with quality label
- [ ] C4 shows integer alert count — "All Clear" or "N High Alerts — Est. €X"
- [ ] V1 shows 96 data points per series per building (24h × 4 per hour = 96)
- [ ] V1 has three series: blue (building kW), teal (HVAC kW), grey dashed (baseline)
- [ ] V2 matrix shows uptime % for each zone × sensor type — no blank cells for active sensors
- [ ] V3 matrix shows compliance % by zone — at least one red/amber cell if simulator injected anomalies
- [ ] V4 table shows only High/Medium rows, sorted by severity, with non-blank action text and cost label

**Interactivity:**
- [ ] S1 (building) filters ALL visuals — selecting B001 shows only B001 data everywhere
- [ ] S2 (date range) updates V1–V4 but C1–C4 are unchanged
- [ ] S3 (sensor type) updates V1–V4 but C1–C4 are unchanged
- [ ] Clicking a row in V4 highlights corresponding sensor in V1

**Visual quality:**
- [ ] Page background loaded (dark theme)
- [ ] C4 background turns red when high alerts > 0
- [ ] No `#ERROR`, `BLANK`, or `(Blank)` text in any card
- [ ] V1 legend is visible and correctly labels 3 series
- [ ] V4 "Severity" column has colored background (not plain text)

---

## Measure Quick Reference

| Measure | Table | Used in | Returns |
|---|---|---|---|
| `C1_Building_kW_Display` | iot_hot_readings | C1 callout | `"87.3 kW"` |
| `C1_Building_kW_Color` | iot_hot_readings | C1 color | hex color string |
| `C2_Zone_Compliance_Display` | iot_hot_readings | C2 callout | `"94% zones OK"` |
| `C2_Zone_Compliance_Color` | iot_hot_readings | C2 color | hex color string |
| `C3_CO2_Display` | iot_hot_readings | C3 callout | `"842 ppm — Good"` |
| `C3_CO2_Color` | iot_hot_readings | C3 color | hex color string |
| `C4_Active_High_Alerts` | iot_hot_readings | C4 callout | integer count |
| `C4_Alert_Label` | iot_hot_readings | C4 reference label | `"3 High Alerts — Est. €47"` |
| `C4_Alert_Color` | iot_hot_readings | C4 background | hex color string |
| `V1_Building_kW` | gold_iot_realtime | V1 line 1 | average kW per 15-min |
| `V1_HVAC_kW` | gold_iot_realtime | V1 line 2 | HVAC kW per 15-min |
| `V1_Baseline_kW` | gold_iot_realtime | V1 line 3 | rolling 30-day baseline |
| `V2_Sensor_Uptime_Pct` | gold_iot_realtime | V2 matrix values | 0–100% |
| `V2_Uptime_Color_Index` | gold_iot_realtime | V2 conditional color | 1/2/3 |
| `V3_Zone_Compliance_Pct` | gold_iot_realtime | V3 matrix values | 0–100% |
| `V3_Zone_Compliance_Color` | gold_iot_realtime | V3 conditional color | hex color string |
| `V3_Zone_Out_Of_Range_Hours` | gold_iot_realtime | V3 tooltip | decimal hours |
| `V4_Cost_Label` | gold_iot_realtime | V4 Est. Cost column | `"Est. €12"` or `"< €1"` |
| `V4_Severity_Sort` | gold_iot_realtime | V4 sort order | 1 (High) / 2 (Med) / 3 (Low) |

---

## Estimated UI Time: ~100 minutes
- Data connections: 15 min
- DAX measures import: 15 min
- Slicers (S1, S2, S3): 10 min
- KPI cards C1–C4: 25 min (conditional formatting is the bulk)
- Visuals V1–V4: 25 min
- Edit interactions: 5 min
- Validation: 5 min
