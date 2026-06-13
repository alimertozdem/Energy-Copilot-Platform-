# Client onboarding runbook — data → reports

A repeatable checklist for bringing **one new client (or one new building)** into EnergyLens
and producing their energy + ESG/compliance reports. Built for two cases:

- **Freelance / consulting** — you onboard a client's portfolio and deliver reports.
- **App users** — the same data shape applies when an existing customer adds a building.

First client: ~half a day while you learn the steps. After that, each client is **1–3 hours**
because the work is the same template + the same notebook run order.

> Honesty / positioning: deliverables are **reporting support** (ESRS-aligned, VSME, GHG
> Protocol framing, CRREM-indicative, EPC/GEG screening) — not audited filings or registered
> certificates. Sell "ESRS/VSME reporting support", not "CSRD-compliant audited filing".

---

## Step 1 — Collect the data (the template)

Send the client **`EnergyLens_Client_Data_Intake_Template.xlsx`** (same folder). They fill:

| Sheet | What | Needed |
|-------|------|--------|
| Buildings | one row per building (attributes + envelope + systems) | **always** |
| Energy readings | electricity consumption per building — **monthly totals are enough** (12 rows/yr) | **always** |
| Solar (optional) | PV generation/export | only if `has_pv` |
| Battery (optional) | battery SoC / power | only if `has_battery` |

**Auto-fetched — the client does NOT provide:** weather (OpenMeteo), electricity prices
(ENTSO-E), grid CO₂ intensity (ElectricityMaps).

Quality gate before you proceed: `building_id` identical across sheets · `true/false` lower-case ·
dates `YYYY-MM-DD HH:MM:SS` · numbers only (no units in cells) · green EXAMPLE rows deleted.

For the reports that matter most, make sure these are filled: **U-values + `primary_hvac_system`**
(GEG), **`energy_certificate`** (EPC), **`has_gas_heating` + `primary_hvac_system`** (Scope 1 /
CO₂ cost), **`has_pv` + `pv_capacity_kwp`** (solar).

## Step 2 — Convert the template to the 4 source CSVs

**Easiest — run the converter** (validates + writes the CSVs for you):

```
python scripts/onboarding/template_to_csv.py <filled_template.xlsx> <output_dir>
```

It checks required fields, confirms every energy/solar/battery `building_id` exists in
Buildings, skips the EXAMPLE row, and writes only the sheets that have data. On any problem
it prints the exact row + field and writes nothing — fix and re-run. (A worked example lives
in `docs/onboarding/sample/`: a filled pilot building + its generated CSVs.)

**Manual alternative** — export each sheet to a UTF-8 CSV with these **exact filenames**
(the bronze notebook reads them):

| Sheet | CSV filename |
|-------|--------------|
| Buildings | `building_master.csv` |
| Energy readings | `raw_energy_readings.csv` |
| Solar (optional) | `raw_solar_generation.csv` |
| Battery (optional) | `raw_battery_status.csv` |

(`raw_weather_data.csv` is a dev sample only — real weather comes from the OpenMeteo loader in Step 4.)

## Step 3 — Upload to Fabric

