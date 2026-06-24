# Power BI Embed Performance Diagnosis — 2026-06-24

## Goal
Find which of three suspects dominates the slow embedded "deep energy" report
**before** changing storage mode. This is the decision gate for DirectLake → Import.

## Context (current state)
- Model: `EnergyCopilotModel`, **DirectLake** — every gold/silver fact + dim table is
  `mode: directLake`; only `Date`, `DayOfWeek_Dim`, `Scope_Category`, `sensor_labels`,
  `Time Grain` are `mode: import`.
- Embed: V2 `GenerateToken`, app-owns-data, RLS via `CUSTOMDATA` dynamic role.
- Embed-token latency already fixed to ~1–2s (commit `6c98a0b`, MSAL singleton + meta cache).
- Capacity: Fabric F-SKU — **confirm which** (F2 assumed in cost notes).
- Model is small: ~10–15 buildings, mostly daily grain → likely a few hundred-k rows total.

---

## Suspect A — Capacity resume penalty
**Pattern:** first load after idle is very slow; an immediate reload is fast.

1. Fabric portal → Capacity settings → is the capacity paused / does it auto-pause when idle?
2. Test: after ≥30 min idle, open the report, stopwatch time-to-fully-rendered.
   Reopen immediately, time again.
3. Record: `cold_load_s`, `warm_load_s`. If `cold − warm > 20s` → resume penalty is a major factor.

## Suspect B — DirectQuery fallback / capacity throttling
**Pattern:** consistently slow; worse with more visuals or concurrent users.

1. Open the **Microsoft Fabric Capacity Metrics** app.
2. During active report use: read CU utilization %, throttling/overload events, interactive delay.
3. Check DirectLake fallback: in Capacity Metrics the semantic-model operations show
   `DirectLake` vs `DirectQuery`; a DQ row = fallback (guardrail exceeded).
4. Record: `peak_CU_pct`, `overload` y/n, `fallback_observed` y/n.

## Suspect C — Heavy visuals / DAX
**Pattern:** specific page(s) slow, others fine.

1. Open the report in Power BI Desktop (open the PBIP under `report-design/_report_export/`,
   or connect live).
2. Optimize ribbon → **Performance Analyzer** → Start recording → click through each page → Stop.
3. Export the log. Per page note the worst visual: DAX query ms + visual display ms.
4. Record: per-page total ms, any single DAX query **> 2000 ms**, visual count on slow pages.

## End-to-end split (browser, 2 min)
App → DevTools → Network → reload the embed:
- `/embed-token` (or `/demo/embed-token`) response time → should be ~1–2s.
- `powerbi.com` report/query requests → everything else.
Separates backend-token cost from report-render cost.

---

## Decision rule
- **A dominant** → keep capacity warm (schedule on during business hours). Cheap, no model change.
- **B dominant** (fallback/throttle) → **Import migration is the right fix** — removes DQ fallback;
  small model fits in F-SKU memory; refresh after gold pipeline keeps it daily-fresh.
- **C dominant** → reduce visuals / optimize DAX first; Import helps but won't fix a 5s measure.
- **Mixed** → Import + capacity-warm + top-3 visual fixes.

## Numbers to bring back to decide
`cold_load_s`, `warm_load_s`, `peak_CU_pct`, `overload y/n`, `fallback y/n`,
`worst_page_ms` + `worst_DAX_ms`, `embed_token_s`, `F-SKU`.

> Note: Import does NOT remove the need for a capacity — app-owns-data embed requires an
> F/A SKU in both modes. This is a performance decision, not a cost-saving one.

---

## FINDINGS — Claude-side, 2026-06-24 (no Fabric/Desktop session needed)

Done by static + data + live inspection (not stopwatch):

**Data volume = tiny.** Mirrored gold (Supabase `mv_`) row counts: `mv_kpi_daily` 13,242 (largest),
`mv_iot_daily_summary` 1,076, `mv_ghg_scope` 438, everything else < 300. Even non-mirrored hourly
tables (`gold_kpi_hourly`, `gold_iot_realtime`) stay in the low-100k range. **Whole model < ~0.5M rows.**
→ At this scale DirectLake↔Import is nearly irrelevant to query speed; both are "small-model fast".

