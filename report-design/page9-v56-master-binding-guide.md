# Page 9 v56 — Master Binding Guide
**Battery Dispatch & Financial Simulation — production-grade refactor**
Date: 2026-05-21 · DAX active: v56 (file `68_dax_v56_page9_master.dax`)

---

## 0. Pre-flight (15 min)

### 0.1 Lakehouse — upload new tables
Drop the following CSVs into the Fabric Lakehouse "Files" area, then use
"Load to Tables" (or run a quick Notebook 16 with `spark.read.csv(...).write.saveAsTable(...)`):

| File | Target Delta table | Rows |
|---|---|---|
| `sample-data/gold_country_regulations.csv` | `gold_country_regulations` | 12 |
| `sample-data/gold_strategy_fitness.csv` | `gold_strategy_fitness` | 49 |
| `sample-data/gold_battery_technologies.csv` | overwrite existing `gold_battery_technologies` | 15 (was 10) |

### 0.2 Semantic-model relationships
In Power BI Desktop → Model view → make sure these relationships exist
(create where missing — direction shown):

| From (Many) | To (One) | Direction | Active |
|---|---|---|---|
| `gold_battery_dispatch[building_id]` | `silver_building_master[building_id]` | both | yes |
| `gold_battery_dispatch[battery_id]` | `gold_battery_technologies[battery_id]` | both | yes |
| `gold_battery_simulation[building_id]` | `silver_building_master[building_id]` | both | yes |
| `gold_battery_simulation[battery_tech]` (?) | `gold_battery_technologies[battery_type]` | both | yes |
| `gold_strategy_fitness[building_type]` | (no relationship — keep table standalone for V1 matrix) | — | — |
| `gold_country_regulations[country_code]` | `silver_building_master[country_code]` | both | yes |

> **Why no relationship on gold_strategy_fitness?**
> V1 visual is a matrix that shows ALL building_types × strategies; we don't
> want building_id slicer to filter the matrix down to one row.

### 0.3 Run the TE2 install script
1. External Tools → **Tabular Editor 2**
2. Advanced Scripting → paste `semantic-model/scripts/page9_v56_master_install.cs`
3. Run (F5) — check Output panel for `[CREATE] / [UPDATE] / [MOVE]` lines
4. **Save** (Ctrl+S)
5. Back in Power BI Desktop → Home → **Refresh**

---

## 1. Page Layout (final)

