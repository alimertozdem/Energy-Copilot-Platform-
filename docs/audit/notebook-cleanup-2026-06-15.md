# Notebook & Model Cleanup Audit — 2026-06-15

> **Status: PROPOSAL. Nothing deleted yet.** This document is the evidence base and
> phased plan for simplifying the Fabric notebook + semantic-model surface.
> Deletions happen only after sign-off, phase by phase, on a `chore/notebook-cleanup` branch.

## TL;DR

- `notebooks/` holds **59 source files** (`.py` / `.ipynb`; `.pyc` are gitignored, not in repo).
- **~24 of them (~40%) are dead-weight**: paste-limit cell-splits, `_KOPYALA` copies, one-time
  patch scripts, and an orphaned Page-9 battery cluster.
- The root problem is not the count — it is the **absence of a single canonical file per logical
  step**. GHG (09) = 5 files; battery (12) = 11 files. Building bridge versions on top of this
  forks already-forked code, so **the cleanup must happen before finishing the bridge migration.**
- **Key safety finding:** no pipeline, orchestrator, or script in the execution path references
  any delete-candidate. The only references are in docs / semantic-model scripts (narrative).
  Deleting the candidates breaks **zero** execution paths.

## Source of truth — what is actually wired

### Batch chain (`pipelines/batch/*.json`)

`04_master_orchestrator` chains the layer pipelines; each pipeline calls these notebooks:

| Pipeline | notebookId(s) called |
|---|---|
| `01_bronze_batch_pipeline` | `00_reference_data_loader`, `01_bronze_ingestion` |
| `02_silver_transform_pipeline` | `02_silver_transformation` |
| `08_occupancy_pipeline` | `08_occupancy_prediction` (soft-fail) |
| `03_gold_analytics_pipeline` | `10_crrem_pathway_loader`, `03_kpi_engine`, `anomaly_detection`, `04_simulation_engine`, `09_ghg_scope_engine`, `05_compliance_checker`, `06_recommendation_engine`, `11_hvac_analytics_engine` |
| `07_forecast_pipeline` | `07_consumption_forecast` |

The batch chain calls **only consolidated notebooks** — never a `_cell`, `_KOPYALA`, patch, or
`12–15` battery file. This is the primary evidence for the verdicts below.

### Bridge chain (app-orchestrated — `web-app/backend/app/services/bridge_orchestrator.py` + `.env`)

`40_bridge_baseline` → `09_ghg_scope_engine_bridge` → `05_compliance_checker_bridge` →
`06_recommendation_engine_bridge`. Driven per-building from `/admin`. `.env` keys:
`FABRIC_BRIDGE_NOTEBOOK_ID`, `FABRIC_GHG_NOTEBOOK_ID`, `FABRIC_COMPLIANCE_NOTEBOOK_ID`,
`FABRIC_RECOMMENDATION_NOTEBOOK_ID` (last one not yet set → 06 import pending).

## Decision matrix

| File(s) | Category | Referenced by (evidence) | Verdict | Confidence |
|---|---|---|---|---|
| `gold/09_ghg_FABRIC_cell1_dataprep.py`, `cell2_scopecalc.py`, `cell3_breakdown_long.py` | Paste-limit cell-split | docs + a comment in `09_ghg_scope_engine.py`; **not** in any pipeline | **DELETE** (Phase 1) | Kesin |
| `simulation/12_FABRIC_cell1.py`, `12_FABRIC_cell2.py` | Paste-limit cell-split | docs only | **DELETE** (Phase 1) | Kesin |
| `forecasting/08_occupancy_prediction_FABRIC_KOPYALA.py` | Copy | docs only; pipeline uses `08_occupancy_prediction` | **DELETE** (Phase 1) | Kesin |
| `gold/10_crrem_pathway_loader_FABRIC_KOPYALA.py` | Copy | docs only; pipeline uses `10_crrem_pathway_loader` | **DELETE** (Phase 1) | Kesin |
| `utils/00_FABRIC_RESET_KOPYALA.py`, `01_NUCLEAR_FIX_KOPYALA.py`, `FINAL_CLEANUP_KOPYALA.py` | Throwaway one-off | none (self only) | **DELETE** (Phase 1) | Muhtemel |
| `simulation/12_battery_dispatch_and_simulation.py`, `13_gold_battery_hourly_profile.py`, `14_gold_battery_simulation_v2.py`, `15_gold_battery_hourly_dispatch.py`, `15b_hourly_dispatch_selfcontained.py`, `12b_patch_*.py`, `12c_patch_simulation.py` | Orphaned Page-9 cluster (deferred) | docs + semantic-model battery scripts; **not** in pipeline (pipeline uses `04_simulation_engine`) | **QUARANTINE** → `notebooks/_deferred/page9-battery/` (Phase 2) | Muhtemel |
| `loaders/16_load_page9_tables.py`, `16b_load_only_missing_tables.py`, `16c_reload_battery_tables.py` | Page-9 table loaders (deferred) | docs only | **QUARANTINE** with battery (Phase 2) | Muhtemel |
| `anomaly-detection/29b_anomaly_resolved_fix.py`, `29c_anomaly_status_column_patch.py` | One-time patch | docs only; parent `anomaly_detection.py` is the wired one | **VERIFY fix-in-parent → DELETE** (Phase 3) | Muhtemel |
| `transformation/21b_fix_B011_building_master.py` | One-time patch | docs only; parent `21_residential_ingestion.py` | **VERIFY → DELETE** (Phase 3) | Muhtemel |
| `sustainability/reference/00b_add_B011_sim_input.py` | One-time patch | docs only; parent `00_reference_data_loader.py` (wired) | **VERIFY → DELETE** (Phase 3) | Muhtemel |
| `bridge/40_bridge_baseline.py` | `.py`/`.ipynb` twin | `.ipynb` is the Fabric-import artifact | **DELETE `.py`, keep `.ipynb`** (Phase 1) | Kesin |

