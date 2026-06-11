# Residential Vertical — Verification Register

**Status:** VERIFIED by static end-to-end trace — 2026-06-12
**BMAD layer:** cross-cutting audit (Data → Logic → Implementation), before any further build
**Method:** read-only contract trace of every layer (Silver → Gold → Backend service/router →
Frontend), plus `py_compile` of the backend modules and a column-contract cross-check. **No
Fabric/Spark run was possible in this environment** — items that can only be confirmed by
executing the notebooks against the Lakehouse are marked **[needs Fabric run]**.
**Why this doc exists:** the growth-strategy §4.5 "❌ new" table implied the residential items
were unbuilt. The trace shows the opposite — they are largely **already built and committed**
(commit `52f7725 "sync local work"`). This register records what is real, what is a placeholder,
and the narrow set of genuine gaps, so the next step is a *targeted fix*, not a duplicate build.

---

## 1. Verdict

| | |
|---|---|
| **Overall** | Residential vertical is **substantially built end-to-end** (Postgres model + 3 notebooks + 2 backend services + 2 routers + 3 frontend pages). |
| **§4.5 "❌ new" table** | **Stale.** All four items are implemented (see §2). |
| **Column contract (writer → readers)** | **PASS** — every column a backend service `SELECT`s is emitted by its notebook. No mismatches (§4). |
| **Backend compile** | **PASS** — all 7 residential modules `py_compile` clean. |
| **Genuine gaps** | Narrow: one energy-logic placeholder (G1), one nav omission (G4), and a few verify/run items (G2, G3, G5). |

The §4.5 four-item status, corrected:

| §4.5 item | Claimed | Actual |
|---|---|---|
| Residential building type + heating KPIs | ❌ new | ✅ **built** — `Residential_MF` type, `gold_residential_unit_kpi`, manager service, frontend |
| Heat-cost-allocation ingestion | ❌ new | ✅ **built (CSV path)** — `21_residential_ingestion.py`; Techem/ista live **API** still a forward-ref |
| Split-incentive + subsidy-aware ROI | ❌ new | ✅ **built** — `LandlordInvestmentCase` (subsidy + Modernisierungsumlage §559 + recovery); engine emits HP/insulation/deep-retrofit + `grant_eur` |
| Common-area vs. unit split | ❌ new | ✅ **built** — `gold_residential_common_split`, HKVO **70/30** |

---

## 2. Layer-by-layer trace

### 2.1 Silver — REAL, coherent

| Object | Producer | Status |
|---|---|---|
| `silver_unit_master` | `20_residential_model_p1.py` (idempotent empty schema) + `21` (seed B011 + 24 units) | ✅ schema `unit_id, building_id, floor, area_m2, unit_type, is_heated, updated_at` |
| `silver_residential_consumption` | `21_residential_ingestion.py` (bill = building grain, heatcost = unit grain; German energy-type normalizer `ne()`) | ✅ `building_id, unit_id, grain, period_start, period_end, energy_type, consumption_kwh, cost_eur, source, ingested_at` |
| `silver_building_master` deltas | `02_silver_transformation.py` defines `unit_count` + `common_area_m2` **defensively** (col-if-present-else-null, lines 274–281); `21` seed merges B011 values in | ✅ columns exist in target → merge lands them (no silent drop) |

### 2.2 Gold — REAL, with one placeholder

`30_residential_gold.py` (consolidated; supersedes the old `30_unit_kpi`/`31_common_split`/
`32_uvi_monthly` whose `.pyc` remain) writes three tables from `silver_residential_consumption`
+ `silver_unit_master`:

| Table | Logic | Status |
|---|---|---|
| `gold_residential_unit_kpi` | annualized heating+DHW ÷ area = EUI; EPC band on `RESIDENTIAL_MF` 50/80/120/180; `vs_building_pct` via window | ✅ real |
| `gold_residential_common_split` | HKVO **70/30** = `0.70·cons_share + 0.30·area_share`, allocated over building total | ✅ real |
| `gold_residential_uvi_monthly` | per-unit monthly heating/DHW kWh + cost + building-avg benchmark | ✅ real |
| `climate_adjustment_factor` / `eui_climate_adjusted_kwh_m2_yr` | **hardcoded `lit(1.0)`; adjusted = raw EUI × 1.0** | ⚠️ **PLACEHOLDER (G1)** — no HDD/weather source joined |

