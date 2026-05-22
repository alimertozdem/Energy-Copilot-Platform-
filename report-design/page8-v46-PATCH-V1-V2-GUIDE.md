# Page 8 — Patch Guide: V1 X-axis Fix + V2 Matrix Clean-up
**Applies on top of:** `page8-v46-FINAL-BINDING-GUIDE.md`
**DAX patch file:** `semantic-model/56_dax_v46_patch_v1_gold.dax`
**Notebook change:** `notebooks/iot/11b_iot_processing.py` (v2.1 — adds `hour_bucket`, `hour_of_day`)

---

## Problem Summary

| Visual | Issue | Root Cause | Fix |
|---|---|---|---|
| V1 Line Chart | X-axis shows dense ISO timestamps ("2026-05-07T14:15:00Z") | KQL DirectQuery treats datetime as string — no hierarchy | Switch X-axis to `gold_iot_realtime[hour_bucket]` (Delta, DirectLake) |
| V2 Matrix | Empty columns for extended sensors (HVAC_supply_temp, lighting_kwh, etc.) | Extended sensors only exist in full-BMS buildings | Visual-level filter: show core sensors only |

---

## Fix 1 — V1: X-axis via gold_iot_realtime

### Step 1a — Re-run Notebook 11b in Fabric

Notebook `11b_iot_processing.py` (v2.1) now adds two columns to `gold_iot_realtime`:

| Column | Type | Example Value | Purpose |
|---|---|---|---|
| `hour_bucket` | String | "05-07 14:00" | Clean X-axis label in Power BI |
| `hour_of_day` | Integer | 14 | For DAX filters and future forecasting |

In Microsoft Fabric:
1. Open the `11b_iot_processing` notebook
2. Replace the Cell [8] gold section with the updated version (contains the two new `.withColumn(...)` lines)
3. Run the notebook → `gold_iot_realtime` table is refreshed with new columns
4. Verify in Lakehouse SQL: `SELECT hour_bucket, hour_of_day FROM gold_iot_realtime LIMIT 5`
   → Should show values like "05-07 14:00", 14

### Step 1b — Add gold_iot_realtime to the Semantic Model

In Power BI Desktop:
1. **Home → Get data → OneLake data hub**
2. Find your **Lakehouse** → select table `gold_iot_realtime`
3. **Import mode** (NOT DirectQuery — Delta tables use DirectLake/Import for best performance)
4. Click **Load**
5. The table appears in the Fields pane as `gold_iot_realtime`

> No relationship needed between `gold_iot_realtime` and `iot_hot_readings` — they are independent visual sources on this page.

### Step 1c — Add V1 Gold Measures

Open `semantic-model/56_dax_v46_patch_v1_gold.dax` in Notepad.
Add all 4 measures to the model. Home table: **`gold_iot_realtime`**

Measures to add:
- `V1_Gold_Building_kW`
- `V1_Gold_HVAC_kW`
- `V1_Gold_Baseline_kW`
- `V1_Gold_HVAC_Share_Pct`

### Step 1d — Rebind the V1 Line Chart

Delete current V1 field bindings and rebind:

| Field slot | Old binding | New binding |
|---|---|---|
| X-axis | `iot_hot_readings[timestamp]` | `gold_iot_realtime[hour_bucket]` |
| Y-axis (series 1) | `[V1_Building_kW]` | `[V1_Gold_Building_kW]` |
| Y-axis (series 2) | `[V1_HVAC_kW]` | `[V1_Gold_HVAC_kW]` |
| Y-axis (series 3) | `[V1_Baseline_kW]` | `[V1_Gold_Baseline_kW]` |
| Tooltip | `[V1_HVAC_Share_Pct]` | `[V1_Gold_HVAC_Share_Pct]` |

**Expected result:** X-axis shows clean labels like "05-07 08:00", "05-07 09:00" ... "05-07 22:00"
~96 data points (15-min intervals) or ~24 (if grouped) — renders cleanly, no drill-down needed.

**Sort:** Format pane → X-axis → Sort by `gold_iot_realtime[hour_bucket]` Ascending
(String "MM-dd HH:00" sorts correctly chronologically — same date prefix, hour sorts alphabetically = chronologically ✓)

---

## Fix 2 — V2 Matrix: Remove Empty Extended-Sensor Columns

Extended sensors (HVAC_supply_temp, HVAC_return_temp, lighting_kwh, plug_load_kwh, pump_pressure, fan_rpm, boiler_eff, chiller_cop) appear as columns in the matrix but most zones don't have them → empty cells, sparse matrix.

### Solution: Visual-level filter — no code changes needed

1. Select the **V2 Sensor Uptime Matrix** visual
2. **Filters pane → Add filter → sensor_type** (drag column to visual-level filters)
3. Set **Filter type: Basic filtering**
4. Check ONLY these 5 core sensor types:
   - ✅ `building_kwh`
   - ✅ `CO2`
   - ✅ `humidity`
   - ✅ `HVAC_temp`
   - ✅ `hvac_kwh`
5. Uncheck everything else (HVAC_supply_temp, lighting_kwh, pump_pressure, etc.)
6. Click **Apply filter**

**Expected result:** Matrix shows exactly 5 columns × N zone rows, all cells populated.

> **Why only 5?** These are the minimum sensor set that all buildings must have (defined in architecture). Extended sensors (sub-metering, delta-T, etc.) will get their own dedicated visual in a future "Advanced Sensor" page when full-BMS customers onboard.

---

## Validation After Both Fixes

- [ ] **V1:** X-axis shows "MM-dd HH:00" format labels (e.g. "05-07 14:00")
- [ ] **V1:** ~24-96 data points visible, two colored lines (building + HVAC) + flat grey baseline
- [ ] **V1:** No dense timestamp text, no "See details" errors
- [ ] **V2:** Matrix has exactly 5 columns: building_kwh, CO2, humidity, HVAC_temp, hvac_kwh
- [ ] **V2:** No empty cells (all core sensors present across all zones)
- [ ] **V2:** Color coding: green (80-100%), orange (50-79%), red (<50%)
- [ ] **C1–C4 cards:** Still working (these are NOT affected by this patch)

---

## What Does NOT Change

- All C1–C4 KPI cards → still use `iot_hot_readings` (KQL DirectQuery) ✓
- V3 Zone Anomaly Bar Chart → still uses `iot_hot_readings` ✓
- V4 Alert Detail Table → still uses `iot_hot_readings` ✓
- DAX v46 measures (v46 file untouched) ✓
- The original V1 measures (`V1_Building_kW`, `V1_HVAC_kW`, `V1_Baseline_kW`) can stay in the model — they are just no longer used by the V1 chart visual
