# EnergyLens Freelance — Listing Copy & Report Narrative

> **Status:** DRAFT v1 — paste-ready copy + report template for product-owner review
> **Date:** 2026-06-18
> **Companion to:** [`2026-06-18_package-build-recipe.md`](./2026-06-18_package-build-recipe.md)
> **Headline sample building (confirmed from code):** **B001 — "Berliner Bürogebäude Alpha"**
> (Office, Berlin DE, 5,200 m², EPC B). Portfolio companions for the mixed view: B003 (Logistics,
> Hamburg), B005 (Healthcare, Frankfurt), B006 (Education, Amsterdam).
> All numbers come from existing app routes; **no invented figures** — placeholders `[from /route]`.

---

## 1. Freelance listing copy — **Offer 1: Energy Analytics & BI Dashboard**

**Title options:** "Energy & ESG analytics dashboard for building portfolios" · "Power BI energy
dashboard — buildings, consumption, CO₂, benchmarks"

**For:** property managers, facility teams, SMEs with one or more buildings and no in-house energy analyst.

**You get:**
- A clean, interactive dashboard: portfolio KPIs (energy use intensity, kWh, €, kgCO₂), per-building
  benchmark + ranking, consumption trends, anomaly flags.
- Each figure labelled *measured / estimated*, with assumptions stated.
- A short walkthrough of where your buildings stand and the 3 quickest wins.

**Format:** hosted dashboard link + a 1-page PDF summary. **Turnaround:** 3–5 working days.
**Indicative price:** €X (fixed) per portfolio, or €400–800/day `[Tahmin — set on the platform]`.

**CTA:** "Send me 12 months of utility bills + a building list — I'll return a working dashboard."

---

## 2. Freelance listing copy — **Offer 2: ESG / EPBD Readiness Report**  *(headline)*

**Title options:** "EPBD / GEG readiness + retrofit ROI report for building portfolios" ·
"ESRS-aligned building carbon & compliance report (no hardware needed)"

**For:** German/EU property managers (*Hausverwaltung*), housing companies, SMEs facing EPBD/MEPS,
rising CO₂ cost, or ESG-reporting pressure — who can't justify a €10k+ enterprise platform.

**You get:**
- Portfolio carbon footprint (Scope 1/2) and **which buildings strand first** (CRREM pathway).
- **EPBD / GEG readiness** per building + a prioritised retrofit plan.
- **BAFA/KfW subsidy-adjusted ROI** for each measure + the rising carbon-cost ("cost of doing
  nothing") curve.
- An **ESRS-aligned** decision-support report. *(Decision-support / screening — not a certified
  Energieausweis or iSFP.)*

**Format:** branded PDF + the dashboard. **Turnaround:** 5–10 working days.
**Indicative price:** €2,500–4,000 per portfolio screening `[Tahmin]`; optional ongoing monitoring
subscription thereafter.

**CTA:** "Bills + EPCs + building list → a board-ready compliance & retrofit-ROI report."

---

## 3. Profile / bio blurb (Malt / freelance.de)

> Energy & ESG analytics specialist for building portfolios. I turn your utility bills and building
> data into a clear compliance + decarbonisation picture — EPBD/GEG readiness, CRREM stranding,
> carbon footprint, and subsidy-adjusted retrofit ROI — using my own analytics platform (Microsoft
> Fabric + Power BI). No hardware, no site visit required. Focus: German/EU commercial &
> residential portfolios.

*(German version for freelance.de = quick follow-up.)*

---

## 4. Report narrative template — ESG / EPBD PDF (section by section)

Each section: what it says + the existing route it's exported from. Build on **B001**.

1. **Cover & scope** — client, portfolio (n buildings), period, "decision-support / indicative".
2. **Executive summary** — 5 bullets: total energy/€/CO₂, worst stranding asset, top opportunity,
   subsidy headline, the cost of doing nothing. *(from `/portfolio` + `/decarbonisation`)*
3. **Portfolio benchmark** — EUI/€/CO₂ per building, ranked; where each sits vs type benchmark.
   *(`/portfolio`, `/buildings/compare`)*
4. **Building deep-dive — B001 (Berlin office, 5,200 m², EPC B)** — consumption profile, EUI vs
   office benchmark, anomalies. *(`/buildings/B001`, `/alerts`)*
5. **CRREM stranding** — the year each building crosses the 1.5 °C pathway. *(`/compliance/crrem-report`)*
6. **EPBD / GEG readiness** — conformity gap per building. *(`/buildings/B001/geg-report`, `/compliance/enefg-report`)*
7. **Carbon footprint (Scope 1/2)** — intensity + trajectory with rising CO₂ price. *(`/compliance/ghg-report`)*
8. **Retrofit measures + MACC** — ranked €/tCO₂ and €/kWh. *(`/decarbonisation`)*
9. **Subsidy-adjusted ROI (BAFA/KfW)** — payback before/after grant. *(`/financing`)*
10. **Action plan** — sequenced next steps. *(`/actions`)*
11. **Assumptions & method** — every range + source; "indicative/screening, not certified". *(`/glossary`)*

---

## 5. How we proceed now (step sequence)

**Track A — listing asset (now, €0, B001):**
1. You run the routes above for B001 (+ 2–3 companions) and export the PDFs / dashboard.
2. I refine the exported narrative into the client-ready report using §4.
3. Anonymise → publish both offers (§1–2) on Malt / freelance.de.

**Track B — validation test (parallel):**
1. I source one **real office building's** public record (UK DEC / NYC LL84 / DE public building),
   shape it to the upload format, and **degrade a few fields** (drop months / blank EPC) to test the
   estimation engine.
2. You create the test building (**B012** next-free, or B015) under a test org, run Tier-1 baseline
   (estimator) + the bridge (batch) — fixing any notebook edges once.
3. Confirms the machine works end-to-end on a fresh, messy, real building.

---

_All figures indicative ranges; energy logic per "state assumptions, prefer ranges". Prices are
launch targets — confirm on the platform / in Stripe._
