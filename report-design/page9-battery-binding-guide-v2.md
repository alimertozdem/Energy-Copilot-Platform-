# PAGE 9 — Battery Dispatch & Financial Simulation
## Power BI Binding Guide — DAX v48 · Layout v2

**Background:** `report-design/backgrounds/09_battery_strategy_v2.png`  
**DAX file:** `semantic-model/59_dax_v48_page9_battery_v2.dax`  
**Canvas:** 1280 × 720 px  
**Date:** 2026-05-08

---

## STEP 0 — Import DAX Measures

1. Open `59_dax_v48_page9_battery_v2.dax`
2. Power BI Desktop → **Modeling** → **New Measure** → paste each measure block
3. Organize into display folder: `_Page9_Battery`
4. Total: **32 measures** in 10 groups

---

## STEP 1 — Page Setup

1. New page → rename **"Battery Strategy"**
2. Format → Page → Canvas background → browse `09_battery_strategy_v2.png`
   - Transparency: **85%**  ← important: lower = darker background
3. Canvas size: **1280 × 720**

---

## STEP 2 — LEFT SIDEBAR  (x: 0–205)

Three slicers + two status cards. Place all inside the left dark panel.

### S1 — Building Slicer
| Setting | Value |
|---|---|
| Visual type | Dropdown |
| Position | x:12, y:88, w:181, h:26 |
| Field | `silver_building_master[building_name]` |
| Visual-level filter | `building_id` is one of: B001, B003, B004, B005, B006 |

### S2 — Strategy Slicer
| Setting | Value |
|---|---|
| Visual type | List (show all 4 strategies) |
| Position | x:12, y:134, w:181, h:26 |
| Field | `gold_battery_dispatch[strategy]` |

### S3 — Date Range Slicer
| Setting | Value |
|---|---|
| Visual type | Between |
| Position | x:12, y:180, w:181, h:26 |
| Field | `gold_battery_dispatch[date]` |

### Active Strategy Card
| Setting | Value |
|---|---|
| Visual type | **New Card** |
| Position | x:12, y:242, w:181, h:58 |
| Value (callout) | `[Active Strategy Label]` |
| Reference label | `[Page9 Data As Of]` |
| Background | Transparent |

### EU Compliance Card
| Setting | Value |
|---|---|
| Visual type | **New Card** |
| Position | x:12, y:322, w:181, h:46 |
| Value | `[EU Compliance Portfolio Label]` |
| Conditional format | Green background if text contains "EU OK", Red if "NON-COMPLIANT" |

---

## STEP 3 — KPI CARDS  (y:72, h:108)

Use **New Card** visual (not legacy card) for all four.

### C1 — Annual Savings  `x:215  w:260`
| Slot | Measure |
|---|---|
| **Value (callout)** | `[C1 Annual Savings EUR]` |
| **Reference label** | `[C1 Label Savings]` |
| Format | Currency, 0 decimals, € prefix |
| Conditional format (value) | Green > €5,000 · Amber €1,000–5,000 · Grey < €1,000 |

### C2 — Payback Period  `x:483  w:260`
| Slot | Measure |
|---|---|
| **Value (callout)** | `[C2 Payback Years]` |
| **Reference label** | `[C2 Label Payback]` |
| Format | Decimal 1 place, "yr" suffix |
| Conditional format | Green ≤ 7yr · Amber 7–12yr · Red > 12yr |

### C3 — CO₂ Avoided  `x:751  w:260`
| Slot | Measure |
|---|---|
| **Value (callout)** | `[C3 CO2 Avoided tCO2 Annual]` |
| **Reference label** | `[C3 Label CO2]` |
| Format | Decimal 1 place, "tCO₂/yr" suffix |

### C4 — Efficiency + EU  `x:1019  w:248`
| Slot | Measure |
|---|---|
| **Value (callout)** | `[C4 Round Trip Efficiency Pct]` |
| **Reference label** | `[C4 Label Efficiency]` |
| Format | Percentage 1 decimal |

---

## STEP 4 — V1: STATE OF CHARGE TREND  `x:215  y:188  w:635  h:225`

**Visual type:** Area chart (or Line chart)

| Slot | Value |
|---|---|
| **X-axis** | `gold_battery_dispatch[date]` |
| **Y-axis (area, primary)** | `[V1 SoC End Percent]` |
| **Secondary series (line, dashed)** | `[V1 SoC Start Percent]` |
| **Legend** | `gold_battery_dispatch[strategy]` |

**Series colors** (Format → Data colors):
- `self_consumption` → **#2ECC71** (green)
- `peak_shaving` → **#F4A62A** (amber)
- `tou` → **#3498DB** (blue)
- `backup` → **#9B59B6** (purple)

