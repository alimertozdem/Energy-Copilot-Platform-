# Fabric Trial Rescue Snapshot — 2026-07-05

Full definition export taken the day the Fabric trial expired (see
`docs/runbooks/fabric-trial-expiry-rescue-2026-07-05.md`). Exported via Fabric
REST `getDefinition` across the whole workspace.

## Contents
| File | What |
|---|---|
| `fabric_definitions_20260705.zip` | ALL item definitions: ~50 notebooks (.ipynb, incl. live-edited 50_materialize / 09_ghg / 06b / 03b / 16), full SemanticModel TMDL, **both Reports** (report.json = layout + 645 report-level measures in modelExtensions + themes + page-background PNGs), KQL Eventhouse + Queryset, 2 DataPipelines, Lakehouse defs, `_inventory.json` |
| `EnergyCopilotModel_tmsl.json` | Whole semantic model as TMSL/JSON — 30 tables, 336 measures (June-finalized: PV Underperformance, Avg Solar PR Pct, Net Arbitrage all present) |
| `measures.csv` | Flat measure list |
| `CustomerRLS_role_from_2026-06-16.tmdl` | RLS role — see gap #1 |

## Known gaps
1. **RLS role not in the fresh export.** Fabric definition export omits security
   roles. The rule is simple and stable (`role CustomerRLS: modelPermission read;
   tablePermission silver_building_master = PATHCONTAINS(CUSTOMDATA(),
   silver_building_master[building_id])`). The 2026-06-16 copy is included here and
   is almost certainly still current. If you want 100% certainty, screenshot the
   role in the service before the trial lapses.
2. **No raw Delta data.** Bronze/silver/gold table *data* was not downloaded (the
   data-zip download was cut off). Fully regenerable by re-running the notebooks.
   The gold subset the web app needs already lives in Supabase (`mv_*`, 13 tables).

## How to restore
- **Within the 7-day grace (until ~2026-07-13):** attach any paid F capacity to the
  workspace → Microsoft revives EVERYTHING in full; this snapshot becomes redundant.
- **After deletion:** create a new Lakehouse + semantic model, import the TMDL /
  TMSL, deploy the notebooks, re-run them to rebuild the Lakehouse tables, redeploy
  `report.json` (PBIR) as the report, re-add the CustomerRLS role.
