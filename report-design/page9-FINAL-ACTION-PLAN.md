# PAGE 9 — Final Action Plan
**Battery Dispatch & Financial Simulation**
Last updated: 2026-05-09 | DAX: v47 + v48 patch | Background: 09_battery_strategy.png (unchanged)

---

## STATUS OVERVIEW

| Area | Status | Notes |
|---|---|---|
| Data (CSVs) | ✅ Complete | 13 scenarios, 15,652 dispatch rows |
| DAX v47 | ✅ Imported | 32 base measures |
| DAX v48 patch | ⏳ Import needed | 4 fix measures (C4 bug + 2 new cards) |
| Visuals bound | ✅ Mostly done | V1/V2/V3/V4/V5 placed |
| Month grouping | ⏳ Notebook first | Run 12b notebook, then Power BI refresh |
| V3 table fix | ⏳ Quick fix | Change 1 column source |
| Layout reorg | ⏳ Move 1 visual | Move V1 from right → left |
| Cards fix | ⏳ Replace 2 cards | Old long-text cards → new short measures |

**Estimated time remaining: ~60 minutes**

---

## STEP A — Fabric: Run Notebook 12b (5 min)

**Why first:** Power BI can't refresh new columns until the table is updated.

1. Open Fabric → go to notebook `12b — Patch gold_battery_dispatch`
   - File is in: `notebooks/simulation/12b_patch_month_year_column.py`
2. **Check left panel → Data items:** EnergyCopilotLakehouse must be attached
   - If not: click **Add data items** → add EnergyCopilotLakehouse → right-click → **Set as default**
3. **Run All**
4. Verify CELL 5 output shows `month_year_en` and `month_year_sort` in the column list
5. ✅ Done when you see: `"✅ Done — gold_battery_dispatch updated"`

---

## STEP B — Power BI: Refresh + Import v48 DAX (10 min)

### B1. Refresh dataset
- Power BI Desktop → **Home → Refresh**
- Wait for complete. Verify `gold_battery_dispatch` table has new columns: `month_year_en`, `month_year_sort`

### B2. Import v48 patch measures (4 measures)
Open file: `semantic-model/59_dax_v48_page9_fixes.dax`

Import these 4 measures (Modeling → New Measure, paste each):

| Measure name | Replaces / New |
|---|---|
| `[C4 Round Trip Efficiency Pct]` | ⚠️ DELETE old v47 version first, then paste new |
| `[C4 Label Efficiency]` | ⚠️ DELETE old v47 version first, then paste new |
| `[Active Strategy Short Label]` | New measure (no old version to delete) |
| `[Active Battery Label]` | New measure (no old version to delete) |

Save all → put in `_Page9_Battery` display folder.

---

## STEP C — Fix V3 Table (5 min)

**Problem:** Many rows blank. Cause: Building column uses `silver_building_master` which cross-joins with simulation rows.

**Fix:**
1. Click the **V3 Scenario Comparison Table** visual
2. In the **Columns** field well → find `building_name` from `silver_building_master`
3. Remove it (click X)
4. From the **Fields** panel, expand `gold_battery_simulation` → drag `building_name` into Columns (first position)
5. ✅ Result: exactly **13 rows**, all with data, no blank rows

---

## STEP D — Fix V1 and V2 Date Axis (10 min)

After Step A + B1 (dataset refreshed), change X-axis on both charts.

### D1. V1 — State of Charge Trend
1. Click V1 (SoC area/line chart)
2. X-axis field well → remove `gold_battery_dispatch[date]`
3. Add `gold_battery_dispatch[month_year_en]`
4. Format → X-axis → **Type: Categorical**
5. Chart title: rename to **"Monthly SoC Trend"**

### D2. V2 — Daily Charge/Discharge
1. Click V2 (bar chart)
2. X-axis field well → remove `gold_battery_dispatch[date]`
3. Add `gold_battery_dispatch[month_year_en]`
4. Format → X-axis → **Type: Categorical**
5. Chart title: rename to **"Monthly Charge / Discharge"**

✅ Both charts now show 42 monthly points (Jan 2023 – Apr 2026), clearly readable, in English.

---

## STEP E — Fix V5 Scatter Labels (5 min)

**Problem:** Bubble labels show `B001_SEL_200kWh` — hard to read.

**Fix (Direct Lake — calculated column not possible in Power BI):**

Option 1 — Quick fix via Notebook (recommended):
- In Fabric, add 1 cell to notebook 12b and run:
  ```python
  from pyspark.sql import functions as F
  df = spark.table("gold_battery_simulation")
  df2 = df.withColumn("scatter_label",
      F.concat(F.col("building_id"), F.lit(" · "), F.col("strategy_label")))
  df2.write.format("delta").mode("overwrite").option("overwriteSchema","true").saveAsTable("gold_battery_simulation")
  ```
- Then Power BI Refresh → in V5 Details field: replace `scenario_id` with `scatter_label`

Option 2 — Skip for now (acceptable):
- Leave `scenario_id` but enable **Data labels: OFF**
- Use Tooltip to show `strategy_label` and `building_name` instead
- Bubbles still communicate via size + color, labels not essential

---

## STEP F — Layout: Move V1 to Left Panel (10 min)

