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
| **G2.1** | B011 building-master **flags** set (`has_heat_pump=False`, `has_pv=False`, `has_battery=False`, `has_led_lighting=False`, `iso50001_certified=False`, `epc_class='E'`, `roof_area_m2`, grid factor). The 21 seed left them NULL and `col("has_heat_pump") == False` is NULL in Spark → HP/DEEP/SOLAR rows were silently dropped. Surgical idempotent patch + the seed dict itself. | `notebooks/transformation/21b_fix_B011_building_master.py`, `21_residential_ingestion.py` |
| **G2.2** | `LandlordInvestmentCase` now scopes to **retrofit measures only** and de-duplicates: when `DEEP_RETROFIT` is present it IS the scope (HP+insulation already bundled), so the card no longer sums standalone HP + insulation + DEEP, nor folds in ops (BMS/HVAC) or solar. | `components/residential/LandlordInvestmentCase.tsx` |
| **G2.3** | **NEW** `ref_envelope_u_by_vintage` table — typical as-built wall/roof/window U by construction era (TABULA + WSchV/EnEV/GEG). Replaces the one-size `WALL_U_CURRENT=0.60` constant. | `00_reference_data_loader.py`, `docs/strategy/envelope-u-values-by-vintage.md` |
| **G2.4** | `04` now resolves per-building envelope U: current from `year_built`→vintage table, target from `ref_simulation_inputs`, module-constant fallback (zero regression). Also: residential MFH → ASHP (not GSHP); per-building gas/elec price preferred over country tariff (B011's approved 0.11 was ignored). B011 `year_built=1973` seeded. | `04_simulation_engine.py`, `21_residential_ingestion.py`, `21b_fix_B011_building_master.py` |

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

The sample data is now a **representative full year (2025, 12 months)** — building ≈ **156 kWh/m²·yr**
(retrofit-candidate baseline), units ≈ EPC band **D** (RESIDENTIAL_MF 120–180). Berlin's annual
average is roughly **8–9 heating-degree-days/day** (base-15), so:

```
factor = REFERENCE_DD_DAY / avg_daily_DD ≈ 11 / ~9 ≈ 1.15–1.25
eui_climate_adjusted ≈ raw_EUI × ~1.2
```

The factor is **> 1** because the fixed reference (11 DD/day) is colder than Berlin's annual mean —
the cross-climate normalisation expresses each building's EUI "as if" in a common reference climate
(same method as the commercial `climate_adjusted_eui`). A full year removes the winter-only
annualisation bias of the earlier 2-month sample.

**Honesty note (UI footnote):** the factor is applied to the **whole EUI** (heating + hot water,
per the 2026-06-12 decision); it lightly over-corrects the weather-independent hot-water base load.
Indicative, screening-grade.

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
| a | `00_reference_data_loader.py` | reloads `ref_simulation_inputs` **with B011** (+ profiles, tariffs) **and builds `ref_envelope_u_by_vintage`** (vintage→U table for the envelope fix) |
| b | `21b_fix_B011_building_master.py` | **NEW — run once.** Sets B011's boolean flags + `epc_class='E'` + roof + grid factor. **Without it the flags are NULL and `has_heat_pump == False` is NULL in Spark → INSTALL_HEAT_PUMP / DEEP_RETROFIT / SOLAR are silently dropped.** |
| c | `04_simulation_engine.py` | `gold_simulation_results` — B011 HP / insulation / deep scenarios + BAFA/KfW grants |
| d | `05_compliance_checker.py` | `gold_compliance_results` — B011 GEG wall/roof compliance + `overall_score`. **Required:** `IMPROVE_INSULATION` is gated on `geg_wall/roof_compliant == False` and `DEEP_RETROFIT` on `overall_score < 60`; with no B011 compliance row both drop (only the heat pump fires). |
| e | `06_recommendation_engine.py` | `gold_recommendations` — B011 `INSTALL_HEAT_PUMP` / `IMPROVE_INSULATION` / `DEEP_RETROFIT` with `capex_eur` + `grant_eur` |

**Then verify** `/buildings/B011/residential` → `LandlordInvestmentCase` shows Investment / Subsidy /
Net cost / rent uplift. The card now scopes to **retrofit measures only**; when `DEEP_RETROFIT` is
present it uses that as the single scope (it already bundles HP + insulation), so it no longer
double-counts standalone HP + insulation nor folds in ops (BMS/HVAC) or solar. **Reconcile** the
figures to `docs/strategy/residential-retrofit-calculations.md` — the card and the calc doc must
tell the same story.

> **Dependency, corrected:** for `RESIDENTIAL_MF` the profile feasibilities are heat-pump **HIGH**,
> insulation **HIGH**, solar **MEDIUM**, battery **LOW** — but feasibility alone is not enough.
> **HP** fires once the flag patch (step b) is in; **insulation + deep-retrofit** additionally need
> the compliance row (step d). Battery is intentionally not recommended for residential. (Column
> order in the profile is heat_pump / solar / battery / insulation — the LOW flag is battery.)

> **Envelope physics — RESOLVED 2026-06-12 (G2.3/G2.4).** The hard-coded current-U constant and the
> ignored target-U / GSHP-selection are fixed via the vintage table (see
> `docs/strategy/envelope-u-values-by-vintage.md`). B011 now computes ~103 kWh/m²·yr (was 77),
> insulation ~€20k/yr (payback ~1.6 y), ASHP +~€6.7k/yr (payback ~9 y) — reconciles with the calc doc.
> **Commercial impact:** only B001/B002/B003 are simulated (they have `ref_simulation_inputs` rows);
> their vintage U-values are better than the old 0.60 constant, so their insulation savings **drop**
> (more correct). **Eyeball B001/B002/B003 recommendations after re-running.**
>
> **Remaining residuals (deferred):**
> 1. Non-residential U-values use the residential TABULA bands as an approximation; the IWU
>    ENOB:dataNWG typology would refine offices/retail/logistics.
> 2. Heat-pump uses the building's flat electricity tariff (0.30), not a dedicated HP tariff (~0.25),
>    so HP savings are conservative — its real lever is CO₂/ETS2 pricing (per the calc doc).
> 3. Ops measures (BMS, HVAC scheduling) fire for B011 with **€0 saving** (B011 isn't in
>    `gold_kpi_monthly`). Now excluded from the investment card, but still surface on `/actions` with
>    €0 — separate cleanup.

---

## 6. Done-criteria

- [ ] **KPI/climate track** (`21 → 02_weather → 30`) runs clean; 3 residential gold tables non-empty for B011.
- [ ] `climate_adjustment_factor ≠ 1.0` for B011 (weather joined).
- [ ] `/residential` reachable from nav; building view shows the adjusted EUI (the "adj" line).
- [ ] **Investment-case track** (`00 → 21b → 04 → 05 → 06`): `gold_recommendations` for B011 carries `INSTALL_HEAT_PUMP` (+ `IMPROVE_INSULATION` / `DEEP_RETROFIT` after step 05) → `LandlordInvestmentCase` shows a single coherent retrofit scope, reconciled to the calc doc.

---

## 7. References

- Built-state audit: `residential-verification-register.md`
- Energy method (single source for tooltips): `../strategy/residential-retrofit-calculations.md`
- Commercial climate method mirrored: `notebooks/gold/03_gold_kpi_engine.py` (audit B1, `REFERENCE_DD_DAY=11`)
- Weather pipeline: `notebooks/ingestion/02_openmeteo_weather_loader.py` (base-15 HDD/CDD)
