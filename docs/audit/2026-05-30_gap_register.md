# EnergyLens — Report Audit & Gap Register
**Date:** 2026-05-30 · **Author:** Senior technical copilot (audit pass) · **Status:** IN PROGRESS

## Purpose
Systematic audit of every report page (calculation engines → DAX → visuals) to confirm it meets
freelance-market demand — above all the **CSRD / ESRS E1 / GHG Protocol** niche that the freelance
strategy positions as PRIMARY. Output = prioritized gap list to fix **before** writing the final
technical documentation (PDF).

## Severity legend
- **P0 — Credibility-breaking.** A competent ESG consultant / energy auditor / DP-600 reviewer would
  catch this in minutes. Must fix before selling.
- **P1 — Important.** Methodology or consistency weakness; defensible short-term but should be closed.
- **P2 — Polish.** Cosmetic, naming, or nice-to-have.

## Coverage tracker
- [x] Cross-cutting (data lineage & consistency)
- [x] Page 1–2 — core KPI engine (`03_gold_kpi_engine.py`)
- [x] Page 6 — sustainability stack (`09_ghg_scope_engine.py`, `10_crrem_pathway_loader.py`, `01_epc_ratings_loader.py`)
- [ ] Page 3 — anomaly (`03` §8 + `anomaly-detection/anomaly_detection.py`)
- [ ] Page 4 — forecast (`07_consumption_forecast.py`)
- [ ] Page 5 — recommendation / compliance / occupancy (`06`, `05`, `08`)
- [ ] Page 7 — HVAC (`11_hvac_analytics_engine.py`)
- [ ] Page 8 — IoT (`11b_iot_processing.py`, `00_iot_adapter_framework.py`)
- [ ] Page 9 — battery (`12`–`15`, `16` loaders)
- [ ] DAX measures (latest version per page)
- [ ] Visuals / layout vs sector expectations

---

## EXECUTIVE SUMMARY (read first)

**Verdict.** The platform is **engineering-strong**: clean medallion architecture, idempotent Delta MERGE, schema-adaptive notebooks, a genuinely good multi-country regulatory-compliance engine, real NPV/IRR with inflation+salvage, full EU-2023/1542 battery fields, and per-building Prophet forecasting. It is **not yet "auditable, CSRD-grade"** — which is the exact phrase the freelance positioning sells. The credibility-breakers cluster in the **sustainability niche you intend to lead with**, so your instinct to check Page 6 first was right.

**The 6 things that would lose you a knowledgeable ESG/energy client — fix before selling Page 6 as CSRD:**
1. **No single source of truth** for emission factors / tariffs / grid CO₂. The TR grid factor alone appears as **0.430 / 0.442 / 0.450** across four files; electricity price as €0.30 / 0.28 / 0.22. "Regulator-grade lineage" is the pitch — this breaks it. (A1–A3, F2–F3, I2)
2. **Scope 3 = flat 8 % of (S1+S2)** (D1) and **market-based Scope 2 = location-based** (D2). Both are indefensible to an ESG reviewer; ESRS E1-6 needs real, dual-method numbers.
3. **EPC portfolio score is a plain average, not area-weighted** (D8/L2) — the product commits the exact "audit failure" your own study guide calls out.
4. **CRREM stranding** compares Scope-2-only intensity to a Scope 1+2 pathway (understates risk), and the **base DAX references non-existent CRREM columns** (D3/L3/L1).
5. **Two anomaly engines write the same table** with conflicting taxonomies → Page 3 is non-deterministic (C1).
6. **DAX lives in 68 patch files** with a stale/broken base (L1); **demo-building identities conflict** across notebooks — B003/B005 each have three cities/types (A4/I1).

**Already strong / sellable now:** Pages 1–5 (especially the compliance engine), the battery financial *model* structure, forecasting, occupancy. P3 (Fabric Audit) and P4 (PBI Tune-up) need no data fixes.

**Recommended fix sequence (BMAD, one module at a time — approval-gated):**
0. **Reference layer first** — one `ref_factors` / `ref_tariffs` source of truth. Highest leverage; unblocks A1–A3, F2–F3, H1, I2.
1. **Page 6 Sustainability** end-to-end — D1, D2, D4, L2, L3, and relabel the "CSRD score." Make the money page genuinely auditable.
2. **Page 3 anomaly** — one engine, one frozen taxonomy (C1–C5).
3. **DAX consolidation** — collapse 68 files into one authoritative model (L1).
4. **Pages 1–2 / 4 / 5** — climate-adjusted EUI method (B1), tariff wiring (A3), forecast `F`-import bug (E1).
5. **Pages 7–9** — HVAC English labels + "modeled" framing (G1–G2), battery ROI realism + lineage (I3–I4).
6. **Demo data** — one canonical building registry (A4/I1).

