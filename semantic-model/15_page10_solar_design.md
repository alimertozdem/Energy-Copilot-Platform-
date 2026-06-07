# Page 10 — Solar (Full Showcase) — Build Guide

**Status:** design / build-ready · **Created:** 2026-06-01
**Owner action:** build in Power BI Desktop using this guide, then publish.

A single dedicated page that tells the whole solar story: strategic KPIs
(generation, self-consumption, performance, CO₂) **plus** the new real-time PV
power and `PV_UNDERPERFORMANCE` fault detection (Solar B) **plus** the
`INSTALL_SOLAR` investment opportunity (Solar E).

All strategic measures already exist in the model (`02_dax_measures.dax`, on
`gold_kpi_daily`). Only the real-time / fault / opportunity measures are new
(Section 2 below).

---

## 0. Scope decision (already approved: "Full Solar")

This page spans **two fact families**:

| Data | Table | Used for |
|---|---|---|
| Strategic solar KPIs | `gold_kpi_daily` | generation, self-consumption, PR, yield, CO₂ |
| Real-time PV power | `gold_iot_realtime` | today's PV power trend |
| PV faults | `gold_iot_fdd` | `PV_UNDERPERFORMANCE` alerts + € loss |
| Investment opportunity | `gold_recommendations` | `INSTALL_SOLAR` for non-PV buildings |

Because real-time PV + faults come from the IoT tables (previously isolated on
Page 8), those two tables must be **added to this semantic model** — Section 1.

---

## 1. Model prerequisite (do this first)

1. **Add tables** from the Lakehouse to the semantic model (DirectLake):
   `gold_iot_realtime` and `gold_iot_fdd`.
   (`gold_recommendations` is already in the model from Page — Actions.)

2. **Relationships** — relate the new tables to the same building dimension your
   existing facts use (the table `gold_kpi_daily[building_id]` relates to —
   referred to here as `dim_building`):
   - `gold_iot_realtime[building_id]` → `dim_building[building_id]` (single, 1→*)
   - `gold_iot_fdd[building_id]` → `dim_building[building_id]` (single, 1→*)
   - If you have a date dimension: `gold_iot_realtime[event_date]` → `dim_date[date]`.
   - If the model has **no** building dimension and facts join on raw
     `building_id`, create a minimal `dim_building` (distinct building_id +
     name + country + `pv_capacity_kwp`) and relate all facts to it. This also
     powers the building slicer for the whole page.

3. **Verify** no relationship is ambiguous (single-direction from the dimension).

> Why a shared dimension: the page's building slicer must filter `gold_kpi_daily`,
> `gold_iot_realtime`, `gold_iot_fdd`, and `gold_recommendations` together. A
> common `dim_building` is the clean way (avoids cross-filter surprises).

---

## 2. New DAX measures (paste into Tabular Editor / the model)

Create a display folder `Solar — Realtime & Opportunity` and add:

```dax
// Average PV AC power across the filtered window (kW). Card + reference.
Realtime PV Power kW =
CALCULATE(
    AVERAGE(gold_iot_realtime[reading_value_avg]),
    gold_iot_realtime[sensor_type] = "pv_ac_power"
)
```

```dax
// Peak PV power in the filtered window (kW).
Peak PV Power kW =
CALCULATE(
    MAX(gold_iot_realtime[reading_value_max]),
    gold_iot_realtime[sensor_type] = "pv_ac_power"
)
```

```dax
// Count of active PV underperformance diagnoses (Solar B fault rule).
PV Underperformance Count =
CALCULATE(
    COUNTROWS(gold_iot_fdd),
    gold_iot_fdd[fault_code] = "PV_UNDERPERFORMANCE"
)
```

```dax
// Estimated € lost to PV underperformance (sum of diagnosed cost).
PV Loss EUR =
CALCULATE(
    SUM(gold_iot_fdd[cost_eur_estimate]),
    gold_iot_fdd[fault_code] = "PV_UNDERPERFORMANCE"
)
```

```dax
// Installed PV nameplate across the filtered portfolio (kWp).
// Adjust the table name to your building dimension.
Solar Capacity kWp =
SUM(dim_building[pv_capacity_kwp])
```

```dax
// Buildings flagged for a new PV install (Solar E recommendation).
INSTALL_SOLAR Opportunities =
CALCULATE(
    COUNTROWS(gold_recommendations),
    gold_recommendations[action_type] = "INSTALL_SOLAR"
)
```

```dax
// Location-specific yield (kWh/kWp). NEW — verify the column exists in
// gold_kpi_daily (solar_specific_yield_kwh_kwp). If it lives only in the
// hourly table, source it from there or roll it into the daily build.
Avg Solar Specific Yield kWh kWp =
AVERAGEX(
    FILTER(gold_kpi_daily, gold_kpi_daily[solar_specific_yield_kwh_kwp] <> BLANK()),
    gold_kpi_daily[solar_specific_yield_kwh_kwp]
)
```

**Already-existing measures reused on this page** (no need to create):
`[Total Solar Generated kWh]`, `[Solar Self Consumed kWh]`,
`[Total Solar Exported kWh]`, `[Solar Coverage Pct]`,
`[Avg Self Consumption Rate Pct]`, `[Avg Solar PR Pct]` (0–100, fault < 75),
`[Renewable Energy Rate Pct]`, `[Total CO2 Savings from Solar tCO2]`,
`[Total Solar Savings EUR]`, `[Net Grid Consumption kWh]`.

---

## 3. Page layout (row by row)

Page name: **Solar**. Background + theme: identical to existing pages (dark
EnergyLens emerald). Use the same card/visual styling as Page 2.