Recommendation grants (`06_recommendation_engine.py`): emits `INSTALL_HEAT_PUMP`,
`IMPROVE_INSULATION`, `DEEP_RETROFIT` with `grant_eur` (KfW/BAFA), building-type-aware (uppercased).
Whether **B011** actually receives quantified measures + grants is data-dependent → **G2 [needs Fabric run]**.

### 2.3 Backend — REAL, contract-consistent, compiles

- `residential_manager_metrics.py` — per-unit KPI + rollups + **UVI/HKVO §12** penalty exposure
  (3% × annual heat cost @ €0.12/kWh, all stated as indicative).
- `residential_metrics.py` — resident own-unit view; reads the climate-adjusted columns and the
  schema documents the placeholder honestly (*"1.0 = not yet wired"*).
- Routers: **manager** (B2B JWT; building visibility → 404; invite requires `can_manage_building`,
  partner-aware) + **resident** (separate Bearer JWT + `RESIDENT_DEV_MODE` fallback;
  tenancy-window scope; **hashed** single-use magic-link).
- Segment detection: `"residential" in building_type.lower()` — **casing-robust**.
- `py_compile`: **all 7 modules OK.**

### 2.4 Frontend — REAL, one nav omission

| Surface | Status |
|---|---|
| `/residential` (portfolio: `UviComplianceBand`, `LandlordPortfolioBand`, building cards) | ✅ renders; fields match backend payload |
| `/buildings/[id]/residential` (per-unit KPIs + `LandlordInvestmentCase`) | ✅ feeds `actions` (building-scoped) + `epc_class` |
| `/residence` (resident own-unit view) | ✅ present |
| `LandlordInvestmentCase` | ✅ split-incentive: subsidy + §559 rent-uplift + recovery + EPC-stranding; **honest empty state** when no quantified measures |
| **Primary nav (`AppChrome`)** | ⚠️ **`/residential` is absent (G4)** — only `ReportNav` (building-level) links it; the portfolio page is **nav-orphaned** |

---

## 3. What is honest / production-grade (keep)

- **No fabricated data:** NULLs pass through as `None`; the HDD placeholder is documented in the
  schema; `LandlordInvestmentCase` shows an explicit "no quantified measures yet" state.
- **Privacy by construction:** no resident PII in the lakehouse; benchmark pre-aggregated into each
  unit's own Gold row (no cross-unit join); tenancy-window (Mieterwechsel) scoping; hashed tokens.
- **Reuse discipline:** RLS-via-building_id filter (the proven Day-15/29 read path), `/actions`
  reused for the investment case, `reportKit`-style patterns — matches the architecture briefs.

---

## 4. Column-contract cross-check — PASS

Every column read by a service is in the set its notebook writes (reader ⊆ writer):

| Gold table | Writer (`30_residential_gold.py`) | Manager service | Resident service | Result |
|---|---|---|---|---|
| `unit_kpi` | building_id, unit_id, is_heated, area_m2, coverage_start/end, cov_days, heating_dhw_kwh_annual, eui_kwh_m2_yr, climate_adjustment_factor, eui_climate_adjusted_kwh_m2_yr, epc_band, building_avg_eui_kwh_m2_yr, vs_building_pct | reads 9 of these | reads all 14 | ✅ |
| `common_split` | building_id, unit_id, coverage_start/end, unit_metered_kwh, area_m2, cons_weight, area_weight, cons_share, area_share, allocation_share, building_total_kwh, unit_allocated_kwh | unit_allocated_kwh, allocation_share | reads all 13 | ✅ |
| `uvi_monthly` | building_id, unit_id, year, month, energy_type, kwh, cost_eur, building_avg_kwh, vs_building_pct | year, month, unit_id (count) | reads all 9 | ✅ |

Silver→Gold is likewise consistent (`30` reads only columns `20`/`21` write).

---

## 5. Gap register

