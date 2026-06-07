# EnergyLens — Final 10-Page Dashboard: Gate D Execution Plan

**Date:** 2026-06-03 · **Owner:** Mert (product owner / energy reviewer) · **Mode:** manual paste,
one page at a time. After each page: refresh → eyeball → send me any error verbatim.

> Companion docs: `report_production_ready_plan.md` (gate model), `gate-d-visual-binding-checklist.md`
> (original per-page binding), `EnergyLens_Finalization_Plan_and_Working_Reference.md` (per-page DoD).
> This plan supersedes them where they differ — it is grounded in the **live model probe**
> (`semantic-model/_probe_output.txt`, 213 measures) so every name below is verified against the
> real schema.

---

## 0. Where we are (verified 2026-06-03)

The **model layer is production-ready** — confirmed against the live probe:

- **Gate A (notebooks):** core engines ran + verified.
- **Gate B (tables + relationships):** 26 tables, all key relationships live, including the toggle
  enabler `gold_kpi_hourly[date] → 'Date'[Date]` and the three IoT tables related to
  `silver_building_master` + `'Date'`.
- **Gate C (DAX):** 213 measures live (v57–v60 consolidation applied).
- **Page 6** is bound and done.

**What remains = Gate D (visual binding) only**, page by page:

| Status | Pages |
|---|---|
| Done | 6 |
| Ready to bind (measures verified present) | 8, 9 |
| In progress — 2 errors | 10 (Solar, new) |
| To bind (visual work + time-grain toggle) | 1, 2, 3, 4, 5, 7 |

The building dimension in the model is **`silver_building_master`** (there is **no** `dim_building`
and **no** `dim_date` — the date table is named `'Date'`). Use those names everywhere.

---

## 1. Immediate fixes — do these before page work

### Fix 1 — `gold_kpi_daily` was missing `solar_specific_yield_kwh_kwp`  ✅ code done

- **Symptom (your screenshot):** `'gold_kpi_daily'[Avg Solar Specific Yield kWh kWp]` →
  "Column `solar_specific_yield_kwh_kwp` cannot be found."
- **Root cause (verified):** the column was only computed in `03_gold_kpi_engine.py` **BÖLÜM 7
  (monthly / `gold_kpi_monthly`)**. `gold_kpi_daily` (41 cols) never had it, but the measure points
  at `gold_kpi_daily`.
- **Applied:** I added the daily-level column to **BÖLÜM 6** (line ~625), mirroring the monthly
  logic — guarded for PV-less buildings (NULL, no divide-by-zero). `py_compile` passes.

  ```python
  .withColumn("solar_specific_yield_kwh_kwp",
      spark_round(
          when((col("has_pv") == True) & (col("pv_capacity_kwp") > 0),
               col("solar_generated_kwh") / col("pv_capacity_kwp"))
          .otherwise(lit(None)), 4)
  )
  ```

- **Your action:** re-run `notebooks/gold/03_gold_kpi_engine.py` in Fabric → let DirectLake refresh.
  `gold_kpi_daily` now exposes `solar_specific_yield_kwh_kwp` and the measure resolves.

- **⚠ Energy-logic note (needs your call):** daily specific yield = daily generation ÷ capacity
  (kWh/kWp **per day**, ≈ 2–4). The Page-10 measure `AVERAGEX`-es daily rows → it returns a **daily**
  figure, not the familiar annual benchmark (Berlin ~900, İstanbul ~1400 kWh/kWp/yr). Pick the framing:
  - **(A)** keep "avg daily specific yield" — fine for the *relative* north-vs-south bar; measure works as-is.
  - **(B)** annualized — I'll give you `Annual Solar Specific Yield kWh kWp = DIVIDE([Total Solar Generated kWh], SUM(silver_building_master[pv_capacity_kwp])) ÷ years-in-context`.

  Tell me A or B and I'll finalize the measure.

### Fix 2 — Page 10 measures reference `dim_building` (which doesn't exist)

