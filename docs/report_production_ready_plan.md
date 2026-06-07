# EnergyLens — Report Production-Readiness Execution Plan

**Date:** 2026-06-01 · **Status:** DRAFT for approval · **Scope:** make the 9-page Power BI
report production-ready (model + DAX + visuals), on top of the 2026-05-30 refactor and the
now-live IoT/Page-8 flagship.

> Read with: `docs/audit/2026-05-30_gap_register.md` (diagnosis),
> `docs/EnergyLens_Finalization_Plan_and_Working_Reference.md` (per-page DoD + methodology),
> `docs/architecture/iot-page8-fdd-architecture.md` (IoT layer).

This plan is **approval-gated**. Nothing is implemented until each gate is signed off. The
order is deliberate: **notebooks first (data correctness)** → **model tables** → **one DAX
consolidation** → **per-page visuals**.

---

## 0. Open decisions (need sign-off before execution)

| # | Decision | Recommendation |
|---|---|---|
| D-1 | **Battery pipeline (audit I4):** notebooks 12 / 13 / 14 / 15 overlap. Which is authoritative? | Keep **v56 set** (`gold_battery_dispatch`, `gold_battery_simulation`, `gold_battery_technologies`, `gold_battery_daily_summary`, `gold_country_regulations`, `gold_strategy_fitness`). Archive 13/14/15 outputs unless a Page-9 visual still binds them. |
| D-2 | **DAX delivery:** 65 patch files → one authoritative definition. | Build **one Tabular Editor C# script** (this plan, §3) as the single source; retire the patch chain. |
| D-3 | **`ref_*` tables in the model:** engines already join them server-side. | **Do not** add to the model now (no measure needs them yet); revisit only if we build lineage tooltips. |
| D-4 | **Hourly toggle scope:** guide targets pages 1/2/3/4/7. | Confirm all five, or trim to 1/2/4 if time-boxed. |
| D-5 | **07 forecast E1 fix** (occupancy regressor silently bypassed) — fix now or accept neutral occupancy? | Fix now (1-line import move) and re-run; it's a credibility item on a forecast page. |

---

## 1. GATE A — Notebook production-readiness (Fabric data layer)

The report can only be as correct as its Gold tables. This gate confirms every engine is
clean, idempotent and live **before** any model/visual work.

| Engine | Produces | Status | Action before report work |
|---|---|---|---|
| `reference/03_ref_factors_tariffs_loader` | ref_grid_emission_factors, ref_electricity_tariffs, ref_fuel_factors | ✅ ran + verified | none |
| `ingestion/02_openmeteo_weather_loader` | silver_weather_clean/daily | ✅ ran + verified | none |
| `gold/03_gold_kpi_engine` | gold_kpi_daily/hourly/monthly | ✅ ran (climate_adjusted_eui, ref-wired) | none |
| `gold/09_ghg_scope_engine` | gold_ghg_scope | ✅ ran (Scope1/2/3, market-based S2) | none |
| `gold/11_hvac_analytics_engine` | gold_hvac_analytics | ✅ ran (EN labels) | none |
| `compliance/05_compliance_checker` | gold_compliance_results/issues | ✅ ran (ref-wired) | none |
| `recommendation/06_recommendation_engine` | gold_recommendations (37) | ✅ ran | none |
| `simulation/12_battery_dispatch_and_simulation` | gold_battery_dispatch/simulation/daily_summary | ✅ ran (ROI realism I3) | confirm D-1 |
| `anomaly-detection/anomaly_detection` | gold_anomaly_log (sole authority) | ✅ ran | none |
| `iot/00_iot_sensor_master_generator` | gold_iot_sensor_master (515) | ✅ ran | none |
| `iot/01_bronze_iot_raw_generator` | bronze_iot_raw | ✅ ran | none |
| `iot/11b_iot_processing` | silver_iot_normalized, gold_iot_realtime, gold_iot_daily_summary | ✅ ran (lookback 50) | none |
| `iot/11c_iot_fdd` | gold_iot_fdd (12 rules) | ✅ ran | none |
| `forecasting/07_consumption_forecast` | gold_consumption_forecast | ⚠️ **E1 bug live** | **FIX**: move `from pyspark.sql import functions as F` above the occupancy block (currently line 301, used line 280) → re-run. Occupancy regressor is silently bypassed today. |
| `forecasting/08_occupancy_prediction` | gold_occupancy_profile | ✅ OPTIMIZE now try/except-guarded | re-run if not in current build |
| `gold/10_crrem_pathway_loader` | gold_crrem_pathway | ◑ runs, but representative data (D6) + hardcoded prefix (D7) | acceptable for demo; label "representative"; adopt `_resolve_tables_prefix()` later |
| `reference/01_epc_ratings_loader` | silver_epc_ratings | ✅ assumed live (Page 6 uses it) | verify present |
| `simulation/04_simulation_engine` | gold_simulation_results | ◑ Page 5 depends on it (F4) | **verify it ran** + produces hp_/bat_/ins_/deep_ columns |
| `reference/00_reference_data_loader` | ref_building_type_profiles, ref_simulation_inputs | ◑ Page 5/6 depend | verify present |
| `loaders/16*` | gold_country_regulations, gold_strategy_fitness, battery tables | ◑ v56 reload path | confirm D-1, then keep one |

