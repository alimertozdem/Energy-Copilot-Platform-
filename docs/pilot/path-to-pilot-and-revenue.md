# EnergyLens — Path to Pilot & Revenue (state-of-platform, 2026-06-11)

_Capstone of the Step 1–4 review. **Headline: the platform is code-complete against the
approved 4-step roadmap.** The binding constraint to a running pilot + revenue is **founder-run
execution in your Fabric/Power BI environment — not more building.**_

## 1. What the review actually found

I set out to (1) dry-run pilot-readiness, (2) finish the report punch-list, (3) build the
self-serve bridge wizard, (4) surface MACC. On inspection, **3 of the 4 were already built** and
the 1st is verified working. The finalization plan (2026-05-30) is stale — the code moved past it.

| Step | Expected work | Actual state |
|---|---|---|
| **1 — Pilot dry-run** | run it | ✅ **Verified live.** Tier-1 engine (baseline KPI + readiness + CSV/PDF parsers) passes all sanity checks against messy/partial data. Zero customer Fabric dependency. |
| **2 — Report punch-list** | fix Page 1–6 logic | ✅ **Code-side done in repo.** B1 (HDD+CDD EUI), B3 (interval-aware peak), C1 (single anomaly authority + legacy redirect), E1 (Prophet F-import), E3 (CI band), RTE×100 normalize — all present. Remainder is PBI-runtime (founder). |
| **3 — Self-serve bridge wizard** | build it | ✅ **Wired.** `bridge_readiness` (deterministic) + `GET /bridge-readiness` + `POST /bridge-request`; `BridgeUnlockPanel` mounted on the building detail page; admin review queue + `/automate` (3.2 scaffold). |
| **4 — MACC / CO₂-forward** | build front-end | ✅ **Wired.** `/decarbonisation` reads `GET /abatement/macc` → MaccChart + CapEx-prioritised table; nav-linked. |
| _Bonus_ | — | `/connections` (Tier-2/3 device & point CRUD) and `/financing` (KfW/BAFA subsidy capture) also present + nav-linked. |

> Caveat: "wired in code" ≠ "runtime-verified against live Fabric." Steps 3/4 are built and
> reachable; their end-to-end runtime check rides on the same founder-run bridge below.

## 2. The critical path to a running pilot (founder-run — your environment)

This is the real remaining work. None of it is new features.

### CP-1 · Report go-live (Fabric + Power BI)
Run the 2026-06-03 sequence: **re-run notebook `03_gold_kpi_engine`** → **run the Tabular Editor
install** (`semantic-model/scripts/final_master_install.cs`) → **rebind Page 8/9/10 visuals** →
**Page 2 time-grain toggle + 24h** → verify Pages 1/3/4. _Per Step-1 scope, Pages 8/9/10 are not
pilot-#1-blocking for a meter-only building (module-gated off)._

### CP-2 · Pilot dry-run in Fabric (the go-live gate)
Run `docs/pilot/pilot-readiness-2026-06-11.md` §4: onboard a real building → upload its CSV/bill
→ confirm baseline KPIs → **founder bridge** (medallion notebooks → mint `fabric_building_id` →
RLS map + refresh) → **RLS 2-customer isolation test** (A sees only A, B sees only B, in embed
*and* the pyodbc reads). Pass = zero cross-customer leakage + pending→live flip works.

### CP-3 · Capacity
Stay **④ static-snapshot (€0)** today. Activate **① Decouple** (Event Hubs + Container App hot
store) only when the first paying IoT customer arrives. See `architecture/iot-capacity-decision.md`.

## 3. Real polish gaps (small, code — optional, I can do these)

1. **Tier-1 engines are already unit-tested** (`backend/tests/`, 379 lines); they just weren't in
   CI — now added (`.github/workflows/backend-ci.yml`, 2026-06-11). Only the frontend TS CSV parser
   stays untested.
2. **Reference-data currency.** `ref_` grid factors / tariffs end 2025; refresh when 2026 values
   publish (carry-forward works + is flagged, so not urgent).
3. **`03` §8 legacy anomaly block still computes** (writes to `…_kpibuiltin_legacy`). Correct, but
   wasted compute — can be removed now that `anomaly_detection.py` is the sole authority.
4. **Page 9 payback/IRR sanity** (reported absurd: payback ~230, IRR ~450%). Battery-only →
   deferred; investigate `battery_simulator.py` output when a battery pilot is in scope.
5. **Verify `/connections` device-entry depth** covers real Tier-3 wiring (template library, point→sensor map).

## 4. Bottom line for the founder

You are **past the build phase**. "How close to final?" → the product is essentially feature-
complete; what's left is **execution** (CP-1 report go-live, CP-2 one real pilot) and
**go-to-market**, plus optional small polish (§3). A Tier-1 pilot can start **today**; the deep
analytics need your one-time Fabric bridge + RLS validation.
