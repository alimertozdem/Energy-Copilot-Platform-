# Fabric Workspace Reconciliation Map — 2026-06-15

Workspace `6b78345d-d672-40ed-8ac5-258b58d60af9` — **52 live notebooks, 1 live pipeline**
(`energy_copilot_master`). Built from `fabric_audit.py` output. GUIDs: see `docs/fabric-sync.md`.

> Confidence: names inferred from the live displayName only (notebook *content* not inspected).
> `[Tahmin]` rows need Mert to open the notebook in Fabric and confirm before acting.

## TL;DR — three big findings
1. **Live is messier than the repo:** ~13 junk/untitled notebooks (`Notebook 1/2/3`, `reset`, `nuclear_fix`, `yeni data`, `bağlantı`…).
2. **~10 canonical notebooks are just RENAMED** (`.py` suffixes, a trailing dot, `Bronz`) — that is why every repo pipeline ref reads MISSING.
3. **Live-only, likely real → must RESCUE to repo before any cleanup:** `50_materialize_to_postgres`, `00_generate_sample_data`.

## Verdict table (52 live notebooks)

### KEEP — aligned with repo (14)
`00_reference_data_loader`, `02_data_quality_aggregator`, `02_openmeteo_weather_loader`,
`02_silver_transformation`, `03_gold_kpi_engine`, `03_ref_factors_tariffs_loader`,
`04_scope3_demo_activity_generator`, `04_simulation_engine`, `05_compliance_checker`,
`05_compliance_checker_bridge`, `06_recommendation_engine`, `11c_iot_fdd`,
`21_residential_ingestion`, `30_residential_gold`.

### RENAME — canonical but live name drifted → align to repo (10)
| Live name | → rename to | Conf |
|---|---|---|
| `11_hvac_analytics_engine.py` | `11_hvac_analytics_engine` | Muhtemel |
| `09_ghg_scope_engine.py` | `09_ghg_scope_engine` | Muhtemel |
| `08_occupancy_prediction.` (trailing dot) | `08_occupancy_prediction` | Muhtemel |
| `10_crrem_pathway` | `10_crrem_pathway_loader` | Muhtemel |
| `20_residential_model_p1.py` | `20_residential_model_p1` | Muhtemel |
| `Bronz` | `01_bronze_ingestion` | Tahmin |
| `07_Anomaly detection_engine` | `anomaly_detection` | Tahmin |
| `gold_consumption_forecast` | `07_consumption_forecast` | Tahmin |
| `iot_sensor_master_generator` | `00_iot_sensor_master_generator` | Muhtemel |
| `bronze_iot_raw` | `01_bronze_iot_raw_generator` | Tahmin |
| `notebooks/bridge/40_bridge_baseline.py` (path as name!) | `40_bridge_baseline` | Muhtemel |

### JUNK — delete from Fabric (13)
`Notebook 1`, `Notebook 2`, `Notebook_1`, `Notebook_2`, `Notebook_3`, `reset`, `reset v5`,
`nuclear_fix`, `anormali ekstra`, `anormaly fix`, `Silver patch` [Tahmin], `yeni data` [Tahmin],
`bağlantı` [Tahmin]. (Repo equivalents were already deleted in Phase 1, or are throwaway.)

### BATTERY / Page-9 — quarantine or delete in live (deferred) (6)
`12b — Patch gold_battery_dispatch`, `13 battery hourly`, `14 Battery`, `15`,
`15b_hourly_dispatch_selfcontained.py`, `Battery month year`. (Repo moved these to `_deferred/` in Phase 2.)

### PATCH — fold into parent, then delete in live (3) — Phase 3
`00b_add_B011_sim_input`, `21b`, `29b_anomaly_resolved`.

### RESCUE — live-only, likely real → export into repo FIRST (2-3)
| Live name | Why | Action |
|---|---|---|
| `50_materialize_to_postgres` | KPI→Postgres (approved direction) — not in repo | export → `notebooks/` then version it |
| `00_generate_sample_data` | synthetic demo-data generator — not in repo | export → `notebooks/` |
| `16 data loader extend` [Tahmin] | unclear; may be battery loader or real | INVESTIGATE then rescue/junk |

### INVESTIGATE — open in Fabric, confirm before acting (3)
| Live name | Suspicion |
|---|---|
| `Notebook 11b` | might be the real `11b_iot_processing` (not junk!) |
| `EPC rating` | might be `01_epc_ratings_loader` (rename) vs throwaway |
| `Silver patch` | one-off patch vs real silver logic |

## Repo notebooks MISSING from live → must DEPLOY (gaps)
These exist in the repo but were never (or no longer) deployed:
`03_entsoe_price_loader`, `05_electricitymaps_co2_loader` (external loaders — also the Fix-2 gap),
`00_iot_adapter_framework`, `11b_iot_processing` (unless `Notebook 11b`),
`01_epc_ratings_loader` (unless `EPC rating`), `07_consumption_forecast` (unless `gold_consumption_forecast`),
`anomaly_detection` (unless `07_Anomaly detection_engine`).

## Reconciliation sequence (proposed)
1. **RESCUE** live-only reals (`50_materialize_to_postgres`, `00_generate_sample_data`) → repo + commit.
2. **INVESTIGATE** the 3 ambiguous (`Notebook 11b`, `EPC rating`, `Silver patch`) → reclassify.
3. **RENAME** the 10 drifted live notebooks to match repo (so pipeline refs bind).
4. **JUNK**: delete the 13 throwaway + 6 battery + 3 folded patches from live.
5. **DEPLOY** the missing repo notebooks + the clean pipeline(s) via `fabric_deploy.py` (v2, GUID-resolved).
6. **SCHEDULE** via the `.schedules` part (02:00 UTC) — only after a clean validation run.
