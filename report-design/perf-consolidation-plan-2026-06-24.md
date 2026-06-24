# Report Perf — Visual Consolidation Plan (T2)
**Date:** 2026-06-24  **Basis:** Performance Analyzer (F4 trial) + report.json inventory
**Goal:** cut query round-trips per page by merging single-value cards into multi-row cards / matrices
and trimming slicers. **No measure logic or data changes** — same numbers, fewer visual containers.

## Why this works
Each visual = 1 query round-trip (~500 ms here; DAX itself is only ~214 ms median, the rest is queue +
round-trip). A page with 18 visuals pays ~18 round-trips. A **multi-row card** or **matrix** shows many
measures in **one** query. Merging 6 cards → 1 visual removes ~5 round-trips (~2.5 s) per cluster.

## Trade-off (decide per page)
- **Win:** fewer queries → faster page; less re-query storm on interaction.
- **Cost:** a multi-row card looks different from individual hero cards — you lose per-card big-number
  styling, conditional color, and per-card sparkline. KPI visuals (trend + goal) cannot fully collapse
  without losing the trend, so only *reduce their count*, don't merge all.
- Recommendation: merge the plain single-number cards (biggest win, least visual loss); keep 2-3 hero
  KPIs per page.

## Expected impact (rough)
| Page | Now | Target | Queries removed |
|---|---|---|---|
| 01 Portfolio | 22 | ~12 | ~10 |
| 02 Building Detail | 20 | ~12 | ~8 |
| 06 Sustainability | 22 | ~12 | ~10 |
| 07 HVAC | 20 | ~10 | ~10 |

Pair with **T1 settings** (slicer Apply buttons + cross-filter default off + Edit Interactions) for the
interaction-time win. Re-run Performance Analyzer after each page to confirm.

---

## 01 — Portfolio Overview (22 → ~12)
**Cards (6) → 1 multi-row card "Portfolio Headlines":** Last Week kWh, Last Month kWh, Consumption MoM %,
Consumption WoW %, Last 30 Days CO₂, **Last 7 Days Cost** (this card alone was the slowest visual, 2.4 s).
→ 6 queries become 1.
**KPIs (5):** keep 3 hero KPIs (Total Energy Cost, Avg EUI, Active Anomalies); fold Total Consumption +
Net Carbon into the multi-row card. → −2.
**Slicers (6 → 3):** keep building_name, Date, building_type. Drop city, country_code, Time Grain
(city/country redundant with building filter; Time Grain rarely changed → move to filter pane). → −3.
**Keep as-is:** Building-Based Consumption, EUI Benchmark, Portfolio Summary table, Consumption Trend,
map (1). *Net ~10 fewer round-trips; the 2.4 s cost card disappears into a shared query.*

## 02 — Building Detail (20 → ~12)
**Cards (4) → 1 multi-row card "Live Status":** Battery SoC, Base Load Ratio, Live Building Power,
Live HVAC Load. → 4 queries become 1.
**KPIs (5):** keep EUI + Peak Demand as KPI; fold Daily Consumption, Carbon Intensity, Solar Generation
into a second multi-row card (or the Live Status one). → −3.
**Redundancy:** **EUI Gauge** duplicates the EUI KPI — drop the gauge. → −1.
**Slicers (4 → 2):** YearMonth + Date + Time Grain all filter time → keep ONE time slicer + building_name. → −2.
**Keep:** load profile, SoC trend, CDD/HDD scatter (2), temp-vs-consumption, solar combo.

## 06 — Sustainability & Compliance (22 → ~12) — most cards, biggest win
**GHG cards (4) → 1 matrix "GHG Summary":** Scope 1/2/3, Total GHG location, Total GHG market
(rows = scope, values = tCO₂e). → 4 → 1.
**Compliance cards (5) → 1 multi-row card "Compliance Scorecard":** CRREM Stranding Yr, EU Carbon Score,
GHG Intensity, EPC Portfolio Grade, ESRS E1 coverage %. → 5 → 1.
**Captions:** keep Priority Actions & Incentives (1); fold Scope 3 caption into the GHG matrix. → −1.
**Slicers (5 → 3):** keep building_name, Date, scope. Drop building_type, data_grade. → −2.
**Keep:** CO₂ trend, Carbon Intensity vs CRREM, Scope 2 Location vs Market, Emissions by building,
CRREM table, map, CO₂ Levy KPI. *10 cards → ~3 containers.*

## 07 — HVAC (20 → ~10) — 10 cards, biggest card-merge
**Performance cards → 1 multi-row card "HVAC Performance":** Avg COP, HVAC Efficiency, HVAC Share %,
Ventilation Energy Share %. → 4 → 1.
**Envelope/retrofit cards → 1 multi-row card "Envelope & Retrofit":** Buildings For Retrofit,
EPC Compliance, Gas Exposure %, Heat Loss Annual, Insulation Score, HVAC CO₂. → 6 → 1.
**Slicers (5 → 3):** keep building_name, Date, system_type. Drop YearMonth (dup of Date),
renovation_priority (move to filter pane). → −2.
**Keep:** Heat Loss Density, Scope-1 CO₂ bar, End-Use Breakdown, COP/SCOP table, Renovation Priority Matrix.
*10 cards → 2 containers.*

