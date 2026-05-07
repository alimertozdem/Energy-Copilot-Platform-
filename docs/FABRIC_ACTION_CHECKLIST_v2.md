# Fabric Action Checklist — v2 (GHG + CRREM + HVAC + 2-Year Sample Data)

**Date:** 2026-04-17  
**Scope:** All changes made since v1 — covers GHG/CRREM fixes, sample data rewrite, HVAC analytics (notebook 11), and Page 7 DAX.  
**Estimated total time:** 60–90 minutes (first run in Trial capacity)

---

## 0. Prerequisites

Before starting, confirm:
- [ ] Microsoft Fabric workspace open (Trial or F-SKU)
- [ ] Lakehouse `EnergyLakehouse` exists with Bronze / Silver / Gold table structure
- [ ] Notebooks 00–10 already deployed and working from v1 setup
- [ ] Power BI Desktop (latest version) connected to semantic model via Direct Lake

---

## STEP 1 — Upload new sample data CSVs (2-year, 6-building set)

**Where:** Fabric workspace → EnergyLakehouse → Files section

**Files to upload** (from `sample-data/` folder in repo):
```
building_master.csv         ← 6 buildings (B001–B006), new columns: has_gas_heating, has_diesel_generator
energy_readings.csv         ← 2023-01-01 to 2024-12-31, 421,056 rows
solar_generation.csv        ← 350,880 rows
battery_storage.csv         ← 210,528 rows
weather_data.csv            ← 421,056 rows
```

**How:**
1. Open EnergyLakehouse → click **Files** (left panel)
2. Click **Upload → Upload files**
3. Select all 5 CSV files at once
4. Overwrite existing files when prompted → **OK**

**Why:** The old data was 3 buildings, 2024 only. The new generator creates 6 buildings × 2 years with `has_gas_heating` and `has_diesel_generator` columns that fix the `09_ghg_scope_engine` column error.

---

## STEP 2 — Run notebooks in order (Bronze → Silver → Gold)

Open each notebook in Fabric, click **Run all**.

### 2a. Reference Data + Bronze Ingestion

| Order | Notebook | Input | Output |
|-------|----------|-------|--------|
| 1 | `00_reference_data_loader` | Files/building_master.csv | bronze_building_master |
| 2 | `01_bronze_ingestion` | Files/energy_readings.csv + others | bronze_energy_readings, bronze_solar, bronze_battery, bronze_weather |

Run these **sequentially** (00 before 01).

### 2b. Silver Transformation

| Order | Notebook | Input | Output |
|-------|----------|-------|--------|
| 3 | `02_silver_transformation` | bronze_* tables | silver_energy_readings, silver_building_master, silver_solar, silver_weather |

**Verify after run:** Open silver_building_master → confirm columns `has_gas_heating` and `has_diesel_generator` are present. If they are missing, the Bronze run did not pick up the new CSV — re-upload and re-run step 2a.

### 2c. Gold Layer — run in this exact order

| Order | Notebook | Depends on | Output table |
|-------|----------|------------|--------------|
| 4 | `03_kpi_engine` | silver_energy_readings + silver_building_master | gold_kpi_daily, gold_kpi_monthly |
| 5 | `09_ghg_scope_engine` | gold_kpi_daily + silver_building_master | gold_ghg_scope |
| 6 | `10_crrem_pathway_loader` | (static, no dependency) | gold_crrem_pathway |
| 7 | `11_hvac_analytics_engine` | gold_kpi_daily + silver_building_master | gold_hvac_analytics |
| 8 | `anomaly_detection` | gold_kpi_daily | gold_anomalies |
| 9 | `04_simulation_engine` | gold_kpi_daily | gold_simulation_results |
| 10 | `05_compliance_checker` | gold_simulation_results | gold_compliance_results |
| 11 | `06_recommendation_engine` | gold_compliance_results | gold_recommendations |
| 12 | `07_consumption_forecast` | gold_kpi_daily + gold_occupancy_profile | gold_forecast |
| 13 | `08_occupancy_prediction` | silver_energy_readings | gold_occupancy_profile |

**Tip:** Notebooks 10 (CRREM) can run in parallel with 09 (GHG) — they have no dependency on each other. In Fabric, open both in separate tabs and click Run All on each.

