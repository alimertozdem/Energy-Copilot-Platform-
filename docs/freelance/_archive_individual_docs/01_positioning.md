# Freelance Positioning Brief — CSRD/ESG + Microsoft Fabric

**Owner:** Ali Mert Özdemir
**Date:** 2026-05-26
**Status:** Draft v1 — awaiting Mert approval before Step 2 (skill gap plan)

---

## 1. One-Line Positioning

> **"I help mid-market property portfolios and ESG teams turn raw building energy data into CSRD-ready Power BI dashboards on Microsoft Fabric — with auditable Scope 1/2/3 numbers and regulator-grade data lineage."**

This sentence drives every profile, every proposal, every cold message. If a sentence in our marketing does not support this, it gets cut.

## 2. Why This Niche (and not a wider one)

Three forces stack here, and almost nobody is positioned at their intersection:

1. **CSRD enforcement wave** — The first wave of EU companies must file ESRS-compliant reports for FY2025 (filed 2026). The second wave (FY2026 / filed 2027) is ~50,000 EU companies. They are *behind* and *panicking*. Demand is structural, not a fad.
2. **Microsoft Fabric is new** — GA in May 2024, still a small specialist pool. DP-600 / DP-700 holders globally are estimated in the low tens of thousands. Most Power BI consultants haven't migrated yet.
3. **Energy domain literacy is rare in BI** — Most Power BI freelancers know finance dashboards, not kWh/m², EnPI, Scope 2 market-based vs location-based, or EPC weighting.

A freelancer at the intersection of these three (Fabric + BI + EU energy regulation) faces near-zero direct competition on Upwork/Malt. Pricing power follows.

## 3. Ideal Client Profile (ICP)

We hunt three ICPs, in order of fit:

### ICP-A — ESG/Sustainability Consultancies (PRIMARY)
- **Size:** 10–150 employees, EU-based (DACH first)
- **Pain:** Client X needs ESRS E1 disclosure in 8 weeks, consultancy has Excel-based methodology but no productized dashboard. They lose deals to bigger firms who have one.
- **Buyer:** Partner / ESG Director
- **Project type:** Build a productized CSRD dashboard template they resell to *their* clients
- **Deal size:** €5k–€20k initial, often retainer follow-up

### ICP-B — Property/Portfolio Managers
- **Size:** 50–500 building portfolio, €50M–€500M AUM
- **Pain:** Has energy data in 5 systems (BMS, utility bills, EPCs, manual Excel, sometimes Power BI). Cannot answer "which buildings are dragging our portfolio score down" in <30 minutes.
- **Buyer:** Head of Asset Management / Sustainability Officer
- **Project type:** Multi-building energy KPI dashboard, EnPI tracking, EPC compliance heat map
- **Deal size:** €2.5k–€8k initial, monthly retainer plausible

### ICP-C — Internal Sustainability Teams (mid-cap)
- **Size:** €100M–€1B revenue, 1–3 person sustainability team
- **Pain:** Company invested in Microsoft Fabric for finance/sales, sustainability team is locked out, builds Scope 1/2/3 in Excel manually each quarter.
- **Buyer:** Head of Sustainability
- **Project type:** "Sustainability layer" on top of their existing Fabric lakehouse — Scope 1/2/3 model + dashboard
- **Deal size:** €8k–€25k, sometimes leads to long retainer

### Anti-ICPs (we say no)
- Tableau-only shops
- "Build me a full ESG SaaS for $500" requests
- Renewable energy *project finance* clients (different niche, not analytics)
- Anyone using "ESG" loosely without naming a framework (CSRD / GRI / SASB)

## 4. Pain Points We Sell To (the language clients use)

Memorize these. Every proposal must hit one of these in the first paragraph:

- "Our auditor flagged our Scope 2 calculation"
- "We have data in 5 systems and can't reconcile ESRS E1 disclosures"
- "Our ESG report takes 6 weeks to compile — regulators want it quarterly"
- "We built a Power BI dashboard but it's slow, wrong, or nobody opens it"
- "We bought Microsoft Fabric and don't know how to use it"
- "We need to benchmark our portfolio against EPC requirements"
- "Our CFO wants one dashboard for energy cost + carbon"

## 5. Proof Points (from EnergyLens — back every claim)

We do not claim things we cannot demo. EnergyLens gives us these concrete, screenshottable assets:

| Asset | What it proves | Where it lives |
|---|---|---|
| **9-page production Power BI report** | End-to-end BI capability, not just toy demos | Pages 1–9, internal pbix |
| **Scope 1/2/3 GHG model with EPC area-weighting (Page 6)** | Real ESRS E1 / GHG Protocol fluency | `gold_ghg_scope`, DAX v56 measures |
| **10-building portfolio benchmark (Pages 1–5)** | EnPI, kWh/m², building-type aware thresholds | `gold_kpi_daily` |
| **IoT real-time monitoring with EventStream + KQL (Page 8)** | Microsoft Fabric Real-Time Intelligence fluency — extremely rare skill | `iot_hot_readings`, Notebook 11b |
| **Battery dispatch + EU 2023/1542 compliance (Page 9)** | Regulation-aware engineering, not generic dashboards | `gold_battery_simulation`, 13 scenarios |
| **DAX measure library (v56)** | Production-grade modeling — not "I copied a SUMX from a tutorial" | semantic-model folder |
| **Microsoft Fabric Data Engineer cert** | Verified technical baseline | LinkedIn |
| **BSBI MSc thesis (Energy + AI)** | Domain academic credibility | Thesis abstract |

