# Runbook — Page 6 "Missing_References" on `gold_ghg_breakdown_long`

**Symptom.** Page 6 (Sustainability Compliance) visuals show *"Düzeltilmesi gereken alanlar / Missing_References"*, naming `(gold_ghg_breakdown_long) Emissions tCO2e` and `(gold_ghg_breakdown_long) category`. Seen 2026-06-03 and 2026-06-14 — recurring.

**Cause.** The Page 6 comparison visuals reference the `gold_ghg_breakdown_long` table, its `[Emissions tCO2e]` measure and its `category` column. In **DirectLake**, if a model refresh can't resolve the table (Delta table missing/renamed, or the table was removed from the model), the table drops out **and its measures are lost with it** — so every visual that used them breaks with `Missing_References`. It is **not** caused by editing the GHG notebook code or restoring a notebook version (those don't touch the semantic model).

**Table schema** (produced by `09_ghg_FABRIC_cell3_breakdown_long.py` from `gold_ghg_scope`):
`building_id, year_month, reporting_year, reporting_month, scope, category, data_grade, value_tco2`

## Fix (Power BI / Fabric)

1. **Is the table in the Lakehouse?** Lakehouse → Tables → `gold_ghg_breakdown_long`.
   - **Missing** → run 09 **cell3** (breakdown_long) once (after cell1+cell2). It overwrites the table from `gold_ghg_scope`.
   - **Present** → the data is fine; the problem is only in the model → step 2.
2. **Re-add the table to the semantic model** (DirectLake). If already there, **Refresh**.
3. **Recreate the measure** on `gold_ghg_breakdown_long` (lost when the table dropped):
   ```DAX
   Emissions tCO2e = SUM ( gold_ghg_breakdown_long[value_tco2] )
   ```
4. **Relationship:** `gold_ghg_breakdown_long[building_id]` → `silver_building_master[building_id]` (many-to-one). Add if missing.
5. **Refresh now** → reload the embed. Page 6 visuals resolve.

## Prevention

Make sure **cell3 runs every time the GHG engine runs**, so `gold_ghg_breakdown_long` always exists in Delta — that stops DirectLake from dropping the table (and the measure) on the next refresh. In the self-serve bridge, the GHG step runs 09 (cell1→cell2→cell3) scoped to the building; for the batch pipeline, keep cell3 in the run order after cell2.
