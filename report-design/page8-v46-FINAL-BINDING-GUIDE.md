# Page 8 — Final Binding Guide (DAX v46)
**IoT Real-Time Monitoring & Anomaly Detection**
**DAX file: `semantic-model/55_dax_v46_page8_final.dax`**
**Status: FINAL — ready to implement**

---

## What Changed from v44

| Issue | Root Cause | Fix in v46 |
|---|---|---|
| C1 shows "--kW" | `timestamp = LatestTS` fails in KQL DirectQuery | Now uses `timestamp >= NOW() - 5min` window |
| C4 shows "--" | Used `iot_anomaly_alerts[is_resolved]` — table not connected | Rewritten to use `iot_hot_readings[is_anomaly]` only |
| V1 chart empty | Raw timestamp axis = too many unique points, no rendering | Use hierarchy → "Hour" level on axis |
| V3 matrix broken | Wrong visual type, value field errored | **Deleted. Replaced with Clustered Bar Chart** |
| V4 shows Sum of reading_value | Raw column added, not a measure | New measures: `V4_Avg_Reading_Value`, `V4_Action_Label`, `V4_Est_Cost_EUR` |

---

## Data Model — Only Two IoT Tables Needed

```
iot_hot_readings   (KQL DirectQuery) ← ALL C1-C4 and V1-V4 measures
iot_anomaly_alerts (KQL DirectQuery) ← NOT REQUIRED — can add later for richer history
```

**Do NOT add `iot_anomaly_alerts` yet** — all v46 measures work without it.

