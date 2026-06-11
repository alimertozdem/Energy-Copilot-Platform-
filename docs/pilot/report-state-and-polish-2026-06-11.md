# EnergyLens — Report State & Polish Plan (2026-06-11)

_Based on a full page-by-page review of the live report PDF (`Energy Co Pilot (5)`). **Supersedes
the 2026-06-03 "Report PDF Findings"** — most of those items are now fixed._

## 1. Bottom line

**The report is ~90% pilot-ready. All 10 pages render — no blank/broken visuals.** The
2026-06-03 blockers (Page 8 all-broken, Page 9 RTE 0.9 / payback 230 headline, Page 10
specific-yield broken) are **fixed**. What remains is a **targeted data-quality + presentation
polish**, not a rebuild — and re-running `03` does **not** fix it (the report already reflects the
repo fixes; these are newly-found issues).

## 2. Per-page verdict

| Page | Renders | Notes |
|---|---|---|
| 1 Portfolio | ✅ | EUI shown **per-day** (1.12) vs annual convention; data-center (EUI 1,615) skews portfolio averages |
| 2 Deep-Dive | ✅ | 24h load profile **present**; monthly trends could use a Day/Month toggle |
| 3 Anomaly | ⚠️ | **Resolution Rate ~blank, Active 100%, Avg Days Open 490** — `gold_anomaly_log` is stale |
| 4 Forecast | ✅ | Confidence band works; MAPE sane (1–6%) |
| 5 Occupancy | ⚠️ | **"Occupied Hrs/Day = 69.1"** — impossible (>24); measure bug |
| 6 ESG | ✅ | Scope 1/2/3 + CRREM + EPC populated; GHG intensity 490 skewed; market (88.9K) > location (68.4K) — sanity-check |
| 7 HVAC | ✅ | "modeled" labelled; **"HVAC CO₂ = 18,115 tCO₂/yr"** exceeds the whole-portfolio 3,680 tCO₂ → aggregation bug |
| 8 IoT/AFDD | ✅ | Full render: 12-rule FDD + zone comfort + waste (static-snapshot mode) |
| 9 Battery | ✅ | Headline fixed (Payback 1.6, RTE 93.83); scenario table still has outlier payback 230 (sim edge) |
| 10 Solar | ✅ | Specific yield works (700–1,100 kWh/kWp); one building shows PV PR 115% (>100, impossible) |

## 3. The 3 pilot-blocking fixes (Pages 1–6) — exact remediation

### ① Page 3 — anomaly resolution → **RE-RUN `anomaly_detection.py`**
Root cause: your Fabric `gold_anomaly_log` is **stale** (pre-backfill). The notebook
(`anomaly_detection.py`, ~L1010–1050) already deterministically marks older-than-45-day anomalies
resolved by severity (CRITICAL ~15%, HIGH ~25%, MEDIUM/LOW ~40%). **Re-run it** → Resolution Rate
populates, Active Rate drops from 100%, Avg Days Open becomes realistic. _This is the one place a
re-run fixes the issue._

### ② Page 5 — "Occupied Hrs/Day = 69.1" → **DAX fix**
Root cause: the measure does `DIVIDE(occupied_rows_per_week, 7)` but does **not** divide by the
number of buildings, so at portfolio level it sums across ~8 buildings (8 × ~8.6 ≈ 69). Corrected
measure (run in Tabular Editor, then bind the card to it):

```dax
Occupied Hours Per Day Calc =
VAR _threshold = 0.30
VAR _occupied_rows =
    CALCULATE( COUNTROWS( gold_occupancy_profile ),
               gold_occupancy_profile[occupancy_probability] >= _threshold )
VAR _buildings = DISTINCTCOUNT( gold_occupancy_profile[building_id] )
RETURN DIVIDE( _occupied_rows, 7 * _buildings )
```
Apply the same `* _buildings` denominator to "Occupied Hours Variance Hours" in
`page5_v54_install.cs` (line ~196) so the variance matches.

### ③ Page 1 — EUI per-day + data-center skew → **presentation choice**
- Show EUI **annualised** (× 365 or a dedicated annual column) so it reads against the 80–200
  kWh/m²/yr benchmark convention; "1.12/day" forces mental math.
- The data center (EUI 1,615 / CRREM 2,238 kgCO₂/m²) is a different archetype and dominates
  portfolio averages. Either **area-weight** the portfolio EUI/intensity, or **segment** the data
  center into its own benchmark band. (Energy-logic: data-center EUI of ~1,600 is realistic — the
  issue is mixing archetypes in one average.)

## 4. Lower priority (not pilot-#1-blocking)

- **Page 7 "HVAC CO₂ 18,115 tCO₂/yr"** — exceeds total portfolio carbon → likely summed over the
  full 2023–2026 range without annualising. Page 7 (HVAC analytics) is **module-gated for
  meter-only pilots**, so fix when IoT/sub-metering is in scope.
- **Page 6** GHG intensity 490 skew (same data-center cause) + **market > location** GHG — confirm
  the market-based factor logic (usually used to *reward* green procurement).
- **Page 9** scenario-table payback 230 — `battery_simulator.py` edge case (battery, deferred).
- **Page 10** PV PR 115% (>100) — clamp / check the performance-ratio calc.
- **Goal-variance colouring** — verify "over goal" (bad for consumption) vs "under goal" (good for
  carbon) colour direction is consistent across cards.
- **Default date range** spans 4 years (2023–2026); consider defaulting to last 12 months.

## 5. Bottom line for pilot #1

To go from ~90% → fully pilot-ready you need **two concrete fixes** (① re-run anomaly notebook,
② the Page-5 DAX one-liner) plus the **Page-1 presentation choice** (annual EUI + data-center
segmentation). Everything else is either already working or out of scope for a meter-only pilot.