## 6. Differentiation — Why Pick Us Over a Cheaper Freelancer

Order of arguments, by power:

1. **"I have already built and operate the platform you are trying to build"** — Show 1–2 EnergyLens screenshots in every proposal. This is the single biggest weapon.
2. **Microsoft Fabric + energy domain + EU regulation** — no other freelancer on Upwork combines these three. We can prove it: search results show <10 freelancers worldwide claiming Fabric + ESG.
3. **Regulation-first thinking** — We don't just build dashboards, we cite EU 2023/1542, ESRS E1, GHG Protocol Corporate Standard, ISO 50001. Clients in this niche need that confidence.
4. **Productized offerings** — We don't quote "I'll think about it and get back to you." We have packages with fixed scope, fixed price, fixed timeline.

## 7. Productized Offerings (start with these 4)

These get baked into proposal templates and profile gallery:

**Pricing strategy (revised 2026-05-26):** We open *below* market to win the first 5-10 deals, build reviews, then raise rates aggressively. Goal is **velocity over margin** for the first 90 days.

### P1 — "CSRD Scope 1/2/3 Quickstart"
- **Scope:** 2-week sprint. Connect 2-3 data sources (utility bills CSV, fleet log, refrigerant data), build Scope 1/2/3 dashboard with ESRS E1 mapping, deliver in client's Power BI tenant.
- **Opening price:** €3,200 fixed | **After 3 closes:** €4,500
- **Margin:** Reusable EnergyLens Scope template — 60% of work pre-built

### P2 — "Building Energy KPI Dashboard (1–10 buildings)"
- **Scope:** 1-week sprint. Ingest energy bills + EPC + (optional) BMS exports, build EnPI / kWh/m² / EPC compliance dashboard.
- **Opening price:** €1,800 fixed for ≤5 buildings, +€250 per building up to 10 | **After 3 closes:** €2,500
- **Margin:** EnergyLens Pages 1–5 template

### P3 — "Microsoft Fabric Audit & Roadmap"
- **Scope:** 3 days. Review existing Fabric setup, identify Direct Lake / Real-Time Intelligence opportunities, deliver written roadmap.
- **Opening price:** €1,200 fixed | **After 3 closes:** €1,800
- **Margin:** Pure consulting, no delivery — high margin, low time

### P4 — "Power BI Performance Tune-up"
- **Scope:** 2 days. Profile a slow Power BI report, fix DAX, optimize model, deliver before/after benchmark.
- **Opening price:** €800 fixed | **After 3 closes:** €1,200
- **Margin:** Pure expertise — quick wins, satisfied client, easy upsell

### Hourly fallback (for non-productized work)
- **Malt:** Open at €450/day, raise to €650 after 3 satisfied clients, target €850 by month 6
- **freelance.de:** Open at €60/hr or €450/day (English-language projects only)
- **Contra:** Open at $50/hr (USD platform), raise to $75 after 5 jobs
- **Toptal (if accepted):** $80-100/hr right out of the gate — platform sets premium floor

## 8. What Wins Proposals (the 5 ingredients)

Every proposal sent must contain:

1. **Pain mirror** — opening line repeats their pain in their language
2. **One concrete relevant artifact from EnergyLens** — screenshot or 1-line description, link if applicable
3. **A specific question** — proves we read the brief, not copy-paste
4. **A productized package match** ("This looks like a fit for our P1 CSRD Quickstart — €4,500 fixed, 2 weeks")
5. **One short paragraph on Fabric/CSRD jargon** — proves domain literacy in 2 sentences

The proposal automation tool (Task #5–7) is built around exactly these 5 ingredients.

## 9. Success Metrics — How We Know This Is Working

Tracked monthly:
- Proposals sent / week (target: 15–25 with automation)
- Reply rate (target: ≥8% — energy/Fabric niche should be high)
- Booked meetings / week (target: 2–4 by week 6)
- Closed deals / month (target: 1 by month 1, 3 by month 3)
- Revenue / month (target: €2k month 1, €5k month 3, €8k+ month 6)

## 10. Open Questions for Mert (resolve before Step 2)

1. **Geographic restriction?** Do we apply to non-EU jobs (US, UK, ME) or EU-only? *Recommendation: open to all English-speaking, but lead positioning with EU regulation.*
2. **GmbH / UG status?** Are you invoicing as Einzelunternehmer (sole trader), through a UG, or as a freelancer registered in TR? This affects which platforms allow you and tax treatment.
3. **Public portfolio — okay to publish?** We will need EnergyLens screenshots on profiles. Anything we *must not* show publicly?
4. **Time availability?** Realistic billable hours per week available right now? (This sets the proposal volume target.)