Phase 3 (per-visual technical documentation, PDF) is written **against the fixed state**, not the current one.

---

## A. CROSS-CUTTING — data lineage & single-source-of-truth
> These matter most: the freelance pitch sells **"auditable Scope 1/2/3 with regulator-grade data
> lineage."** Lineage gaps here directly undercut the headline value proposition.

### A1 [P0] Grid emission factor has three sources of truth — and they disagree
- **Evidence:**
  - `03_gold_kpi_engine.py` reads `silver_building_master.emission_factor_kg_kwh` (per-building column) for Scope-2 CO₂ (L227, L373).
  - `09_ghg_scope_engine.py` uses a **hardcoded Python dict** (`GRID_EMISSION_FACTORS`): DE 0.380, **TR 0.430**, AT 0.158, NL 0.290, FR 0.052, PL 0.720 (L160-168).
  - `docs/` (data-dictionary, stated-assumptions, kpi-formulas) all say **TR 0.442** and reference a `silver.grid_emission_factors` table.
- **So:** TR is `0.430` in the engine but `0.442` everywhere in the docs; the documented reference table `silver.grid_emission_factors` is not actually the source the engines read.
- **Why it matters:** An auditor's first question is "where does this factor come from and is it consistent?" Three divergent sources = immediate red flag.
- **Fix:** One reference table `silver_grid_emission_factors (country, year, factor, source, url)`; every engine reads from it. Reconcile TR to a single sourced value. Stamp `source` + `url` on output.

### A2 [P0] No single emission-factor / tariff reference table actually wired in
- The data model documents `silver.grid_emission_factors`, `silver.electricity_tariffs`, but engines use hardcoded constants / building-master columns instead. The documented lineage is aspirational, not real.
- **Fix:** Build and load the reference tables; refactor engines to join them. This is the literal "row-level lineage from raw factor to disclosed kg CO₂" selling point.

### A3 [P1] Electricity tariff hardcoded and not country-specific
- `03_gold_kpi_engine.py` L119: `ELECTRICITY_TARIFF_EUR_KWH = 0.30` applied to **all** buildings (L568). Docs say DE ≈ €0.22, TR ≈ €0.08. TR buildings are billed at German rates; cost KPIs are wrong for non-DE.
- **Fix:** Join `silver_electricity_tariffs` by country (+ time-of-use where available).

### A4 [P1] Demo-building identities inconsistent across notebooks
- `01_epc_ratings_loader.py`: B005 = "Berlin Healthcare DE". `10_crrem_pathway_loader.py` comment: B005 = "Frankfurt Klinikum". EPC says B003 = Vienna Hotel; CRREM comment says B003 = "Wien Grand Hotel Delta". Page-7 memory adds B007–B010.
- **Why it matters:** In a demo, a sharp prospect will notice a building that changes city/name between pages.
- **Fix:** One canonical building registry; all notebooks/comments reference it.

### A5 [P1] Schema drift — documented column names ≠ engine output
- `data-dictionary.md` `gold.kpi_daily` lists `climate_adjusted_eui`, `base_load_kw`, `co2_consumption_kg`. The engine outputs `hdd_normalized_eui`, **no** `base_load_kw`, and `co2_emissions_kg`. `09_ghg_scope` even reads `co2_emissions_kg` from kpi_daily (works), but the dictionary is wrong.
- **Fix:** Reconcile the data dictionary to the real Gold schema (or rename engine columns). The data dictionary is a client-facing artifact — it must match reality.

---

## B. PAGE 1–2 — Portfolio Overview / Building Deep-Dive (`03_gold_kpi_engine.py`)