**Expected run times (Trial F2 capacity):**
- KPI engine: ~8–12 min (421k rows × 2 years)
- GHG engine: ~3–5 min
- HVAC engine: ~4–6 min
- Forecast: ~10–15 min (Prophet per building)

---

## STEP 3 — Verify Gold tables exist

In EnergyLakehouse, expand **Tables** section. Confirm these tables are present:

```
gold_kpi_daily            ✓ (existing)
gold_kpi_monthly          ✓ (existing)
gold_anomalies            ✓ (existing)
gold_simulation_results   ✓ (existing)
gold_compliance_results   ✓ (existing)
gold_recommendations      ✓ (existing)
gold_forecast             ✓ (existing)
gold_occupancy_profile    ✓ (existing)
gold_ghg_scope            ← NEW (from notebook 09)
gold_crrem_pathway        ← NEW (from notebook 10)
gold_hvac_analytics       ← NEW (from notebook 11)
```

If any new table is missing → re-run the corresponding notebook and check for errors in the output cell.

---

## STEP 4 — Deploy updated pipeline JSON files

**Where:** Fabric workspace → Data Factory → Pipelines

### 4a. Update `03_gold_analytics_pipeline`
1. Open pipeline `03_gold_analytics_pipeline` in edit mode
2. Import/update from `pipelines/batch/03_gold_analytics_pipeline.json`
3. Confirm new activity `Run_HVAC_Analytics` appears after `Run_GHG_Scope_Engine`
4. Save and validate

### 4b. Verify `04_master_orchestrator` (no structural change needed)
- Master orchestrator calls `03_gold_analytics_pipeline` as a sub-pipeline
- No changes needed — just verify it still resolves correctly
- Check version annotation: should show `version:2.1-with-ghg-crrem-occupancy-forecast`

---

## STEP 5 — Power BI Desktop: Add new tables to semantic model

Open your `.pbix` file in Power BI Desktop.

### 5a. Add `gold_ghg_scope` table
1. **Home → Transform data → Get data → Microsoft Fabric (Direct Lake)**  
   OR: **Modeling → New table** if manually defining
2. Select table `gold_ghg_scope` from EnergyLakehouse
3. Load table

**Columns you need:**
- `building_id`, `year_month`, `scope1_tco2`, `scope2_location_tco2`, `scope2_market_tco2`, `scope3_estimated_tco2`, `total_ghg_tco2`, `carbon_intensity_kgco2_m2`, `grid_emission_factor_kgco2_kwh`

### 5b. Add `gold_crrem_pathway` table
1. Load table `gold_crrem_pathway` from EnergyLakehouse
2. Columns: `building_type`, `country_code`, `pathway_year`, `carbon_budget_2c_kgco2_m2_yr`, `carbon_budget_15c_kgco2_m2_yr`

### 5c. Add `gold_hvac_analytics` table
1. Load table `gold_hvac_analytics` from EnergyLakehouse
2. Columns: `building_id`, `month_start`, `heating_kwh`, `cooling_kwh`, `ventilation_kwh`, `hvac_total_kwh`, `u_composite`, `insulation_score`, `scop_rolling`, `hvac_efficiency_score`, `heat_loss_kwh_m2`, `renovation_priority`, `system_type`

---

## STEP 6 — Power BI Desktop: Create relationships

In **Model view**, create these relationships (drag-and-drop or Manage Relationships):

### New relationships for gold_ghg_scope:
| From | To | Cardinality | Direction | Active |
|------|----|-------------|-----------|--------|
| `gold_ghg_scope[building_id]` | `silver_building_master[building_id]` | Many → One | Single | ✅ Yes |
| `gold_ghg_scope[year_month]` | `'Date'[Date]` | Many → One | Single | ✅ Yes |

> **Note on year_month:** `year_month` is a date column (first day of each month, e.g. `2024-01-01`). It connects to the Date table. In the `year_month → Date[Date]` relationship, Power BI will show month-level data naturally because each GHG row represents one month.

### New relationships for gold_crrem_pathway:
- **No direct relationship** — CRREM uses `LOOKUPVALUE` in DAX (composite key: building_type + country_code + year). Do NOT create a relationship for this table.