**Reference line** (Analytics pane → Constant Line):
- Value: **10** · Label: "Min SoC 10%" · Color: Red · Style: Dashed

**Edit interactions:**
- S1 Building → Cross-filter V1 ✅
- S2 Strategy → Cross-filter V1 ✅
- S3 Date → Cross-filter V1 ✅
- V3 Table row click → Cross-filter V1 ✅

---

## STEP 5 — V4: ROI GAUGE  `x:858  y:188  w:409  h:108`

**Visual type:** Gauge

| Slot | Value |
|---|---|
| **Value (needle)** | `[V4 ROI Gauge Pct]` |
| **Minimum** | 0 |
| **Maximum** | 150 |
| **Target** | 100 |
| **Callout value** | `[C1 Annual Savings EUR]` |
| **Subtitle / Reference label** | `[V4 ROI Status Label]` |

**Gauge fill color rules:**
- > 100% → **#27AE60** (green)
- 70–100% → **#F39C12** (amber)
- < 70% → **#E74C3C** (red)

---

## STEP 6 — V2: DAILY CHARGE / DISCHARGE  `x:858  y:304  w:409  h:109`

**Visual type:** Clustered Bar Chart + Line overlay

| Slot | Measure | Color |
|---|---|---|
| **Y-axis bar 1** | `[V2 Charge kWh Daily]` | **#2980B9** (blue) |
| **Y-axis bar 2** | `[V2 Discharge kWh Daily]` | **#F39C12** (orange) |
| **Line overlay** | `[V2 PV Generation kWh]` | **#F1C40F** dashed |
| **X-axis** | `gold_battery_dispatch[date]` | — |

**Tooltip fields (drag to Tooltip well):**
- `[V2 Grid Charge kWh Daily]`
- `[V2 PV Charge kWh Daily]`
- `[V2 Net Savings EUR Daily]`

---

## STEP 7 — V5: CAPEX vs PAYBACK SCATTER  `x:215  y:423  w:370  h:287`

**Visual type:** Scatter Chart

| Slot | Measure | Note |
|---|---|---|
| **X-axis** | `[V5 Battery Cost EUR]` | Axis title: "Battery CAPEX (€)" |
| **Y-axis** | `[V5 Payback Years]` | Axis title: "Payback (years)" |
| **Size** | `[V5 Capacity kWh]` | Bubble size = battery capacity |
| **Color saturation** | `[V5 Comparison Score]` | Green = high, Red = low |
| **Details** | `gold_battery_simulation[scenario_id]` | One bubble per scenario |
| **Tooltip** | `[V5 Quadrant Label]` | + strategy_label, eu_compliant |

**Reference lines** (Analytics pane):
- Horizontal Y = **7** → "Good payback" · #27AE60 dashed
- Horizontal Y = **12** → "Max acceptable" · #E74C3C dashed

---

## STEP 8 — V3: SCENARIO COMPARISON TABLE  `x:593  y:423  w:674  h:287`

**Visual type:** Table

**Columns in order:**

| # | Column | Source | Format | Notes |
|---|---|---|---|---|
| 1 | Building | `silver_building_master[building_name]` | Text | — |
| 2 | Strategy | `gold_battery_simulation[strategy_label]` | Text | Bold for active |
| 3 | Battery | `gold_battery_simulation[battery_type]` | Text | — |
| 4 | kWh | `gold_battery_simulation[battery_capacity_kwh]` | 0 dec | — |
| 5 | CAPEX | `gold_battery_simulation[total_capex_eur]` | € #,##0 | — |
| 6 | Savings/yr | `gold_battery_simulation[annual_savings_eur]` | € #,##0 | — |
| 7 | Payback | `gold_battery_simulation[payback_years]` | #,##0.0 "yr" | Cond. format via `[V3 Payback Status]` |
| 8 | NPV 10yr | `[V3 NPV Display]` | Text | Pre-formatted |
| 9 | IRR | `gold_battery_simulation[irr_percent]` | #,##0.0 "%" | — |
| 10 | CO₂ t/yr | `gold_battery_simulation[annual_co2_avoided_kg]` ÷ 1000 | #,##0.1 | Use ÷1000 in measure or format |
| 11 | **EU** | `[V3 EU Compliance Label]` | Text | **Green/Red cond. format** |
| 12 | Score | `gold_battery_simulation[comparison_score]` | Data bar 0–100 | Blue bar |

**Conditional formatting:**
- Column 11 (EU): Background → "EU Compliant" → #D4EDDA · "NON-COMPLIANT" → #F8D7DA
- Column 7 (Payback): Background using `[V3 Payback Status]` rules  
  → Value 1: #D4EDDA (green) · Value 2: #FFF3CD (amber) · Value 3: #F8D7DA (red)