### B1 [P0] "Climate-adjusted EUI" is not the documented method, and ignores cooling
- **Documented** (kpi-formulas.md): `EUI_adj = EUI × (Reference HDD+CDD / Actual HDD+CDD)` — a ratio normalization using **both** HDD and CDD.
- **Implemented** (L550-555): `hdd_normalized_eui = eui_kwh_m2 / hdd_day` — a simple division by HDD only, no reference baseline, **CDD entirely ignored** (cdd_day is summed but never used for normalization).
- **Why it matters:** This is the EnPI / ISO 50001 normalization clients explicitly ask about. The implemented metric is dimensionally different (kWh/m² per degree-day) and not comparable to the benchmarks in the docs. Cooling-dominated buildings (data centres, southern climates) are mis-normalized.
- **Fix:** Implement the ratio method with a stated reference HDD+CDD baseline; include CDD.

### B2 [P1] EUI is daily (kWh/m²/day); benchmarks are annual (kWh/m²/yr)
- Engine computes daily `eui_kwh_m2` (L540). Benchmarks (<80 / 80–130 / …) are annual. Comparison only works if DAX sums to annual (or annualizes a partial period). **Must verify in DAX audit** — a missing ×365 / period-annualization would make the benchmark badge meaningless.

### B3 [P1] Peak demand assumes 15-min data; overstates for hourly Tier-1
- `peak_demand_kw = MAX(consumption_kwh) × 4` (L269) converts 15-min kWh→kW. For a Tier-1 building delivering **hourly** kWh, the single hourly value × 4 overstates peak ~4×. Demand-charge savings (a headline number) would be inflated.
- **Fix:** Derive the ×N factor from actual reading interval, or compute kW from interval length.

### B4 [P2] Cost & savings use the single hardcoded tariff (see A3); no demand charge
- `estimated_cost_eur = net_grid × 0.30` only. No demand-charge component, although the docs' cost formula includes `peak_demand_kw × demand_charge_€/kW/month`. Page-1 "total cost" understates the structure clients actually pay.

---

## D. PAGE 6 — Sustainability / ESG (`09_ghg_scope_engine.py`, `10_crrem_pathway_loader.py`, `01_epc_ratings_loader.py`)
> Highest commercial stakes — this is the PRIMARY niche (CSRD Quickstart €3.2–4.5k).

### D1 [P0] Scope 3 = flat 8% of (Scope 1 + Scope 2)
- `09` L176, L343-352: `scope3_estimated = (scope1 + scope2_location) × 0.08`.
- **Why it matters:** For real building portfolios, Scope 3 (esp. Cat. 13 downstream leased assets, Cat. 1 purchased goods / embodied carbon) is frequently the **largest** bucket — often multiples of Scope 1+2, not 8% of it. An ESG consultant will reject an 8% flat ratio instantly. ESRS E1-6 requires Scope 3 by material category.
- **Fix:** Either (a) model the material Scope 3 categories explicitly from activity data, or (b) clearly label it "indicative screening estimate — not disclosure-grade" and never present it as ESRS-ready. Recommend a category-based Scope-3 input table.

### D2 [P0] Market-based Scope 2 = location-based (no differentiation)
- `09` L336-339: `scope2_market = scope2_location`. The study guide actively **sells** market-based Scope 2 as a differentiator ("most companies forget this and get flagged").
- **Why it matters:** ESRS E1-6 mandates **both** methods reported separately. Right now the two numbers are identical → the product does not actually do what the pitch claims.
- **Fix:** Add a contract/supplier table (residual mix or green-tariff EF); compute market-based from it. Even a per-building `contract_ef` column makes the dual disclosure real.

### D3 [P0 — CONFIRMED via DAX] CRREM stranding compares Scope-2-only intensity to a Scope 1+2 pathway
- Verified: the measure on the CRREM line is `Carbon Intensity kgCO2 m2 yr = [Avg Carbon Intensity kg m2] × 365`, and that daily intensity = `co2_emissions_kg / area`, where `co2_emissions_kg` (from `03`) = `net_grid × EF` = **Scope 2 location only** — Scope 1 gas excluded, Scope 3 excluded.
- CRREM pathway (loader B2) = **Scope 1+2**. So the building line omits Scope 1 → looks better than reality → **understates** stranding (direction corrected from my first hypothesis). See L1/L3.
- **Fix:** Build a Scope 1+2 intensity measure for the CRREM comparison; keep Scope 3 out (CRREM excludes it).

