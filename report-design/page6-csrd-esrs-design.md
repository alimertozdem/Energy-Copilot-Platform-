# Page 6 — Sustainability / ESG: CSRD · ESRS E1 · EU Taxonomy (auditable design)

**Purpose.** This is the flagship disclosure page and the core sellable artifact for the
CSRD/ESG freelance niche. Every visual maps to a specific **ESRS E1 (Climate Change)**
datapoint or **EU Taxonomy** criterion, with row-level lineage back to the reference layer
(`ref_grid_emission_factors` / `ref_electricity_tariffs` / `ref_fuel_factors`, year-matched + sourced).

**Pitch line (use verbatim with clients):** *"Every figure on this page maps to an ESRS E1
datapoint, computed from year-matched national emission factors with row-level lineage —
location- and market-based Scope 2 reported separately, area-weighted EPC, and CRREM stranding
against the 1.5 °C pathway."*

---

## 1. ESRS datapoint → visual map (the audit story)

| ESRS / Taxonomy | Datapoint | Visual on this page |
|---|---|---|
| **E1-5** | Energy consumption & mix; renewable share | "Solar PV Share %" card; (energy intensity on Page 1) |
| **E1-6** | Gross Scope 1, 2 (location **and** market), 3; GHG intensity | Scope 1/2/3 bar; Scope-mix donut; **Scope 2 location-vs-market** bar; GHG-intensity card |
| **E1-4** | Targets / trajectory | "CO₂ Emission Trend (annual)" line |
| **E1-8** | Carbon pricing | "CO₂ Carbon Levy" card (ETS2 / BEHG) |
| **E1-9** | Anticipated financial effects — transition risk | "CRREM Stranding Year" card + "CRREM Status by Building" table |
| **E1-3** | Actions & resources | "Priority Actions & Incentives" strip |
| **EU Taxonomy** | Substantial contribution (energy performance) | "EPC Portfolio Grade" card (area-weighted) |
| **Meta** | Disclosure completeness | **"CSRD Disclosure Readiness %"** card (new) |

---

## 2. KPI cards (top row) — rebind to the audit-correct measures

| Card | Bind to | Why / ESRS |
|---|---|---|
| GHG Intensity (kgCO₂/m²/yr) | **`[Carbon Intensity S1S2 kgCO2 m2 yr]`** | E1-6 intensity must be **Scope 1+2** (not Scope-2-only). Rebind. |
| EPC Portfolio Grade | **`[EPC Class Area-Weighted]`** (+ `[EPC Score Area-Weighted kWh m2]` as subtitle) | EU Taxonomy / "area-weighted, not building-count". Rebind. |
| Solar PV Share % | keep | E1-5 renewable share. Goal line OK. |
| CO₂ Carbon Levy € | keep | E1-8 carbon pricing exposure. |
| CRREM Stranding Year | keep + add `[CRREM Stranding Status]` as the status chip | E1-9 transition risk. |
| **+ NEW: CSRD Disclosure Readiness %** | **`[CSRD Disclosure Readiness Pct]`** | The self-audit headline: are all required datapoints present (S1, S2-loc, S2-mkt, S3-screening, lineage)? |

> Add the CSRD Disclosure Readiness card as the 6th card (or replace a redundant one). It is the
> single most differentiating element — it tells a buyer "this dataset is disclosure-complete."

---

## 3. Main visuals — bind / fix / add

### 3.1 Scope 1/2/3 by building (stacked bar) — keep
- Series: `scope1_total_tco2`, `scope2_location_tco2`, `scope3_estimated_tco2` (use the **location**
  Scope 2 here). Already correct. Add a footnote: "Scope 2 = location-based; market-based shown separately."

### 3.2 Portfolio Scope Mix (donut) — keep, label honestly
- Keep the 3-slice mix. **Label the Scope 3 slice "est. (screening, 8 % of S1+S2)"** so it is never
  mistaken for disclosure-grade. This honesty *is* the expertise signal.

### 3.3 NEW — Scope 2: Location vs Market (clustered bar) ⭐
- Two bars: `SUM(scope2_location_tco2)` vs `SUM(scope2_market_tco2)`. This is the **E1-6 dual-method**
  disclosure most products forget. Even if they're equal today (no green contract), showing both
  *separately* is the auditable requirement.
- Title: "Scope 2 — Location vs Market-based (ESRS E1-6)".

### 3.4 CO₂ Emission Trend (annual) — keep, add a target line
- Keep Total CO₂ / Net Footprint / Savings lines. **Overlay the CRREM 1.5 °C pathway** (or a target)
  as a reference line so the trend reads against E1-4 targets.

### 3.5 CRREM Status by Building (table) — rebind + fix "No data"
- Columns: Building, **`[Carbon Intensity S1S2 kgCO2 m2 yr]`**, **`[CRREM Pathway 2C kgCO2 m2 yr]`**,
  **`[CRREM Stranding Status]`**. Rebind the intensity to **S1+2** (apples-to-apples with the pathway).
- **"No data" rows** (Stockholm BioLab = Lab, Frankfurt Datacenter = Data_Center): the CRREM loader
  has no pathway for those building types → no benchmark. **Fix:** add `Lab` and `Data_Center` rows
  to `gold_crrem_pathway` (10_crrem_pathway_loader) — or label them "Pathway N/A (sector)" rather
  than blank. (Engine follow-up; flag, not blocking.)

### 3.6 Priority Actions & Incentives (strip) — keep
- E1-3 actions. Sourced from `gold_recommendations` (grants: KfW/BAFA/YEKA…). Keep.

---

## 4. The "Something's wrong with one or more fields" error
A visual is bound to a field that was renamed/removed in the refresh. Most likely the old EPC
or CRREM measure (e.g., a Scope-2-only intensity or `pathway_kgco2_m2_yr`). **Action:** click
"See details" → note the field → rebind that visual to the v57 measure above
(`[Carbon Intensity S1S2 kgCO2 m2 yr]` / `[EPC Score Area-Weighted kWh m2]` / `[CRREM Pathway 2C kgCO2 m2 yr]`).

---

## 5. Cross-page CSRD framing (apply while building every page)
- **Page 1** Portfolio = energy intensity / EUI (E1-5 context).
- **Page 4** Forecast = forward trajectory → supports **E1-4 targets**.
- **Page 5** Decision = compliance + grants → **E1-3 actions & resources** + multi-country regulation.
- **Page 6** = the **core E1 disclosure** (this page).
- **Page 7** HVAC = decarbonisation levers (heat-pump, envelope) → E1-3 evidence.
- Keep one consistent message: *year-matched factors, dual-method Scope 2, area-weighted EPC,
  CRREM 1.5 °C, honest screening labels.* That sentence is the product.

---

## 6. Build order for this page
1. Rebind the 5 existing cards + add the **CSRD Disclosure Readiness** card.
2. Fix the broken-field visual (rebind to v57 measure).
3. Add the **Scope 2 Location-vs-Market** bar.
4. Rebind the CRREM table to S1+2 intensity vs pathway.
5. Label Scope 3 "est.", overlay the target line on the trend.
6. (Engine follow-up) add Lab / Data_Center CRREM pathway rows.
