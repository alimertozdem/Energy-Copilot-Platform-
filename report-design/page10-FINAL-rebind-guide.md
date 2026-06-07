# Page 10 (10_Solar) — FINAL rebind guide

Pairs with `semantic-model/scripts/page10_final_install.cs`.

## 0. Order of operations
1. **TE2:** File → Open `EnergyCopilotModel` (live) → C# Script tab → paste `page10_final_install.cs` → **F5** → **Ctrl+S**.
2. **Power BI Desktop:** Home → **Refresh**.
3. Do the visual rebinds below (clears the two `Missing_References`).
4. **Do NOT** re-run the "PAGE 10 + GATE-D FIXES" block in `final_master_install.cs` — its `DelAll("Avg Solar Specific Yield kWh kWp")` is what orphaned the bar. `page10_final_install.cs` replaces it (pure upsert).

> Why two red errors today: a prior `DelAll` deleted-and-recreated `Avg Solar Specific Yield kWh kWp`, and the `Feed-in Tariff EUR kWh` measure was created on `gold_recommendations` while a visual still pointed at `gold_country_regulations`. Both are dangling **visual** references — the model itself is fine. Deletes can't fix this on a live DirectLake model; re-binding the field in the visual does.

## 1. Fix the two broken visuals (Missing_References)

**Specific yield bar (Row 3, right):**
- Select the bar → in the field well remove the ⚠ `Avg Solar Specific Yield kWh kWp` → from `gold_kpi_daily` drag the (now updated) `Avg Solar Specific Yield kWh kWp` back in.
- Axis = `silver_building_master[building_id]`. Title: `Specific yield by building (kWh/kWp·yr)`.

**Install-solar table (Row 5) — Feed-in Tariff:**
- Select the table → remove the ⚠ `Feed-in Tariff EUR kWh` field → from **gold_recommendations** drag `Feed-in Tariff EUR kWh` back in (it must come from gold_recommendations, not gold_country_regulations).

If a tile still shows "Fix this", delete that tile and rebuild it per the layout below — faster than fighting the orphan.

## 2. Visual-by-visual binding

**Row 1 — KPI cards**
| Card | Measure |
|---|---|
| Total Generation | `Total Solar Generated kWh` |
| Installed Capacity | `Solar Capacity kWp` |
| Self-Consumption % | `Solar Self-Consumption Rate Pct` *(new — kWh-weighted, matches the donut ~37–40%)* |
| Avg Performance Ratio | `Avg Solar PR Pct` |
| CO₂ Avoided (t) | `Total CO2 Savings from Solar tCO2` |
| Renewable Rate % | `Solar Coverage Pct` *(set card format to `0.0%`)* |

**Row 2 — generation profile**
- Stacked area `Solar generation — self-consumed vs exported`: values `Solar Self Consumed kWh` + `Total Solar Exported kWh`; axis `Date[Year Month]` (chronological, readable).
- Donut `Self-consumption split`: `Solar Self Consumed kWh` vs `Total Solar Exported kWh`.

**Row 3 — per-building benchmarks**
- Bar `Performance ratio by building`: `Avg Solar PR Pct` by `building_id`; constant ref line at 75% (PR > 100 on a few buildings is synthetic-solar noise — known, cosmetic).
- Bar `Specific yield by building`: `Avg Solar Specific Yield kWh kWp` by `building_id`.

**Row 4 — live PV + faults**
- Line `Today's PV power (kW)`: `Realtime PV Power kW` (axis = hour/timestamp). **Remove** the `Total Solar Exported kWh` series and the raw `reading_value_avg` — those made the old chart unreadable. Optional `Peak PV Power kW` card in the corner.
- Table `PV underperformance — est. € loss`: visual-level filter `gold_iot_fdd[fault_code] = "PV_UNDERPERFORMANCE"`; columns `building_id`, `equipment`, `severity`, `occurrence_count`, `PV Loss EUR`. (DoD: B007 appears.)

**Row 5 — opportunities**
- Table `Install-solar opportunities`: visual-level filter `gold_recommendations[action_type] = "INSTALL_SOLAR"`; columns `building_name`, `country_code`, `Sum of capex_eur`, `Sum of payback_years`, `Sum of npv_eur`, `Sum of co2_saving_kg`, `Feed-in Tariff EUR kWh`.

## 3. Energy-logic assumption to confirm (Mert)
`Avg Solar Specific Yield kWh kWp` is **annualized** (`period yield × 365 / days-in-context`) so it reads as a recognizable ~900–1400 kWh/kWp·yr regardless of the date filter. To use **daily** yield (~2–4) instead, remove `* 365.0` and `/ _days` in the measure. Self-contained — computed from `solar_generated_kwh` and `pv_capacity_kwp`, so it does **not** require the `solar_specific_yield_kwh_kwp` column / the 03 re-run.