**Report is heavy.** 10 pages, **186 visuals** (20–22 on Portfolio, Sustainability, Building Detail, HVAC),
**45 slicers**, 70 cards, 20 KPI, **308 measures** in the model. Each visual = its own DAX query →
~20+ concurrent queries per page load. **This is the #1 mode-independent slowness driver.**

**DAX not pathological.** No `FILTER(ALL(...))` over fact tables; no `SUMX/AVERAGEX/RANKX` over the
hourly/realtime tables. Slowness is query *volume*, not individual measure cost.

**Embed path healthy.** Live `/demo` loads the report iframe (200) from the **Germany West Central**
capacity; `/embed-token` already optimized (~1–2s, commit 6c98a0b). Backend token is NOT the bottleneck.

### Interpretation
Bottleneck is very likely **report design (visual count) + capacity warmth**, NOT storage mode.
Import would help only marginally here (removes per-query transcoding cold-start, which mostly bites on a
cold/paused capacity). Migrating is the heavy lever for the smallest expected gain.

### Still Mert-only to confirm (2 measurements)
- **Capacity state:** Fabric portal — is the F-SKU paused / auto-pause? Then stopwatch: cold reload vs
  immediate warm reload of `/demo`. `cold − warm > 20s` ⇒ resume penalty (Suspect A).
- **Performance Analyzer** (PBI Desktop, slowest 2 pages): per-visual DAX ms + display ms. Confirms it's
  death-by-many-visuals vs one slow visual.

### Recommended order (pending those 2 numbers)
1. Keep capacity warm during business hours (kill resume penalty) — free, no model change.
2. Cut visuals/slicers per page on the 20–22-visual pages (biggest win, mode-independent).
3. Optimize any >2s visual Performance Analyzer flags.
4. Re-measure. Only if still slow → consider Import (or composite: Import daily/hourly gold +
   DirectQuery-to-KQL for a truly live IoT page).

---

## MEASURED RESULTS — Performance Analyzer export, 2026-06-24 (capacity = F4 trial)

- **Capacity F4 trial → not paused** ⇒ resume penalty (Suspect A) ruled OUT.
- Session 108 s / 6 page visits ⇒ **~12–17 s per page** (the "annoying slow").
- 16–18 visuals/page, **9–11 single-value cards each**.
- Query : render = **152 s : 51 s (≈3:1)** — query round-trip dominates, not client render.
- **No DAX > 1 s** (max 973 ms, median 214 ms). The model/DirectLake answers every query fast.
- Per-visual query ≈ 510 ms avg vs 214 ms median actual DAX ⇒ ~300 ms/visual is round-trip + queue
  overhead × ~18 visuals = the page cost. It's the *count* of queries, not any slow query.
- Worst page = Portfolio: 18 visuals; time-intel cards 2.2–2.4 s each (Last 7 Days Cost, MoM %, WoW %,
  Total Energy Cost, Avg EUI).

### VERDICT (evidence-backed, not estimate)
**Import is ruled OUT.** No query > 1 s ⇒ Import can't make queries faster; F4 isn't paused ⇒ no resume
penalty. Root cause = too many visuals (mostly cards) per page → too many query round-trips. Fully
storage-mode-independent.

### Fix tiers
- **T1 — settings, reversible, ~10 min:** File → Options → Query reduction → slicer **Apply buttons** +
  **disable cross-highlight/filter by default**; then Edit Interactions so cards/slicers don't re-query
  every unrelated visual. No visual changes. Re-measure.
- **T2 — consolidation, biggest durable win:** merge the 9–11 cards/page into multi-row cards / small
  matrices; target ~10 visuals/page ⇒ roughly halves page time (one query replaces six).
- **T3 — only if residual:** pre-compute Portfolio time-intel into a gold summary row; or temporarily
  bump F4→F8 to test capacity queuing under the 18-query burst.
