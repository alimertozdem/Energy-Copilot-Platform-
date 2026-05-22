# Cross-Page IoT Enrichment — Binding Guide
**DAX version: v45 | File: 54_dax_v45_cross_page_iot.dax**
**Date: 2026-05-07**

---

## What This Guide Does

Connects `iot_hot_readings` to the rest of the semantic model so that:
- **Page 2** (Building Energy Overview) shows live building & HVAC power alongside historical kWh
- **Page 7** (HVAC Analysis) shows live Delta-T, zone compliance, and CO₂ alongside historical HVAC analytics
- **Building slicer** on any page filters IoT data automatically

This is the "cross-page enrichment" sprint — IoT data is no longer isolated to Page 8.

---

## Step 1 — Verify Shortcuts Are in the Lakehouse

In Fabric portal → `EnergyCopiloLakehouse` → **Tables** — confirm you see:
- ✅ `iot_hot_readings`
- ✅ `iot_anomaly_alerts`

If not visible, they need to be created as OneLake shortcuts (see EventStream setup guide).

---

## Step 2 — Refresh the Semantic Model in Power BI Desktop

1. Power BI Desktop → **Home** → **Refresh**
2. Wait for refresh to complete
3. In the **Data pane** (right side), scroll down — you should now see:
   - `iot_hot_readings`
   - `iot_anomaly_alerts`

If they don't appear, go to **Home → Transform data → Data source settings** and verify the Lakehouse connection includes the new tables.

---

## Step 3 — Create Relationships in Model View

1. Power BI Desktop → click **Model view** (icon on left sidebar, looks like a diagram)
2. You'll see all tables as boxes. Find `iot_hot_readings` and `iot_anomaly_alerts`.

### Relationship 1: iot_hot_readings → silver_building_master

- Drag `iot_hot_readings[building_id]` → drop onto `silver_building_master[building_id]`
- Settings in the relationship dialog:

| Setting | Value |
|---|---|
| Cardinality | Many to one (*:1) |
| Cross filter direction | Single (silver → iot) |
| Active | ✅ Yes |

### Relationship 2: iot_anomaly_alerts → silver_building_master

- Drag `iot_anomaly_alerts[building_id]` → drop onto `silver_building_master[building_id]`
- Same settings: Many to one, Single direction, Active

### Result
```
silver_building_master [building_id]
    ├── gold_kpi_daily[building_id]          ← existing
    ├── gold_hvac_analytics[building_id]     ← existing
    ├── iot_hot_readings[building_id]        ← NEW ✅
    └── iot_anomaly_alerts[building_id]      ← NEW ✅
```

The building slicer (`silver_building_master[building_name]`) now filters all four fact tables simultaneously.

---

## Step 4 — Import DAX v45 Measures

1. Open `54_dax_v45_cross_page_iot.dax` in a text editor
2. Power BI Desktop → **Modeling** → **New measure**
3. Paste each measure block, press Enter to save
4. **Home table for all v45 measures:** `iot_hot_readings`

### Measures by page:

**Utility (used everywhere):**
- `IoT_Building_Has_Sensors` — TRUE/FALSE flag (use for conditional card visibility)
- `IoT_Last_Reading_Age_Min` — minutes since last reading
- `IoT_Last_Reading_Age_Label` — "Updated 3 min ago"

**Page 2:**
- `IoT_Building_kW_Now` — raw kW value
- `IoT_Building_kW_Display` — "87.3 kW ✓ Normal"
- `IoT_Building_kW_Color` — hex color
- `IoT_HVAC_kW_Now` — raw HVAC kW
- `IoT_HVAC_Share_Of_Building_Pct` — HVAC as % of total
- `IoT_HVAC_kW_Display` — "34.2 kW — 39% of total"
- `IoT_HVAC_kW_Color` — hex color (red if HVAC >60% of building)

**Page 7:**
- `IoT_Supply_Temp_Live` — supply temp °C (raw)
- `IoT_Return_Temp_Live` — return temp °C (raw)
- `IoT_Delta_T_Live` — |supply − return| °C (raw)
- `IoT_Delta_T_Label` — "11.2°C — ✓ Optimal range"
- `IoT_Delta_T_Color` — hex color
- `IoT_Zone_Compliance_Live` — % zones in setpoint (last 24h, raw)
- `IoT_Zone_Compliance_Label` — "91% zones OK — ✓ Good"
- `IoT_Zone_Compliance_Color` — hex color
- `IoT_CO2_Live` — max CO₂ ppm (raw)
- `IoT_CO2_Label` — "847 ppm — IDA 2 Good"
- `IoT_CO2_Color` — hex color

**Summary (tooltips / cross-page badges):**
- `IoT_Total_Cost_Today_EUR` — total anomaly cost estimate today
- `IoT_High_Alert_Count` — active high alerts count

---

## Step 5 — Add IoT Cards to Page 2

Navigate to **Page 2** (Building Energy Overview) in the report.

Add **two new Card (New) visuals** — place them in a new row below or beside the existing cards. Suggested position: bottom-left area, labeled "Live Now" section.

### Card A: Real-Time Building Power

