# PAGE 9 — Battery Dispatch Strategies & Financial Simulation
## Power BI Binding Guide — DAX v47

**Status:** Ready to implement  
**DAX File:** `semantic-model/58_dax_v47_page9_battery.dax`  
**Background:** `report-design/backgrounds/09_battery_strategy.png`  
**Data tables:** `gold_battery_dispatch`, `gold_battery_simulation`, `gold_battery_daily_summary`, `gold_battery_technologies`  
**Date:** 2026-05-08

---

## STEP 0 — Import DAX Measures

1. Open `58_dax_v47_page9_battery.dax` in a text editor
2. In Power BI Desktop → **Modeling tab** → **New Measure** (paste each measure block)
3. Organize into a display folder called `_Page9_Battery`
4. Total measures to import: **32 measures** in 9 groups

---

## STEP 1 — Data Model Connections

Verify these tables are in your Power BI data model before starting:

| Table | Source | Relationship |
|---|---|---|
| `gold_battery_dispatch` | Fabric Lakehouse (Delta) | FK: building_id → silver_building_master |
| `gold_battery_simulation` | Fabric Lakehouse (Delta) | FK: building_id → silver_building_master |
| `gold_battery_daily_summary` | Fabric Lakehouse (Delta) | FK: building_id → silver_building_master |
| `gold_battery_technologies` | Fabric Lakehouse (Delta) | standalone reference |
| `silver_building_master` | Fabric Lakehouse (Delta) | hub table |

**Relationships to create (if not already present):**
```
gold_battery_dispatch[building_id]     →  silver_building_master[building_id]  (Many:1)
gold_battery_simulation[building_id]   →  silver_building_master[building_id]  (Many:1)
gold_battery_daily_summary[building_id]→  silver_building_master[building_id]  (Many:1)
```

---

## STEP 2 — Page Layout & Background

1. Add new page to the report → rename to **"Battery Strategy"**
2. Set background image: `09_battery_strategy.png`
   - Format → Page → Canvas background → Transparency: 85%
3. Canvas size: 1280 × 720 (standard widescreen)

### Layout Grid (pixel positions)

```
┌──────────────────────────────────────────────────────────────────────┐  Y:0
│  PAGE TITLE (text box): "Battery Dispatch & Financial Simulation"   │  H:40
├────────────────┬─────────────────┬──────────────────┬───────────────┤  Y:50
│   C1 card      │   C2 card       │   C3 card        │   C4 card     │
│ Annual Savings │ Payback Period  │ CO₂ Avoided      │ Efficiency    │
│  X:10 Y:50     │  X:330 Y:50     │  X:650 Y:50      │  X:970 Y:50  │
│  W:310 H:90    │  W:310 H:90     │  W:310 H:90      │  W:300 H:90  │
├────────────────┴─────────────────┴──────────────────┴───────────────┤  Y:150
│                      V1: SoC Trend (Area Chart)                      │
│                      X:10 Y:150  W:780  H:190                        │
├────────────────────────────────────┬─────────────────────────────────┤  Y:150
│  V4: ROI Gauge                     │  (right panel top)              │
│  X:800 Y:150  W:470 H:190          │                                 │
├────────────────────────────────────┴─────────────────────────────────┤  Y:350
│                      V2: Daily Charge/Discharge (Clustered Bar)      │
│                      X:10 Y:350  W:780  H:170                        │
├────────────────────────────────────┬─────────────────────────────────┤  Y:350
│  Active Strategy Info Card         │  EU Compliance Card             │
│  X:800 Y:350  W:230 H:170          │  X:1040 Y:350 W:230 H:170      │
├────────────────────────────────────┴─────────────────────────────────┤  Y:530
│                      V3: Scenario Comparison Table                    │
│                      X:10 Y:530  W:780  H:180                        │
├────────────────────────────────────────────────────────────────────── │  Y:530
│  V5: Cost vs Payback Scatter                                          │
│  X:800 Y:530  W:470 H:180                                             │
└──────────────────────────────────────────────────────────────────────┘  Y:720
```

---

## STEP 3 — KPI Cards (C1–C4)

Use **New Card visual** (not legacy card).

### C1 — Annual Savings

| Field | Value |
|---|---|
| Value | `[C1 Annual Savings EUR]` |
| Reference label | `[C1 Label Savings]` |
| Value format | Currency, 0 decimals, € prefix |
| Callout value | `[C1 Annual Savings EUR]` |
| Conditional format | Green if > €5,000; amber if €1,000–5,000; grey if < €1,000 |

### C2 — Payback Period