| # | Gap | Severity | Owner | Fix |
|---|---|---|---|---|
| **G1** | **HDD climate factor is a no-op** (`climate_adjustment_factor = 1.0`). Decision **E6** wanted real HDD-normalized kWh/m²·yr — the KPI that makes cross-building/cross-year comparison valid. Currently raw EUI passes through; manager view doesn't even read the adjusted column. | **HIGH** (energy-logic correctness) | **Mert approves method**, then code | Join an HDD/Gradtagzahl source per building location, compute `factor = HDD_ref / HDD_local` (base + reference to confirm), set `eui_climate_adjusted = eui × factor`; surface the adjusted KPI in the manager view. |
| **G2** | Residential measures may not be **quantified for B011** (capex + `grant_eur`), so `LandlordInvestmentCase` could show its empty state; and figures aren't traced to the approved `residential-retrofit-calculations.md` 6-measure catalogue. | MED | code + **[needs Fabric run]** | Confirm `gold_recommendations` emits HP/insulation/deep-retrofit with grants for B011; reconcile capex/grant values to the calc doc (single source). |
| **G3** | Pipeline **never run end-to-end**; committed as one bulk "sync local work". Notebook `21` reads CSVs from `Files/` but they live at `sample-data/residential/` → must be **uploaded to the Lakehouse Files root** first. | MED | **Mert (Fabric)** | Upload the 2 sample CSVs to `Files/`; run `21 → 30`; confirm row counts; open `/residential` + a building view. |
| **G4** | **`/residential` portfolio page is nav-orphaned** — built but missing from `AppChrome` primary nav (only `ReportNav` links the building-level view). | LOW effort / HIGH value | code (frontend) | Add a "Residential" item to `AppChrome` nav (one entry, beside `/financing`/`/decarbonisation`). |
| **G5** | `building_type` casing: seed writes **`Residential_MF`** while reference data + measures use **`RESIDENTIAL_MF`**. Backend is case-insensitive (safe), but **exact-match joins** (e.g. `ref_building_type_profiles` in the commercial compliance path) would miss the seed. | LOW | code | Normalize the seed token to `RESIDENTIAL_MF` (or uppercase at join sites). |

**Cleared during the trace (not gaps):** `02_silver` *does* define `unit_count`/`common_area_m2`;
the Gold→service column contract is fully consistent; the old `30/31/32` notebooks are consolidated
into `30_residential_gold.py` (not lost).

---

## 6. Recommended fix order

1. **G1 — HDD climate adjustment** (energy-logic; the highest-integrity fix). *Gate: Mert approves
   the method — HDD base (e.g. 15/20 °C), reference year/location, per-building vs. portfolio
   reference — before code.*
2. **G4 — nav link** (5-minute, unlocks the already-built portfolio view).
3. **G2 — measure ↔ calc-doc reconciliation** (so the investment case populates and traces to the
   single source).
4. **G5 — casing normalization** (cheap consistency).
5. **G3 — Mert runs `21 → 30` in Fabric** and confirms the pages render (validates G2 and the whole
   chain in one pass).

---

## 7. Evidence (files traced)

- Notebooks: `notebooks/transformation/20_residential_model_p1.py`, `21_residential_ingestion.py`,
  `notebooks/gold/30_residential_gold.py`, `notebooks/recommendation/06_recommendation_engine.py`,
  `notebooks/transformation/02_silver_transformation.py`
- Backend: `app/db/models/residential.py`, `app/services/residential_manager_metrics.py`,
  `app/services/residential_metrics.py`, `app/routers/residential.py`, `app/routers/residence.py`,
  `app/schemas/residential.py`, `app/schemas/residence.py`, `app/services/actions_data.py`
- Frontend: `app/residential/page.tsx`, `app/buildings/[fabric_building_id]/residential/page.tsx`,
  `components/residential/LandlordInvestmentCase.tsx`, `components/AppChrome.tsx`,
  `components/ReportNav.tsx`
- Data: `sample-data/residential/sample_bills_B011.csv`, `sample_heatcost_B011.csv`
- Design refs: `docs/architecture/residential-{segment-architecture,data-model,ingestion-p2}.md`,
  `docs/strategy/2026-06_growth_strategy.md` (§4.5), `residential-retrofit-calculations.md`