| Field | Value |
|---|---|
| Visual type | Card (New) |
| Callout value | `[IoT_Building_kW_Now]` (format: 0.0) |
| Reference label | `[IoT_Building_kW_Display]` |
| Conditional font color | `[IoT_Building_kW_Color]` |
| Tooltip | `[IoT_Last_Reading_Age_Label]` |
| Card title | "Live Building Power" |

### Card B: Live HVAC Load

| Field | Value |
|---|---|
| Visual type | Card (New) |
| Callout value | `[IoT_HVAC_kW_Now]` (format: 0.0) |
| Reference label | `[IoT_HVAC_kW_Display]` |
| Conditional font color | `[IoT_HVAC_kW_Color]` |
| Tooltip | `[IoT_HVAC_Share_Of_Building_Pct]` |
| Card title | "Live HVAC Load" |

> **If building has no IoT sensors:** Both cards will show `BLANK` — add a visual-level filter: `[IoT_Building_Has_Sensors] = TRUE` so the card is hidden rather than showing an error.

---

## Step 6 — Add IoT Cards to Page 7

Navigate to **Page 7** (HVAC Analysis / Building Envelope).

Add **three new Card (New) visuals** — place them in a "Live Sensors" row, ideally near the top where C1–C4 existing cards are, or as a separate IoT section at the bottom.

### Card A: Supply/Return Delta-T

| Field | Value |
|---|---|
| Visual type | Card (New) |
| Callout value | `[IoT_Delta_T_Live]` (format: 0.0 "°C") |
| Reference label | `[IoT_Delta_T_Label]` |
| Conditional font color | `[IoT_Delta_T_Color]` |
| Card title | "HVAC Delta-T (Live)" |

> **Why Delta-T matters on Page 7:** Page 7 already shows historical COP/SCOP. Delta-T is the real-time complement — a low Delta-T today explains why COP dropped this month. The two measures tell the same story from different time horizons.

### Card B: Zone Compliance (Live)

| Field | Value |
|---|---|
| Visual type | Card (New) |
| Callout value | `[IoT_Zone_Compliance_Live]` (format: 0%) |
| Reference label | `[IoT_Zone_Compliance_Label]` |
| Conditional font color | `[IoT_Zone_Compliance_Color]` |
| Card title | "Zone Comfort (Live 24h)" |

### Card C: CO₂ Level (Live)

| Field | Value |
|---|---|
| Visual type | Card (New) |
| Callout value | `[IoT_CO2_Live]` (format: #,##0 "ppm") |
| Reference label | `[IoT_CO2_Label]` |
| Conditional font color | `[IoT_CO2_Color]` |
| Card title | "CO₂ Level (Live)" |

> **IDA classification** used in CO₂ labels follows EN 13779 / EN 16798 — the EU standard for indoor air quality in non-residential buildings. This is the same standard referenced in CSRD ESG reporting (Page 6).

---

## Step 7 — Edit Interactions (Pages 2 and 7)

For both pages, the new IoT cards must:

| Slicer | IoT cards | Behavior |
|---|---|---|
| Building slicer (S1) | ✅ Filter | Shows IoT data for selected building only |
| Date slicer (S2) | ❌ None | IoT cards always show latest — date slicer irrelevant |

To set this:
1. Click the date slicer → **Format** → **Edit interactions**
2. On each new IoT card, click the **None** (circle with slash) icon
3. IoT cards are now immune to date filtering

---

## Step 8 — Validation Checklist

**Relationships:**
- [ ] Model view shows `iot_hot_readings → silver_building_master` relationship line
- [ ] Model view shows `iot_anomaly_alerts → silver_building_master` relationship line
- [ ] Selecting a building in any slicer updates all pages including IoT cards

**Page 2:**
- [ ] "Live Building Power" card shows a kW value (50–300 range for commercial building)
- [ ] Card color is green in normal hours
- [ ] Changing date slicer does NOT change IoT card values
- [ ] Selecting a different building updates BOTH historical and IoT cards

**Page 7:**
- [ ] "HVAC Delta-T" card shows a value (0–25°C realistic range)
  - If building has no supply/return sensors (e.g. B005 minimum set): card shows "No supply/return sensors" — this is correct
- [ ] "Zone Compliance" shows a % value or "No comfort sensors"
- [ ] "CO₂ Level" shows ppm value with IDA label
- [ ] CO₂ card turns amber/red if simulator injected a CO₂ anomaly

**Cross-page:**
- [ ] Building slicer on Page 2 → switch building → IoT cards update immediately
- [ ] Building slicer on Page 7 → switch building → IoT cards update immediately
- [ ] No `#ERROR` or `(Blank)` label in any of the new cards

---

## Architecture Note: Why Date Slicer Is Ignored

All v45 measures use `REMOVEFILTERS('Date')` intentionally.

IoT readings are live sensor data, not historical aggregates. The date slicer on Pages 2 and 7 controls the historical kWh/HVAC analytics period — for example "show me Q1 2025 data." The IoT cards answer a different question: "what is the building doing RIGHT NOW?"

If a user selects "2024 data" in the date slicer, the historical cards show 2024 figures while the IoT cards still show today's live readings. This is correct behavior — they are two separate data layers on the same page.

---

## Estimated UI Time: ~45 minutes
- Refresh + verify tables: 5 min
- Relationships in Model view: 10 min
- DAX measures import: 15 min
- Add cards to Pages 2 and 7: 10 min
- Edit interactions + validation: 5 min