### D4 [P1] Refrigerant / fugitive Scope 1 excluded — but pitched as a "power move"
- `09` assumption A5 excludes refrigerant leakage. Study guide §19 recommends saying "Refrigerant leaks are Scope 1 and routinely missed" to clients. Gap between pitch and product if a prospect probes.
- **Fix:** Add a `silver_refrigerant_log` (gas type, kg recharged, GWP) → Scope 1 fugitive. Even optional, it backs the talking point.

### D5 [P1] Scope 1 gas derived from electricity (25% heating proxy)
- `09` L287-304: when `has_gas`, gas = `monthly_consumption_kwh × 0.25 / 10.55 / 0.85 × 2.04`. Heating share proxied from **electricity**, then converted to m³. Defensible only as a screening estimate; real gas-meter data needed for disclosure.
- **Fix:** Prefer actual gas-meter table; keep proxy as labelled fallback.

### D6 [P1] CRREM pathways are representative/estimated, not official tool data
- `10` header + B1–B5: values are "temsili (representative)"; TR & several EU curves flagged `data_source = "estimated"`. Fine for demo; must not be presented to a client as official CRREM v2 output.
- **Fix:** Load official CRREM v2 pathway export for the building types/countries you actually sell into; keep `data_source` honest.

### D7 [P1] `10_crrem_pathway_loader.py` ignores the dynamic Tables/ prefix pattern
- Uses hardcoded `OUTPUT_TABLE = "Tables/gold_crrem_pathway"` (L69) and `.replace("Tables/","")`. Every other gold notebook uses `_resolve_tables_prefix()` to support schema-enabled lakehouses (`Tables/dbo/`). On a schema-enabled lakehouse this notebook can write to the wrong place / fail.
- **Fix:** Adopt the `_resolve_tables_prefix()` pattern (consistency with `09`, `07`).

### D8 [P1 — CONFIRMED via DAX] EPC portfolio score is a PLAIN average, not area-weighted
- Verified live measure: `Avg EPC Score kWh m2 = AVERAGE(silver_epc_ratings[epc_score_kwh_m2])` (`16_dax_v11_…:254`) — an unweighted mean across buildings.
- The study guide sells the **opposite** ("area-weighted EPC … not average of building averages — a common audit failure"). The product currently commits exactly that failure on the flagship page.
- **Fix:** Area-weight: `DIVIDE(SUMX(epc, area × score), SUMX(epc, area))` via `conditioned_area_m2`. (See L2.)

### D9 [P2] Two CO₂ numbers per building that won't reconcile
- EPC certificate carries `co2_kg_m2_year` (e.g. B001 = 65.4); the GHG/KPI engine computes its own carbon intensity from consumption. If a visual shows both, they will differ (different scope, year, method). Decide which is authoritative and label the other.

---

## C. PAGE 3 — Anomaly Detection (`03` §8 + `anomaly-detection/anomaly_detection.py`)

### C1 [P0] TWO engines write the SAME table with different taxonomies, schemas, and ID formats
- `03_gold_kpi_engine.py` §8 writes `gold_anomaly_log` with **6 types**: `CONSUMPTION_SPIKE, NIGHT_OVERCONSUMPTION, SOLAR_PR_DROP, BATTERY_OVERDISCHARGE, BATTERY_OVERCHARGE, DATA_QUALITY_GAP`; **lowercase** severity (`"high"`); `anomaly_id = sha2(...)`; only `description_en`.
- `anomaly_detection.py` **also** writes `gold_anomaly_log` (PATHS["anomalies"]) with **7 different types**: `CONSUMPTION_SPIKE, COP_DEGRADATION, SOLAR_UNDERPERFORM, BATTERY_IDLE, HIGH_CARBON_INTENSITY, DATA_GAP, AFTER_HOURS_WASTE`; **UPPERCASE** severity; `anomaly_id = "bid__type__date"`; full `description_en/de/tr` + `recommended_action_en`. `BACKFILL_MODE=True` → **overwrites** the table.
- **So:** whichever notebook runs last wins; the type set, severity casing, ID scheme and column set all differ. Page 3 visuals can't depend on a stable schema.
- **Why it matters:** The anomaly page is a core demo asset. A taxonomy that changes depending on run order is indefensible.
- **Fix:** Pick ONE anomaly engine (recommend `anomaly_detection.py` — richer, trilingual, resolved-status logic). Remove §8 anomaly block from `03` (keep it KPI-only). Freeze one type vocabulary.