**Current (wrong):** V4 Gauge top-right | V1 SoC Trend bottom-right (too small)
**Target:** V4 Gauge fills full right-top | V1 moves to left middle | right middle = cards

### F1. Delete V1 from right panel
- Click V1 SoC Trend visual (bottom-right area) → **Delete**

### F2. Delete old left-panel cards
- Click the **"Active Strategy"** text card on the left panel → **Delete**
- Click the **"EU 2023/1670"** text card on the left panel → **Delete**

### F3. Add V1 back in left middle zone
- Insert → Line chart (or Area chart)
- Position: **left side, between V2 and V3** (middle row, left column)
- Approximate pixel position: X:10, Y:375, W:755, H:155
- Bind same as before:
  - X-axis: `month_year_en`
  - Y-axis: `[V1 SoC End Percent]` (series 1), `[V1 SoC Start Percent]` (series 2)
  - Legend: `gold_battery_dispatch[strategy]`
  - Reference line: constant 10% (Min SoC)

### F4. Resize V4 Gauge (right top)
- Click V4 ROI Gauge → expand to fill the full right-top zone
- Approximate: X:780, Y:155, W:490, H:215

### F5. Add 2 new cards in right middle zone
**Card 1 — Active Strategy:**
- Insert → Card (new) → Value: `[Active Strategy Short Label]`
- Subtitle: `[Page9 Data As Of]`
- Position: X:780, Y:378, W:490, H:75
- Style: dark background + electric blue border

**Card 2 — Battery Status:**
- Insert → Card (new) → Value: `[Active Battery Label]`
- Subtitle: `[EU Compliance Portfolio Label]`
- Position: X:780, Y:460, W:490, H:75
- Style: dark background + gold/amber border for non-compliant, teal for compliant

---

## STEP G — Fix C4 Card (2 min)

- Click C4 "Efficiency + EU" card
- Value field: if showing blank, remove old measure → add `[C4 Round Trip Efficiency Pct]` (v48 version)
- Reference label: `[C4 Label Efficiency]` (v48 version)
- ✅ Should show ~94.5% LFP (Berlin) or ~90.5% NMC (Frankfurt)

---

## STEP H — Final Validation (15 min)

Work through this checklist after all steps above:

### Data correctness
- [ ] V3 table: 13 rows visible (All buildings, All strategies)
- [ ] V3: B005 rows show red "NON-COMPLIANT" in EU Status column
- [ ] V3: sorting by Score shows Hamburg Peak-Shaving first (score=100)
- [ ] C4: shows numeric % value — not blank or "--"
- [ ] C1 + C2 single building + active strategy: Hamburg=~€66k, Berlin=~€599, Frankfurt=~€3k

### Visual quality
- [ ] V1 X-axis: English month names (Jan, Feb, Mar…), 42 monthly points
- [ ] V2 X-axis: same (Jan–Apr 2026), seasonal pattern visible
- [ ] V5 scatter: bubble labels readable (either scatter_label or tooltips)
- [ ] V4 gauge: fills right-top zone cleanly, not cramped
- [ ] Active Strategy card: shows "● Active | Peak-Shaving" format (short, no building name)
- [ ] Battery card: shows "LFP · 800 kWh · EU ✓" or "NMC · 400 kWh · NON-EU ✗"

### Interactions
- [ ] S1 Building slicer → changes all visuals including V3 table row count
- [ ] S2 Strategy slicer → filters V1/V2 to selected strategy only
- [ ] Clicking V3 table row → cross-filters V4 gauge and V1 SoC for that scenario

---

## QUICK REFERENCE: Files

| File | Purpose |
|---|---|
| `notebooks/simulation/12b_patch_month_year_column.py` | ⚠️ Run in Fabric FIRST |
| `semantic-model/59_dax_v48_page9_fixes.dax` | Import 4 measures in Power BI |
| `semantic-model/58_dax_v47_page9_battery.dax` | Original 32 measures (already imported) |
| `report-design/page9-battery-binding-guide.md` | Original full binding reference |
| `report-design/backgrounds/09_battery_strategy.png` | Background (unchanged — keep as is) |

---

## EXPECTED FINAL STATE

```
┌─────────────────────────────────────────────────────────────┐
│  ENERGY LENS   Battery Dispatch & Financial Simulation      │
├──────────┬──────────┬──────────┬───────────────────────────┤
│ C1 Sav.  │ C2 Pay.  │ C3 CO₂   │ C4 Efficiency             │
├──────────┴──────────┴──────────┴───┬───────────────────────┤
│  V2: Monthly Charge / Discharge    │  V4: ROI Gauge         │
│  (bar chart, Jan 2023–Apr 2026)    │  (large, breathing rm) │
├────────────────────────────────────┤                        │
│  V1: SoC Monthly Trend             ├───────────────────────┤
│  (line chart, 3 strategy series)   │  ● Active | Strategy   │
│                                    │  LFP · 800kWh · EU ✓  │
├────────────────────────────────────┼───────────────────────┤
│  V3: Scenario Comparison (13 rows) │  V5: Cost vs Payback   │
│  EU compliance, score data bar     │  (scatter bubbles)     │
└────────────────────────────────────┴───────────────────────┘
  S1: Building ▾   S2: Strategy ▾   S3: Date range ──●──
```
