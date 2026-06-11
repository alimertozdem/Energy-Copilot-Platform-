# EnergyLens — CP-1 Report Go-Live Runbook (founder-run)

_What this is: a **runbook** = a step-by-step checklist **you** execute in your Fabric / Power BI
environment (which the copilot's sandbox can't reach). Each step is: **☐ action → ✅ verify → ⚠
if-fail**. Work top to bottom; don't skip a ✅._

**Scope note:** for a **meter-only pilot #1**, Phases 1–3 + 5–6 (Pages 1–6) are the real go-live.
**Phase 4 (Pages 8/9/10)** is demo-completeness — defer it until a pilot actually has
IoT / battery / solar.

---

## Phase 0 — Backup (5 min)
- ☐ Save a copy of the current report: `EnergyLens_v60_backup.pbix`.
- ☐ Screenshot which pages render vs. show "No data" now (so you can confirm the fix later).

## Phase 1 — Refresh the gold data layer (Fabric)
- ☐ Fabric workspace → open notebook `03_gold_kpi_engine` → **Run all**.
- ✅ `gold_kpi_daily` rebuilds with **no error**, and its columns include **`climate_adjusted_eui`**
  and **`specific_yield`** (Gate-D Fix 1 + Fix 3).
- ⚠ If `03` fails on a missing upstream table, run the silver/transformation notebook it reads
  from first, then re-run `03`.
- ℹ `03` also writes `gold_anomaly_log_kpibuiltin_legacy` — expected and harmless (C1: the real
  authority is `anomaly_detection.py`).

## Phase 2 — Install measures + refresh the semantic model
- ☐ Open the semantic model in **Tabular Editor**.
- ☐ Run the script `semantic-model/scripts/final_master_install.cs`.
- ✅ Output ≈ **57 Upserts, 0 errors**. **Save** to the model.
- ☐ **Refresh** the semantic model (DirectLake picks up the new columns).
- ✅ No "Missing_References" / `QueryUserError`. ⚠ If a measure errors on a column, that column
  didn't get produced in Phase 1 → recheck `03`.

## Phase 3 — Time-grain toggle (the main Page 2 complaint)
_Symptom: Page 2's 3 trend visuals are stuck monthly; no 24-hour profile._
- ☐ Confirm the `Date` table has the **`[Month Year]`** column (sorted by `YearMonth`) — the
  install script adds it.
- ☐ Verify/add the **grain toggle** (field parameter or the time-grain measures) so trends switch
  **Day / Month**, and point the **24h profile** visual at the hourly measure.
- ✅ Page 2 trends switch grain; a 24-hour kW profile renders.

## Phase 4 — Rebind broken visuals  _(demo-completeness; deferrable for pilot #1)_
- **Page 8 (all visuals broken):**
  - ☐ For each "No data" visual, rebind its fields to the `gold_iot_realtime` / `gold_iot_fdd`
    measures (C1 building power, C2 zone compliance, C3 CO₂, C4 alerts + €).
  - ✅ Cards + 24h power trend + alert table render. ⚠ Needs static-snapshot IoT tables present —
    if empty, run `01_bronze_iot_raw_generator` → `11b_iot_processing` → `11c_iot_fdd` first.
- **Page 9 (24h Battery + EU Compliance broken; ROI absurd):**
  - ☐ Rebind the "24h Battery" and "EU Compliance" visuals to their measures.
  - ✅ RTE now shows **~90** (the new `C4 Round Trip Efficiency Pct` normalizes 0.9→90).
  - ⚠ Payback ~230 / IRR ~450% is a **data** issue (`battery_simulator.py` output), not DAX —
    flag and defer (battery-only; not pilot-#1).
- **Page 10 (specific-yield broken):**
  - ☐ Rebind the specific-yield visual to `gold_kpi_daily[specific_yield]` (produced in Phase 1).
  - ✅ Specific yield (kWh/kWp) renders.

## Phase 5 — Verify Pages 1 / 3 / 4
- ✅ Page 1: EUI **annualized**; CO₂ + cost from the `ref_` layer.
- ✅ Page 3: single anomaly source (`gold_anomaly_log`); severity UPPERCASE.
- ✅ Page 4: forecast renders **with the confidence band** (E3).
- ⚠ If Page 4 or 7 shows "0 measures", that page's measures didn't install → re-run the relevant
  section of `final_master_install.cs`.

## Phase 6 — Final verification (sanity vs. known-good numbers)
- ✅ Every page renders; no "No data"; no measure errors.
- ✅ Spot-check a DE office (~4–5k m²): **EUI ≈ 80–120**, **CO₂ = kWh × 0.363**, cost from the ref
  tariff — these match the Step-1 dry-run sanity figures.
- ✅ Save the `.pbix` and **publish** to the workspace → embedded views auto-update.
- → RLS isolation is verified separately in **CP-2** (the pilot runbook).

---

### Done-definition
Pages 1–6 render with correct, sanity-checked numbers and no measure errors; embedded report
refreshed. (Pages 8/9/10 green is a bonus unless your first pilot has those modules.)
