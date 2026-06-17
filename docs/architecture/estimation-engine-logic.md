# EnergyLens — Estimation Engine — Logic Design (BMAD: Logic)

> **Status:** energy assumptions **signed off 2026-06-17**, then **validated + recalibrated in a
> research pass (2026-06-17)** against authoritative sources (see §4b). Implemented in
> `web-app/backend/app/services/estimation/` and green on the backtest harness.
> **Principle:** screening-grade. Every layer states its assumption, outputs a **band**, narrows it
> honestly, and is recalibrated by the §5 backtest as real data arrives.

---

## 0. What "Logic" computes

The engine carries a **point** EUI estimate `eui` (kWh/m²/yr) and a **relative half-width** `w`
(uncertainty). Each layer refines both: informative evidence **moves** `eui` and **shrinks** `w`;
a missing input (e.g. no area) **widens** it. The reported band is `eui·(1 ± w)`. Then
`E = eui · area`, and cost / CO₂ follow from `E`. Measured bills and EPC are merged by
**inverse-variance blending** — the statistically correct way to let the more reliable source dominate.

---

## 1. Per-layer math

**L0 — Archetype prior** — `building_type → (eui_lo, eui_hi)` + heating fraction `h` (A1).
`eui ← (eui_lo+eui_hi)/2 ; w ← (eui_hi−eui_lo)/(eui_lo+eui_hi)` (≈0.30–0.40).
Bands are total final energy (heating+DHW+electricity), cross-checked vs CIBSE TM46 + Heizspiegel.
**Residential recalibrated this pass: band 90–180 → 100–240, h 0.65 → 0.72** (see §4b).

**L1 — Vintage** (reposition within the band, does NOT multiply → avoids double-counting). A3.
`era(construction_year) → p ∈ [0,1]` (old→1 high end); `eui ← eui_lo + p·(eui_hi−eui_lo) ; w ← w·0.8`.

**L2 — Climate (HDD)** — scales the **heating fraction only**. A2.
`m_clim = HDD_building / HDD_ref ; eui ← eui·[(1−h) + h·m_clim] ; w ← w·0.95`.
**HDD uses an 18 °C base throughout** (consistent with gold `mv_kpi_daily.hdd_day` + open-meteo);
**`HDD_ref = 3200`** (DE national @18 °C). Not the VDI 3807 Gradtagzahl (20/15, ≈3500) — see §4b.

**L3 — Geometry fallback** (area only, when area is missing). A7.
`storeys = floors_above_ground ?? round(height/3.2)` ; `area = footprint × storeys × 0.8` ; `w_area ≈ 0.35`.
Never overrides a user / gold (`conditioned_area_m2`) area.

**L4 — Partial-bill ANCHOR** (strongest). A4/A5.
≥12 mo → `baseline_kpi` run-rate = **actual** (estimate retires). 1–11 mo → annualise via the archetype
monthly shape + HDD weighting (NOT flat ×12), then inverse-variance blend (`w_bill` 0.08 ≥6 mo / 0.15 <6 mo).

**L5 — EPC anchor** (region-gated, weaker than a bill). A6 — **now the real German GEG class bands.**
`epc_class → GEG Energieausweis final-energy band (kWh/m²/yr)`, anchored at the class midpoint, blended
(`w 0.22` — asset rating + AN area basis). Residential auto-lookup is DE-unavailable; the class is taken
from the user-entered field (or UK auto). Non-residential letter scales differ → screening-only.

---

## 2. Confidence & range

`HIGH` real gold or ≥12-mo bill · `MEDIUM` <12-mo bill OR (vintage+HDD) OR EPC · `LOW` archetype(+vintage)
· `VERY LOW` footprint-derived area. Output `{eui·(1−w), eui, eui·(1+w)}` + tier + method + editable.
The §5 backtest **calibrates `w`** so a band contains truth at the rate its tier claims.

---

## 3. Derived KPIs (banded, "Estimated", editable)

`E = eui × area`. **Cost / CO₂ fuel-split (A8):** when the heating fuel is known
(`has_gas_heating` / `heating_system`), the heating share `h` uses that fuel's price + emission factor
and the rest uses electricity — covering **gas · oil · district heat**. Unknown / electric / heat-pump →
electricity proxy (with the mixed-fuel caveat; heat-pump COP deferred, A9-adjacent). Factors come from
the canonical `reference_factors` (electricity) + `factors.py` (heating fuels).

