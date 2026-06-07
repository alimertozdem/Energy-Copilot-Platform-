# Page 8 — Real-Time IoT (Flagship) · FINAL Rebind Guide

**Status:** FINAL · **Date:** 2026-06-05 · **Owner:** Mert (product owner / energy reviewer)
**Supersedes:** `page8-v46-FINAL-BINDING-GUIDE.md` (the v46 layout bound to the now-removed
`iot_hot_readings` table).
**Companion script:** `semantic-model/scripts/page8_final_install.cs` (run this first).

---

## 1. Why the page broke (root cause)

The Page 8 visuals were bound to the old v44/v46 measures (`C1_Building_kW_*`, `C2_Zone_*`,
`V1_*`, `V2_*`, `V4_*`). Those measures lived on **`iot_hot_readings`** / **`iot_anomaly_alerts`**,
which were removed from the model during the production refactor. After a DirectLake refresh the
tables lost their columns, so the measures could no longer resolve their references →
**`Missing_References`** (the `C1_Building_kW_Color: Move measure to another table` dialog) → every
bound visual shows *"Something's wrong with one or more fields."*

The fix is two steps, in order:

1. **Model** — run `page8_final_install.cs`: it **sweeps** the orphan measures (clearing all the
   `Missing_References` errors) and **installs** the final Page 8 measure set on the live tables.
2. **Report** — **rebind** each Page 8 visual to the new measures (this document).

> Lineage note: deleting a measure and recreating it on a different table breaks any visual that
> referenced it. That is why the visuals must be repointed once, by hand, after the script runs.

---

## 2. Live data model (verified against `_probe_output.txt`)

All three IoT tables are already in the model and related to `silver_building_master[building_id]`
and `'Date'[Date]`:

| Table | Role | Key columns |
|---|---|---|
| `gold_iot_realtime` | Latest-window readings (C1–C3, V1) | `sensor_type`, `reading_value_avg`, `baseline_value`, `in_setpoint_pct`, `hour_bucket`, `sensor_location`, `event_date` |
| `gold_iot_fdd` | AFDD diagnoses (C4, FDD cards, V5) | `equipment`, `fault_code`, `severity`, `priority_score`, `confidence`, `cost_eur_estimate`, `energy_impact_kwh`, `probable_cause`, `event_date` |
| `gold_iot_daily_summary` | Daily rollups (V2) | `sensor_type`, `sensor_uptime_pct`, `compliance_pct`, `event_date` |

`sensor_type` values present in the data (confirmed from `notebooks/iot/11b_iot_processing.py`):
`building_kwh`, `hvac_kwh`, `HVAC_temp`, `humidity`, `CO2`, plus extended types
(`pv_ac_power`, `lighting_kwh`, `plug_load_kwh`) on full-BMS buildings.

After the script runs, every measure below sits in one display folder: **`IoT (Page 8)`**.

---

## 3. Layout — full flagship showcase

```
┌──────────── Slicers (left) ────────────┬──────────────────────────────────────────────┐
│ Building Name · Building Type          │  [C1 kW]  [C2 Zone %]  [C3 CO₂]  [C4 Faults+€] │  ← KPI row
│                                        │                                                │
│  (FDD summary strip — 4 small cards)   │  [V1  Building & HVAC Power — Last 24h]         │  ← trend
│  Diagnoses · Max Priority ·            │                                                │
│  Avg Confidence · Energy Impact        ├───────────────────────┬────────────────────────┤
│                                        │  [V2 Sensor Uptime]    │  [V5 FDD Findings ]     │  ← matrix + table
└────────────────────────────────────────┴───────────────────────┴────────────────────────┘
```

---

## 4. KPI cards (C1–C4) — top row

Each card = **Card (new)** visual. Callout value = the *Display* measure; font/background color =
the *Color* measure via **conditional formatting → Format style: Field value**.