### C2 [P1] Anomaly taxonomy disagrees across FOUR sources
- `03` (6 types), `anomaly_detection.py` (7 types), `kpi-formulas.md` (A1–A7: includes `base_load_high`, `holiday_overconsumption`, `insulation_degradation`, `cop_drop`), `data-dictionary.md` (yet another list). None fully match. Memory note says "4 active in production."
- **Fix:** One canonical list, reflected in code + both docs. Map each to an ESRS/operations rationale.

### C3 [P1] COP & carbon anomalies are proxies, and carbon thresholds duplicate CRREM
- `COP_DEGRADATION` has no real COP input — it infers from heating EUI (`eui > 8/cop_rated × 1.5`). Defensible only as screening.
- `HIGH_CARBON_INTENSITY` uses a **hardcoded** `CARBON_REF_DAILY` dict (Office 47/365…) — a *second* copy of CRREM numbers separate from `gold_crrem_pathway`. Same single-source-of-truth problem as A1.
- **Fix:** Drive carbon anomaly thresholds from `gold_crrem_pathway`; label COP anomaly "proxy" until real COP telemetry exists (Page 7 has it — bridge it).

### C4 [P1] Boolean compared to string literal — may silently never fire
- `anomaly_detection.py` filters `col("has_heat_pump") == "true"` / `== "true"` (L557, L608, L660) on columns that are real booleans in `gold_kpi_daily`. This relies on implicit cast; if it resolves false, COP/solar/battery anomalies silently produce **zero** rows.
- **Fix:** Use `col("has_heat_pump") == True` (or `isNotNull & col(...)`). Verify each rule actually emits on demo data.

### C5 [P2] Cosmetic inconsistencies
- Severity casing differs between engines (lowercase vs UPPERCASE) — visuals/DAX filtering by severity will mismatch. Final summary prints "Çıktı tablosu: Tables/gold_anomalies" while it writes `gold_anomaly_log`.

---

## F. PAGE 5 — Decision Support (`05_compliance_checker.py`, `06_recommendation_engine.py`, `08_occupancy`)
> **Strong overall.** Multi-country regulatory scoring (DE GEG/EnEfG/EEG, AT OIB-RL6/EAG, NL Energielabel/Wet milieubeheer, TR BEP-TR, EU EPBD) + BEHG CO₂-Preis cost + grant matching + trilingual recommendations is a genuine differentiator. Issues are about labeling and constant-sprawl, not structure.

### F1 [P1] "CSRD score" is mislabeled — CSRD is a disclosure directive, not a kg/m² threshold
- `05` computes a `csrd_score` purely from carbon intensity vs EU-Taxonomy-style thresholds (<10 / <20 / <40 kg CO₂/m²/yr). CSRD compliance is about **disclosure completeness** (double materiality, ESRS datapoints), not a performance cutoff.
- **Why it matters:** This is the PRIMARY niche. An ESG consultant will say "CSRD doesn't set a 10 kg/m² limit." Mislabeling here undercuts the exact expertise we're selling.
- **Fix:** Rename to `eu_taxonomy_score` / `carbon_intensity_score`. Reserve "CSRD readiness" for an actual disclosure-completeness checklist (scopes present, both Scope-2 methods, material Scope-3, lineage).

### F2 [P1] Gas CO₂ computed two different ways across engines
- `05` uses `GAS_CO2_KG_PER_KWH = 0.202` (HHV basis). `09_ghg_scope` uses `2.04 kg/m³` (LHV basis). Same fuel, two methods → gas carbon won't reconcile between the compliance cost page and the GHG page.
- **Fix:** One gas emission constant + basis, centralized.

### F3 [P1] Electricity price exists in ≥4 values across the codebase
- `03` €0.30; `05`/`06` DE €0.28, TR €0.10, AT €0.25, NL €0.26; `stated-assumptions` DE €0.22, TR €0.08. No single tariff source. Cost, payback, NPV and ROI all shift depending on which file you read.
- **Fix:** Central `ref_tariffs` table (extends A3); every engine joins it.

### F4 [P1] Page 5 depends on `gold_simulation_results` + `ref_*` tables — verify they exist
- `05` and `06` read `gold_simulation_results`, `ref_building_type_profiles`, `ref_simulation_inputs`. `06` degrades gracefully (financial scores → 0) if simulation is missing — which would silently make recommendations compliance-only. Confirm `04_simulation_engine.py` + `00_reference_data_loader.py` populate these.

