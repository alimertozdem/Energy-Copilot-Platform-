# Continue: EnergyLens — Engine Calibration (B), then Report Finalization resume

> Paste this whole file as the opening prompt of a NEW conversation to continue.
> Project memory ([[report-finalization-2026-06-18]]) auto-loads the full method,
> verified thresholds, and gotchas — this prompt orients the new session.

## Where we are
Page-by-page, GATED finalization of the embedded 10-page Power BI report
(semantic model `EnergyCopilotModel`).
- **FINAL / approved:** Page 1 Portfolio Overview · Page 2 Building Detail ·
  Page 3 Anomalies & Alerts. Fix scripts in `semantic-model/scripts/pageN_fixpack_*.csx`.
- **PAUSED:** Page 4 Forecast & Recommendations — we hit the real blocker.

## Why we pivot to engine calibration first
Report-layer polish hit a ceiling: the synthetic **data engines** produce
physically implausible numbers. Verified against live Supabase mirror
(`mv_*`, project `vuiqfaklvlbushkiapnp`):
- **Recommendations:** 8/10 buildings' total recommended annual savings EXCEED
  their annual energy cost (102–219%). You cannot save more energy than you use.
- **EUI:** non-office building types read 2–3× their sector benchmark.
- **Anomalies:** 2,962 total (~100/building/month) — unrealistic.

No DAX fix repairs "savings > bill". Fix at the generators. Decision (Mert):
**B (calibrate engines) → A (interim report caps + Page 4 bug fixes) → resume pages.**

---

## TASK B (this conversation, FIRST): recalibrate the generator notebooks
Locate the generators (sample-data / recommendation / anomaly notebooks — in
`notebooks/` or the Fabric workspace; memory mentions "sample data v5.1 generator",
`gold_recommendations`, `gold_anomaly_log`). **Claude writes the calibration logic;
Mert runs the notebooks in Fabric**, then re-mirrors to Supabase `mv_*` and
Claude re-verifies ranges with SQL.

### B1 — Recommendation engine (`gold_recommendations`)
- Cap each building's **TOTAL** `annual_saving_eur` at **~30–40% of its annual
  energy cost** (deep-retrofit ceiling; >50% is implausible).
- Per-measure realistic saving ranges (% of building annual consumption/cost):
  LED 2–5% · HVAC scheduling/controls 5–15% · BMS optimization 5–10% ·
  insulation/envelope 10–20% · peak-demand mgmt 3–8% (cost) ·
  **sub-metering ~0% DIRECT** (it's an enabler — set saving ≈ 0 or flag
  "enables 2–5% via behaviour", do NOT credit direct kWh).
- Ensure the **sum** of a building's measures ≤ the total cap (7 measures each at
  max must not sum past it).
- Recompute `payback_years = net_capex_eur / annual_saving_eur` after capping.

### B2 — Consumption / EUI generator (`gold_kpi_daily`)
- Calibrate **electricity-EUI per building TYPE** into sector bands (kWh/m²·yr):
  Office 50–130 · Hotel 80–150 · Healthcare 90–200 · Education 60–120 ·
  Retail 100–250 · Logistics 30–70 · Lab 200–450 · Data_Center 800–2000.
- Currently too high (scale consumption down to land in-band): Healthcare 513,
  Hotel 278, Retail 244, Education 158. **Keep DC (~1615 is fine).**
- Note: model EUI = electricity only; CO2 = consumption × grid factor.

### B3 — Anomaly generator (`gold_anomaly_log`)
- Reduce volume to realistic: **~1–3 anomalies/building/month** (not 100+).
  Keep resolved-history modest; keep the current OPEN-anomaly logic (9 open is fine:
  2 Critical + 2 High + 5 Medium, mostly SOLAR_UNDERPERFORM).

After each engine change: re-mirror gold→`mv_*`, then SQL-verify the numbers land
in plausible ranges before moving on.

---

## TASK A (after B): interim report safety + Page 4 finish
- If B is thorough the report shows correct numbers (A is then light). Otherwise
  add DAX clamps as a safety net.
- Fix Page 4 measure bugs regardless: **7-Day Forecast** + **Savings Potential**
  return Blank for a single building; forecast end-spike artifact; hardcoded goals;
  sub-metering-as-saving.

## THEN: resume page-by-page (same 4-axis GATED method)
Finish Page 4, then **5 Occupancy · 6 Sustainability Compliance · 7 HVAC ·
8 IoT (visuals broken) · 9 Battery (ROI absurd → suppress numbers) · 10 Solar.**
One page at a time; don't advance until Mert says "approved".

## Deferred model-layer workstreams (do once, helps every page)
1. **Date-dimension relationship:** `'Date'`↔`gold_kpi_daily` is ACTIVE, yet a
   `'Date'[Date]` slicer does NOT filter the fact (only `gold_kpi_daily[date]`
   does) — so Page 2/3 time-series charts ignore the slicer (show 2023–25).
   Investigate cardinality/cross-filter direction and any competing `data`-table
   path. Goal: one date dimension filters cards AND charts consistently.
2. **Performance → Import mode:** model is DirectLake on small capacity = slow;
   data is tiny → convert to Import (sub-second). Handle RLS fixed-identity →
   import refresh credential. Embedded customer experience unchanged, just faster.

## Working conventions (keep)
- Claude cannot render PBI → Mert screenshots per page. Claude reads the repo
  (`web-app/frontend/lib/config/reportPages.ts`, DAX files, `semantic-model/measures_dump.txt`)
  and **verifies every number via Supabase `mv_*` before claiming it** — no "probably".
- Fixes = **Tabular Editor C# scripts** in `semantic-model/scripts/`. NO LINQ
  (his TE build rejects it) — use a no-LINQ `foreach` upsert; never alias/duplicate
  an existing measure; any DAX with embedded quotes must be a `@"verbatim"` string.
- Energy logic locked: EUI = electricity-only, annualized, master
  `gross_floor_area_m2`; type-index gauge (`P1 EUI Index Pct`, 100 = sector norm).
  DAX string compare is case-insensitive. `REMOVEFILTERS()` (empty) makes a KPI
  slicer-proof; `ALL(table)` does NOT remove a dimension-sourced filter.
- Tone: advisor, TR chat / EN app; lead with the uncomfortable truth; confidence
  tags [Kesin]/[Muhtemel]/[Tahmin]; no praise filler.