### Row 1 — KPI cards (six small cards across the top)

| Card | Measure | Format |
|---|---|---|
| Total Generation | `[Total Solar Generated kWh]` | `#,##0` kWh |
| Self-Consumption | `[Avg Self Consumption Rate Pct]` | `0.0` % |
| Avg Performance Ratio | `[Avg Solar PR Pct]` | `0.0` (fault < 75) |
| CO₂ Avoided | `[Total CO2 Savings from Solar tCO2]` | `#,##0.0` t |
| Renewable Rate | `[Renewable Energy Rate Pct]` | `0.0` % |
| Installed Capacity | `[Solar Capacity kWp]` | `#,##0` kWp |

### Row 2 — generation over time + split

| Visual | Type | Fields |
|---|---|---|
| **Solar Generation & Use** | Stacked area (or line+stacked column) | Axis: date · Series: `[Solar Self Consumed kWh]` (emerald), `[Total Solar Exported kWh]` (light gold). Title: *Solar Generation — Self-Consumed vs Exported* |
| **Self-Consumption Split** | Donut | `[Solar Self Consumed kWh]` vs `[Total Solar Exported kWh]`, current period. Center label: `[Avg Self Consumption Rate Pct]` |

### Row 3 — per-building performance

| Visual | Type | Fields |
|---|---|---|
| **Performance Ratio by Building** | Clustered bar | Axis: `dim_building[building_id]` · Value: `[Avg Solar PR Pct]` · **Constant line at 75** (red) = fault threshold. Bars below 75 → conditional red. Title: *PV Performance Ratio (fault < 75)* |
| **Specific Yield by Building** | Clustered bar | Axis: `dim_building[building_id]` · Value: `[Avg Solar Specific Yield kWh kWp]`. Shows location effect (north vs south). Title: *Specific Yield (kWh/kWp)* |

### Row 4 — real-time PV + fault alerts (Solar B)

| Visual | Type | Fields |
|---|---|---|
| **Today's PV Power** | Line | Axis: `gold_iot_realtime[hour_bucket]` (categorical, designed for PBI) · Value: `AVERAGE(gold_iot_realtime[reading_value_avg])` · Legend: `gold_iot_realtime[building_id]` · **Visual-level filter: `sensor_type = "pv_ac_power"`**. Title: *Live PV Power by Building (kW)* |
| **PV Underperformance Alerts** | Table | **Visual filter: `gold_iot_fdd[fault_code] = "PV_UNDERPERFORMANCE"`** · Columns: `building_id`, `severity`, `occurrence_count`, `cost_eur_estimate` (or `[PV Loss EUR]`), `description`. Sort: `priority_score` desc. Title: *PV Faults — Est. € Loss* |

> Expected today: **B007** appears here (injected inverter fault) with a
> High/Medium severity and an estimated € loss — the headline "AI catches a
> solar fault" demo moment.

### Row 5 — investment opportunity (Solar E)

| Visual | Type | Fields |
|---|---|---|
| **Solar Install Opportunities** | Table | **Visual filter: `gold_recommendations[action_type] = "INSTALL_SOLAR"`** · Columns: `building_id`, `country_code`, `priority_label`, `capex_eur`, `payback_years`, `npv_eur`, `co2_saving_kg`. Sort: `payback_years` asc. Title: *Where to Add Solar Next* |

Small KPI strip next to Row 5 (optional): `[INSTALL_SOLAR Opportunities]`,
`[PV Underperformance Count]`, `[PV Loss EUR]`, `[Total Solar Savings EUR]`.

---

## 4. Slicers & page-level filters

- **Building slicer** (`dim_building[building_id]` or `building_name`) — filters
  the whole page across all four tables (works thanks to Section 1 relationships).
- **Date slicer** (`dim_date`) for Rows 1–3. Row 4 (real-time) is the recent
  IoT window; leave it on the latest data (don't constrain to a single day).
- Keep the same slicer placement/style as your other pages for consistency.

---

## 5. Brand & formatting

- Colors: self-consumed = `#1D9E75` (emerald), exported = `#F1C40F` (light gold),
  fault/red = `#EF4444`, grid = neutral grey — matching Page 2's solar palette.
- Percentages: format `0.0`, never `0%` (model convention).
- All titles in English (app UI language).
- Cards: large value + small caption, same component as Pages 1–7.

---

## 6. Build checklist

- [ ] Add `gold_iot_realtime` + `gold_iot_fdd` to the semantic model
- [ ] Create / confirm `dim_building` relationships (4 fact tables)
- [ ] Add the 7 new measures (Section 2); confirm `solar_specific_yield_kwh_kwp` column
- [ ] Build Rows 1–5 visuals
- [ ] Add building + date slicers
- [ ] Verify B007 shows in the PV underperformance table
- [ ] Verify building slicer cross-filters all visuals
- [ ] Publish; embed slot stays the same (locked report template)

---

## Notes / open items

- **Real-time on a strategic page:** Row 4 mixes the IoT (recent window) with
  daily KPIs. That's intentional for the showcase, but the IoT window is short
  (driven by `11b_iot_processing` `lookback_hours`). Keep Row 4 unfiltered by the
  page date slicer so it always shows the latest PV data.
- **PR threshold:** `[Avg Solar PR Pct]` returns 0–100; the in-model comment flags
  **< 75** as soiling/shading/fault. The gold KPI engine uses < 0.65 as a hard
  problem — both are fine; the page reference line uses 75 to match the measure.
- If you'd rather not extend this model with the IoT tables, fall back to the
  "Strategic Solar" scope (Rows 1–3 + 5 only) — no model change needed.
