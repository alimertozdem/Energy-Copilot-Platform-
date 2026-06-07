# Gate D — Per-Page Visual Binding Checklist

**Prereq:** the model is production-ready (0 errors). All measures below exist and are verified
against the live schema. Work one page at a time; after each page, refresh and eyeball.

---

## Prerequisite — create the `Time Grain` field parameter (once)

Needed for the Hourly/Daily/Monthly toggle on pages 1/2/3/4/7.

Power BI Desktop → **Modeling → New parameter → Fields**. Name: `Time Grain`. Uncheck
"Add slicer to this page". Add these three fields **in order**:

1. `gold_kpi_hourly[hour_utc]`  → rename row to **"Hourly"**
2. `'Date'[Date]`               → **"Daily"**
3. `'Date'[YearMonth]`          → **"Monthly"**  (NOT `Date[Month]` — that merges all years' Januaries)

This creates a `Time Grain` table. Then the `Selected Grain Label` measure resolves — re-run
`consolidate_measures_v57_v60.cs` once so it stops skipping that measure.

**Toggle pattern (reuse on every time-series visual):** Line chart → X-axis = `Time Grain` →
Values = the `TS …` measure(s) → add a **Tile slicer** bound to `Time Grain` (single-select,
default Daily).

---

## Page 1 — Portfolio Overview
- **ADD:** Time-Grain toggle on the portfolio consumption trend → Values = `[TS Consumption kWh]`.
- **VERIFY:** EUI compares **annualized** vs benchmark; CO₂/cost come from the ref layer.
- **DELETE:** none.

## Page 2 — Building Deep-Dive ⭐
- **ADD:** Time-Grain toggle on the demand/grid line → `[TS Avg Demand kW]`, `[TS Net Grid kWh]`
  (+ `[TS Solar Generated kWh]` for solar buildings).
- **ADD:** dedicated **24-hour load profile** chart → X = `gold_kpi_hourly[hour]` (0–23),
  Y = `[Profile Avg Demand by Hour kW]`; add a **Base Load Ratio** card = `[Base Load Ratio Pct]`.
- **VERIFY:** climate-adjusted EUI uses the ratio method (the engine column is `climate_adjusted_eui`).

## Page 3 — Anomaly Detection
- **ADD:** Time-Grain toggle on the consumption-vs-baseline context chart.
- **VERIFY/REBIND:** every visual reads `gold_anomaly_log` only (single engine). Remove any visual
  still bound to a legacy anomaly source.

## Page 4 — Forecasting
- **ADD:** confidence band → line `[Forecast Predicted kWh]` + shaded area between
  `[Forecast Lower Bound kWh]` and `[Forecast Upper Bound kWh]`.
- **ADD:** Time-Grain toggle on **actuals only** (`[TS Consumption kWh]`); forecast stays daily.
- **RELABEL:** the accuracy figure → "in-sample fit" (MAPE is in-sample).

## Page 5 — Decision Support
- **RELABEL:** the "CSRD score" card → bind to **`[EU Taxonomy Carbon Score]`** (v57); keep the
  "CSRD" wording only for a disclosure-readiness indicator.
- **VERIFY:** `gold_simulation_results` is live (financial scores populate the recommendations).

## Page 6 — Sustainability / ESG ⭐ (highest commercial value)
- **REBIND:** EPC heat map → `[EPC Score Area-Weighted kWh m2]` / `[EPC Class Area-Weighted]`
  (area-weighted, not a plain average).
- **REBIND:** CRREM stranding line → building intensity `[Carbon Intensity S1S2 kgCO2 m2 yr]`
  vs pathway `[CRREM Pathway 2C kgCO2 m2 yr]`; gap = `[CRREM Stranding Gap S1S2 kgCO2 m2 yr]`,
  status = `[CRREM Stranding Status]`.
- **ADD cards:** `[EU Taxonomy Carbon Score]` and `[CSRD Disclosure Readiness Pct]`.
- **SCOPE 2:** show **location vs market** as separate donut slices (`scope2_location_tco2` vs
  `scope2_market_tco2`); add an **"est."** label on the Scope 3 slice.
- **DELETE:** the old single "CSRD score" card and any Scope-2-only CRREM measure.

## Page 7 — HVAC & Envelope
- **ADD:** label the HVAC-share / heating-cooling split visual "modeled (HDD/CDD method)".
- **ADD:** Time-Grain toggle on consumption + temperature (`[TS Consumption kWh]`,
  `[TS Avg Temperature C]`). COP / split visuals stay monthly.
- **VERIFY:** `system_label` / `renovation_reason` render in English.

## Page 8 — Real-Time IoT ⭐ (flagship)
- **ADD V5 "FDD Findings" table** → bind to `gold_iot_fdd`; columns: `equipment`, `fault_code`,
  `severity`, `[IoT FDD Priority Band]`, `[IoT FDD Row Confidence]`, `[IoT FDD Row Cost Label]`,
  `probable_cause`; **sort by `priority_score` DESC**. (Use `[IoT FDD Priority Color]` for
  conditional formatting.)
- **C2** (zone compliance) → `[IoT Zone Compliance Display]` + `[IoT Zone Compliance Color]`.
- **C4** (faults + €) → `[IoT C4 Label v59]` + `[IoT C4 Color v59]`.
- **Cards:** `[IoT FDD Diagnoses Today]`, `[IoT FDD Max Priority]`, `[IoT FDD Avg Confidence Pct]`,
  `[IoT FDD Energy Impact kWh Today]`.
- **DELETE:** any visual still bound to `iot_anomaly_alerts` / `iot_hot_readings`.

## Page 9 — Battery Dispatch & ROI
- **VERIFY:** all v56 visuals render (measures restored). V7 SoH/cycles now populated
  (`battery_health_percent`, `cumulative_cycles`); C1/C2 use `is_active_strategy`.
- **VERIFY:** EU-2023/1542 compliance flag visible (`[C5 EU Compliance Status Text]` /
  `[I3 Compliance Flag Text]`).
- **KEEP:** V2 24h chart bound to `gold_battery_hourly_dispatch` (charge/discharge/soc/grid_price_index).

---

## Suggested order
1. **Page 6** (money page — CSRD niche) and **Page 8** (flagship IoT) first — highest value, fully prepped.
2. **Hourly toggle** across 1/2/3/4/7 (after the `Time Grain` parameter exists).
3. **Page 2** 24h profile, **Page 4** band, **Page 9** verify, **Page 5/7** relabels.

After each page: refresh, sanity-check the numbers, then move on.