**Gate A verdict:** core engines are production-ready and live. **Blockers:** (1) 07 E1 fix
(D-5); (2) verify `04_simulation_engine` + `00_reference_data_loader` outputs exist (Page 5
silently degrades to compliance-only if missing); (3) confirm battery pipeline (D-1). Cleanup
(non-blocking): retire `gold_anomaly_log_kpibuiltin_legacy` from any consumer; keep
`*_KOPYALA` / `utils/*reset*` notebooks out of the production path.

---

## 2. GATE B — Model tables: delete / add / relationships

Current model (inferred from live DAX + page completions): `gold_kpi_daily`,
`gold_hvac_analytics`, `gold_crrem_pathway`, `gold_ghg_scope`, `gold_recommendations`,
`gold_compliance_results`, `gold_anomaly_log`, `gold_consumption_forecast`,
`gold_occupancy_profile`, `silver_epc_ratings`, `silver_building_master`, v56 battery set,
`Date`.

### 2.1 ADD to model

| Table | Why | Relationship(s) |
|---|---|---|
| `gold_kpi_hourly` | hourly toggle (v58); currently orphan | `[date] → Date[Date]` (M:1, single) **— this is the toggle enabler** |
| `gold_iot_realtime` | Page 8 C1/C2/V1/V3 | `building_id → silver_building_master`; `event_date → Date[Date]` |
| `gold_iot_fdd` | Page 8 V5 FDD + C4 | `building_id → silver_building_master`; `event_date → Date[Date]` |
| `gold_iot_daily_summary` | Page 8 uptime/compliance daily | `building_id`; `event_date → Date[Date]` |

Also: **refresh `gold_ghg_scope` schema** in the model so the new columns (market-based
Scope 2, `scope3_disclosure_grade`, EU-taxonomy/CSRD fields) are available to v57 measures.

### 2.2 DELETE / keep-out of model

| Table | Reason |
|---|---|
| `gold_anomaly_log_kpibuiltin_legacy` | legacy §8 output; Page 3 must read **only** `gold_anomaly_log` (single-engine, audit C1) |
| `gold_battery_hourly_profile` / `gold_battery_simulation_v2` / `gold_battery_hourly_dispatch` | superseded by v56 set **if** D-1 = keep v56; remove only after confirming no Page-9 visual binds them |

### 2.3 Stale references to purge (not tables — measure refs in old DAX)

