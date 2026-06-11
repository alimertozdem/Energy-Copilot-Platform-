# EnergyLens — Report: Remaining Visual Fixes (2026-06-11)

_Page 1's **substance is verified correct** (data + measures). Below are the remaining
**cosmetic/polish** tweaks across pages. **None block a pilot.** Do them at your own pace._

## Root-cause note (applies to every total-card)
The Page-1 KPI cards had been bound to **per-building AVERAGE** measures (they returned
`total ÷ building-count`), not the **SUM** measures the building chart uses. **Fix pattern:**
bind the card's **Value** to the **SUM** measure (the same one the chart uses); verify by
grouping that measure by building in a table and reading the **Total**. Prefer a plain **Card**
visual over the **KPI** visual (the KPI trend-axis chokes on `'Date'[Month]` = int collapses
years, and `'Date'[YearMonth]` = string → blank; use `'Date'[Date]` only if you keep a KPI
trend). Ground truth (raw meter aggregation): **Data Center ≈ 15M kWh/yr, portfolio ≈ 32M/yr.**

## Page 1 — Portfolio (leftover)
- [ ] **Net Carbon** card → convert to **Card** + bind Value to **`Net Carbon Footprint tCO2`** (SUM).
  It still shows ~3,740 (average); should be ~**7–10K tCO₂**. Verify vs the building-grouped table sum.
- [ ] **Last Week / Last Month / Last 7 Days Cost / Last 30 Days CO2** cards → bind each to its **SUM**
  measure (they are likely still on average measures). _(Total Energy ✅ and Cost ✅ are done.)_
- [ ] **Avg EUI** → **leave as area-weighted AVERAGE** (correct — EUI is an intensity, never summed).
  Its high/red look is from (a) **daily** display and (b) the **data center** dominating — handle below, do NOT sum it.
- [ ] **EUI presentation:** show **annual** (×365 or an annual measure) instead of per-day; and/or
  exclude `Data_Center` via the **Building Type slicer** for a comparable portfolio EUI.

## Page 2 — Building Deep-Dive
- [ ] **Time-grain field parameter:** Modeling → New parameter → Fields → name "Time Grain" →
  add `'Date'[Date]`, `'Date'[YearMonth]` (Sort by `'Date'[MonthIndex]`), and a Year field → "Add
  slicer to page" → put the parameter on the monthly trend's X-axis.
- [ ] **Page 1 → Page 2 drill-through:** on Page 2, drag `silver_building_master[building_name]`
  into the **Drill through** well. Then right-click a building on Page 1 → Drill through → Page 2.

## Page 5 — Occupancy
- [ ] Bind the **"Occupied Hrs/Day"** card to **`Occupied Hours Per Day Calc`** (building-normalized).
  Should read **~8–11**, not 69.

## Page 6 — Sustainability
- [ ] **GHG intensity skew:** exclude `Data_Center` via the Building Type slicer for the portfolio
  intensity average (or area-weight). The DC genuinely dominates (real ~15M kWh/yr).
- [ ] Sanity-check **market-based GHG > location-based** (usually market ≤ location with green procurement).

## Page 7 — HVAC (deferred for a meter-only pilot)
- [ ] **"HVAC CO₂ tCO₂/yr"** card shows ~18,115 (> whole-portfolio carbon) → annualize/aggregate fix.
  Page 7 is **module-gated OFF** for meter-only pilots → defer until IoT/sub-metering is in scope.

---
**Pilot-readiness:** the report's numbers are correct after the Page-1 card rebinds. Everything
here is presentation polish — safe to ship a meter-only pilot demo before finishing it.
