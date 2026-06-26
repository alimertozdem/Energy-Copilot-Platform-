# Root-fix: "savings > bill" + 999-yr payback in recommendations (2026-06-24)

## What was wrong (verified against live `mv_recommendations`, assessed 2026-06-22)

The recommendation values shown in the reports were physically impossible:

- **Total recommended saving exceeded the whole annual energy bill** for 8/10 buildings
  (B004 207%, B005 206%, B003 149%, B002 136%, B001 136%, B007 116%, B008 102%).
  Even single measures hit 65–76% of the bill (B005 CHP, B004).
- **Payback 999 yr** (B003 heat pump — annual saving was **−€2,290**, so the engine
  wrote a 999 sentinel).
- **Heat pump that increases CO₂** still listed as a benefit (B002 Istanbul, −15 t —
  carbon-heavy TR grid).
- **Sub-metering credited a direct kWh saving** (B001 €15.6k) when it is only an enabler.

## Root cause

Notebook **04 (simulation) → 06 (recommendation engine)** credit each measure as a
percentage of the **electricity-only** bill. Heating measures (CHP, BMS, heat pump)
therefore over-credit, and a gas→electric heat-pump switch looks like a loss on an
electricity-only ledger (→ 999-yr payback).

**The fix already exists in the repo but was never run in Fabric:**

- `notebooks/gold/03b_total_energy_ledger.py` — builds `gold_energy_ledger`
  (electricity **+ fuel/gas** via the validated degree-day model) so cost/EUI sit on a
  true total-energy basis.
- `notebooks/recommendation/06b_recommendation_calibration.py` — re-bases every measure
  on **total** annual energy cost, applies realistic per-measure ceilings, an aggregate
  ceiling (Σ ≤ 35% × EPC factor of total cost), recomputes payback + NPV, zeroes
  sub-metering, and recomputes the heat pump properly (avoided gas € − extra electricity €).

So the live data is still the **pre-calibration** output. Running the chain fixes it.

## Change made this session (2026-06-24)

- `06b` — added a guard so a **heat pump that does not cut CO₂** (carbon-heavy grid) is
  **not promoted as a saving** (its saving is nulled → shows "—", ranks low).
  *Review this assumption.*
- Frontend/back-end **display guards** (already in the web-app push): any payback ≥ 40 yr
  or null shows "—" in every report (`reportKit.fmtPayback` + `finance_model` /
  `heating_assessment` caps). This protects the reports **even before** the Fabric re-run.

## Run order in Fabric (do not skip a step)

1. **`03b_total_energy_ledger.py`** → writes `gold_energy_ledger`.
2. **`06_recommendation_engine.py`** → base recommendations (unchanged).
3. **`06b_recommendation_calibration.py`** → calibrates in place (Delta MERGE).
4. **Re-materialize** `gold_recommendations` → Postgres `mv_recommendations`
   (the materialize notebook), so the app/reports read the calibrated values.

## Assumptions to confirm (energy review)

- **03b knobs** (already validated 2026-06-19, doc §11): `PHI_HDD=1.5` (biggest),
  `C_ENV=1.5`, `ETA_BOILER=0.90`, DHW-by-type. See `docs/strategy/total-energy-ledger.md`.
- **06b ceilings** (`MEASURE_CAP_PCT`, screening bands — Energieberater-tunable):
  CHP 22%, insulation 20%, HVAC scheduling 15%, BMS 10%, PV 25%, deep retrofit 35%,
  sub-metering 0%. Aggregate `TOTAL_CAP_PCT=35%` × EPC factor (A 0.35 … G 1.0).

## Verification (built in)

`06b` CELL 6 prints **total recommended saving as % of total annual energy cost** per
building. After the run, **every building must be ≤ ~35%** (less for efficient A/B
stock). If any row is still > 35%, stop — the ledger (03b) or a cap band is off.