```
┌────────────────────────────────────────────────────────────────────┐
│  EnergyLens · Battery Dispatch & Financial Simulation              │
│  STRATEGY COMPARISON · EU 2023/1542 · NPV / IRR / PAYBACK          │
├────────────────────────────────────────────────────────────────────┤
│ Slicer strip:  S1 Building  S2 Strategy  S3 Chemistry  S4 Country  │
├──────────────────┬─────────────────────────────────────────────────┤
│ C1  C2  C3  C4  C5    (5 KPI cards, equal width)                   │
├──────────────────┼─────────────────────────────────────────────────┤
│ V1 Strategy      │ V2 24h Battery Behavior                          │
│    Recommender   │   (Charge + Discharge + SoC + Price)            │
│    Matrix        │                                                  │
├──────────────────┼─────────────────────────────────────────────────┤
│ V3 CAPEX vs      │ V4 Monthly Net Savings + CO₂                    │
│    Payback       │                                                  │
│    Scatter       │                                                  │
├──────────────────┼─────────────────────────────────────────────────┤
│ V5 Country ×     │ V6 Scenario Comparison Table                    │
│    Chemistry     │                                                  │
│    Heatmap       │                                                  │
├──────────────────┴─────────────────────────────────────────────────┤
│ V7 Battery Health Strip:  SoH%  ·  Cycles Used%  ·  Yrs to Replace │
├────────────────────────────────────────────────────────────────────┤
│ I1 Strategy rec   I2 Chemistry rec   I3 Compliance   I4 Next action│
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. Slicers (S1–S4)

| Slicer | Field | Style | Notes |
|---|---|---|---|
| S1 Building | `silver_building_master[building_name]` | Tile | already exists |
| S2 Strategy | `gold_battery_dispatch[strategy_label]` | Tile, single-select | already exists |
| S3 Chemistry **(NEW)** | `gold_battery_technologies[battery_type]` | Dropdown, multi-select | add at top-right |
| S4 Country **(NEW)** | `silver_building_master[country_code]` | Dropdown, single-select default ALL | adds country gating context |

Set **Edit Interactions**: S3 and S4 must NOT filter V1 (the recommender matrix
must remain global). V1 only listens to S1 (building → building_type infer).

---

## 3. KPI Cards (C1–C5)

| Card | Field bound | Format | Color rule |
|---|---|---|---|
| C1 Annual Savings | `[C1 Annual Savings EUR]` | € #,##0 | Green ≥ 25k, Amber ≥ 10k, else Grey |
| C2 Payback | `[C2 Payback Years]` + callout `[C2 Payback Status Label]` | 0.0 "yr" | colour from label |
| C3 CO₂ Avoided | `[C3 CO2 Avoided Tonnes Annual]` | 0.0 "tCO₂" | Green ≥ 30, Amber ≥ 10 |
| C4 Round-Trip Eff | `[C4 Round Trip Efficiency Pct]` | % 0.0 | Green ≥ 0.92, Amber ≥ 0.85, Red < 0.85 |
| C5 Compliance | `[C5 EU Compliance Status Text]` | text | Green ✓ / Amber ⚠ / Red ❌ |

> If you previously had a 4-card row, **resize cards to ~20% width each** so
> all five fit. Increase font on label, shrink value if needed.

---

## 4. V1 — Strategy Recommender Matrix (NEW)

**Visual type:** Matrix
**Rows:** `gold_strategy_fitness[building_type]`
**Columns:** `gold_strategy_fitness[strategy_label]`
**Values:** `[V1 Strategy Fitness Score]`

**Conditional formatting → Background color → Field value → `[V1 Fitness Color Bucket]`**

Result: a 7×7 heatmap (7 building_types × 7 strategies). Cells coloured
green/amber/red based on fitness score. Sells the "build-type aware" story.

Title: *"Strategy Fitness Matrix — pick the right strategy for the building"*

---

## 5. V2 — 24h Battery Behavior (KEEP — already working in your screenshot)

No changes required. This is the only working visual on your current Page 9
based on the screenshot — keep it as-is.

---

## 6. V3 — CAPEX vs Payback Scatter (enhance with chemistry color)

**Visual type:** Scatter chart
**X-axis:** `[V3 CAPEX EUR]`
**Y-axis:** `[V3 Payback Years]`
**Legend / play axis:** `gold_battery_simulation[battery_tech]`
**Size:** `gold_battery_simulation[battery_capacity_kwh]`
**Tooltip:** `gold_battery_simulation[strategy_label]`, `[V3 Battery Chemistry Color]`

**Conditional formatting → Color → fx → `[V3 Battery Chemistry Color]`**

Title: *"CAPEX vs Payback — bubble size = capacity, colour = chemistry"*

---

## 7. V4 — Monthly Net Savings + CO₂ (NEW dual-axis)

**Visual type:** Line and clustered column chart
**X-axis:** `gold_battery_dispatch[month_year_en]` (categorical, sort by month index)
**Column Y-axis:** `[V4 Monthly Net Savings EUR]`
**Line Y-axis:** `[V4 Monthly CO2 Avoided Kg]`
**Legend (column):** `gold_battery_dispatch[strategy_label]`

Title: *"Monthly Savings & CO₂ Avoided"*

Energy manager reads this as: "summer = high savings (PV abundant), winter =
strategy-dependent".

---

## 8. V5 — Country × Chemistry Heatmap (NEW — flagship innovation visual)

**Visual type:** Matrix
**Rows:** `gold_country_regulations[country_name]`
**Columns:** `gold_battery_technologies[battery_type]`
**Values:** `[V5 Country Chemistry Symbol]`

**Conditional formatting → Background color → Rules:**
- if `[V5 Country Chemistry Flag]` = 1 → `#27AE60` (green)
- if `[V5 Country Chemistry Flag]` = 0 → `#F39C12` (amber)
- if `[V5 Country Chemistry Flag]` = -1 → `#C0392B` (red)
- blank → grey `#444`

Title: *"EU Regulation Heatmap — which chemistry is approved where"*

This is the visual that says *"we know your market"* to a German prospect
and *"we cover Türkiye too"* to a Turkish prospect.

---

## 9. V6 — Scenario Comparison Table (KEEP from v48, expand columns)

**Visual type:** Table
**Columns to show (in this order):**
1. `gold_battery_simulation[building_name]`
2. `gold_battery_simulation[strategy_label]`
3. `gold_battery_simulation[battery_tech]`  ← chemistry
4. `gold_battery_simulation[battery_capacity_kwh]`
5. `[V3 CAPEX EUR]`
6. `gold_battery_simulation[annual_savings_eur]`
7. `gold_battery_simulation[payback_years]`
8. `gold_battery_simulation[irr_percent]`
9. `gold_battery_simulation[npv_10yr_eur]`
10. `gold_battery_simulation[comparison_score]`

Visual-level filter: `gold_battery_simulation[battery_capacity_kwh] > 0`
(removes empty scenario rows).

Sort: comparison_score DESC.

---

## 10. V7 — Battery Health Strip (NEW)

3 small cards side-by-side, full width row:

| Card | Field | Format |
|---|---|---|
| SoH % | `[V7 Current SoH Pct]` | 0.0% |
| Cycles Used % | `[V7 Cycles Used Pct]` | 0.0% |
| Years to Replacement | `[V7 Years Until Replacement]` | 0.0 yr |

