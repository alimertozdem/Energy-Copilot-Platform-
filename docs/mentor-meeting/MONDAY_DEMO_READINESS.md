# Monday Demo Readiness — Professor Walkthrough (web app + embedded Power BI)

_Written 2026-06-06 for the ~2026-06-08 meeting with Dr. Chelabi. Demo surface
(Mert's choice): the **live web app** + the **embedded Power BI reports**, clicked
through page by page. This is the orchestration layer — it points at the existing
fix assets, ordered by **what the professor will actually see**._

Existing assets (don't recreate — execute):
- `EnergyLens_Final_Update_Plan.pdf` — the visual fix plan (grain map + Page 10 layout + per-page cards).
- `semantic-model/scripts/final_master_install.cs` — Tabular Editor consolidate script (v57–v60 + Page 10 + climate EUI + forecast band + RTE×100 + Date[Month Year]).
- `docs/dashboard_final_10page_plan.md` — Gate D 10-page master plan (213 measures).
- `report-design/gate-d-visual-binding-checklist.md` — per-visual binding checklist.

---

## 0. The honest framing (say this, don't hide it)
The web app is production-grade and demo-clean. The **embedded reports** have a few
visuals still mid-fix from the Gate D pass. If a report visual looks off live, narrate
it as *"this page is in final QA — here's the logic behind it"* and pivot to the web
app. The energy logic is sound; the gap is visual binding, not correctness. This is
exactly the honesty layer in the master reference (§9).

---

## 1. Web app — runtime checks (do first, €0, ~15 min)
These are environment/runtime, not code (code is done + E2E-tested):

- [ ] Backend up: `uvicorn` running; `BACKEND_URL=127.0.0.1` (not `localhost` — IPv6 gotcha).
- [ ] Frontend up: `npm run dev` (or prod build) — no stale `.next`; clear if pages 404/flash.
- [ ] Fabric SQL endpoint reachable (else `/portfolio·/actions·/solar·/alerts` show the calm "temporarily unavailable" notice — acceptable but check capacity/tables are up).
- [ ] Log in with your founder Google/Microsoft account (= platform admin) so `/admin` is visible if you want to show the bridge queue.
- [ ] Walk the click-path once end-to-end: `/` → `/demo` → `/portfolio` → `/solar` → `/compliance` → `/actions` → `/alerts` → `/copilot`. Note anything that 500s or looks empty.
- [ ] ✅ EU Battery Regulation number is now **2023/1542** everywhere (fixed 2026-06-06) — landing trust strip + OG + Page 9 data/SVG/DAX. Re-deploy the Page 9 SVG background + battery CSVs to Fabric so the report shows the corrected number.

## 2. Power BI / Fabric — fix sequence (your side, ordered by demo visibility)
Run in this order (from `EnergyLens_Final_Update_Plan.pdf` + `final_master_install.cs`):

1. [ ] **03 notebook re-run** (`gold/03_gold_kpi_engine.py`) — produces specific-yield in `gold_kpi_daily` + climate-adjusted EUI. Prerequisite for Page 10 + benchmark.
2. [ ] **Tabular Editor**: run `final_master_install.cs` (57 upserts — consolidates v57–v60, Page 10 measures, climate EUI, forecast band, **RTE×100** fix, `Date[Month Year]`). Then **refresh model** (mandatory after TE).
3. [ ] **Page 8 (IoT)** — all visuals were broken: rebind to `gold_iot_realtime` / `iot_hot_readings`. Highest visible risk — this is the flagship page.
4. [ ] **Page 9 (Battery)** — fix `24h Battery` + `EU Compliance` visuals; verify ROI is sane (payback was 230 / IRR 450% — check tariff + RTE×100); confirm regulation label = 2023/1542.
5. [ ] **Page 10 (Solar)** — rebind specific-yield (now exists in gold after step 1).
6. [ ] **Page 2 (Trends)** — the main grain complaint: 3 trends were monthly; switch to daily + add the 24h view. Other pages' monthly grain is correct.
7. [ ] **Pages 1 / 3 / 4** — quick verify against the binding checklist.
8. [ ] **Data sanity** (flag, don't necessarily fix before Monday): GHG 497, DC 2224, Berlin 793, Occupied 69.1, EUI 1.12 — know these numbers so you can explain/caveat if asked.

## 3. Optional wow-moment — the bridge story
If the professor asks "how does a new customer get онboarded?", you can show the
**self-serve bridge** narrative (Access Layer 3): a pending building → `/admin` bridge
queue → **Dry-run** the automated bridge (works today, €0, no capacity) → it plans the
5 steps live. This demonstrates the productised, self-serve onboarding — a strong USP
for EXIST. (Live Auto-bridge needs an active capacity; Dry-run is the safe demo.)

---

## Priority if time runs short
Web app is the reliable spine — lead with it. For PBI, prioritise **steps 1–2 + Page 8
+ Page 9** (the pages most likely to be opened). Everything else degrades gracefully or
can be narrated as "in final QA."

---

## Demo runbook — the guided walk (≈8–10 min)

**Lead with the guided tour `/tour`.** It is data-free, so it never breaks; each stop
has an "Open live →" that drops into the real page (same tab) and a floating
"← Back to tour" returns you to the same step. If Fabric is flaky, the tour alone still
tells the whole story.

### Pre-flight (2 min, before they arrive)
- [ ] Backend up (`uvicorn`), frontend up (`npm run dev`), logged in as your founder account.
- [ ] Open `/tour` and `/portfolio` once to warm the Fabric connection (first query is slow).
- [ ] Optional: `.env` `FABRIC_SQL_CACHE_TTL=45` + uvicorn restart → snappier repeat clicks.
- [ ] Have `/demo` (public, no login) open in a spare tab as the ultimate fallback.

### The walk (drive `/tour` with → ; dive live where data is good)
1. **Intro** — what EnergyLens is: data they already have → KPIs, faults, decarbonisation, EU-compliance, no new hardware, on Microsoft Fabric.
2. **Portfolio** → Open live `/portfolio` — EUI/cost/carbon across buildings; worst performers first.
3. **Decarbonisation** → Open live `/decarbonisation` — the MACC + the no-regret bundle; "where every euro abates the most CO₂." Show **Export PDF**.
4. **Alerts** → `/alerts` — €-quantified fault detection.
5. **Actions** → `/actions` — recommendations with payback + status tracking.
6. **Compliance** → `/compliance` — MEPS / CRREM / EU-Taxonomy / ESRS-E1 (say "indicative screening").
7. **Solar & battery** → `/solar` (+ Page 9 in PBI if fixed).
8. **Residential** → `/residential` — the UVI-compliance wedge (Jan-2027 deadline + €3% penalty exposure) + investment potential; open a building for the **landlord investment case**; `/residence` for the tenant view.
9. **Self-serve onboarding & bridging** — narrate; optionally show `/admin` bridge queue **Dry-run** (€0, no capacity).
10. **Copilot** → `/copilot` — try a suggested prompt.
11. **Architecture & close** — medallion + interoperability; the closing slide.

### If something breaks live
Don't debug in front of them. Say "this view is in final QA" and **click Back to tour** —
the narrative continues. The tour + `/demo` are the two things that always work.
