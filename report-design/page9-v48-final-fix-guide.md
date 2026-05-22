# PAGE 9 — Final Fix Guide (v48)
## Battery Dispatch & Financial Simulation

**Status:** Ready to apply  
**DAX Patch:** `semantic-model/59_dax_v48_page9_fixes.dax`  
**Background:** `report-design/backgrounds/09_battery_strategy_v3.png` (new layout)  
**Date:** 2026-05-09  
**Prerequisite:** v47 DAX already imported + all visuals bound per page9-battery-binding-guide.md

---

## QUICK REFERENCE: WHAT TO DELETE / MOVE / ADD

| Action | Visual | Reason |
|---|---|---|
| 🗑 **DELETE** | V1 SoC Trend — current position (bottom-right panel) | Right panel too small for chart |
| 🗑 **DELETE** | Active Strategy text card (left panel) | Too long text; replaced by right panel card |
| 🗑 **DELETE** | EU Compliance text card (left panel) | Merged into right panel card subtitle |
| ➕ **ADD** | V1 SoC Trend — new position: left middle zone | Same visual, moved to wider left area |
| ➕ **ADD** | Active Strategy card (right panel, zone: ACTIVE STRATEGY) | Use `[Active Strategy Short Label]` |
| ➕ **ADD** | Battery Status card (right panel, zone: ACTIVE STRATEGY) | Use `[Active Battery Label]` |
| ✏️ **RESIZE** | V4 ROI Gauge — expand to fill full right top zone | More breathing room without V1 next to it |
| ✏️ **UPDATE** | Background image → `09_battery_strategy_v3.png` | New layout zones match the grid above |

> Direct Lake mode note: Do NOT try to add calculated columns in Power BI Desktop.
> Run `notebooks/simulation/12b_patch_month_year_column.py` in Fabric first, then Refresh dataset.

---

## SUMMARY OF ALL FIXES