Energy manager reads: "battery is at 91% SoH, used 38% of warranty cycles,
~7 years left before mandatory replacement."

---

## 11. Insight Strip (I1–I4 — bottom of page)

4 text cards equal width:

| Card | Field | Title |
|---|---|---|
| I1 | `[I1 Strategy Recommendation Text]` | *Strategy Recommendation* |
| I2 | `[I2 Chemistry Recommendation Text]` | *Chemistry Recommendation* |
| I3 | `[I3 Compliance Flag Text]` | *Compliance Status* |
| I4 | `[I4 Next Action Text]` | *Next Action* |

Card visual → Format → Callout value font: 11pt regular (long text fits)
Text wrap: ON

These four cards are the **prescriptive layer** — they tell the user what to
do. This is the Page 5 v54 pattern reapplied to Page 9.

---

## 12. Edit Interactions Rule

Building slicer (S1) must filter:
- C1, C2, C3, C4, C5 ✓
- V2, V3, V4, V6, V7 ✓
- V1 ✓ (filters via inferred building_type)
- V5 ✗ (V5 is global market reference — should NOT filter by building)
- I1, I2, I3, I4 ✓

Strategy slicer (S2) must filter:
- C1, C3, C4, V2, V4, V6 ✓
- C2, C5, V3, V5, V7, I1, I2, I3, I4 ✗

Chemistry slicer (S3) and Country slicer (S4):
- V5 ✓
- All others ✗ (to keep them clean)

To configure: click each slicer → Format → Edit Interactions → click each
visual and choose **None** (no filter icon) where listed ✗.

---

## 13. Expected Final Look

```
Frankfurt (B005) selected, S2 = All:
  C1: €36 990/yr     C2: 1.5 yr ✓ Excellent     C3: 60.9 tCO₂
  C4: 90.0%          C5: ❌ NMC banned in DE — replace before 2027

  V1 Matrix: healthcare row → backup green (100), peak_shaving amber (78)
  V3 Scatter: blue NMC bubble bottom-left (cheap but red flag)
  V5 Heatmap: row DE × col NMC → red ✗
  I1: "For this healthcare building in DE, primary strategy: Backup +
       Opportunistic (combined with Peak-Shaving). Estimated annual savings
       ≈ €38 000 (range ±25%)."
  I2: "Recommended: LFP (CATL or Fluence) — NMC chemistry banned for new
       installs in DE per BattG 2025 amendment. ..."
  I3: "⚠ Active battery is NMC — banned in DE for new installs from
       2025-01. Replacement window: 2027-Q1."
  I4: "Cycle headroom 5.8 years. Schedule mid-life maintenance + warranty
       audit."

Hamburg (B003) Logistics selected, S2 = peak_shaving:
  C1: ≈ €100 000/yr  C2: 1.7 yr ✓ Excellent     C3: ≈ 137 tCO₂
  C4: 94.0%          C5: ✓ EU 2023/1542 compliant

  V1 Matrix: logistics × peak_shaving = bright green (95)
  V5 Heatmap: row DE × col LFP = green ✓
  I1: "...Logistics building in DE, primary strategy: Peak-Shaving..."
  I2: "Recommended: LFP (CATL or Fluence) — ..."
  I3: "✓ Active battery fully EU 2023/1542 compliant ..."
  I4: "✓ Strong investment case (payback < 5 years). Recommend portfolio
       rollout to similar buildings."
```

---

## 14. Smoke-Test Checklist

- [ ] All five KPI cards render values (no ❌ See details panels)
- [ ] V1 matrix shows 7×7 colored cells
- [ ] V2 24h chart still working as before
- [ ] V3 scatter shows chemistry colors (legend visible)
- [ ] V4 dual-axis renders bars + line
- [ ] V5 heatmap colors: DE × NMC = red, NL × LFP-V2G = green, NO × LFP = green
- [ ] V6 table shows 13+ rows, no empty rows
- [ ] V7 health strip cards populated for active-battery buildings
- [ ] I1–I4 text cards display rich prescriptive sentences
- [ ] No yellow warning triangles in field-well of any visual
- [ ] No "(gold_battery_dispatch) Move measure to another table" warnings

---

## 15. Files Reference

| File | Purpose |
|---|---|
| `semantic-model/68_dax_v56_page9_master.dax` | Full DAX (26 measures) |
| `semantic-model/scripts/page9_v56_master_install.cs` | TE2 bulk install |
| `sample-data/gold_country_regulations.csv` | 12 countries (DACH+Benelux+Nordics+TR+UK) |
| `sample-data/gold_strategy_fitness.csv` | 49 rows: 7 bldg-types × 7 strategies |
| `sample-data/gold_battery_technologies.csv` | now 15 rows (LFP + NMC + NCA + Sodium-Ion + Solid-State + V2G + Second-Life + Hybrid) |
| `docs/page9_v56_master_design.md` | Architecture rationale & energy logic (Sprint 4 deliverable) |