### F5 [P2] CO₂ conversion constants proliferate inside rule-of-thumb actions
- `06` uses 0.35 and 0.4 kg CO₂/kWh in different actions; battery CO₂ proxied via €0.30. Fine for an estimator, but centralize + cite for the "auditable" story.

---

## E. PAGE 4 — Forecasting (`07_consumption_forecast.py`)
> **Good design.** Per-building Prophet, HDD/CDD + occupancy regressors, 80% interval, MAPE, graceful degradation, and it uses the dynamic `_resolve_tables_prefix()` pattern (the model CRREM should copy). Issues are narrow.

### E1 [P1] Latent crash: `F.dayofweek` used before `F` is imported (only when occupancy table is present)
- L280 calls `F.dayofweek("date")` inside the `OCCUPANCY_AVAILABLE` branch, but `from pyspark.sql import functions as F` is at L301 — *after* that block. When `gold_occupancy_profile` exists with valid rows, the forecast notebook raises `NameError` and falls into the except → neutral 0.5 occupancy. So the occupancy regressor likely **never actually applies**; it's silently bypassed.
- **Fix:** Move the `import functions as F` above the read section; verify occupancy regressor truly feeds the model.

### E2 [P2] MAPE is in-sample, presented as model accuracy
- Accuracy is computed by predicting the training set itself (L446-452). In-sample MAPE flatters the model. For a client number, use Prophet `cross_validation` (rolling-origin) or label it "in-sample fit," not "accuracy."

### E3 [P2] Confidence band is computed but reportedly not shown
- `lower_bound_kwh` / `upper_bound_kwh` are stored, yet Page 4's band is in the v54 backlog (deferred). Wiring the existing band into the visual is free credibility for a forecast page — prospects expect uncertainty shown.

---

### F6–F7 [P2] Page 5 occupancy (`08_occupancy_prediction.py`) — solid, minor notes
- **Good:** ASHRAE-derived archetypes per building type, two-step hybrid (base + consumption-min/max calibration), profile-modulated blend (correctly gates weekend office to 0), full no-data handling, row-count validation.
- F6: header calls it "Phase 2 ML" but it's rule-based + min-max calibration (no trained model). Rename to avoid overclaiming "ML" to a technical buyer.
- F7: the no-data branch's building_type whitelist (L619-623) omits `data_center`/`lab` that the main branch (L482) includes → those types get the "other" archetype if they have zero readings. Align the two lists.

---

## G. PAGE 7 — HVAC & Building Envelope (`11_hvac_analytics_engine.py`)
> **Sophisticated** (HDD/CDD disaggregation, EN ISO 13370 heat loss, 3-part insulation curve with passive-house discrimination, SCOP rolling, renovation matrix). Uses the dynamic prefix pattern. Two issues are client-facing.

### G1 [P1] The HVAC heating/cooling/ventilation split is a TYPE-based proxy, not sub-metered
- `heating = total_annual × heating_sens × hdd_fraction`, where `heating_sens` is a fixed per-building-type constant (Office 0.35, etc.; `HVAC_COEFFICIENTS` L188-205). There is no sub-metering. So the headline Page-7 figures — **HVAC share %, heating %, cooling %** — are largely *determined by building type + weather shape*, not measured. An Office's HVAC share is essentially pinned near 0.35+0.12+0.15.
- **Why it matters:** A facilities/HVAC engineer (the Page-7 reader) will recognize a type-coefficient model immediately. Honest in code (V1), but the **visual** currently presents it as fact.
- **Fix:** Label the visual "modeled split (HDD/CDD method) — sub-metering refines this." Offer sub-meter ingestion as a Tier-3 upsell. Keep the method; fix the framing.

### G2 [P1] HVAC labels are Turkish-only — violates the English-UI rule and is inconsistent with other engines
- `system_label` ("ASHP İnverter (Premium)", "Gaz Yoğuşmalı Kazan", "Bölgesel Isıtma") and `renovation_reason` (full Turkish sentences) are **Turkish only**. The anomaly and recommendation engines are trilingual (en/de/tr). Page-7 visuals would render Turkish text in an otherwise-English report — and memory `feedback_language` says the web-app UI must be fully English.
- **Fix:** Make `system_label` / `renovation_reason` trilingual (or English) like the other gold tables.