**Table settings:**
- Default sort: `comparison_score` DESC
- Row highlight rule: `is_active_strategy = TRUE` → bold text
- Visual-level filter: `building_id` is not B002

**Edit interactions:**
- V3 row click → Cross-filter V1, V4, V2 ✅

---

## STEP 9 — INTERACTION MATRIX

Set via **Edit Interactions** mode (Format ribbon):

|  | C1 | C2 | C3 | C4 | V1 | V4 | V2 | V5 | V3 |
|---|---|---|---|---|---|---|---|---|---|
| **S1 Building** | F | F | F | F | F | F | F | F | F |
| **S2 Strategy** | F | F | F | F | F | F | F | F | F |
| **S3 Date** | F | – | F | F | F | – | F | – | – |
| **V3 row click** | F | – | – | – | F | F | F | H | – |

`F` = Cross-filter · `H` = Highlight · `–` = No interaction

---

## STEP 10 — VALIDATION CHECKLIST

Run after binding all visuals:

- [ ] **C1** Annual Savings: B001 ~€14,921/yr · B003 ~€66,039/yr · B005 ~€3,037/yr
- [ ] **C2** Payback: B001 ~2.0yr (green) · B003 ~1.7yr (green) · B005 ~17.8yr (red)
- [ ] **C3** CO₂: B001 ~16 tCO₂/yr · B003 ~75 tCO₂/yr
- [ ] **C4** Efficiency: 93–95% LFP → "EU OK" label visible
- [ ] **Sidebar** Active Strategy card shows building name + strategy text
- [ ] **Sidebar** EU Compliance card shows red badge for B005 NMC
- [ ] **V1** SoC curves vary 10–95%, NOT flat lines
- [ ] **V1** peak_shaving curve (amber) visibly different from self_consumption (green)
- [ ] **V4** Gauge: B003 peak_shaving ≥ 100% (green fill)
- [ ] **V2** Bars non-zero · PV line seasonal (higher in summer months)
- [ ] **V3** B005 "NON-COMPLIANT" row has red EU cell
- [ ] **V3** Sort shows B003 peak_shaving at top (score ≈ 100)
- [ ] **V3** Active strategy rows appear **bold**
- [ ] **V5** B003 peak_shaving bubble: upper-left area (low payback, higher cost) largest
- [ ] **S1** Switching building changes ALL visuals simultaneously
- [ ] **S3** Date 1yr vs 3yr changes C1 savings value

---

## QUICK REFERENCE — Measure → Visual Slot

```
[Active Strategy Label]          → Sidebar Active Strategy card · Value
[Page9 Data As Of]               → Sidebar Active Strategy card · Reference label
[EU Compliance Portfolio Label]  → Sidebar EU Compliance card · Value

[C1 Annual Savings EUR]          → C1 card · Value (callout)
[C1 Label Savings]               → C1 card · Reference label
[C2 Payback Years]               → C2 card · Value (callout)
[C2 Label Payback]               → C2 card · Reference label
[C3 CO2 Avoided tCO2 Annual]     → C3 card · Value (callout)
[C3 Label CO2]                   → C3 card · Reference label
[C4 Round Trip Efficiency Pct]   → C4 card · Value (callout)
[C4 Label Efficiency]            → C4 card · Reference label

[V1 SoC End Percent]             → V1 area chart · Y-axis (primary area)
[V1 SoC Start Percent]           → V1 area chart · Secondary series (dashed line)

[V4 ROI Gauge Pct]               → V4 gauge · Value
[V4 ROI Status Label]            → V4 gauge · Subtitle / Reference label

[V2 Charge kWh Daily]            → V2 bar chart · Bar 1 (blue)
[V2 Discharge kWh Daily]         → V2 bar chart · Bar 2 (orange)
[V2 PV Generation kWh]           → V2 bar chart · Line overlay (yellow dashed)
[V2 Grid Charge kWh Daily]       → V2 · Tooltip
[V2 PV Charge kWh Daily]         → V2 · Tooltip
[V2 Net Savings EUR Daily]       → V2 · Tooltip

[V5 Battery Cost EUR]            → V5 scatter · X-axis
[V5 Payback Years]               → V5 scatter · Y-axis
[V5 Capacity kWh]                → V5 scatter · Size
[V5 Comparison Score]            → V5 scatter · Color saturation
[V5 Quadrant Label]              → V5 scatter · Tooltip

[V3 NPV Display]                 → V3 table · Column 8
[V3 EU Compliance Label]         → V3 table · Column 11 (conditional format)
[V3 Payback Status]              → V3 table · Column 7 background color rule
```