`gold_crrem_pathways` (→ `gold_crrem_pathway`), `gold_kpi_engine` (→ `gold_kpi_daily`),
`gold_anomaly_alerts`, `gold_forecast_daily` (→ `gold_consumption_forecast`),
`silver_refrigerant_log`, `silver_energy_readings`, `silver_transformation`. These come from
the base `02_dax_measures` + early patches and are removed by the §3 consolidation.

---

## 3. GATE C — DAX consolidation (single Tabular Editor transfer)

**Goal:** replace the 65-file patch chain with **one authoritative measure set**, delivered as
**one Tabular Editor 2 C# script**, with **zero broken references**.

### 3.1 Authoritative version per page (the "live" set)

| Page | Live source file | Notes |
|---|---|---|
| 1 Portfolio | `60_dax_v52_page1_portfolio_scorecard` | + hourly TS measures (v58) |
| 2 Deep-Dive | v52 + `70_dax_v58` (TS + 24h profile) | |
| 3 Anomaly | `30/31/32_dax_v21–v23` | align to single `gold_anomaly_log` taxonomy |
| 4 Forecast | `65_dax_v53_page4_final_polish` | + confidence band measures |
| 5 Decision | `66_dax_v54` + `67_dax_v55_headcount` | CSRD→EU-taxonomy relabel |
| 6 Sustainability | `69_dax_v57_page6_audit_fixes` | EPC area-weighted, CRREM S1+2, taxonomy/CSRD |
| 7 HVAC | `51/52_dax_v42–v43` | "modeled" framing |
| 8 IoT | `71_dax_v59_iot_fdd_and_fixes` | + **new v60** (priority_score / confidence / probable_cause + V5 table) |
| 9 Battery | `68_dax_v56_page9_master` | v56 authoritative |
| Hourly (cross) | `70_dax_v58_hourly_granularity` | Time Grain field param |

### 3.2 Must-purge from base

`02_dax_measures` references **non-existent CRREM columns** (`pathway_kgco2_m2_yr`, `[year]`);
the loader produces `pathway_2c_kgco2_m2_yr` / `pathway_year`. Re-applying base reintroduces
BLANK CRREM cards. The consolidated script must use the corrected columns (already in v7/v13/v57)
and never re-create the broken ones.

### 3.3 New measures to add this round (not yet loaded)

`v57` (Page 6), `v58` (hourly), `v59` (Page 8 IoT) — plus a small **`v60`** for the new
`gold_iot_fdd` columns: `IoT FDD Priority`, `IoT FDD Avg Confidence`, `IoT FDD Probable Cause`,
and a V5-table-ready measure set sorted by `priority_score`.

### 3.4 One-script delivery + Tabular Editor pitfalls (from memory)

- **One C# script**, idempotent: for each measure, create-or-update in its **correct home
  table** (`Measure.Table` is read-only — set at creation; to move, delete + recreate).
- Apply the `hdd_normalized_eui → climate_adjusted_eui` rename everywhere it's referenced.
- After the script: **Model → Refresh / Recalculate is mandatory** before measures resolve;
  save to the model in Git (TMDL), not as another patch file.
- Build the script against the **live model's actual table/column names** (run a probe first —
  the `scripts/probe_model_tables*.cs` pattern — so the script never references a renamed column).

---

## 4. GATE D — Per-page visual plan (delete / add / how)

Targets from the finalization plan's per-page DoD. "How" = the concrete binding.

### Page 1 — Portfolio Overview
- **ADD:** Time-Grain toggle on the portfolio consumption trend (X = `Time Grain` field param;
  Y = `TS Consumption kWh`; Tile slicer default Daily).
- **VERIFY:** EUI annualized vs benchmark; CO₂ + cost from ref. **DELETE:** none.

### Page 2 — Building Deep-Dive ⭐
- **ADD:** Time-Grain toggle on demand/net-grid line (`TS Avg Demand kW`, `TS Net Grid kWh`,
  + `TS Solar Generated kWh` for solar buildings).