### New relationships for gold_hvac_analytics:
| From | To | Cardinality | Direction | Active |
|------|----|-------------|-----------|--------|
| `gold_hvac_analytics[building_id]` | `silver_building_master[building_id]` | Many → One | Single | ✅ Yes |
| `gold_hvac_analytics[month_start]` | `'Date'[Date]` | Many → One | Single | ✅ Yes |

---

## STEP 7 — Import DAX measures

### 7a. GHG + CRREM measures (from `12_dax_v7_ghg_crrem.dax`)
If not already imported from previous session:
1. Open DAX Studio (or use Power BI Desktop Modeling tab)
2. Copy/paste each measure from `semantic-model/12_dax_v7_ghg_crrem.dax`
3. Place all measures in a measure table named `_GHG Measures`

**Critical check — DATEADD fix:**  
Find measures `[Scope 1 PY tCO2]`, `[Scope 2 Location PY tCO2]`, `[Scope 3 PY tCO2]`, `[Total GHG PY tCO2]`.  
They must use `DATEADD('Date'[Date], -1, YEAR)` — NOT `DATEADD(gold_ghg_scope[year_month], -1, YEAR)`.  
If the old version is present, delete and re-paste from the v7 file.

### 7b. HVAC + Envelope measures (from `13_dax_v8_hvac_envelope.dax`) ← NEW
1. Create a new measure table named `_HVAC Measures`
2. Copy/paste all measures from `semantic-model/13_dax_v8_hvac_envelope.dax`
3. Sections to import:
   - A: HVAC Energy Disaggregation (8 measures)
   - B: HVAC Efficiency & COP (7 measures)
   - C: Envelope & Insulation (10 measures)
   - D: Renovation Priority & System Labels (5 measures)
   - E: Technology Benchmarks (6 measures)
   - F: KPI Cards (8 measures)

**Total new measures for Page 7: 44**

---

## STEP 8 — Build Page 7: HVAC & Envelope Intelligence

In Power BI Desktop, add a new page named **"7 — HVAC & Envelope"**.

### Layout: Top row — KPI Cards (6 cards across)

| Card | Measure | Good/Bad direction |
|------|---------|-------------------|
| Avg Insulation Score | `[Card: Avg Portfolio Insulation Score]` | Higher = better (target ≥ 75) |
| Avg Heat Pump COP | `[Card: Avg Portfolio COP]` | Higher = better (target ≥ 3.0) |
| HVAC Share of Energy | `[Card: HVAC Share of Total Energy]` | Context-dependent |
| Buildings Needing Renovation | `[Card: Buildings Needing Renovation]` | Lower = better |
| Gas Boiler Risk Count | `[Card: Gas Boiler Risk Count]` | Lower = better |
| HP Portfolio Penetration | `[Card: HP Portfolio Penetration]` | Higher = better |

### Layout: Middle left — Insulation Profile

**Visual type: Clustered bar chart**
- Axis: `silver_building_master[building_name]`
- Values: `[U Wall Actual]`, `[U Roof Actual]`, `[U Window Actual]`
- Add reference line at each GEG 2023 standard: Wall=0.24, Roof=0.20, Window=1.30
- Title: "U-Value Profile vs GEG 2023 Standard"

### Layout: Middle center — HVAC Energy Split

**Visual type: 100% Stacked bar chart (monthly)**
- Axis: `'Date'[Month Year]` (or `gold_hvac_analytics[month_start]`)
- Values: `[Heating Energy kWh]`, `[Cooling Energy kWh]`, `[Ventilation Energy kWh]`
- Legend: Heating / Cooling / Ventilation
- Title: "Monthly HVAC Energy Breakdown"

### Layout: Middle right — COP Trend

**Visual type: Line chart**
- Axis: `'Date'[Month Year]`
- Line 1: `[SCOP Rolling 3M]` (actual)
- Line 2 (constant reference): `[Benchmark COP ASHP Market 2024]` = 3.1
- Line 3 (constant reference): 3.0 (minimum target)
- Title: "Heat Pump SCOP — 3-Month Rolling vs Benchmark"

### Layout: Bottom left — Renovation Priority Matrix

