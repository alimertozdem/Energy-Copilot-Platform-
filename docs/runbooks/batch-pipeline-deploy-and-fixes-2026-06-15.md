# Batch Pipeline — Fix, Deploy & Schedule Runbook (2026-06-15)

## Status
The 5 batch pipeline JSONs in `pipelines/batch/` are **design templates, not deployed**:
they use `${FABRIC_WORKSPACE_ID}` placeholders and notebook **names** (not Fabric object
GUIDs). The schedule is already designed: `04_master_orchestrator` → trigger
`DailySchedule_0200_UTC` (daily 02:00 UTC = 04:00 Berlin / 05:00 Istanbul).

Orchestration is sound: Bronze → Silver → Occupancy (soft) → Gold (KPI → sim → compliance →
reco; + anomaly / CRREM / HVAC) → Forecast (soft). Hard-fail guards on Bronze/Silver/Gold;
soft-fail on Occupancy/Forecast. Trial-mode = sequential (avoids 430 TooManyRequests).

## Fixes before deploy

### Fix 1 — Notebook name mismatch (BLOCKER)
`03_gold_analytics_pipeline.json` line 33: `"notebookId": "03_kpi_engine"`.
File is `03_gold_kpi_engine.py`; `04_master_orchestrator` description says `03_gold_kpi_engine`.
→ Confirm the **live Fabric notebook name**, then make all three agree. Almost certainly change
the pipeline activity to `"03_gold_kpi_engine"`. If runs resolve notebooks by name, this mismatch
makes `Compute_KPIs` fail to find its notebook — and KPI failure hard-aborts the whole batch.

### Fix 2 — External loaders not wired (data gap)
`02_openmeteo_weather_loader`, `03_entsoe_price_loader`, `05_electricitymaps_co2_loader` exist
but are in **no pipeline** → weather / price / grid-CO2 bronze tables never refresh on schedule,
so KPI/GHG run on stale external data. Add them to `01_bronze_batch_pipeline.json` as
**best-effort parallel** activities (they have fallbacks per the Phase-2 design), with **soft-fail**
on the barrier so a flaky external API never aborts the nightly batch.

Add these three activities to the `activities` array:

```json
{
  "name": "Load_Weather_Data",
  "type": "TridentNotebook",
  "description": "02_openmeteo_weather_loader — daily HDD/CDD + weather. Best-effort; fallback to last-known if API down.",
  "dependsOn": [],
  "policy": { "timeout": "0.00:20:00", "retry": 3, "retryIntervalInSeconds": 90 },
  "typeProperties": { "notebookId": "02_openmeteo_weather_loader", "workspaceId": "${FABRIC_WORKSPACE_ID}", "parameters": {} }
},
{
  "name": "Load_Electricity_Prices",
  "type": "TridentNotebook",
  "description": "03_entsoe_price_loader — day-ahead prices. Best-effort; fallback to EU-typical rates if API down.",
  "dependsOn": [],
  "policy": { "timeout": "0.00:20:00", "retry": 3, "retryIntervalInSeconds": 90 },
  "typeProperties": { "notebookId": "03_entsoe_price_loader", "workspaceId": "${FABRIC_WORKSPACE_ID}", "parameters": {} }
},
{
  "name": "Load_Grid_CO2",
  "type": "TridentNotebook",
  "description": "05_electricitymaps_co2_loader — grid carbon intensity. Best-effort; fallback to annual residual-mix factor if API down.",
  "dependsOn": [],
  "policy": { "timeout": "0.00:20:00", "retry": 3, "retryIntervalInSeconds": 90 },
  "typeProperties": { "notebookId": "05_electricitymaps_co2_loader", "workspaceId": "${FABRIC_WORKSPACE_ID}", "parameters": {} }
}
```

Then add to `Bronze_Completed.dependsOn` (soft — failure does not block downstream):

```json
{ "activity": "Load_Weather_Data",       "dependencyConditions": ["Succeeded", "Skipped", "Failed"] },
{ "activity": "Load_Electricity_Prices", "dependencyConditions": ["Succeeded", "Skipped", "Failed"] },
{ "activity": "Load_Grid_CO2",           "dependencyConditions": ["Succeeded", "Skipped", "Failed"] }
```

> Downstream KPI/GHG notebooks must keep their built-in fallbacks (last-known weather, EU-typical
> price, residual-mix CO2). The soft-fail wiring only works because those fallbacks exist.

### Fix 3 — Verify anomaly dependency
`Detect_Anomalies` has `dependsOn: []` (runs at pipeline start), but `04_master_orchestrator`
notes say anomaly depends on Gold KPI. If `anomaly_detection` reads `gold_kpi_*`, add a
`Compute_KPIs` (Succeeded) dependency; if it reads silver directly, leave as-is. Verify in the notebook.

## Deploy (once fixes applied)
These JSONs are specs — Fabric won't import them as-is. Options:
1. **Fabric UI build** (recommended for now): recreate the 5 pipelines from these blueprints
   (activities + dependencies + the 02:00 trigger). One-time, most reliable on trial.
2. **Git integration**: connect workspace ↔ repo; Fabric syncs items — but needs Fabric's native
   item format, not these hand-written specs (conversion required).
3. **Fabric REST API**: programmatic create — needs an Entra app registration (same hurdle as the MCP connector).

## Capacity gate (confirm BEFORE scheduling)
CLAUDE.md trial deadline was **2026-05-21** (now past). Nightly batch consumes Spark capacity.
Confirm current Fabric capacity (paid F-SKU / startup credits / expired) before activating the
02:00 trigger — otherwise the scheduled run can't start.

## Open questions for Mert
1. Is any batch pipeline actually deployed/running in Fabric, or only these repo JSONs?
2. Current Fabric capacity after trial (F-SKU? credits? expired)?
3. Live name of the KPI notebook: `03_kpi_engine` or `03_gold_kpi_engine`?

## UPDATE — 2026-06-15 (answers from Mert)

- **Capacity:** trial still active, **F4** → capacity is NOT the blocker; nightly batch can run.
- **Deployment:** pipelines **were deployed but are stale** ("kurmuştum ama çok şey değişti"), **schedule OFF**.
- **Do NOT re-enable the stale schedule as-is.** Phase 1+2 cleanup just deleted/moved 22 notebooks;
  the deployed pipeline almost certainly references renamed/removed notebooks → a scheduled run would
  fail or write partial/garbage data unattended at 02:00.
- **Revised recommendation:** the stale-deployment pain is repo↔Fabric **drift**. Fix the drift
  (sync strategy — see item 3) and re-validate/rebuild the pipelines against the *current* notebook
  set BEFORE re-enabling any schedule. Batch deploy is parked on this, not on capacity.