---

## How to build a multi-row card (one query for N measures)
1. Insert **Multi-row card** (or **Matrix** for grouped values).
2. Drag the measures into **Fields** (multi-row card) / **Values** (matrix).
3. Format → Category labels on, adjust text size; for matrix, turn off row subtotals.
4. Delete the individual cards it replaces.
5. **Edit Interactions** (Format ribbon): set slicers to filter only the visuals that need it.

## Order of work
Do **07 HVAC** and **06 Sustainability** first (10 cards each = biggest win), then 01 Portfolio
(kills the 2.4 s cost card), then 02. Re-measure with Performance Analyzer after each to confirm the drop.

---

## T0 — FREE DELETES (do first; no rebuild, no analytical loss)
Scan result: **45 slicers / 10 pages (avg 4.5)**, no duplicate data visuals. The deletable fat is slicers.

**Redundant TIME slicers (4 pages carry overlapping ones — keep `Date`, delete the rest):**
| Page | Has | Delete | Keep |
|---|---|---|---|
| 02 Building Detail | YearMonth + Date + Time Grain | YearMonth, Time Grain | Date |
| 01 Portfolio | Time Grain + Date (6 slicers total) | Time Grain + city + country_code* | Date, building_name, building_type |
| 07 HVAC | YearMonth + Date | YearMonth | Date |
| 04 Forecast | Time Grain + Date | Time Grain | Date |

*city/country_code on Portfolio are redundant with the map + building_name filter.
Each deleted slicer removes one query + cross-filter overhead. **Zero analytical content lost.**

**No duplicate data visuals exist** — don't delete analysis visuals; consolidate them (T2) instead.

**Optional judgment cuts (render-heavy, you decide):**
- `02` **EUI Gauge** overlaps the EUI KPI (both = EUI vs target) → safe to drop one.
- `06` **azureMap "Building-Type Distribution (kWh)"** is off-theme on a compliance page and rendered ~0.8 s
  → drop here, keep the same map on Portfolio.

## Model cleanup (measures / columns) — NOT a speed lever, and risky
- Unused **measures** cost **0 ms** at query time — they only execute when a visual uses them. Trimming
  308 → fewer = tidiness, **no speed gain**.
- **Columns** at 13 k rows: DirectLake pages columns on demand; unused ones never load. Pruning matters at
  tens of millions of rows, not here. **~0 speed.**
- **Risk of scripted "unused" deletion:** a model-only scan cannot see report-level measures (absent from
  the model dump), measure chains, conditional-formatting/data-color refs, tooltips/bookmarks, or the
  embedded app's filter/RLS config → false positives that silently break visuals.
- **Verdict: skip for speed.** If ever wanted for maintainability, do it as a separate careful task with
  dependency tracing (INFO.CALCDEPENDENCY / Tabular Editor) + report-level check + a model backup.

## Net "minimal-fiddling" path (ranked by effort : gain)
1. **T0 delete redundant slicers** (~5 min, pure win, no content loss).
2. **T1 query-reduction settings** (~10 min, reversible).
3. **T2 card consolidation** (more work, biggest structural win) — optional / later.
4. *Not:* model measure/column cleanup (0 speed, real risk).
5. *Last resort:* F4→F8 capacity (money) only if a residual queue remains after 1-3.

---

## Battery page (09) — two building slicers → fix with ONE relationship
**Root (verified in relationships.tmdl):** `gold_battery_simulation` and `gold_battery_daily_summary`
have a `building_id` column but **no relationship** to `silver_building_master`. So a slicer on
`silver_building_master[building_name]` can't filter visuals built on those tables (e.g. Scenario
Comparison reads from `gold_battery_simulation`) — hence the 2nd slicer bound to the battery table's own
`building_name`. Two slicers = band-aid for a missing relationship.

**Fix (Model view, ~2 min — the proper star-schema solution):**
1. New relationship `gold_battery_simulation[building_id]` → `silver_building_master[building_id]`
   (many-to-one, **single** cross-filter direction).
2. Same for `gold_battery_daily_summary[building_id]` → `silver_building_master[building_id]`.
3. Repoint the page's building slicer to `silver_building_master[building_name]`; **delete** the
   battery-table slicer. One slicer now filters every battery visual through the relationships.

**Pre-checks:** `silver_building_master[building_id]` is unique (it's the dimension, 1 row/building) ✓;
keep direction SINGLE (not both) to avoid ambiguity/overhead; building_id values match (B001…) ✓.

**Note:** `gold_strategy_fitness` (Strategy Fitness Matrix) has **no building_id** — it's *building_type*
grain (data_center / education / healthcare). It won't follow a single-building slicer by design; leave it.
If you ever want it building-filtered, that's a building_type-level relationship, a separate decision.

**Report-only fallback (worse):** "Sync slicers" can move two slicers together since the building_name
strings match — but it still leaves two slicers and is cosmetic. Prefer the relationship.
