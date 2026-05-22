# Page 5 — v55 Headcount Surgical Fix Guide

**Date:** 2026-05-21
**Scope:** Page 5 (`05_occupancy_analysis`) — fix broken V6 building bar chart

## 1. The Bug (what Power BI told us)

```
The report measure 'gold_occupancy_profile'[Building Avg Headcount Business Hours]
has a syntax or semantic error at line 3, position 19, reported by Analysis
Services: 'Column estimated_headcount in table gold_occupancy_profile cannot
be found or may not be used in this expression.'
```

## 2. Root Cause

The deployed `08_occupancy_prediction.py` (Fabric notebook) writes a Delta table
with **9 columns only**:

```
building_id, day_of_week, hour_of_day, occupancy_probability,
profile_source, calibration_weeks, confidence_score,
model_version, computed_at
```

`estimated_headcount` was only present in the deprecated `_FABRIC_KOPYALA.py`
copy. Two DAX measures in `38_dax_v29_page5_occupancy_fix.dax` still reference
it, so Page 5 fails as soon as the bar chart visual renders.

## 3. Decision — Why Surgical, Not Pipeline Rerun

| Option | Cost | Risk |
|---|---|---|
| Add column back to notebook 08 + full pipeline rerun | 30–60 min compute + revalidate Page 5 | High — notebook has the OPTIMIZE IF EXISTS bug + reset risk |
| **Surgical DAX rewrite (chosen)** | 2 min in TE2 | Near-zero |
| Remove measures entirely | 2 min | Loses V6 visual entirely |

We pick the surgical rewrite because `silver_building_master[max_occupants]` is
already in the model, so we can compute headcount on-the-fly:

```
headcount = occupancy_probability × max_occupants
```

This is mathematically identical to what the deleted column produced.

## 4. How to Apply

### Step A — Tabular Editor 2 (fastest)

1. In Power BI Desktop, open `EnergyLens` report (live to `EnergyCopilotModel`).
2. External Tools → **Tabular Editor**.
3. Open the *Advanced Scripting* tab and paste the contents of
   [`semantic-model/scripts/page5_v55_headcount_fix_install.cs`](../semantic-model/scripts/page5_v55_headcount_fix_install.cs).
4. **Run** (F5). Confirm the Info log shows both measures updated.
5. **Save** (Ctrl+S).
6. Switch back to Power BI Desktop → Home → **Refresh**.

### Step B — Manual (if TE2 unavailable)

In Power BI Desktop, open Model view → find the two measures on
`gold_occupancy_profile` and replace their expression bodies with the DAX in
[`semantic-model/67_dax_v55_page5_headcount_surgical_fix.dax`](../semantic-model/67_dax_v55_page5_headcount_surgical_fix.dax).

## 5. Validation Checklist

After refresh:

- [ ] No yellow warning triangles on Page 5 measures.
- [ ] V6 bar chart renders 6 bars (no error panel).
- [ ] Portfolio view shows ~300–500 avg business-hours headcount.
- [ ] Drill to B005 Frankfurt Healthcare → ~450.
- [ ] Drill to B003 Hamburg Logistics → ~45.
- [ ] `Building Peak Headcount` (if used in tooltip) returns higher values
      than the avg measure.

## 6. Why It Works

* `TREATAS(VALUES(gold_occupancy_profile[building_id]), silver_building_master[building_id])`
  pushes the current building filter context onto `silver_building_master`,
  regardless of relationship state.
* Bracketing with `ISBLANK / =0` guards portfolio-empty contexts and prevents
  `#NUM` div-by-zero artifacts.
* The 8–18 hour filter on the first measure matches the original definition —
  business-hours mean, not the 24h average.

## 7. Follow-up (Optional, Post-Trial)

The notebook's `_FABRIC_KOPYALA.py` and the active `08_occupancy_prediction.py`
should be reconciled — either by re-adding `estimated_headcount` to the active
notebook's `OUTPUT_SCHEMA` (Cell 9), or by deleting the FABRIC_KOPYALA copy so
the schema source-of-truth is unambiguous. Deferred until after 2026-05-21
trial deadline.
