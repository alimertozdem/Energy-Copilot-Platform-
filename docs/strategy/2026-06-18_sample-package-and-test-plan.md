# EnergyLens — Sample Package & Test Plan

> **Status:** DRAFT v1 — for product-owner (Mert) review
> **Date:** 2026-06-18
> **Companion to:** [`2026-06-18_founder-operating-plan.md`](./2026-06-18_founder-operating-plan.md) ·
> [`2026-06-18_freelance-service-map.md`](./2026-06-18_freelance-service-map.md)
> **Purpose:** define the productized deliverables to list on Malt / freelance.de, and the test plan
> that validates them on a new building — including the estimation engine on messy data.

---

## 0. Decisions locked this round

- **Featured building:** multi-family **residential**, shown inside a small **portfolio** view with
  the residential block as the headline drill-down. *(Aligns to the Hausverwaltung wedge. Fallback =
  office, if you want the most universal / lowest-effort first sample.)*
- **Capacity model:** scheduled **batch** (1–2×/day) on a **paused/scheduled small F-SKU (F2)** —
  **no always-on capacity.** `[Kesin]` architecturally (the ① Decouple decision). ⚠️ The Fabric
  *trial* deadline was 2026-05-21 (CLAUDE.md) — confirm what capacity you are actually on now.
- **Sequencing:** the **listing asset** is built on an **existing demo building** (zero infra, now);
  the **new building + found dataset** is the **validation test** (parallel, batch). The listing is
  never blocked on the bridge.

---

## 1. The two productized packages (what the client actually receives)

### Package A — Energy Analytics & BI Dashboard  *(cash engine)*
An embedded, branded dashboard the client logs into. Built from existing report pages.

| Section | Source (existing) |
|---|---|
| Portfolio KPI overview (EUI, kWh, €, kgCO₂) | `gold_kpi_daily` / Postgres `mv_` |
| Per-building benchmark + ranking | portfolio page / `mv_` |
| Consumption trend + anomalies | KPI gold + alerts |
| Data-basis badges (measured / estimated / sample) | existing provenance layer |

### Package B — ESG / EPBD Decision-Support Report  *(identity / wedge engine — headline)*
A branded PDF (+ the dashboard). **"ESRS-aligned"** decision-support — *not* certified.

| Section | Source (existing) |
|---|---|
| Portfolio carbon (Scope 1/2, intensity) | `gold_ghg_scope` |
| EPBD / MEPS readiness + CRREM stranding view | compliance hub / `10_crrem_pathway` |
| Worst-performer ranking (which buildings first) | benchmark + compliance |
| Retrofit measures + CapEx + **BAFA/KfW-adjusted ROI** | `06_recommendation_engine` + `/financing` |
| Rising carbon-cost trajectory (do-nothing cost) | CO₂ price curve |
| Assumptions & ranges (every figure) | calc-transparency layer |

*(Companion upsell: ongoing monitoring subscription = the same dashboard on a batch refresh.)*

---

## 2. The featured sample

- Use the existing demo **portfolio**; headline a multi-family residential block as the drill-down.
- Show the **portfolio screening** value (rank worst stock, prioritise CapEx) + **one building deep
  dive** (measures, ROI, subsidy, stranding year).
- Anonymise before publishing. Label clearly: *indicative / screening, assumptions stated.*

---

## 3. Capacity model — confirming the batch instinct

- These report services are **100% batch** (baseline, gold, GHG, compliance, recommendations, the
  materialise-to-Postgres step). None needs real-time. `[Kesin]`
- Cheapest path: a small F-SKU **paused** and resumed only for the scheduled run window (1–2×/day),
  or run at onboarding then refresh daily. No always-on, no F64.
- The **app reads pg-first** (materialised `mv_` in Postgres), so the *client-facing* dashboard
  stays live and cheap even while Fabric is paused.
- ⚠️ Confirm current capacity (trial likely expired). The batch *approach* is right regardless; only
  the €-cost depends on which F-SKU you resume.

---

## 4. Test plan — the new building (the validation you want)

**Step 1 — listing asset (now, €0, no infra).** Produce Package A + B on an **existing demo
building**. This is what goes on Malt / freelance.de. Not blocked on anything.

**Step 2 — new-building end-to-end test (parallel, batch).** Take a found, real-ish, deliberately
**messy/incomplete** dataset → create **one new building** under a **new test org**, fresh
`fabric_building_id` (**B012**), kept separate from demo (B001–B010) and synthetic.

- **2a — estimation engine (€0, no Fabric):** load the messy data via the **Tier-1 Postgres
  baseline** path. This is the highest-value, zero-cost test: does the estimator fill gaps with
  sensible **ranges** when bills/EPC/area are missing or broken? *(Directly tests the free engine
  that is the product foundation.)*
- **2b — bridge + deep report (batch, needs capacity):** run the **bridge** (`40_bridge_baseline` +
  `09/05/06_*_bridge` + `50_materialize_to_postgres`) for B012 in a batch window. Expect edges —
  B011 needed manual fixups (`00b_add_B011`, `21b_fix_B011`); fix them once, cleanly, here.

**Separation / isolation checks:**
- B012 lands in its own org; demo/synthetic rows untouched.
- **RLS is the real isolation gap** — the orchestrator notes RLS for a real customer org is a
  *documented follow-up, not done* (demo filters via a DAX rule). Close RLS **before any real
  customer's data** goes in — not required for this internal test, but the blocker for customer #1.

**Acceptance ("are the packages correct?"):**
- Numbers fall in plausible ranges (EUI, savings %, payback) — sanity-flag outliers.
- Every figure carries assumptions + "indicative/screening".
- The PDF + dashboard render for B012 with no demo bleed-through.

---

## 5. What needs your Fabric vs what doesn't

| Task | Needs capacity? |
|---|---|
| Listing sample on a demo building | ❌ No (reads materialised Postgres) |
| Estimation-engine test on messy data (2a) | ❌ No (Tier-1 Postgres) |
| Bridge a new building → deep gold report (2b) | ✅ Yes — **batch** on a paused F2 |
| Client-facing dashboard (ongoing) | ❌ No (pg-first read; Fabric paused) |
| Real customer multi-tenant isolation (RLS) | ✅ Yes — follow-up before customer #1 |

---

## 6. Open confirmations

1. **Current Fabric capacity status** (trial expired? on F2? credits?) — sets the €-cost of Step 2b.
2. **Building type** — confirm residential-headline, or switch to office for the first sample.
3. **Test dataset source** — candidates to validate (open, real building energy data): **Building
   Data Genome Project 2** (hourly meter data, ~1,600 non-residential), **NYC LL84** benchmarking
   (annual EUI, thousands of buildings), **UK Display Energy Certificates**, **EU Building Stock
   Observatory**. *(I can fetch and shape the best fit next.)*

---

_All figures/ranges are indicative, not commitments. Energy logic per the project's
"state assumptions, prefer ranges" rule._