Put the CSVs in the lakehouse at **`Files/sample-data/`** (the dev-mode landing zone; the bronze
notebook's `MODE = "development"` reads from there). For production ingestion (Eventstream/API),
switch `MODE = "production"` — see `01_bronze_ingestion.py`.

## Step 4 — Run the notebooks in order

Run top-to-bottom; skip the conditional rows that don't apply.

| # | Notebook | Produces | When |
|---|----------|----------|------|
| 1 | `ingestion/01_bronze_ingestion.py` | bronze raw tables (energy, solar, battery, building_master) | always |
| 2 | `ingestion/02_openmeteo_weather_loader.py` | weather (HDD/CDD, irradiance) | always |
| 3 | `ingestion/03_entsoe_price_loader.py` | electricity prices | always |
| 4 | `ingestion/05_electricitymaps_co2_loader.py` | grid CO₂ intensity | always |
| 5 | `transformation/02_silver_transformation.py` | `silver_building_master`, clean energy/solar | always |
| 6 | `transformation/20_residential_model_p1.py` + `21_residential_ingestion.py` | residential unit data | residential only |
| 7 | `gold/03_gold_kpi_engine.py` | `gold_kpi_daily/monthly` (EUI, solar, CO₂, intensity) | always |
| 8 | `simulation/04_simulation_engine.py` | `gold_simulation_results` (HP / insulation feasibility) | always |
| 9 | `gold/09_ghg_scope_engine.py` | `gold_ghg_scope` (Scope 1/2/3) | always |
| 10 | `gold/10_crrem_pathway_loader.py` | CRREM pathway refs | always |
| 11 | `gold/11_hvac_analytics_engine.py` | HVAC analytics | always |
| 12 | `gold/30_residential_gold.py` | `gold_residential_unit_kpi` (climate-adj EUI, UVI) | residential only |
| 13 | `compliance/05_compliance_checker.py` | `gold_compliance_results` (GEG, EnEfG, EPBD…) | always |
| 14 | `recommendation/06_recommendation_engine.py` | `gold_recommendations` (retrofit measures, ROI) | always |
| 15 | `anomaly-detection/anomaly_detection.py` | `gold_anomaly_log` | optional |
| 16 | `forecasting/07_consumption_forecast.py` | forecasts | optional |
| 17 | battery (`simulation/12/14/15…`) + `iot/*` | battery + IoT gold | only if battery / IoT |

Tip: a Fabric **pipeline** that chains 1→14 makes this one click per client.

## Step 5 — Register in the app + bridge

So the web app (and per-customer RLS) see the buildings:

1. Create the client **organization** + invite their users (app: `/settings`, or admin `/admin`).
2. Create the **buildings** (app onboarding wizard `/onboarding`, or `POST /buildings`).
3. **Bridge** each building's app record to its Fabric `building_id` — set `fabric_building_id`
   (admin `/admin` → set `fabric_id`, or `bridge_orchestrator`). This is what links the report
   data to the customer account and the RLS scope.

## Step 6 — Verify the gold tables

Quick checks (Fabric SQL endpoint), replacing `B001`:

```sql
SELECT COUNT(*) FROM gold_kpi_daily            WHERE building_id='B001';
SELECT * FROM gold_ghg_scope                    WHERE building_id='B001';
SELECT geg_score,geg_status FROM gold_compliance_results WHERE building_id='B001';
SELECT COUNT(*) FROM gold_recommendations       WHERE building_id='B001';
```

If a report is empty, the cause is almost always a missing gold row for that building → re-run
the notebook that produces it (e.g. GEG empty → `05_compliance_checker`).

## Step 7 — Generate and deliver the reports

In the app:

1. **Building → Reports & documents** → pick a report; portfolio ESG reports open **scoped to that
   building** (`?building_id`). Or `/compliance` → pick a building in the slicer.
2. For the **narrative** reports (ESRS E-1, VSME) fill the company text in the editor
   (`/compliance` → *Edit ESRS / VSME narrative*) — the guided drafts prompt for exactly what to
   provide; quantitative parts are already auto-filled.
3. Export: **Print / Save as PDF**, or **⬇ Word** (ESRS / VSME) for an editable deliverable.

Deliverable set per client: ESRS E-1 · VSME (Basic / Comprehensive) · GHG Inventory · CRREM
stranding · GRESB readiness · CO₂ Cost Split · GEG conformity · EPC pre-assessment · EnEfG plan.

---

## Repeatability checklist (print this)

- [ ] Sent template, received clean Buildings + Energy (+ Solar/Battery) sheets
- [ ] Exported the 4 CSVs with the exact filenames
- [ ] Uploaded to `Files/sample-data/`
- [ ] Ran notebooks 1→14 (+ residential/battery/IoT if needed)
- [ ] Created org + buildings + set `fabric_building_id`
- [ ] Verified gold tables for each `building_id`
- [ ] Filled narrative, exported PDF/Word, delivered