---

## 4. Energy assumptions — signed off + research-pass status

| # | Assumption | Value (after research pass) | Status |
|---|---|---|---|
| **A1** | `heat_frac` by type | Office .40 · Retail .30 · Hotel .45 · Hospital .35 · Logistics .55 · School .55 · **Residential .72** · Lab .45 · default .45 | **REVISED** (Residential .65→.72) |
| **L0** | Residential EUI band | **100–240** kWh/m²/yr (total final) | **REVISED** (was 90–180) |
| **A2** | `HDD_ref` + base | **3200 Kd @18 °C** (not VDI 3807 20/15) | **REVISED** (3300→3200, base clarified) |
| **A3** | era → position `p` | ≤1978 .85 · –94 .60 · –2008 .40 · –2015 .20 · ≥2016 .10 | kept (IWU TABULA eras) |
| **A4** | <12-mo annualisation | archetype monthly shape + HDD weighting | kept |
| **A5** | inverse-variance blend `w` | prior .35 · vintage ×.8 · bill .08/.15 · EPC .22 | kept (backtest-calibrated) |
| **A6** | EPC anchor | **real GEG Energieausweis class bands** (A+ <30 … D 100–130 … H >250) | **REVISED** (was position-in-band) |
| **A7** | footprint → area | storeys=floors or h/3.2 m · usable .8 · `w_area` .35 | kept |
| **A8** | cost/CO₂ fuel-split | gas **EF 0.201** / €0.11 (confirmed) **+ oil 0.266 · district 0.20** | **CONFIRMED + EXTENDED** |
| **A9** | cooling (CDD) | deferred V1 (heating-only HDD) | kept |

### 4b. Validation & sources (2026-06-17 research pass)

- **EPC classes (A6):** German GEG **Energieausweis** efficiency classes are real kWh/m²/yr bands
  (A+ 0–30 · A 30–50 · B 50–75 · C 75–100 · D 100–130 · E 130–160 · F 160–200 · G 200–250 · H >250).
  → replaced the archetype-position heuristic. Caveat: residential, final energy per m² *Gebäudenutzfläche*
  (AN ≈ 1.2× Wohnfläche) → wide σ; NWG letter scales differ.
- **Residential band + `heat_frac` (A1/L0):** Heizspiegel 2025 MFH gas heating+DHW reference **114**
  kWh/m²/yr (range ~70–200); RWI/AGEB Anwendungsbilanz residential space-heating+hot-water ≈ **80%** of
  final energy → band 100–240, h 0.72. Backtest: B011 (1972, unrenovated) now implies heating+DHW ≈158.
- **HDD base (A2):** German VDI 3807 Gradtagzahl uses 20/15 base (≈3500); the gold + open-meteo use an
  **18 °C base** → standardised on 18 °C, `HDD_ref` 3200, to avoid a ~10–15% mismatch.
- **Gas EF/price (A8):** UBA natural-gas EF ≈ **0.20–0.202** kg/kWh (kept 0.201); DE gas ≈ **10–12 ct/kWh**
  2026 (Heizspiegel 12.1 · new-customer ~10; kept 0.11). Extended fuel-split to oil + district heat.
- **Non-residential bands:** cross-checked vs CIBSE TM46 (general office elec 95 + fossil 120 ≈ 215);
  kept — DE-specific NWG benchmarks (ENOB:dataNWG) are a future refinement.

---

## 5. Backtest calibration (closes the honesty loop)

Withhold bills on `B001–B003`, `B011` (+ public Heizspiegel benchmarks); compare the band to actual;
**calibrate the `w` values (A5) so each tier's stated confidence matches its observed hit-rate**. The
synthetic harness (`scripts/estimation_backtest.py`) is green; the real-data calibration runs against
gold `mv_kpi_daily` (task #8).

---

## 6. Implementation

`web-app/backend/app/services/estimation/` — `archetypes.py` · `vintage.py` · `factors.py` · `engine.py`
(`EngineInput → EngineResult`), pure functions, `reference_factors` reused. Harness:
`scripts/estimation_backtest.py`. Next: source assembler (DB→`EngineInput`) + API + `EstimatedBaselineCard`
UI (task #7); real-data calibration (task #8).
