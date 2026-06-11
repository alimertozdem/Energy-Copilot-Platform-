# Residential Vertical — Activation Runbook (Fabric-side)

**Status:** READY TO RUN — 2026-06-12
**Audience:** product owner (Mert), running the Fabric workspace.
**Pairs with:** `residential-verification-register.md` (what's built) — this is the *run* side.
**Why:** the residential code is complete and committed, but never executed end-to-end. This
runbook activates it and turns on the new **G1 climate-adjusted EUI** (the placeholder fix).

> All code changes (G1, G4, G5) are already in the repo. This runbook is the **Fabric/run**
> half (G2/G3) that only the workspace owner can do. Each step states the *why*.

---

## 0. What changed in code (already done, for context)

| Gap | Change | File |
|---|---|---|
| **G1** | Climate factor is now real: `EUI_adj = EUI × REFERENCE_DD_DAY(11) / avg_daily_DD`, reusing `silver_weather_daily` (base-15, HDD+CDD) — **same method as the commercial `climate_adjusted_eui`**. Building-level factor, weather-missing → 1.0 fallback. | `notebooks/gold/30_residential_gold.py` |
| **G1a** | B011 (Berlin 52.52, 13.405) added to the weather loader so it gets HDD. | `notebooks/ingestion/02_openmeteo_weather_loader.py` |
| **G1c** | Manager view now surfaces the adjusted EUI (per-unit "adj" line + building `×factor` hint). Resident view already showed it. | `services/residential_manager_metrics.py`, `schemas/residential.py`, `lib/api/residentialManager.ts`, `components/residential/ResidentialDashboard.tsx` |
| **G4** | `/residential` portfolio page added to the primary nav (was nav-orphaned). | `components/AppChrome.tsx` |
| **G5** | Seed `building_type` normalized `Residential_MF` → `RESIDENTIAL_MF` (exact-match-join safety). | `notebooks/transformation/21_residential_ingestion.py` |
| **G2** | B011 added to `ref_simulation_inputs` (RADIATOR_LT@60, GEG U-targets, gas 0.11; reviewer-approved) so simulation→recommendation emits quantified residential measures + BAFA/KfW grants. | `notebooks/sustainability/reference/00_reference_data_loader.py` |

---

## 1. Prerequisites

- `02_silver_transformation.py` has run (it defines `unit_count` + `common_area_m2` on
  `silver_building_master` — verified present).
- Lakehouse **Files/** root can receive CSV uploads.

---

## 2. Run sequence (in order)

| # | Action | Why | Expect |
|---|---|---|---|
| 1 | **Upload** `sample-data/residential/sample_bills_B011.csv` and `sample_heatcost_B011.csv` to the Lakehouse **`Files/`** root | notebook 21 reads `Files/sample_*_B011.csv`; the repo keeps them under `sample-data/` | 2 files in `Files/` |
| 2 | Run **`21_residential_ingestion.py`** | seeds B011 (`RESIDENTIAL_MF`) + 24 units → `silver_unit_master`; ingests bill + heatcost → `silver_residential_consumption` | prints seed + `silver_residential_consumption` row count; grain×energy_type table |
| 3 | Run **`02_openmeteo_weather_loader.py`** | now includes B011 → fetches Berlin HDD into `silver_weather_daily` (the input to the G1 climate factor) | B011 appears in the per-building HDD summary |
| 4 | Run **`30_residential_gold.py`** | builds the 3 gold tables **with the real climate factor** | 3 `✅` prints; the final `.show()` lists `climate_adjustment_factor ≠ 1.0` for B011 units |

> **If you skip step 3:** notebook 30 prints `⚠️ silver_weather_daily yok` and the factor falls
> back to **1.0** (honest — `eui_climate_adjusted = raw`). Nothing breaks; the adjustment is just off. The split-incentive **investment case** needs a second track — see §5.

---

## 3. Expected climate result for B011 (sanity check, indicative)

The sample data is **only Jan–Feb 2026** (2 winter months). Berlin deep-winter averages roughly
**13–15 degree-days/day** (base-15), so:

```
factor = REFERENCE_DD_DAY / avg_daily_DD ≈ 11 / ~14 ≈ 0.78–0.85
eui_climate_adjusted ≈ raw_EUI × ~0.8
```

This is **correct and expected**: annualising 2 winter months (`×365/days`) inflates the raw EUI,
and dividing by the cold-period degree-days scales it back toward a reference season — the ratio
method **partly self-corrects the annualisation bias**. For a representative factor, load a fuller
consumption year (the 2-month sample is a demo).

**Honesty note (surfaced in the UI footnote):** the factor is applied to the **whole EUI**
(heating + hot water, per the 2026-06-12 product-owner decision). It therefore *lightly
over-corrects* the weather-independent hot-water base load. Indicative, screening-grade.

---

## 4. App / report verification

1. **Refresh** the Fabric **SQL Analytics Endpoint** (the backend reads the gold tables through it).
2. Open **`/residential`** (now in the primary nav) → B011 card shows units, avg EUI, EPC mix, UVI.
3. Open **`/buildings/B011/residential`** → per-unit table shows the **"adj"** EUI sub-line and the
   building **"climate-adj ×0.8x"** hint on the avg-EUI card.
4. Open the **resident view** (`/residence` via a minted invite, or `?resident=` in dev) → the KPI
   card's climate-adjusted figure is no longer equal to raw.

---

## 5. G2 — residential measures + subsidy ROI (now wired)

**Root cause (found + fixed):** the simulation engine **inner-joins** `ref_simulation_inputs`,
which held only **3 buildings (B001 / B002 / B003)**. B011 had no row → no scenario → no quantified
measures → `LandlordInvestmentCase` empty. **Fix (code, reviewer-approved 2026-06-12):** B011 added
to `ref_simulation_inputs` (`00_reference_data_loader.py`) with a 1970s-MFH profile —
**RADIATOR_LT @ 60 °C** (→ heat-pump feasible), **GEG U-targets 0.22 / 0.95 / 0.20**, gas
0.11 €/kWh — aligned to the calc doc.

**Run (the investment-case track):**

| # | Notebook | Produces |
|---|---|---|
| a | `00_reference_data_loader.py` | reloads `ref_simulation_inputs` **with B011** (+ profiles, tariffs) |
| b | `04_simulation_engine.py` | `gold_simulation_results` — B011 HP / insulation / deep scenarios + BAFA/KfW grants |
| c | `06_recommendation_engine.py` | `gold_recommendations` — B011 `INSTALL_HEAT_PUMP` / `IMPROVE_INSULATION` / `DEEP_RETROFIT` with `capex_eur` + `grant_eur` |

**Then verify** `/buildings/B011/residential` → `LandlordInvestmentCase` shows Investment / Subsidy
/ Net cost / rent uplift, and **reconcile** the figures to
`docs/strategy/residential-retrofit-calculations.md` (6-measure T0–T2, 2026 BAFA/KfW 30–70 % cap,
€30k/WE) — the card and the calc doc must tell the same story.

> Note: the `RESIDENTIAL_MF` profile's `insulation_feasibility` is `LOW`; if `IMPROVE_INSULATION`
> does not fire, that flag (in `00_reference_data_loader.py`) is the lever — flag if you want it raised.

---

## 6. Done-criteria

- [ ] **KPI/climate track** (`21 → 02_weather → 30`) runs clean; 3 residential gold tables non-empty for B011.
- [ ] `climate_adjustment_factor ≠ 1.0` for B011 (weather joined).
- [ ] `/residential` reachable from nav; building view shows the adjusted EUI (the "adj" line).
- [ ] **Investment-case track** (`00 → 04 → 06`): `gold_recommendations` for B011 populated → `LandlordInvestmentCase` shows numbers, reconciled to the calc doc.

---

## 7. References

- Built-state audit: `residential-verification-register.md`
- Energy method (single source for tooltips): `../strategy/residential-retrofit-calculations.md`
- Commercial climate method mirrored: `notebooks/gold/03_gold_kpi_engine.py` (audit B1, `REFERENCE_DD_DAY=11`)
- Weather pipeline: `notebooks/ingestion/02_openmeteo_weather_loader.py` (base-15 HDD/CDD)