## Phased cleanup plan (each phase needs sign-off)

- **Phase 1 — Safe deletes (zero execution risk).** Cell-splits + `_KOPYALA` copies + `40_bridge_baseline.py` twin + empty `fabric/` dir. ~11 files. Provably safe: pipeline uses the consolidated versions, nothing imports these.
- **Phase 2 — Quarantine Page-9 battery cluster.** Move (not delete) `12–15` + `16x` loaders into `notebooks/_deferred/page9-battery/`. Page 9 battery ROI is deferred (absurd payback/IRR); keep the code, get it out of the active tree.
- **Phase 3 — Verify-then-fold patches.** For each `29b/29c`, `21b`, `00b`: confirm the fix already lives in the parent notebook; if not, fold it in; then delete the patch. This is the only group where careless deletion could lose a fix.
- **Phase 4 — (separate) semantic-model `.dax` consolidation.** 66 `.dax` files (v5→v60) are an append-only patch changelog applied to the **live** model (213 measures, source of truth). Repo `.dax` are historical. Deleting them does not touch the live model, but this is a larger, separate task — handled after notebooks.

## Canonical keep-list (the clean target)

**Batch (wired in pipelines):** `00_reference_data_loader`, `01_bronze_ingestion`,
`02_silver_transformation`, `03_gold_kpi_engine`, `10_crrem_pathway_loader`, `anomaly_detection`,
`04_simulation_engine`, `09_ghg_scope_engine`, `05_compliance_checker`, `06_recommendation_engine`,
`11_hvac_analytics_engine`, `07_consumption_forecast`, `08_occupancy_prediction`.

**Bridge (app-orchestrated):** `40_bridge_baseline.ipynb`, `09_ghg_scope_engine_bridge.ipynb`,
`05_compliance_checker_bridge.ipynb`, `06_recommendation_engine_bridge.ipynb`.

**Domain modules (not in batch pipeline, run via their own path — KEEP):**
IoT (`iot/00_*`, `01_bronze_iot_raw_generator`, `11b_iot_processing`, `11c_iot_fdd`) — isolated by
design (Page 8); Residential (`transformation/20_*`, `21_residential_ingestion`, `gold/30_residential_gold`);
Reference loaders (`reference/01_epc_ratings_loader`, `02_data_quality_aggregator`,
`03_ref_factors_tariffs_loader`); External loaders (`ingestion/02_openmeteo`, `03_entsoe`,
`05_electricitymaps`); `sustainability/04_scope3_demo_activity_generator`;
`utils/00_diagnostic_and_reset`.

## Open issues to resolve during cleanup

1. **Naming mismatch:** pipeline calls `03_kpi_engine` but the file is `03_gold_kpi_engine.py`.
   Confirm the live Fabric notebook name matches the pipeline `notebookId`, or the batch run fails.
2. **External loaders not in any pipeline:** `02_openmeteo`, `03_entsoe`, `05_electricitymaps` are
   not referenced by `01_bronze_batch_pipeline`. Confirm they are scheduled separately (or wire them in).
3. **`.py` vs `.ipynb` convention:** decide one storage format per notebook class
   (proposed: bridge = `.ipynb`, batch = `.py` source). Ties into the bridge-workspace decision.

## REVISION — 2026-06-15 (Phase 3 verification result)

Read the four patch files against their parents. **3 of 4 are NOT dead** — they
carry logic/data the parent notebooks do not have. Revised verdicts:

| Patch | Finding | Revised verdict |
|---|---|---|
| `29b_anomaly_resolved_fix` | Parent `anomaly_detection.py` BÖLÜM 7b was rewritten to do the resolved-status update itself (episode-aware DeltaTable MERGE). Superseded. | DELETE (safe) |
| `29c_anomaly_status_column_patch` | Adds a physical `anomaly_status` ("Resolved"/"Open") column the parent does NOT create; DirectLake cannot add it as a DAX column, so Page 3 reads the physical column. | KEEP → fold into parent, then delete |
| `21b_fix_B011_building_master` | Sets B011 boolean flags (has_heat_pump…) left NULL by parent; without them B011 recommendations never fire. | KEEP → fold B011 seed into parent |
| `00b_add_B011_sim_input` | Seeds B011 row in `ref_simulation_inputs`; parent seeds only B001/B002/B003. | KEEP → fold into parent |

**Implication:** the patch group is not blind-deletable. Folding 29c/21b/00b into
their parents is a separate, careful task (requires a Fabric re-run), not Phase 1.
Only `29b` joins the safe-delete set.