### C1 — Real-Time Building Power
- Callout value: **`[C1 Building Power Display]`** → shows e.g. `87.3 kW`
- Callout **font color** → conditional → field **`[C1 Building Power Color]`** (green normal /
  amber > 105 % of baseline / red > 120 %)
- Reference label (type manually): `Building Power (Live)`
- *If it shows `-- kW`:* the table has no `sensor_type = "building_kwh"` rows for the current filter.

### C2 — Zone Comfort Compliance (EN 16798)
- Callout value: **`[IoT Zone Compliance Display]`** → `91% in setpoint (EN 16798)`
- Callout **font color** → field **`[IoT Zone Compliance Color]`** (≥90 green / ≥75 amber / red)

### C3 — Indoor Air Quality (CO₂)
- Callout value: **`[IoT CO2 Display]`** → `Good 612 ppm` / `Fair …` / `Poor …`
- Callout **font color** → field **`[IoT CO2 Color]`** (<800 green / ≤1200 amber / red)

### C4 — Active Faults + Estimated Cost
- Callout value: **`[IoT C4 Label v59]`** → `All Clear` or `3 faults - Est. EUR 47 today`
- Callout **background color** → field **`[IoT C4 Color v59]`** (0 green / ≤2 amber / red)

---

## 5. FDD summary strip — 4 small cards (left, under slicers)

Plain **Card** visuals, no conditional formatting:

| Card | Measure |
|---|---|
| Diagnoses today | `[IoT FDD Diagnoses Today]` |
| Max priority (0–100) | `[IoT FDD Max Priority]` |
| Avg confidence | `[IoT FDD Avg Confidence Pct]` |
| Energy impact today | `[IoT FDD Energy Impact kWh Today]` (kWh) |

---

## 6. V1 — "Building & HVAC Power — Last 24h" (line chart)

| Field slot | Bind to |
|---|---|
| X-axis | `gold_iot_realtime[hour_bucket]` (string `MM-dd HH:00` → ~24 clean categorical points) |
| Y series 1 | `[Realtime Building Power kW]` — legend: *Building Total* |
| Y series 2 | `[V1 HVAC Power kW]` — legend: *HVAC Only* |
| Y series 3 | `[Realtime Building Baseline kW]` — legend: *Baseline*; format dashed grey |

- Sort X-axis ascending by `hour_bucket`.
- **Edit interactions:** Building slicer → filters V1. (Date slicer, if present → filters V1 only,
  not the cards.)

---

## 7. V2 — Zone Comfort heatmap + Sensor Health strip

The old "Sensor Uptime matrix" is **replaced**. Reason: it was a date×type grid of
`round(avg(reading_quality))` mislabelled as "uptime", and the IoT tables are a rolling window
(always ~2-3 days) so a date axis is structurally wrong. Measures: run `page8_sensorhealth.cs`.

### 7a. Zone Comfort heatmap — Matrix on `gold_iot_realtime`

| Field slot | Bind to |
|---|---|
| Rows | `gold_iot_realtime[sensor_location]` |
| Columns | `gold_iot_realtime[sensor_type]` |
| Values | `[Zone Comfort Cell Pct]` — % of readings within setpoint |

- **Visual-level filter:** `sensor_type` is one of `HVAC_temp`, `humidity`, `CO2` (comfort sensors).
- **Cell background** → conditional formatting → Format style **Gradient** on
  `[Zone Comfort Cell Pct]` → Min = number **50** muted red `#E6A0A0`, Max = number **100** muted
  green `#A9DFBF`. A red cell = that zone's sensor is out of comfort range often.
- Best viewed with a **building selected** (across all buildings, same-named zones aggregate).
- Title: **"Zone Comfort — % in setpoint (recent)"**.

### 7b. Sensor Health strip — 3 small Cards (compact, beside/above the heatmap)

| Card | Measure |
|---|---|
| Data Quality | `[Data Quality Pct]` (latest day; honest avg reading-quality — **not** "uptime") |
| Active Sensors | `[Active Sensor Locations]` |
| Anomaly Rate | `[Sensor Anomaly Rate Pct]` |