| Field | Value |
|---|---|
| Value | `[C2 Payback Years]` |
| Reference label | `[C2 Label Payback]` |
| Value format | Decimal, 1 place, "yr" suffix |
| Conditional format | Green ≤ 7yr; amber 7–12yr; red > 12yr |

### C3 — CO₂ Avoided

| Field | Value |
|---|---|
| Value | `[C3 CO2 Avoided tCO2 Annual]` |
| Reference label | `[C3 Label CO2]` |
| Value format | Decimal, 1 place, "tCO₂/yr" suffix |

### C4 — Round-Trip Efficiency

| Field | Value |
|---|---|
| Value | `[C4 Round Trip Efficiency Pct]` |
| Reference label | `[C4 Label Efficiency]` |
| Value format | Percentage, 1 decimal |
| Subtitle | `[Active Strategy Label]` |

---

## STEP 4 — V1: State of Charge Trend (Area Chart)

**Visual type:** Area chart (or Line chart)

| Setting | Value |
|---|---|
| X-axis | `gold_battery_dispatch[date]` |
| Y-axis | `[V1 SoC End Percent]` |
| Legend | `gold_battery_dispatch[strategy]` |
| Secondary line | `[V1 SoC Start Percent]` (dashed) |

**Series colors:**
- `self_consumption` → Green (#2ECC71)
- `peak_shaving` → Orange (#E67E22)  
- `tou` → Blue (#3498DB)
- `backup` → Purple (#9B59B6)

**Reference line:** Add constant line at Y=10% (min safe SoC)
- Label: "Min SoC (10%)" in red

**Edit interactions:**
- S1 (building slicer) → Cross-filter V1 ✅
- S2 (strategy slicer) → Cross-filter V1 ✅
- S3 (date slicer) → Cross-filter V1 ✅
- V3 table → Cross-filter V1 ✅

---

## STEP 5 — V2: Daily Charge / Discharge (Clustered Bar)

**Visual type:** Clustered bar chart (or Stacked bar)

| Setting | Value |
|---|---|
| X-axis | `gold_battery_dispatch[date]` |
| Y-axis (bar 1) | `[V2 Charge kWh Daily]` |
| Y-axis (bar 2) | `[V2 Discharge kWh Daily]` |
| Line overlay | `[V2 PV Generation kWh]` |

**Colors:**
- Charge bars: Blue (#2980B9)
- Discharge bars: Amber (#F39C12)
- PV line: Yellow-green (#F1C40F), dashed

**Tooltips (add to tooltip field well):**
- `[V2 Grid Charge kWh Daily]`
- `[V2 PV Charge kWh Daily]`
- `[V2 Net Savings EUR Daily]`

---

## STEP 6 — V3: Scenario Comparison Table

**Visual type:** Table

**Columns (in order):**

| Column | Source | Format |
|---|---|---|
| Building | `silver_building_master[building_name]` | Text |
| Strategy | `gold_battery_simulation[strategy_label]` | Text |
| Battery | `gold_battery_simulation[battery_type]` | Text |
| Capacity (kWh) | `gold_battery_simulation[battery_capacity_kwh]` | Number, 0 dec |
| CAPEX (€) | `gold_battery_simulation[total_capex_eur]` | Currency, 0 dec |
| Ann. Savings (€) | `gold_battery_simulation[annual_savings_eur]` | Currency, 0 dec |
| Payback (yr) | `gold_battery_simulation[payback_years]` | Number, 1 dec |
| NPV 10yr | `[V3 NPV Display]` | Text (pre-formatted) |
| IRR (%) | `gold_battery_simulation[irr_percent]` | Number, 1 dec, "%" |
| CO₂ (tCO₂/yr) | `gold_battery_simulation[annual_co2_avoided_kg]` (÷1000) | Number, 1 dec |
| **EU Compliance** | `[V3 EU Compliance Label]` | **Conditional format** |
| Score | `gold_battery_simulation[comparison_score]` | Data bar, 0–100 |

**Conditional formatting:**
- `[V3 EU Compliance Label]`: Green background if "EU Compliant", Red if "NON-COMPLIANT"
- `[V3 Payback Status]`: Green ≤7yr, Amber 7-12yr, Red >12yr (apply to Payback column)
- `comparison_score`: Blue data bar (0–100)

**Sort:** Default = `comparison_score` DESC

**Row highlight:** Active strategy rows (`gold_battery_simulation[is_active_strategy]` = TRUE) → bold text

---

## STEP 7 — V4: ROI Gauge

**Visual type:** Gauge

| Setting | Value |
|---|---|
| Value | `[V4 ROI Gauge Pct]` |
| Minimum | 0 |
| Maximum | 150 |
| Target | 100 |
| Callout value | `[C1 Annual Savings EUR]` |
| Subtitle | `[V4 ROI Status Label]` |

**Colors:**
- Gauge fill: Green (#27AE60) if > 100%, Amber (#F39C12) if 70–100%, Red (#E74C3C) if < 70%

---

## STEP 8 — V5: Cost vs Payback Scatter

**Visual type:** Scatter chart

| Setting | Value |
|---|---|
| X-axis | `[V5 Battery Cost EUR]` |
| Y-axis | `[V5 Payback Years]` |
| Size | `[V5 Capacity kWh]` |
| Color saturation | `[V5 Comparison Score]` |
| Legend/Details | `gold_battery_simulation[scenario_id]` |
| Tooltip | `[V5 Quadrant Label]`, strategy_label, eu_compliant |

**Axis labels:**
- X-axis title: "Battery CAPEX (€)"
- Y-axis title: "Simple Payback (years)"

**Color scale:** Green (high score) → Red (low score)

**Reference lines:**
- Y-axis horizontal line at 7yr: "Good payback threshold" (dashed green)
- Y-axis horizontal line at 12yr: "Max acceptable" (dashed red)

---

## STEP 9 — Supporting Cards

### Active Strategy Info Card (text card)
- Field: `[Active Strategy Label]`
- Secondary: `[Page9 Data As Of]`

### EU Compliance Summary Card
- Field: `[EU Compliance Portfolio Label]`
- Conditional format: Green if 0 non-compliant, Red if > 0

---

## STEP 10 — Slicers

| Slicer | Source | Type | Position |
|---|---|---|---|
| S1 Building | `silver_building_master[building_name]` | Dropdown | Top-right |
| S2 Strategy | `gold_battery_dispatch[strategy]` | List | Top-right |
| S3 Date Range | `gold_battery_dispatch[date]` | Between | Top-right |

**Filter S1 to Page 9 buildings only** (B001, B003, B004, B005, B006):
- Edit interactions: Add visual-level filter on `building_id NOT IN (B002)`

---

## STEP 11 — Validation Checklist

After binding all visuals, verify:

- [ ] C1 Annual Savings: B001 ~€14,000–15,000/yr (peak-shaving), B003 ~€60,000–70,000/yr
- [ ] C2 Payback: B001 ~2yr, B003 ~1.7yr, B005 (backup) ~17yr
- [ ] C3 CO₂: B001 ~16 tCO₂/yr, B003 ~75 tCO₂/yr
- [ ] C4 Efficiency: 93–95% LFP, 90–91% NMC; "(EU OK)" or "(NON-EU)" label visible
- [ ] V1 shows SoC variation 10–95% (not flat line)
- [ ] V1 strategies show different curves (peak_shaving higher SoC, self_consumption varies)
- [ ] V2 bars non-zero, PV generation line visible and seasonal
- [ ] V3 table: B005 shows "NON-COMPLIANT" in red for NMC battery
- [ ] V3 EU Compliance column color-coded (green/red clearly visible)
- [ ] V3 sort by comparison_score shows B003 peak_shaving first (score ≈100)
- [ ] V4 gauge: B003 peak_shaving at ~100% or above (on target)
- [ ] V5 scatter: B003_PEA at top-right area (high cost, low payback = large bubble)
- [ ] B004/B006 labeled as "Simulation only" in active strategy card
- [ ] S1 building filter changes all visuals simultaneously
- [ ] Date slicer works: selecting 1yr vs 3yr changes C1 annual savings correctly

---

## NOTES FOR ENERGY DOMAIN EXPERT (Mert)

**Why B001 self-consumption savings are low (€598/yr):**  
Berlin receives ~1,100 kWh/kWp/yr of solar. The 200 kWh battery is large relative to daily PV surplus in winter. Self-consumption strategy without grid charging leaves the battery underutilized Nov–Feb. This is realistic — self-consumption is best for smaller batteries or buildings with high daytime load. The peak-shaving strategy (€14,921/yr) dominates because German demand charges (€13.50/kW/month) make it highly profitable.

**Why B005 NMC backup strategy shows poor payback (17.8yr):**  
Healthcare backup batteries are sized for emergency reserve, not energy arbitrage. The NMC chemistry also degrades faster (3.5%/1000 cycles vs LFP 1.8%). The EU non-compliance warning reflects that NMC batteries installed post-2024 require a replacement plan. Recommendation: at next maintenance cycle, replace with CATL LFP 400kWh (€54,000 CAPEX, payback improves to ~8yr with TOU strategy).

**B004 and B006 are simulation scenarios:**  
These buildings have PV but no battery. Page 9 shows what the ROI would be if they added a battery. This is a key sales tool: "Your building could save X per year with this investment."