**Visual type: Matrix table**
- Rows: `silver_building_master[building_name]`
- Columns: `[System Type Display]`, `[Insulation Rating Label]`, `[Renovation Priority Icon]`, `[HVAC Efficiency Label]`, `[Insulation Score]`, `[COP Rating Label]`
- Conditional formatting: `[Renovation Priority Icon]` → background red/yellow/green

### Layout: Bottom center — Heat Loss vs Benchmark

**Visual type: Scatter chart**
- X-axis: `[Insulation Score]`
- Y-axis: `[Heat Loss kWh m2 Annual]`
- Size: `[HVAC Total kWh]`
- Tooltip: building_name, system_type, renovation_priority
- Title: "Insulation Score vs Annual Heat Loss Intensity"

### Layout: Bottom right — GEG Compliance Summary

**Visual type: Table**
- Columns: `silver_building_master[building_name]`, `[GEG Compliance Wall]`, `[GEG Compliance Roof]`, `[GEG Compliance Window]`, `[Thermal Bridge Penalty]`
- Title: "GEG 2023 Envelope Compliance Checklist"

---

## STEP 9 — Slicers for Page 7

Add these slicers (top of page, horizontal):
1. **Building Name** → `silver_building_master[building_name]` (multi-select dropdown)
2. **Building Type** → `silver_building_master[building_type]` (button slicer)
3. **Date Range** → `'Date'[Date]` (between slider)
4. **System Type** → `[System Type Label]` from gold_hvac_analytics (button slicer)

---

## STEP 10 — Final validation checklist

### Data validation:
- [ ] `gold_ghg_scope` has rows for all 6 buildings × 24 months
- [ ] `gold_crrem_pathway` has rows for all 5 building types × countries × years 2020–2050
- [ ] `gold_hvac_analytics` has rows for all 6 buildings × 24 months
- [ ] `[Heating Energy kWh]` > 0 for winter months in German buildings (B001, B003)
- [ ] `[COP Monthly Actual]` returns BLANK for B002 (gas-only building — no heat pump)
- [ ] `[Insulation Score]` for B002 (1998, high U-values) < 50 (poor)
- [ ] `[Insulation Score]` for B003 (2018 logistics, renovated) > 70 (good)

### DAX validation:
- [ ] `[Total GHG PY tCO2]` returns values (not BLANK) when Date slicer spans 2 years
- [ ] `[CRREM Pathway 2C kgCO2 m2 yr]` returns values for at least one building in scope (uses LOOKUPVALUE)
- [ ] `[Card: Buildings Needing Renovation]` returns a number (not BLANK or error)

### Pipeline validation:
- [ ] Run `03_gold_analytics_pipeline` manually — all stages succeed
- [ ] `Run_HVAC_Analytics` appears in execution log with Succeeded status
- [ ] `04_master_orchestrator` scheduled trigger still set to 02:00 UTC daily

---

## STEP 11 — Schedule trigger verification

1. Open `04_master_orchestrator` pipeline
2. Click **Trigger → Manage triggers**
3. Verify `DailySchedule_0200_UTC` is:
   - Status: **Active**
   - Time: **02:00 UTC** (= 04:00 Berlin / 05:00 Istanbul)
   - Recurrence: **Daily**

---

## Summary of all new files deployed in this session

| File | Type | Purpose |
|------|------|---------|
| `sample-data/generate_sample_data.py` | Python | Rewrote — 6 buildings, 2 years, real columns |
| `sample-data/*.csv` | CSV | Re-generated 5 CSV files |
| `notebooks/gold/09_ghg_scope_engine.py` | PySpark | Fixed column error, added proxy logic |
| `notebooks/gold/11_hvac_analytics_engine.py` | PySpark | **NEW** — HVAC disaggregation + envelope analytics |
| `pipelines/batch/03_gold_analytics_pipeline.json` | JSON | Added Run_HVAC_Analytics activity, v2.2 |
| `semantic-model/12_dax_v7_ghg_crrem.dax` | DAX | GHG + CRREM measures (DATEADD fix) |
| `semantic-model/13_dax_v8_hvac_envelope.dax` | DAX | **NEW** — 44 HVAC + envelope measures |
| `docs/FABRIC_ACTION_CHECKLIST_v2.md` | Markdown | This file |

---

*Energy Copilot Platform — Microsoft Fabric — v2.2*