If you previously added it: either keep it (it won't break anything) or remove it from the model.

---

## Step 1 — Import v46 Measures

1. Open `semantic-model/55_dax_v46_page8_final.dax` in Notepad
2. In Power BI Desktop → **Modeling** tab → **New measure**
3. Copy-paste each measure block one at a time
4. Home table for all measures: **`iot_hot_readings`**
5. After importing, delete old v44 versions of same measures (C1_, C2_, C3_, C4_, V1_, V2_, V3_, V4_ prefixes)

> Measures to delete from v44: `C1_Building_kW_Raw` (old), `C4_Active_High_Alerts` (old), `C4_Alert_Cost_Today_EUR` (old)
> Keep: `C2_`, `C3_` (unchanged), `V2_` (unchanged)

---

## Step 2 — KPI Cards (C1–C4) — Top Row

### C1: Real-Time Building Power
- Visual type: **Card (New)**
- Callout value: **`[C1_Building_kW_Display]`** (text measure — shows "87.3 kW ✓ Normal")
- Reference label: type manually "Building Power (Live)"
- Conditional font color rule:
  - Field: `[C1_Building_kW_Color]` → Apply to: Callout value → Value is field value

> If callout still shows "--kW": verify that `iot_hot_readings` has rows with `sensor_type = "building_kwh"`.
> Quick check: run `iot_hot_readings | where sensor_type == "building_kwh" | limit 5` in KQL editor.

### C2: Zone Comfort Compliance ✅ (already working — no change needed)
- Callout: **`[C2_Zone_Compliance_Display]`**
- Conditional color: **`[C2_Zone_Compliance_Color]`**

### C3: CO₂ Level ✅ (already working — no change needed)
- Callout: **`[C3_CO2_Display]`**
- Reference label: **`[C3_CO2_Quality_Label]`**
- Conditional color: **`[C3_CO2_Color]`**

### C4: Active Alerts + Estimated Cost (REWRITTEN)
- Visual type: **Card (New)**
- Callout value: **`[C4_Active_High_Alerts]`** (number — shows integer count)
- Reference label: **`[C4_Alert_Label]`** (shows "All Clear" or "3 Active — Est. €47 today")
- Conditional background color: **`[C4_Alert_Color]`**

> Why callout = number (not text): lets Power BI render "0" large and "All Clear" as subtitle.
> If you prefer full text in callout: swap to `[C4_Alert_Label]` as callout instead.

---

## Step 3 — V1: Building & HVAC Power — Last 24h (Line Chart)

**Visual type:** Line chart

| Field slot | What to put |
|---|---|
| X-axis | `iot_hot_readings[timestamp]` — then in axis formatting, set **date hierarchy level to "Hour"** |
| Y-axis (series 1) | `[V1_Building_kW]` — label: "Building Total" |
| Y-axis (series 2) | `[V1_HVAC_kW]` — label: "HVAC Only" |
| Y-axis (series 3) | `[V1_Baseline_kW]` — label: "Baseline" — format as dashed line, grey |
| Tooltip | `[V1_HVAC_Share_Pct]` — label: "HVAC %" |

**Axis fix:** Right-click the X-axis → click the drill-down arrow → select **Hour** level (not Date, not Minute).
This groups all readings per hour → ~24 data points for last 24h → renders cleanly.

**Edit interactions:** S1 (Building slicer) → YES filters V1. Date slicer (if any) → YES filters V1.

---

## Step 4 — V2: Sensor Uptime Matrix ✅ (already working — minor fix)

**Visual type:** Matrix (keep as-is)

| Field slot | What to put |
|---|---|
| Rows | `iot_hot_readings[sensor_location]` |
| Columns | `iot_hot_readings[sensor_type]` |
| Values | `[V2_Sensor_Uptime_Pct]` |

**Add color formatting:**
1. Select the matrix → Format pane → Cell elements → Values → Background color → Advanced controls
2. Field: `[V2_Uptime_Color_Index]`
3. Rules: 1 = #2ECC40 (green), 2 = #FF851B (orange), 3 = #FF4136 (red)

---

## Step 5 — V3: Zone Anomaly Overview (REDESIGNED — was broken matrix)

**Action: DELETE the second matrix ("Zone Comfort Compliance — Last 24h") → INSERT new visual**

**Visual type:** Clustered Bar Chart (horizontal bars — better for reading zone names)

| Field slot | What to put |
|---|---|
| Y-axis (Category) | `iot_hot_readings[sensor_location]` |
| X-axis (Values) | `[V3_Anomaly_Count_High]` → color red |
|  | `[V3_Anomaly_Count_Medium]` → color orange |
|  | `[V3_Anomaly_Count_Low]` → color yellow |
| Tooltip | `[V3_Zone_Compliance_Pct]` → label "Zone Compliance %" |
| Sort | Sort Y-axis by `[V3_Total_Anomalies]` Descending (worst zones at top) |

**Title:** "Zone Anomaly Count — by Severity"

**Why this visual makes sense:** Facility Manager sees immediately which floor/zone needs attention. Red bars = go there now. Much more actionable than a compliance % matrix.

**Visual-level filter (optional but recommended):**
Add filter: `iot_hot_readings[is_anomaly]` = TRUE
→ Shows only zones that have at least 1 anomaly. Zones with no anomalies disappear from chart (clean view).

---

## Step 6 — V4: Alert Detail Table (FIXED)

**Delete all existing fields from the table → rebind correctly:**

| Column | Source | Format |
|---|---|---|
| Zone | `iot_hot_readings[sensor_location]` | text |
| Sensor | `iot_hot_readings[sensor_type]` | text |
| Reading | `[V4_Avg_Reading_Value]` | 0.0 (one decimal) |
| Unit | `iot_hot_readings[reading_unit]` | text |
| Severity | `iot_hot_readings[anomaly_severity]` | text |
| Action | `[V4_Action_Label]` | text (wrap) |
| Est. Cost | `[V4_Est_Cost_EUR]` | €0.00 |
| _Sort key_ | `[V4_Severity_Sort]` | hidden — used for sort only |

**Visual-level filter — CRITICAL:**
Add: `iot_hot_readings[is_anomaly]` = TRUE
→ Without this filter, all normal readings appear in the table (thousands of rows).

**Sort:** Sort by `[V4_Severity_Sort]` Ascending → High alerts appear first.

**Conditional row color (optional):**
- `anomaly_severity = "High"` → background #FF4136 (red), font white
- `anomaly_severity = "Medium"` → background #FF851B (orange), font white

---

## Step 7 — Edit Interactions

| Slicer / Visual | Affects |
|---|---|
| S1 Building Name slicer | ALL visuals (C1–C4, V1–V4) |
| Date slicer (if added) | Only V1, V3, V4 — NOT C1–C4 (cards must stay live) |
| V3 (Bar Chart) | Clicking a bar → filters V4 to that zone's anomalies only |
| V4 (Table) | Does NOT filter back to V3 (one-way drill) |

To set: Select V3 → Format → Edit interactions → set V4 to Filter icon.

---

## Step 8 — Validation Checklist

After binding, verify each visual:

- [ ] **C1:** Shows a kW number (not "--"). Value should be in range 50–200 kW for simulator data.
- [ ] **C2:** Shows "91% zones OK" or similar — currently working ✅
- [ ] **C3:** Shows ppm value with IDA label — currently working ✅
- [ ] **C4:** Shows "All Clear" or an integer alert count. Should NOT be blank.
- [ ] **V1:** Shows two colored lines (building + HVAC) and a flat grey baseline across 24 hours.
- [ ] **V2:** Matrix fills all cells with 80–100 values and color-coded backgrounds.
- [ ] **V3:** Horizontal bars, zones sorted by total anomaly count. Worst zone at top.
- [ ] **V4:** Only anomaly rows (no normal readings). "Action" column has text, not blank. "Est. Cost" shows €values.

---

## Cross-Page IoT Cards (Pages 2 and 7)

DAX v45 file (`54_dax_v45_cross_page_iot.dax`) already has all cross-page measures.

### Page 2 — Building Energy Overview: Add 2 new cards
- New Card → `[IoT_Building_kW_Display]` — "Real-Time kW"
- New Card → `[IoT_HVAC_kW_Display]` — "HVAC Load"
- Place next to existing daily kWh cards (complementary: one is live kW, other is cumulative kWh)
- Both cards: visual-level filter `[IoT_Building_Has_Sensors] = TRUE` → card disappears if no IoT

### Page 7 — HVAC Analysis: Add 3 new KPI cards
- `[IoT_Delta_T_Label]` → "Supply/Return ΔT (Live)" — delta-T efficiency
- `[IoT_Zone_Compliance_Label]` → "Zone Compliance (Live)"
- `[IoT_CO2_Label]` → "Air Quality (Live)"
- Place in a dedicated "Live Sensor Status" row above existing HVAC charts
- All three: filter by `[IoT_Building_Has_Sensors] = TRUE`

> Note: these cards show "--" or "No data" gracefully if the selected building has no IoT sensors. This is intentional — module visibility is controlled at app layer (Next.js), not Power BI.