The build guide (`semantic-model/15_page10_solar_design.md`) assumed a `dim_building`. The model uses
`silver_building_master`. Corrected, paste-ready versions are in **§4**. The visible card errors will
clear once you swap:

- `SUM(dim_building[pv_capacity_kwp])` → `SUM(silver_building_master[pv_capacity_kwp])`
- per-building bar axis `dim_building[building_id]` → `silver_building_master[building_id]`
- date axis `dim_date` → `'Date'[Date]`

### Fix 3 — `Avg HDD Normalized EUI` points at a renamed column

The KPI engine renamed `hdd_normalized_eui` → **`climate_adjusted_eui`** (the ratio method, HDD+CDD).
The measure `gold_kpi_daily[Avg HDD Normalized EUI]` still exists in the model and most likely
references the **old** name → blank/error wherever it's used (pages 1/2/7). Redefine:

```dax
Avg Climate-Adjusted EUI =
AVERAGE ( gold_kpi_daily[climate_adjusted_eui] )
```

Rebind any visual using the old measure to this one. (Keep the old name as an alias if a visual is
hard-wired to it.)

---

## 2. Prerequisite — `Time Grain` field parameter (Hourly / Daily / Monthly toggle)

This is the "time-intelligence" toggle for pages 1/2/3/4/7. All the `TS …` measures already exist
(verified) — you only need the parameter + binding.

**Create once:** Power BI Desktop → Modeling → New parameter → **Fields**. Name `Time Grain`, uncheck
"Add slicer to this page", add in order:

