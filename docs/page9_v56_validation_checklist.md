# Page 9 v56 — Validation Checklist

Use this checklist after running the install script and binding visuals.

## A. Data layer

- [ ] `gold_country_regulations` Delta table exists, 12 rows
- [ ] `gold_strategy_fitness` Delta table exists, 49 rows
- [ ] `gold_battery_technologies` Delta table — 15 rows (was 10, +5 new)
  - CATL_NAXTRA_100, QUANTUMSCAPE_SS_150, BYD_HVS_V2G_120,
    CONNECTED_2L_NMC_250, SKELETON_SKELGRID_80
- [ ] `gold_battery_dispatch` schema unchanged — columns charge_kwh, discharge_kwh,
      pv_generation_kwh, grid_charge_kwh, pv_charge_kwh, net_savings_eur present

## B. Relationships

- [ ] `gold_battery_dispatch[building_id]` ↔ `silver_building_master[building_id]` active
- [ ] `gold_battery_dispatch[battery_id]` ↔ `gold_battery_technologies[battery_id]` active
- [ ] `gold_battery_simulation[building_id]` ↔ `silver_building_master[building_id]` active
- [ ] `gold_country_regulations[country_code]` ↔ `silver_building_master[country_code]` active
- [ ] `gold_strategy_fitness` standalone (no relationship — intended)

## C. DAX install (TE2 Output should show)

- [ ] [UPDATE] gold_battery_dispatch.V2 Charge kWh Daily (or [MOVE] if rehoming)
- [ ] [UPDATE] gold_battery_dispatch.V2 Discharge kWh Daily
- [ ] [UPDATE] gold_battery_dispatch.V2 PV Generation kWh
- [ ] [UPDATE] gold_battery_dispatch.V2 Grid Charge kWh Daily
- [ ] [UPDATE] gold_battery_dispatch.V2 PV Charge kWh Daily
- [ ] [UPDATE] gold_battery_dispatch.V2 Net Savings EUR Daily
- [ ] [CREATE] for 20 new measures (C1..C5, V1, V3..V5, V7, I1..I4, helpers)
- [ ] No SKIP warnings (all tables found)

## D. Spot-check measure values (Frankfurt B005)

- [ ] [C1 Annual Savings EUR] ≈ €36 990 (LFP simulation fallback, NMC is non-compliant)
- [ ] [C2 Payback Years] ≈ 1.5 (Excellent)
- [ ] [C3 CO2 Avoided Tonnes Annual] ≈ 60.9 t
- [ ] [C4 Round Trip Efficiency Pct] ≈ 90.0%
- [ ] [C5 EU Compliance Status Text] = "❌ NMC banned for new installs in DE"
- [ ] [I2 Chemistry Recommendation Text] starts with "Recommended: LFP..."
- [ ] [I3 Compliance Flag Text] starts with "⚠ Active battery is NMC..."

## E. Spot-check measure values (Hamburg B003)

- [ ] [C1 Annual Savings EUR] ≈ €100 000
- [ ] [C2 Payback Years] ≈ 1.7-2.0
- [ ] [C5] = "✓ EU 2023/1542 compliant"
- [ ] [I1] mentions "logistics" + "Peak-Shaving"
- [ ] [I3] = "✓ Active battery fully EU 2023/1542 compliant..."

## F. Visual layer

- [ ] V1 matrix renders 7 rows × 7 cols, colored cells, no errors
- [ ] V2 24h chart still works (unchanged)
- [ ] V3 scatter shows colored bubbles by chemistry
- [ ] V4 dual-axis renders (bars + line)
- [ ] V5 heatmap row DE × col NMC = red ✗
- [ ] V5 heatmap row NO × col LFP = green ✓
- [ ] V5 heatmap row TR × col NMC = amber ⚠ (legal in TR but cautioned)
- [ ] V6 scenario table — no empty rows, score-sorted DESC
- [ ] V7 SoH / Cycles Used / Years to Replace cards populated
- [ ] I1–I4 text cards visible with prescriptive sentences

## G. Edge-case tests

- [ ] Set S1 = Hamburg, S2 = peak_shaving → V4 column-chart highlights peak_shaving
- [ ] Set S1 = Vienna (no battery) → C1 falls back to simulation, C5 says
      "ℹ Outside EU framework" or "—"
- [ ] Set S4 = TR → V5 country row visible, NMC=amber, Sodium-Ion=amber
- [ ] Set S3 = LFP only → V5 still global (S3 should not filter V5)
- [ ] All slicers cleared → all KPIs show portfolio aggregates, no errors

## H. Smoke test — no regressions

- [ ] Pages 1–8 still load (open each page, check for new errors)
- [ ] No yellow warning triangles in any visual field-well

## I. Performance

- [ ] Each Page 9 visual renders in < 4 seconds
- [ ] No DAX query timeout warnings in Performance Analyzer

## J. Energy-logic sanity check (RANGES, not absolutes)

- [ ] C1 across portfolio: €60-200k total (5 buildings with batteries)
- [ ] C2 payback: any active strategy 1-5 yr, NMC backup outlier acceptable
- [ ] C3 CO2 avoided: 60-200 tCO₂ total portfolio
- [ ] V5 DE column: LFP green, NMC red, Sodium green, Solid-State green
      (DE is most permissive on new tech), NCA amber
- [ ] V5 TR column: all chemistries amber or green (no red — TR relaxed)
- [ ] V5 NO column: LFP green, Sodium green, all others green or amber

If any check fails, re-run the TE2 script with the Output panel visible and
report the SKIP/error lines for diagnosis.