### G3 [P2] Envelope/heat-loss are geometric estimates; COP real only for heat-pump buildings
- Envelope area = square-plan/3-floor assumption (V3); heat loss derived from it. COP is real only for the heat-pump building; others fall back to `cop_rated`/target. Fine as estimates — label "estimated" on `heat_loss_kwh_m2` and `hvac_efficiency_score` visuals.

### G4 [P2] `HVAC_COEFFICIENTS` keyed on Title-Case `building_type`
- Matches "Office"/"Data_Center" exactly; if upstream casing drifts (lowercase), it silently falls to DEFAULT. Same building_type-casing fragility seen in anomaly (C) and recommendation engines. Normalize casing once, upstream.

---

## H. PAGE 8 — Real-Time IoT (`11b_iot_processing.py`)
> **Clean** medallion (bronze→silver→gold 15-min), setpoint-based severity, per-sensor action text, daily summary, built-in validation checks. Mostly an architecture/consistency note.

### H1 [P1] Page-8 "Est. €cost today" comes from a value injected upstream, not computed here
- `cost_eur_estimate` is read from `bronze_iot_raw` and summed (`cost_eur_window`, coalesced to 0). The documented cost formula (`duration × power_waste_kw × grid_price`) lives in the **simulator/EventStream**, not in this engine. On a real BACnet/Modbus feed that doesn't inject cost, Page-8 cost shows **€0**.
- **Fix:** Move anomaly-cost logic into the silver IoT step (product logic), driven by the central grid-price table (A2/A3). Don't rely on the data source to pre-compute money.

### H2 [P2] Third severity casing in the platform
- IoT uses `"High"/"Medium"/"Low"` (Title case); `03` uses lowercase; `anomaly_detection.py` uses UPPERCASE. Page 8 is isolated so it's internally consistent, but the platform has **three** severity vocabularies. Unify.

### H3 [P2] Uses UDFs where other engines deliberately avoid them
- `action_udf`, `severity_udf` are Python UDFs; `03`/`09` explicitly prefer native `when/otherwise` ("DP-600 best practice: UDF yerine…"). UDFs block Catalyst optimization. Convert to native expressions / a mapping join for consistency + speed.

### Architecture note (not a defect)
- Page 8 depends on EventStream → `bronze_iot_raw`. Post-trial the stream is off → for client demos you need a **static IoT snapshot** or a running simulator, or Page 8 renders empty.

---

## I. PAGE 9 — Battery Dispatch & ROI (`12_battery_dispatch_and_simulation.py` + `13`–`16`)
> **Strong financial model** (NPV with inflation+salvage, Newton-Raphson IRR, payback, comparison score, full EU 2023/1542 fields: carbon footprint, recycled content, warranty cycles, `eu_compliant`; self-contained CSV fallback). This is a real differentiator — but it has the messiest data lineage and some optimistic ROI.

### I1 [P1] Demo-building identities conflict a THIRD time
- Battery nb header (L26-33): **B003 = Hamburg Logistics (800 kWh)**, **B005 = Frankfurt (NMC)**. EPC loader: B003 = Vienna Hotel, B005 = Berlin Healthcare. CRREM comments: B005 = Frankfurt Klinikum. So B003 and B005 each have **three** different cities/types across notebooks. (Escalates A4 from "inconsistent" to "will visibly break a demo.")

### I2 [P1] Grid CO₂ intensity hardcoded again — and disagrees with every other engine
- Battery pricing table (L268-272): CO₂ g/kWh = DE 380, AT 210, NL 320, **TR 450**. GHG engine: DE 380, AT **158**, NL **290**, TR **430**. Docs: TR **442**. → four sources, and TR alone is 430 / 442 / 450. AT and NL differ too. (Escalates A1.)

### I3 [P1] Battery savings are likely overstated (inflates payback/NPV/IRR — the headline numbers)
- `cost_avoided = discharge_kwh × peak_eur_kwh` (L350-352): **all** discharge is valued at the **peak** tariff, regardless of when it actually offsets load. Real dispatch offsets a peak/mid/off-peak mix.
- `demand_reduction_eur` (L357-363): `(discharge/max(1,cap)) × cap × 0.25 × demand_rate/30` algebraically reduces to `discharge × 0.25 × demand_rate/30` — i.e. proportional to **daily discharge energy**, not to the **peak-kW reduction** that demand charges actually bill on (kWh × €/kW/month is dimensionally muddled).
- **Why it matters:** Page 9 sells ROI to a CFO/investor. Over-stated savings → over-stated NPV/IRR/short payback → fails diligence.
- **Fix:** Value discharge by the tariff of the hour it displaces; base demand savings on modelled peak-kW shaved.