- **ADD:** dedicated **24h load-profile** chart (X = `gold_kpi_hourly[hour]`, Y =
  `Profile Avg Demand by Hour kW`) + **Base Load Ratio** card.
- **VERIFY:** climate-adjusted EUI uses the ratio method + CDD (B1). **DELETE:** none.

### Page 3 — Anomaly Detection
- **ADD:** Time-Grain toggle on consumption-vs-baseline context chart.
- **DELETE/REBIND:** any visual bound to the legacy §8 anomaly set → rebind to
  `gold_anomaly_log`. Freeze one taxonomy + severity casing.

### Page 4 — Forecasting
- **ADD:** confidence band on the forecast chart (`lower_bound_kwh` / `upper_bound_kwh` — E3);
  Time-Grain toggle on **actuals** only (forecast stays daily).
- **RELABEL:** MAPE → "in-sample fit". **DELETE:** none.

### Page 5 — Decision Support
- **RELABEL:** "CSRD score" → **EU Taxonomy Carbon Score**; reserve "CSRD readiness" for a
  disclosure-completeness checklist. **VERIFY:** simulation table live (Gate A). **DELETE:** none.

### Page 6 — Sustainability ⭐ (primary niche)
- **ADD/REBIND:** EPC heat map → **area-weighted** measure (v57); CRREM line → **Scope 1+2**
  intensity (v57); cards **EU Taxonomy Carbon Score** + **CSRD Disclosure Readiness %**.
- **ADD:** Scope 2 **location vs market** as separate donut slices; "est." label on Scope 3.
- **DELETE:** old single "CSRD score" card / any Scope-2-only CRREM measure.

### Page 7 — HVAC & Envelope
- **ADD:** "modeled (HDD/CDD method)" labels on HVAC-share / heating-cooling split; Time-Grain
  toggle on consumption + temperature. COP / split visuals stay monthly.
- **VERIFY:** labels English (engine G2 done). **DELETE:** none.

### Page 8 — Real-Time IoT (flagship)
- **ADD:** **V5 "FDD Findings"** table from `gold_iot_fdd` sorted by `priority_score` DESC
  (equipment + fault_code + confidence% + Est. €). Wire C2/C4 to v59; optional v60 priority card.
- **VERIFY:** static snapshot connected (done). **DELETE:** any visual on the unused
  `iot_anomaly_alerts`.

### Page 9 — Battery Dispatch & ROI
- **CONSOLIDATE:** bind only the v56 table set (D-1); remove visuals on superseded battery
  tables. **VERIFY:** ROI realism (I3 engine done), EU-2023/1542 compliance flag visible.
- **DELETE:** superseded-pipeline visuals/tables per D-1.

---

## 5. Execution sequence (BMAD, approval-gated)

1. **Gate A** — fix 07 E1, verify simulation/reference tables, confirm D-1 → re-run the few
   engines. *(Mert in Fabric; I prep the 07 fix.)*
2. **Gate B** — add 4 tables + relationships; remove legacy/superseded; refresh ghg schema.
3. **Gate C** — I author the single TE2 C# script (probe-first); Mert runs it once + refresh.
4. **Gate D** — per-page visuals, page by page (priority 6 → 8 → 9 → 2, then 1/3/4/7).
5. **Validation** — per-page DoD checklist; `TS …` monthly ≈ daily totals; FDD priority sane.
6. **Phase 3** — per-visual methodology PDF (separate effort, after Final).

Each gate is independently testable and reversible. No gate starts before the prior one is
signed off.

---

## 6. What I will prepare next (on approval)

- The **07 E1 one-line fix** (ready to paste).
- The **probe C# script** to read the live model's exact tables/columns.
- The **single consolidated TE2 C# script** (all live measures + v57/v58/v59/v60, no broken refs).
- A **per-page binding checklist** (delete/add/bind) you can execute in Power BI Desktop.

*No model or visual changes are made until you approve Gates A–D.*