1. `gold_kpi_hourly[hour_utc]` → rename row **"Hourly"**
2. `'Date'[Date]` → **"Daily"**
3. `'Date'[YearMonth]` → **"Monthly"**  (not `'Date'[Month]` — that merges all years' Januaries)

**Toggle pattern (reuse everywhere):** line/area visual → X-axis = `Time Grain` → Values = a `TS …`
measure → add a **Tile slicer** bound to `Time Grain` (single-select, default Daily).

**After creating it:** re-run `semantic-model/scripts/consolidate_measures_v57_v60.cs` once so the
`Selected Grain Label` measure stops being skipped.

**Verified TS / profile measures (home: `gold_kpi_hourly`):**
`TS Consumption kWh`, `TS Avg Demand kW`, `TS Net Grid kWh`, `TS Solar Generated kWh`,
`TS Solar Self-Consumed kWh`, `TS Avg Temperature C`, `TS CO2 kg`, `TS Peak Demand kW`,
`TS Battery SoC Pct`, `Profile Avg Demand by Hour kW`, `Profile Avg Consumption by Hour kWh`,
`Profile Avg Solar by Hour kWh`, `Base Load Ratio Pct`.

---

## 3. Page-by-page Gate D checklist (all 10)

Legend: **ADD** = new visual/field · **REBIND** = repoint existing visual · **VERIFY** = check it
renders · **DEL** = remove. Measure names are verified against the live model.

### Page 1 — Portfolio Overview · *to bind*
- **ADD:** Time-Grain toggle on the consumption trend → Values `[TS Consumption kWh]`.
- **VERIFY:** cards `[Total Consumption kWh]`, `[Avg EUI kWh m2]`, `[Total CO2 Emissions tCO2]`,
  `[Total Energy Cost EUR]`, `[Peak Demand kW]`, `[Buildings Count]`, `[Solar Coverage Pct]`.
- **DoD:** EUI compared **annualized** vs benchmark; CO₂/cost from the ref layer; toggle switches grain.

### Page 2 — Building Deep-Dive ⭐ · *to bind*
- **ADD:** Time-Grain toggle on demand/grid line → `[TS Avg Demand kW]`, `[TS Net Grid kWh]`
  (+ `[TS Solar Generated kWh]` for solar buildings).
- **ADD:** 24-hour load profile → X = `gold_kpi_hourly[hour]` (0–23), Y =
  `[Profile Avg Demand by Hour kW]`; card `[Base Load Ratio Pct]`.
- **VERIFY:** climate-adjusted EUI uses `gold_kpi_daily[climate_adjusted_eui]` (see Fix 3).
- **DoD:** building slicer drives every visual; 24h profile shows a sane day shape.

### Page 3 — Anomaly Detection · *to bind*
- **ADD:** Time-Grain toggle on the consumption-vs-baseline context chart → `[TS Consumption kWh]`.
- **VERIFY/REBIND:** every visual reads **`gold_anomaly_log` only**. Cards use the `P3 …` set
  (`P3 Total Anomaly Count`, `P3 Critical Anomaly Count`, `P3 High Priority Open Count`,
  `P3 Resolution Rate Pct`, `P3 Top Risk Building Name`, `P3 Unresolved Count`, …).
- **DEL:** any visual still bound to `gold_anomaly_log_kpibuiltin_legacy` (single-engine rule).
- **DoD:** one taxonomy + one severity casing; counts reconcile with the table.

### Page 4 — Forecasting · *to bind* · ⚠ band needs columns/measures
- **ADD:** confidence band on the forecast chart. **`gold_consumption_forecast` has 0 measures**, so
  bind its **columns directly** in an area/line combo: `predicted_kwh` + shaded
  `lower_bound_kwh`…`upper_bound_kwh` (the building + `forecast_date → 'Date'` relationships exist).
  *(Optional: I'll add `Forecast Predicted / Lower / Upper kWh` SUM measures if you prefer measures.)*
- **ADD:** Time-Grain toggle on **actuals only** (`[TS Consumption kWh]`); forecast stays daily.
- **RELABEL:** accuracy → "in-sample fit" (`model_mape_pct` is in-sample).
- **DoD:** band brackets actuals; no negative lower bound shown as fact.

### Page 5 — Decision Support · *to bind* · ⚠ verify simulation table
- **RELABEL:** "CSRD score" card → `[EU Taxonomy Carbon Score]` (home `gold_compliance_results`).
  Keep "CSRD" wording only for a disclosure-completeness indicator.
- **VERIFY:** occupancy/decision measures render — `[Ghost Load Risk Pct]`, `[Ghost Load Risk Status]`,
  `[Building Avg Headcount Business Hours]`, `[Avg Business Hours Occupancy Pct]`,
  `[Energy per Occupant Goal kWh]`, `[Occupancy Top Insight]`; recommendation cards
  `[Total Annual Saving EUR]`, `[Total Capex EUR]`, `[Avg Payback Years]`,
  `[Critical Recommendations]`, `[High Priority Recommendations]`.
- **⚠ Reliability:** `gold_simulation_results` is **not in the model** (probe). If a Page-5 visual
  expects simulated hp_/bat_/ins_/deep_ scenarios it will be blank — decide: add the table, or keep
  Page 5 on recommendations + compliance only. Confirm with me.

### Page 6 — Sustainability / ESG ⭐ · **done** (verify on refresh)
- Cards/visuals already bound: `[EPC Score Area-Weighted kWh m2]` / `[EPC Class Area-Weighted]`,
  `[Carbon Intensity S1S2 kgCO2 m2 yr]` vs `[CRREM Pathway 2C kgCO2 m2 yr]`,
  `[CRREM Stranding Gap S1S2 …]` + `[CRREM Stranding Status]`, `[EU Taxonomy Carbon Score]`,
  `[CSRD Disclosure Readiness Pct]`, Scope `[Scope 1 tCO2]` / `[Scope 2 Location tCO2]` /
  `[Scope 3 Est tCO2]` (+ Share Pct), donut `[Selected Scope tCO2]`.
- **VERIFY only:** numbers re-populate after the latest refresh; "est." label on the Scope 3 slice.

### Page 7 — HVAC & Envelope · *to bind* · ⚠ verify display measures
- **ADD:** "modeled (HDD/CDD method)" label on the HVAC-share / heating-cooling split.
- **ADD:** Time-Grain toggle on consumption + temperature (`[TS Consumption kWh]`,
  `[TS Avg Temperature C]`). COP / split visuals stay monthly.
- **VERIFY:** `gold_hvac_analytics` has **0 measures** in the model — bind its **columns directly**
  (`hvac_share_pct`, `heating_share_pct`, `cooling_share_pct`, `cop_actual_avg`, `scop_rolling`,
  `heat_loss_kwh_m2`, `insulation_score`, `system_label`, `renovation_priority`, `renovation_reason`,
  `u_composite`). The old `System Type Display v39 / COP Display v39 / Scope Badge v40` measures are
  **not** in the current model — recreate them or bind columns. `system_label` / `renovation_reason`
  must read English.

### Page 8 — Real-Time IoT ⭐ (flagship) · **ready to bind**
- **ADD V5 "FDD Findings" table** → `gold_iot_fdd`; columns `equipment`, `fault_code`, `severity`,
  `[IoT FDD Priority Band]`, `[IoT FDD Row Confidence]`, `[IoT FDD Row Cost Label]`, `probable_cause`;
  **sort by `priority_score` DESC**; conditional format with `[IoT FDD Priority Color]`.
- **C2** (zone compliance) → `[IoT Zone Compliance Display]` + `[IoT Zone Compliance Color]`.
- **C4** (faults + €) → `[IoT C4 Label v59]` + `[IoT C4 Color v59]`.
- **Cards:** `[IoT FDD Diagnoses Today]`, `[IoT FDD Max Priority]`, `[IoT FDD Avg Confidence Pct]`,
  `[IoT FDD Energy Impact kWh Today]`.
- **DEL:** any visual on `iot_anomaly_alerts` / `iot_hot_readings` (removed from the model).
- **DoD:** B007 PV/HVAC faults surface at the top of V5.

### Page 9 — Battery Dispatch & ROI · **ready / verify**
- **VERIFY cards:** `[C1 Annual Savings EUR]`, `[C2 Payback Years]`, `[C3 CO2 Avoided Tonnes Annual]`,
  `[C4 Round Trip Efficiency Pct]`, `[C5 EU Compliance Status Text]`.
- **VERIFY insights:** `[I1 Strategy Recommendation Text]`, `[I2 Chemistry Recommendation Text]`,
  `[I3 Compliance Flag Text]`, `[I4 Next Action Text]`; recommender `[V1 Best Strategy For Building Type]`;
  heatmap `[V5 Country Chemistry Flag]` / `[V5 Country Chemistry Symbol]`; dual-axis
  `[V4 Monthly Net Savings EUR]` / `[V4 Monthly CO2 Avoided Kg]`.
- **⚠ V7 SoH strip:** `[V7 Current SoH Pct]` / `[V7 Cycles Used Pct]` / `[V7 Years Until Replacement]`
  depend on `battery_health_percent` / `cumulative_cycles` / `is_active_strategy`. These columns were
  **not** in `gold_battery_dispatch` at probe time — verify they exist after the notebook-12 re-run
  that re-added them; if blank, re-run 12 then refresh.
- **KEEP:** V2 24h chart on `gold_battery_hourly_dispatch` (charge/discharge/soc/grid_price_index).

### Page 10 — Solar (Full Showcase) · **in progress — 2 errors**
- **Prereq (done):** `gold_iot_realtime` + `gold_iot_fdd` are in the model and related (verified).
- **Fix the specific-yield error** → Fix 1 (re-run 03). **Fix `dim_building`** → Fix 2 + §4 measures.
- **Rows:** 1 KPI cards · 2 generation area + self-consumption donut · 3 PR-by-building + yield-by-building
  bars · 4 today's PV line (`gold_iot_realtime`, filter `sensor_type = "pv_ac_power"`) + PV
  underperformance table (`gold_iot_fdd`, filter `fault_code = "PV_UNDERPERFORMANCE"`) · 5 INSTALL_SOLAR
  opportunities table (`gold_recommendations`, filter `action_type = "INSTALL_SOLAR"`).
- **DoD:** specific-yield bar renders; B007 shows in the PV-fault table.

---

## 4. Page 10 — Solar new measures (corrected, paste-ready)

Display folder `Solar — Realtime & Opportunity`:

```dax
Realtime PV Power kW =
CALCULATE ( AVERAGE ( gold_iot_realtime[reading_value_avg] ),
            gold_iot_realtime[sensor_type] = "pv_ac_power" )

Peak PV Power kW =
CALCULATE ( MAX ( gold_iot_realtime[reading_value_max] ),
            gold_iot_realtime[sensor_type] = "pv_ac_power" )

PV Underperformance Count =
CALCULATE ( COUNTROWS ( gold_iot_fdd ),
            gold_iot_fdd[fault_code] = "PV_UNDERPERFORMANCE" )

PV Loss EUR =
CALCULATE ( SUM ( gold_iot_fdd[cost_eur_estimate] ),
            gold_iot_fdd[fault_code] = "PV_UNDERPERFORMANCE" )

Solar Capacity kWp =
SUM ( silver_building_master[pv_capacity_kwp] )          -- was dim_building

INSTALL_SOLAR Opportunities =
CALCULATE ( COUNTROWS ( gold_recommendations ),
            gold_recommendations[action_type] = "INSTALL_SOLAR" )

Avg Solar Specific Yield kWh kWp =                        -- resolves after Fix 1 re-run
AVERAGEX (
    FILTER ( gold_kpi_daily, gold_kpi_daily[solar_specific_yield_kwh_kwp] <> BLANK() ),
    gold_kpi_daily[solar_specific_yield_kwh_kwp]
)
```

Reused existing measures (no need to create): `[Total Solar Generated kWh]`,
`[Solar Self Consumed kWh]`, `[Total Solar Exported kWh]`, `[Solar Coverage Pct]`,
`[Avg Self Consumption Rate Pct]`, `[Avg Solar PR Pct]`, `[Total CO2 Savings from Solar tCO2]`,
`[Total Solar Savings EUR]`. *(If a Page-10 card shows a "Renewable Rate" using a name not in the
probe, send it to me — I'll confirm the exact measure.)*

---

## 5. Reliability flags — verify, don't assume

1. **Page 5 simulation:** `gold_simulation_results` absent from the model → simulated scenarios blank.
2. **Page 9 V7:** SoH/cycles/active-strategy columns may be missing unless notebook 12 was re-run with
   the re-added columns.
3. **Page 4 band & Page 7 HVAC:** those tables carry **0 measures** — bind columns directly or create
   measures (noted per page).
4. **Fix 3** `Avg HDD Normalized EUI` → `climate_adjusted_eui`.
5. **Page 3** single-source: no `gold_anomaly_log_kpibuiltin_legacy` in any visual.
6. **Solar PR noise:** synthetic solar vs real irradiance makes some `SOLAR_PR_DROP` anomalies noisy
   on pages 2/3 — known, cosmetic; don't chase it during Gate D.

---

## 6. Execution order & verification

1. **Re-run `03_gold_kpi_engine`** in Fabric (Fix 1) → DirectLake refresh.
2. **Page 10 Solar** — apply Fix 2 + §4 measures → bind Rows 1–5.
3. **Page 8 IoT** — V5 FDD table + C2/C4 (all measures ready).
4. **Page 9 Battery** — verify v56 visuals + V7 + EU flag.
5. **Create `Time Grain`** parameter → toggle on pages 1 / 2 / 3 / 4 / 7.
6. **Page 2** 24h profile + base-load · **Page 4** band · **Page 5** relabel · **Page 7** labels.
7. **Validation pass:** per-page DoD; `TS …` monthly totals ≈ daily totals; FDD priority order sane;
   no blank cards; Fix 3 EUI populated.

**Working loop:** do one numbered step, refresh, and paste me any error (measure name + screenshot).
I return the exact corrected DAX/binding, and we clear all 10 pages together.
