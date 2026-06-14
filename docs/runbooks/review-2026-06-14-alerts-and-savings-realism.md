# Review 2026-06-14 — Alert overload + savings realism

Web-app KPI/value review. Two correctness problems were found in the data the app
serves and fixed end-to-end (web-app presentation + Fabric root cause + demo data).

## What was wrong

1. **Alert overload.** `gold_anomaly_log` keys every anomaly by
   `(building_id, anomaly_type, DATE)`, so a chronic fault emits a new row every
   day. The portfolio showed **2,962 unresolved alerts, 0% resolved** — one demo
   building alone had 508. Building cards showed the raw all-time unresolved count.
   A facility manager can't act on that.

2. **Savings exceeded the bill.** The 50 recommendations summed to **€6.5M/yr
   (≈120% of the ~€5.4M annual bill)** and **10,570 tCO₂ (≈116% of ~9,100 t
   emissions)**. Individual measures are fine, but they overlap (CHP + BMS + heat
   recovery target the same kWh) and were summed naively.

3. **Nothing ever closed.** Alerts 0% resolved, actions 100% "open" — the whole
   portfolio read as an untouched crisis.

## What changed

### Alerts → "ongoing issue" model
- **`backend/app/services/alerts_data.py`** — rewritten to collapse occurrences
  into one issue per `(building, anomaly_type)`: representative = worst+latest,
  plus `occurrence_count`, `first/last_detected_at`. All counts are issue-level.
  (Unit-tested: 510 raw events → 3 issues.)
- **`backend/app/schemas/alerts.py`** — `AlertItem` gains `occurrence_count`,
  `first_detected_at`, `last_detected_at`.
- **Frontend** — `AlertsTable` shows a `↻ N× recurring` chip; `AlertDetailPanel`
  shows an active-since banner; `/alerts` copy + subtitle now say "issues";
  `lib/api/alerts.ts` types updated.
- **`backend/app/services/portfolio_metrics.py`** — building-card `open_anomalies`
  is now `COUNT(DISTINCT anomaly_type)` of open HIGH/CRITICAL issues (508 → ~0–3).
- **Root cause — `notebooks/anomaly-detection/anomaly_detection.py`** (Bölüm 7b):
  episode-aware resolution. Only the latest occurrence of an *active* issue (last
  seen within `ACTIVE_WINDOW_DAYS = 14` of the data anchor) stays open; everything
  else resolves. Open rows ≈ active issue count. Grain unchanged → Page 3 structure
  intact, only `is_resolved` distribution becomes realistic.

### Savings realism
- **Root cause — `notebooks/recommendation/06_recommendation_engine.py`** (§9b):
  per-building cap. A building's measure savings are scaled so their SUM ≤
  `0.65 × annual cost` (EUR) and `0.75 × annual emissions` (CO₂). Ranking is
  preserved; `payback_years` and `npv_eur` are recomputed from the scaled saving
  via the row's implied annuity, so each row stays self-consistent. Guarded by
  try/except — never breaks the pipeline.
- **Web-app caveats** — `/decarbonisation` and the EnEfG report now state the
  totals are indicative and measures aren't strictly additive (no double-capping;
  the engine is the source of truth).

### Demo data
- **`backend/app/data/sample_fallback.json`** regenerated (script:
  `scripts/transform_snapshot.py`, copied into the repo outputs) to the new shape:
  **46 issues / 20 open** (was 2,962), savings **41% of bill**, CO₂ **46% of
  emissions**, and a realistic action status mix (open/in-progress/completed/
  dismissed). This is what the live demo serves when Fabric is unreachable.

## What Mert needs to run
1. **Fabric:** re-run `anomaly_detection.py` then `06_recommendation_engine.py`
   (rebuilds `gold_anomaly_log` + `gold_recommendations` with the new logic).
2. **Backend:** restart uvicorn (picks up the new services + snapshot).
3. **Optional:** `npx tsc` locally to confirm types (sandbox tsc was too slow to
   finish; all 6 changed files parse clean and were rebuilt from the compiling
   git base). No DB migration.

## Tunables
- `ACTIVE_WINDOW_DAYS` (anomaly_detection.py) — widen to keep more issues "open".
- `SAVING_CAP_FRACTION_EUR / _CO2` (recommendation engine) — realistic-saving share.

## Verification done
py_compile (3 backend + 2 notebooks) ✓ · alerts grouping unit test ✓ ·
snapshot valid JSON + all schema fields + recomputed totals within bounds ✓ ·
6 frontend files parse clean ✓ · no file corruption ✓.