### I4 [P1] Multiple battery-notebook generations — unclear which is authoritative
- `12` produces 4 strategies on ~6 buildings; `13`/`14`/`15` (hourly profile, simulation v2, hourly dispatch) + `16*` loaders exist; the marketed Page-9 v56 design claims **12 countries × 7 strategies × 8 chemistries (672 sims + 49 fitness)**. Memory notes 5 Page-9 tables were dropped from the model and reloaded via nb 16. → overlapping/auto-superseding logic, fragile lineage.
- **Fix:** Designate ONE authoritative battery pipeline (v56), archive the rest, and write down the table lineage so a reload doesn't silently change Page 9.

---

## J. SIMULATION ENGINE (`04_simulation_engine.py`) — not yet read
- Feeds `gold_simulation_results` consumed by Page 5 (`05`/`06`). Page-5 financial scores and the whole recommendation ranking depend on it. **To verify in fix phase:** that it runs, produces the columns `06` expects (`hp_*`, `bat_*`, `ins_*`, `deep_*`), and uses centralized constants (it likely re-hardcodes prices/CO₂ too).

---

## K. DAX & VISUALS — open items being resolved
- D3 (CRREM stranding scope), D8 (EPC area-weighting), B2 (EUI annual vs daily) — verified via grep below; results folded into sections D and B.
- Full per-visual "how to read / how computed / why it matters" write-ups are the **documentation deliverable** (Phase 3, PDF), not gap items — except where a visual is outright wrong, which is captured above.

---
## L. DAX LAYER — version sprawl + two confirmed sustainability gaps

### L1 [P1] 68 incremental `.dax` patch files; the base file is stale-and-broken
- `semantic-model/` holds `02_dax_measures.dax` (base) + ~66 incremental `vN` patches. The same measures are redefined repeatedly; which definition is live depends on apply-order.
- **Proof:** base `02` references `gold_crrem_pathway[pathway_kgco2_m2_yr]` and `[year]` — columns that **don't exist** (loader produces `pathway_2c_kgco2_m2_yr` / `pathway_year`). `12_dax_v7` and `18_dax_v13` fix it (the v13 header literally documents "❌ pathway_kgco2_m2_yr → kolon yok"). Re-applying `02` silently reintroduces BLANK CRREM cards.
- **Fix:** Consolidate to ONE authoritative model definition (TMDL / the live semantic model in Git); retire the patch chain. A clean, documented semantic model is itself a sellable artifact.

### L2 [P1 — confirmed] EPC score not area-weighted — see D8.
### L3 [P1 — confirmed] CRREM intensity is Scope-2-only vs Scope 1+2 pathway — see D3.

---

## M. PACKAGING & PRICING — provisional, tied to findings
> Goal: sell only what survives scrutiny; don't over-claim "auditable/ESRS-ready" before Page 6 is fixed.

- **P2 "Building Energy KPI Dashboard" (Pages 1–5):** closest to sellable. The multi-country compliance engine (`05`) is a genuine differentiator. Ship after the reference-layer fix (single source of truth) + anomaly-taxonomy consolidation. Tier 1 (Insight) maps here.
- **P1 "CSRD Scope 1/2/3 Quickstart" (Page 6):** **do not** market as "ESRS-ready / auditable" until D1 (Scope 3), D2 (market-based S2), D8/L2 (EPC weighting), L3 (CRREM scope) are fixed. Until then it's a "Scope 1/2 screening dashboard," priced accordingly.
- **P3 "Fabric Audit" / P4 "PBI Tune-up":** deliverable now — pure expertise, independent of these data gaps.
- **Tiering (mirror the app):** Tier 1 Insight → P2 pages; Tier 2 Monitor → +Page 7/8 (only quote Page 8 "live" once a static IoT snapshot exists); Tier 3 Copilot → +Page 9 (only once battery-notebook lineage is settled, I4).
- **Hourly/daily:** opening slightly below market (Malt €450/day, €60/hr) is fine and matches the freelance plan. The gating risk is **claims**, not price.

---
*End of audit. Executive summary is at the top.*