| # | Problem | Root Cause | Fix |
|---|---|---|---|
| 1 | Month names in Turkish (Oca, Tem…) | Report locale = Turkish | Change to English (United States) |
| 2 | Charts too dense — daily 3.5yr data | X-axis uses raw `date` (1204 pts) | Add MonthYear calculated column → use on X-axis |
| 3 | V3 table mostly blank rows | `silver_building_master[building_name]` causes cross-join | Replace with `gold_battery_simulation[building_name]` |
| 4 | C4 card shows blank / wrong value | DAX column name bug: `round_trip_efficiency` (doesn't exist) | v48 fix: `round_trip_efficiency_percent` |
| 5 | Scatter labels unreadable (B001_SEL_200kWh) | scenario_id used as detail | Add `Scatter Label` calculated column |
| 6 | Right panel too small for 2 charts | V1 SoC Trend placed in right panel | Move V1 to left side, right = Gauge + cards only |
| 7 | Active Strategy card too long | Shows "Building Name — strategy" | Replace measure with `[Active Strategy Short Label]` |

---

## STEP 0 — Fix Report Locale (English Month Names)

**Why this matters:** Power BI uses the report locale to format dates. Turkish locale renders months as Oca/Şub/Mar/Nis/May/Haz/Tem/Ağu/Eyl/Eki/Kas/Ara. This affects all date-formatted X-axes.

1. In Power BI Desktop: **File → Options & Settings → Options**
2. Left panel → **Current File → Regional Settings**
3. Change **Locale for import** dropdown to: `English (United States)`
4. Click OK
5. **Close and reopen** the report (or Refresh)

✅ After this fix, months will render as Jan/Feb/Mar/Apr/May/Jun/Jul/Aug/Sep/Oct/Nov/Dec.

> **Note:** This change also affects how number separators render (period vs comma for decimals). Check your card format strings after applying — if values looked correct before, no change needed.

---

## STEP 1 — Import v48 DAX Measures

1. Open `semantic-model/59_dax_v48_page9_fixes.dax` in a text editor
2. In Power BI Desktop → **Modeling tab → New Measure**
3. Import these 4 measures (paste each block individually):
   - `[C4 Round Trip Efficiency Pct]` — replaces v47 version (bug fix)
   - `[C4 Label Efficiency]` — replaces v47 version
   - `[Active Strategy Short Label]` — new shorter card text
   - `[Active Battery Label]` — new card for battery details
4. Save to `_Page9_Battery` display folder

> **Important:** For `[C4 Round Trip Efficiency Pct]`, if the measure already exists from v47, **delete it first** before importing the v48 version.

---

## STEP 2 — Add Calculated Columns (Data View)

These are **calculated columns**, not measures. Go to **Data view** in Power BI Desktop.

### 2a. gold_battery_dispatch — MonthYear column

1. Click on `gold_battery_dispatch` table in the Fields panel
2. **Table Tools → New Column**
3. Enter:
   ```
   MonthYear = FORMAT(gold_battery_dispatch[date], "MMM YYYY")
   ```
4. Add a second column for sorting:
   ```
   MonthYearSort = YEAR(gold_battery_dispatch[date]) * 100 + MONTH(gold_battery_dispatch[date])
   ```
5. Set sort order: Click `MonthYear` column → **Column Tools → Sort by Column → MonthYearSort**

### 2b. gold_battery_simulation — Scatter Label column

1. Click on `gold_battery_simulation` table in the Fields panel
2. **Table Tools → New Column**
3. Enter:
   ```
   Scatter Label = gold_battery_simulation[building_id] & " · " & gold_battery_simulation[strategy_label]
   ```

**Result examples:**
- `B001 · Peak-Shaving`
- `B003 · Time-of-Use (ToU)`
- `B005 · Backup + Opportunistic`

---

## STEP 3 — Fix V3 Table (Scenario Comparison)

This is the **most important fix**. The table is showing mostly blank rows because `silver_building_master[building_name]` is the Building column, which creates a cross-join with gold_battery_simulation rows.

### 3a. Open the V3 table visual

1. Click on the V3 table visual on Page 9
2. Go to the **Fields** panel (right side)

### 3b. Replace Building column

1. In the Columns field well, find `building_name` from `silver_building_master`
2. **Remove it** (click X)
3. **Add** `gold_battery_simulation[building_name]` in its place (drag from Fields panel)
4. Position it as the **first column**

### 3c. Verify all 13 columns are correctly bound

After the fix, the V3 table should use ONLY `gold_battery_simulation` columns:

| Column Label | Field Source |
|---|---|
| Building | `gold_battery_simulation[building_name]` ← **CHANGED** |
| Strategy | `gold_battery_simulation[strategy_label]` |
| Battery | `gold_battery_simulation[battery_type]` |
| kWh | `gold_battery_simulation[battery_capacity_kwh]` |
| CAPEX (€) | `gold_battery_simulation[total_capex_eur]` |
| Savings/yr (€) | `gold_battery_simulation[annual_savings_eur]` |
| Payback (yr) | `gold_battery_simulation[payback_years]` |
| NPV 10yr | `[V3 NPV Display]` |
| IRR (%) | `gold_battery_simulation[irr_percent]` |
| CO₂ (tCO₂/yr) | `gold_battery_simulation[annual_co2_avoided_kg]` |
| EU Status | `[V3 EU Compliance Label]` |
| Score | `gold_battery_simulation[comparison_score]` |

### 3d. Expected result after fix

- **13 rows** visible when Building = All (not blank rows)
- **5 rows** for Berlin (B001) only, **3 rows** for Hamburg (B003) only
- B005 rows highlighted red in EU Status column
- comparison_score data bar visible in all rows

### 3e. Note on rows with 0 savings / 25yr payback

Several scenarios intentionally show poor performance — this is correct data:
- B001 self_consumption: €598/yr savings, 25yr payback → Berlin winter lacks PV surplus
- B003 self_consumption: €0 savings → Hamburg 800kWh battery too large for self-consumption
- B005 self_consumption: €0 savings → Hospital battery only used for backup

These rows are **valid and important** — they show WHY the recommended strategy is better.

---

## STEP 4 — Fix V1 and V2 Date Axis (Monthly Grouping)

After adding MonthYear column (Step 2a), update both chart X-axes.

### 4a. V1 — SoC Trend (Area Chart)

1. Click V1 (State of Charge Trend visual)
2. In **X-axis** field well:
   - Remove `gold_battery_dispatch[date]`
   - Add `gold_battery_dispatch[MonthYear]`
3. In **Format Visual → X-axis:**
   - Type: Categorical (not continuous)
   - Values: Auto (will group by month)
4. Reduce **marker density** or turn off markers for cleaner line

✅ Result: 42 monthly points (Jan 2023 – Apr 2026) instead of 1204 daily points.

### 4b. V2 — Daily Charge/Discharge (Bar/Line Chart)

1. Click V2 visual
2. In **X-axis** field well:
   - Remove `gold_battery_dispatch[date]`
   - Add `gold_battery_dispatch[MonthYear]`
3. The measures `[V2 Charge kWh Daily]`, `[V2 Discharge kWh Daily]`, `[V2 PV Generation kWh]` will automatically **SUM to monthly totals** — this is correct behavior.
4. Rename chart title to: **"Monthly Charge / Discharge"** (was "Daily Charge / Discharge")

✅ Result: Clear seasonal pattern visible — charge peaks in summer months, discharge smoothly distributed.

### Visual readability improvements for both charts

- **Line thickness:** Increase to 2.5px for all series
- **Transparency:** Set area chart opacity to 40% (not 100%) so series don't hide each other
- **Data labels:** OFF (too many points)
- **Gridlines:** Reduce to major gridlines only
- **Legend:** Move to top of chart

---

## STEP 5 — Fix V5 Scatter Chart (Readable Labels)

1. Click V5 (Cost vs Payback Scatter)
2. In **Details** field well (determines bubble label / legend):
   - Remove `gold_battery_simulation[scenario_id]`
   - Add `gold_battery_simulation[Scatter Label]` (calculated column from Step 2b)
3. In **Format Visual → Data labels:**
   - Turn ON data labels
   - Position: Above
   - Font size: 9pt
   - Max labels shown: 13 (all scenarios)

**Expected bubble labels after fix:**
- `B001 · Peak-Shaving` (top left area — low cost, very short payback)
- `B003 · Peak-Shaving` (top right — high cost, very short payback)
- `B005 · Backup + Opp.` (bottom area — poor payback)
- etc.

---

## STEP 6 — Layout Reorganization (Right Panel)

**Problem:** Both V4 (ROI Gauge) and V1 (SoC Trend) are on the right panel which is too narrow for two chart-type visuals.

**Fix:** Move V1 (SoC Trend) to the **left side**. Right panel = Gauge + cards only.

### New recommended layout

```
┌──────────────────────────────────────────────────────────────────────┐  Y:0
│  TITLE + subtitle                                                    │  H:40
├────────────┬────────────┬────────────┬────────────────────────────── ┤  Y:50
│  C1 Savings│ C2 Payback │ C3 CO₂     │ C4 Efficiency                │
│  X:10 W:290│ X:310 W:290│ X:610 W:290│ X:910 W:350                  │
├────────────────────────────────────┬─────────────────────────────────┤  Y:150
│  V2: Monthly Charge/Discharge      │  V4: ROI Gauge                  │
│  X:10 Y:150  W:760  H:200          │  X:780 Y:150  W:490 H:200       │
├────────────────────────────────────┤─────────────────────────────────┤  Y:360
│  V1: SoC Monthly Trend             │  [Active Strategy Short Label]  │
│  X:10 Y:360  W:760  H:170          │  card  X:780 Y:360  W:490 H:80  │
│                                    ├─────────────────────────────────┤
│                                    │  [Active Battery Label]         │
│                                    │  card  X:780 Y:450  W:490 H:80  │
├────────────────────────────────────┤─────────────────────────────────┤  Y:540
│  V3: Scenario Table                │  V5: Cost vs Payback Scatter    │
│  X:10 Y:540  W:760  H:170          │  X:780 Y:540  W:490 H:170       │
└──────────────────────────────────────────────────────────────────────┘  Y:720
```

### Steps to reorganize

1. **Move V1 (SoC Trend)** from right side → left side
   - Position: X:10, Y:360, W:760, H:170
   - Resize accordingly

2. **Resize V4 (ROI Gauge)** to take full right top
   - Position: X:780, Y:150, W:490, H:200

3. **Remove** the current Active Strategy card and EU Compliance card from left
4. **Add two cards** on the right middle:
   - Card 1: `[Active Strategy Short Label]` + `[Page9 Data As Of]` as subtitle
   - Card 2: `[Active Battery Label]` + `[EU Compliance Portfolio Label]` as subtitle
   - Stack vertically at X:780, Y:360–540

5. **V3 Table:** move to bottom left (X:10, Y:540, W:760, H:170)
6. **V5 Scatter:** bottom right (X:780, Y:540, W:490, H:170)

### Right panel card formatting

For both right panel cards:
- Background: dark navy `#0D1B2A` with 80% transparency
- Border: 1px `#1E90FF` (electric blue)
- Text color: white
- Font size: 12pt for value, 9pt for subtitle
- Padding: 8px

---

## STEP 7 — Update Active Strategy Card

1. Click the current **Active Strategy info card** (left panel)
2. In the **Fields** panel:
   - Remove current `[Active Strategy Label]` (v47 version)
   - Add `[Active Strategy Short Label]` (v48 new measure)
3. For the subtitle line: keep `[Page9 Data As Of]` (no change)

**Before:** `Hamburg Logistics Hub Gamma — peak_shaving`  
**After:** `● Active | Peak-Shaving`

---

## STEP 8 — Validation Checklist (v48)

After applying all fixes, verify:

### Locale & Dates
- [ ] Month labels on V1/V2 X-axis show **Jan, Feb, Mar...** (not Oca, Şub, Mar)
- [ ] V1/V2 X-axis shows ~42 monthly points (Jan 2023 to Apr 2026)
- [ ] Lines/bars are clearly readable with no excessive density

### V3 Table
- [ ] Exactly **13 rows** visible when Building = All, Strategy = All
- [ ] All rows have values (no blank/dash rows except intentional 0-savings scenarios)
- [ ] B005 rows show **"NON-COMPLIANT"** in red EU Status column
- [ ] Sorting by Score DESC shows B003_PEA first (score=100)
- [ ] When Berlin selected → 3 rows; Hamburg → 3 rows; Frankfurt → 3 rows

### V5 Scatter
- [ ] Bubble labels show readable format: "B001 · Peak-Shaving" not "B001_PEA_200kWh"
- [ ] All 13 bubbles visible (may need to scroll or zoom)
- [ ] Reference lines at 7yr and 12yr visible

### C4 Card
- [ ] C4 shows numeric efficiency value (90–95%) — not blank
- [ ] Label shows "LFP — High Efficiency (EU OK)" or "NMC/NCA — Moderate (NON-EU)"

### Active Strategy Card
- [ ] Shows "● Active | Peak-Shaving" format (not long building name)
- [ ] For B004/B006: shows "◌ Simulation | Time-of-Use (ToU)"

### Layout
- [ ] Right panel: V4 Gauge (top) + 2 text cards (middle) only — no chart on right bottom except V5 scatter
- [ ] V1 SoC Trend: visible on left side, all strategies clearly distinguishable
- [ ] V2 Charge/Discharge: monthly bars, seasonal pattern visible

---

## DATA NOTES (for validation)

### Expected KPI Card values (single building + active strategy)

| Building | Active Strategy | C1 Savings | C2 Payback | C3 CO₂ | C4 Efficiency |
|---|---|---|---|---|---|
| Berliner (B001) | Self-Consumption | ~€598/yr | 25yr | ~0.8 tCO₂ | 94.5% LFP |
| Hamburg (B003) | Peak-Shaving | ~€66,039/yr | 1.7yr | ~75.6 tCO₂ | 95.0% LFP |
| Frankfurt (B005) | Backup+Opp. | ~€3,037/yr | 17.8yr | ~5.3 tCO₂ | 90.5% NMC |
| Wien (B004) | Simulation only | ~€2,713/yr | 11yr | ~3.0 tCO₂ | 94.5% LFP |
| Amsterdam (B006) | Simulation only | ~€2,038/yr | 10.5yr | ~2.8 tCO₂ | 93.5% LFP |

> Cards use dispatch data annualized — values may differ slightly from simulation table (within ±10%).

### Why some scenarios show €0 savings
- These are **intentional design data points**, not errors
- B001 Self-Consumption: Berlin winter PV insufficient → self-consumption strategy fails
- B003 Self-Consumption: 800kWh battery too large for self-consumption in Hamburg
- Recommendation engine on Page 9 table should guide user away from these strategies

---

*Fix guide version: v48 — 2026-05-09*