- Optional richer Data Quality card: callout `[Data Quality Display]`, font color `[Data Quality Color]`.
- *(Future)* to turn "Data Quality" into a true device **Uptime %**, add an expected-vs-received
  reading count in `notebooks/iot/11b_iot_processing.py` and repoint `[Data Quality Pct]`
  (notebook re-run).

---

## 8. V5 — "FDD Findings" table ⭐ (the flagship visual)

**Visual type:** Table, bound to **`gold_iot_fdd`**.

| Column | Source | Notes |
|---|---|---|
| Equipment | `gold_iot_fdd[equipment]` | text |
| Fault | `gold_iot_fdd[fault_code]` | text |
| Severity | `gold_iot_fdd[severity]` | text |
| Priority | `[IoT FDD Priority Band]` | Urgent / High / Medium / Low |
| Confidence | `[IoT FDD Row Confidence]` | `0%` format |
| Est. cost | `[IoT FDD Row Cost Label]` | `Est. EUR x.xx` |
| Probable cause | `gold_iot_fdd[probable_cause]` | text (wrap) |

- **Sort:** the visual by `gold_iot_fdd[priority_score]` **Descending** (worst first). Add
  `priority_score` to the table, sort by it, then hide that column (Format → drag out, or set to
  a thin width) — or use the column header sort once and lock it.
- **Row color:** conditional formatting on the *Priority* (or *Equipment*) column →
  Format style **Field value** → **`[IoT FDD Priority Color]`**.
- **DoD:** building **B007** (Copenhagen Net-Plus) surfaces a PV/HVAC fault at or near the top.

---

## 9. Slicers + edit interactions

- **S1 Building Name** (`silver_building_master[building_name]`) → filters **all** visuals.
- **S2 Building Type** (`silver_building_master[building_type]`) → filters all visuals.
- **V5 row click** → cross-filters nothing by default (keep it a read view); optionally let it
  filter the FDD summary cards.
- Cards C1–C4 should stay **live** — do not wire a Date slicer to them.

---

## 10. ✅ Data freshness — resolved (latest-available-day)

The FDD cards (Diagnoses, Energy impact) and C4 originally filtered `event_date = TODAY()`, so they
read blank / *All Clear* whenever the simulator data didn't reach today. **`page8_polish.cs` already
fixes this** — those measures now use the **latest day present in the data** (respects the building
slicer). When the IoT pipeline runs daily, "latest day" becomes literally today, no further change.

---

## 11. Validation checklist

- [ ] Scripts ran in order: `page8_final_install.cs` → `page8_polish.cs` → `page8_sensorhealth.cs`;
      no red errors in the model.
- [ ] **C1** shows a kW number (≈ 50–200 for simulator data), not `-- kW`.
- [ ] **C2** shows `…% in setpoint (EN 16798)` with a green/amber/red color.
- [ ] **C3** shows `Good/Fair/Poor … ppm`.
- [ ] **C4** shows `N faults - Est. EUR … today` — no longer stuck on *All Clear*, and it must agree
      with the FDD table (if the table lists High/Urgent faults, C4 cannot say All Clear).
- [ ] **FDD summary cards** all populate: Diagnoses, Max priority, Avg confidence, Energy impact.
- [ ] **V1** draws three series across ~24 hourly buckets (Building, HVAC, dashed Baseline); Y-axis
      starts above 0 so the curve is visible.
- [ ] **V5** lists diagnoses worst-first with no blank Priority/Confidence/Cost cells; B007 PV/HVAC
      fault near the top; Total row off.
- [ ] **Zone Comfort heatmap** fills with muted green/red; red cells flag out-of-comfort zones.
- [ ] **Sensor Health strip** shows Data Quality %, Active Sensors, Anomaly Rate %.
- [ ] No visual references `iot_hot_readings` / `iot_anomaly_alerts`.
