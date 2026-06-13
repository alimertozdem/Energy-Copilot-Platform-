---
title: "EnergyLens"
subtitle: "Energy intelligence, EU-compliance reporting and decision-support for European buildings, on Microsoft Fabric — EXIST-Gründungsstipendium application"
author: "Ali Mert Özdemir — Founder · M.Sc. Energy Management (BSBI) · Microsoft DP-600"
date: "June 2026"
---

# 1. Idea sketch (the 60-second read)

**The problem.** Buildings consume about **40 % of EU energy** and produce about **36 % of
energy-related CO₂** — the single largest sector. Yet most building portfolios are still run on
monthly utility bills and spreadsheets. They cannot see the anomalies that waste energy nightly,
cannot keep up with a fast-tightening wall of EU regulation (EPBD minimum standards, EnEfG, GEG,
CSRD/ESRS, the CO₂ cost-allocation law, the EU Battery Regulation), and cannot prioritise the
cheapest path to decarbonisation. Large vendors (Schneider, Siemens, Measurabl) serve the top of
the market; the **mid-market and residential property managers are underserved**.

**The solution.** **EnergyLens** is a **Microsoft Fabric-native** energy-intelligence, EU-compliance
and decision-support platform. It unifies meter, sensor, weather, solar and battery data into one
auditable data model and delivers it through five layers: a **10-page analytics report**, a
**multi-tenant web application**, an **AI copilot** that answers questions by running real queries
over the data (tool use, not text summaries) and can take action, a **compliance & ESG reporting
engine** that produces the actual regulatory documents a building owner needs, and an emerging
**execution marketplace** that closes the loop from insight to action to delivery.

**The innovation.** EnergyLens is not a dashboard. Its defensible core is (a) an **agentic AI copilot**
that reasons over a building-energy Lakehouse through typed tools, (b) a **regulator-grade, fully
traceable carbon-lineage methodology** for ESRS/VSME reporting, and (c) **multi-protocol IoT fault
detection** (ASHRAE Guideline 36) delivered at mid-market prices. The funded year develops these from
a working prototype into a defensible, validated, research-anchored product (see §4).

**The market.** The Building Energy Management Systems (BEMS) software market is independently
estimated at roughly **US $8.4 bn in 2026 → ~$24 bn by 2035 (~8.7 % CAGR)**. The focus is the
**DACH mid-market** — the highest-value EU compliance market and the founder's home market — with a
second vertical in **residential property management (Hausverwaltung)**.

**Why this team.** The founder combines genuine **energy-engineering domain knowledge** (B.Sc. Energy
Engineering, M.Sc. Energy Management) with modern **data-engineering skill** (Microsoft DP-600) and
has already built the full platform — pipeline, analytics, web app, AI copilot and a 13-report
compliance engine — **solo, end-to-end**. This domain × data-engineering intersection is rare.

**The 12-month goal.** Convert a working prototype + a first pilot into an **incorporated company
(UG)** with **5+ paying customers** and **€5–10k MRR**, a **published carbon-methodology paper**, and
a defensible agentic-AI product — a fundable, post-grant business.

---

# 2. The problem & why now

European real estate sits at the centre of the EU's climate agenda, and the regulatory pressure is
now **binding, not aspirational**:

- **EPBD recast (Directive (EU) 2024/1275):** national minimum-energy-performance standards for
  non-residential buildings by **1 Jan 2027**; worst-performing **16 % improved by 2030, 26 % by 2033**;
  new buildings zero-emission from 2030.
- **EnEfG (Germany):** organisations above ~**2.5–7.5 GWh/year** must run energy-management and an
  economic-measures plan; larger users need ISO 50001 / DIN EN 16247 audits.
- **GEG §71 (Germany):** new heating systems must use **≥ 65 % renewable energy**; minimum envelope
  U-values for renovations.
- **CO₂ cost-allocation law (CO2KostAufG):** every landlord must split the carbon price on heating
  fuel with tenants on a 10-step model — an **annual, mandatory** calculation.
- **CSRD / ESRS E1:** sustainability disclosure, narrowed by the 2026 Omnibus to firms **> 1,000
  employees & > €450 m turnover**, with smaller firms reporting voluntarily via **VSME**.
- **EU Battery Regulation (2023/1542):** carbon-footprint and recycled-content disclosure; digital
  battery passport from 2027.

At the same time the structural reasons to act all arrived together: the post-2022 energy-price shock
made energy a board-level topic; **Microsoft Fabric** reached general availability (2024); IoT sensor
costs collapsed; and AI made pattern recognition affordable. Owners face rising compliance exposure
with no modern, affordable tooling — a real, time-bound demand.

---

# 3. The solution & what is already built

The product is **not a concept — it already runs end-to-end**. That de-risks the venture and is
itself evidence of execution capability. Built solo, April–June 2026:

## 3.1 Data foundation
A full Microsoft Fabric **medallion architecture** (Bronze → Silver → Gold) on OneLake, ~**57
Lakehouse tables**, with a **single sourced reference layer** for emission factors, tariffs and
envelope U-values by construction vintage. **Real external data** is already integrated: Open-Meteo
weather (real HDD/CDD), ENTSO-E day-ahead prices, ElectricityMaps grid-carbon intensity.

## 3.2 Analytics — 10-page Power BI report
Consumption, building deep-dive, anomalies, forecasting, decision-support, sustainability/GHG, HVAC,
real-time IoT, battery ROI and **solar (on-site generation & self-consumption)** — on a custom DAX
model (50+ measures, building-type-aware thresholds), reading live via **DirectLake**.

## 3.3 Multi-tenant web application
Next.js + FastAPI + Azure PostgreSQL, with **three-provider authentication** (Microsoft Entra ID,
Google, email) and a **three-layer access model** (row-level security on data, module gating per
subscription, commercial tiers). Custom pages — portfolio, building, solar, actions, alerts —
read Fabric through the SQL Analytics Endpoint. Includes **Stripe billing**, an **audit log**,
**PDF export**, an in-app **glossary/tooltip** layer, an **alerts triage** queue, accessibility and
end-to-end tests, plus public **/demo** and **/pricing**.

## 3.4 AI copilot
**Six production tools** over the Lakehouse (query KPIs, compare buildings, list recommendations, get
anomalies, simulate battery scenarios, update action status), server-sent-events streaming, and a
**provider abstraction** (Anthropic / Azure OpenAI / Mock). Most BI "copilots" summarise a page;
this one **runs real queries and can write back** — it can act, not only describe.

## 3.5 Compliance & ESG reporting engine
A generic report engine with a template registry produces the **actual documents** an owner needs —
**13 reports built**, each framed honestly as *reporting support, not legal or audited filing*:

- **German-mandatory set:** CO₂ cost-allocation (CO2KostAufG, 10-step Stufenmodell), GEG conformity,
  Energieausweis pre-assessment.
- **Voluntary / high-demand:** GHG Inventory (GHG Protocol, dual-scope), **ESRS E-1** (flagship,
  E1-1…E1-9 with auto-filled energy/Scope figures + guided narrative editor), **VSME** Basic and
  Comprehensive modules (EFRAG SME standard), CRREM-aligned stranding, GRESB readiness, EnEfG
  measures plan, residential summary.
- **Authoring & output:** a structured **narrative editor** with PostgreSQL persistence (auto numbers
  + human narrative, no AI auto-draft), **per-building scoping**, and DOCX/PDF export.

## 3.6 IoT / fault detection
A real-time layer implementing **ASHRAE Guideline 36** automated fault detection (12 diagnostic rules,
~31 sensor types) with multi-protocol adapters for **BACnet / Modbus / MQTT**.

## 3.7 Residential vertical (Hausverwaltung)
A full second vertical for residential property management: unit-level data model, **heat-cost &
CO₂-cost allocation**, a **landlord investment case** that resolves the split-incentive problem
(who pays for retrofits vs. who benefits), and **climate-adjusted EUI** consistent with the
commercial engine — with separate resident and manager views.

## 3.8 Execution marketplace (Phase 0)
The first step of the **insight → action → execution** loop: a lean, founder-brokered "Request an
installer" capture on every recommendation, with honest framing ("EnergyLens introduces; it does not
warrant or contract"). The roadmap — vendor matching, RFQ/quotes, take-rate commission — is a future
revenue line (see §6).

## 3.9 Self-serve onboarding + Data Score
A gamified **Data Score** maps data completeness to report readiness: each building shows what is
ready / partial / locked and exactly which input unlocks which report — an indirect incentive to
improve data quality, and the foundation for fully automated, self-serve onboarding.

**Maturity, stated plainly.** The platform runs on **ten representative buildings** (Germany, Turkey,
Austria, the Netherlands; ~3.5 years; ~693,000 data points). The **methodology and external data are
real**; building-level operational data is **synthetic** until the first pilot. There are **no paying
customers yet** — a first pilot is in active outreach. The funded year converts this proven prototype
into a validated, incorporated company.

---

# 4. Innovation & unique selling proposition

EnergyLens's innovation is not a single feature but a **combination no competitor offers at the
mid-market**, backed by a research-grade development agenda. What already works and what the coming
year develops are kept distinct below.

## 4.1 The unique combination (already working)
1. **Fabric-native, with auditable carbon lineage.** Because every workload reads one copy of the data
   on OneLake, every disclosed kilogram of CO₂ traces back to the raw bill row — the "regulator-grade
   lineage" ESRS/VSME reporting requires, and structurally hard for spreadsheet or multi-tool
   competitors to match.
2. **An AI copilot that uses tool use, not text summaries** — it runs real Lakehouse queries and one
   tool writes back, so it can act.
3. **Multi-protocol IoT fault detection at mid-market price** — ASHRAE Guideline 36 across BACnet,
   Modbus and MQTT, as affordable SaaS rather than a six-figure enterprise install.
4. **A multi-country EU-regulation & reporting engine** (DE, AT, NL, TR, EU) that turns findings into
   **ranked actions and the actual regulatory documents**.
5. **A closed insight → action → execution loop** — from anomaly to recommendation to a brokered
   installer, with a Data-Score onboarding that makes the whole thing self-serve.

## 4.2 The innovation agenda (developed during the funded year)
The year turns the working platform into a defensible, research-grade product along **four axes**:

- **A — Agentic AI copilot.** Evolve from answering questions to **proposing and sequencing** retrofit
  and dispatch plans — an autonomous "decarbonisation advisor" grounded in the building's own data.
- **P — Predictive intelligence.** Move beyond statistical forecasting to **ML predictive
  maintenance** that detects developing faults before they cost money.
- **O — Closed-loop optimisation.** Move from simulation to control: optimal battery dispatch, HVAC
  setpoint optimisation and **automated demand response**, aligned with the EU Demand-Response
  Network Code.
- **M — Auditable carbon methodology (academic IP).** Formalise the traceable carbon-lineage method
  into a **publishable methodology, developed jointly with the academic host** — strengthening both
  the product's defensibility and its research-transfer character.

## 4.3 Defensibility (moat)
The moat is the compounding combination: domain-specific data models + an auditable methodology
(potential academic IP) + a Fabric-native architecture + an agentic AI layer + an EU-regulatory
knowledge base + a two-sided execution loop, all aimed at a segment incumbents under-serve. None
alone is unassailable; together, with first-mover reference customers in DACH, they create a
defensible position. Microsoft-ecosystem alignment (DP-600, Partner Network track) adds distribution.

---

# 5. Market & business model

## 5.1 Market size
- **External anchor:** the BEMS software market is independently estimated at **~US $8.4 bn (2026) →
  ~$24 bn (2035), ~8.7 % CAGR** (market-research consensus; figures vary by definition).
- **Illustrative top-down TAM/SAM:** ~5 million EU non-residential buildings at €100–700/building/month
  imply an order-of-magnitude **TAM ~€18 bn/yr**, with a DACH-focused **SAM ~€4.3 bn/yr**. These are
  illustrative framing figures, not bottom-up forecasts.
- **Serviceable obtainable (3-year, realistic):** 100–200 customers → €1–2 m ARR.

## 5.2 Customers & segments
Validation-first: start where deals close in 2–8 weeks — **university campuses** and **DACH
mid-market property managers (5–50 buildings)** — then use case studies to reach hotels, healthcare
and REITs. A distinct second vertical, **residential property management (Hausverwaltung)**, is
already built and addresses a large, compliance-driven (CO2KostAufG) market. Enterprise procurement
is deliberately deferred until product and references are mature.

## 5.3 Business model & pricing (per building / month)

| Tier | Price | Target segment |
|------|-------|----------------|
| Insight | €99 | SME offices |
| Monitor | €299 | mid-market property management |
| Copilot | €699+ | enterprise, healthcare, IoT-equipped |
| Portfolio (custom) | €5–50k/mo | 10+ building portfolios |

A pilot is **free for the first three months** to win reference cases. A future **marketplace
take-rate** (§6) adds a second, usage-aligned revenue line on top of subscriptions.

## 5.4 Unit economics (targets, pre-revenue)
Targets to validate in the first pilots, not results: ARR per customer ≈ **€17k** (5 buildings ×
€299/mo); gross margin **~85 %** (SaaS-typical minus cloud/inference); target **CAC payback < 6
months** in a founder-led, content- and network-driven motion; designed to break even on
infrastructure cost around the second customer. Headline LTV/CAC multiples are deliberately omitted
until real acquisition data exists.

## 5.5 Competitive landscape

| Competitor | Position | Gap EnergyLens fills |
|------------|----------|----------------------|
| Measurabl / Aquicore | US enterprise, well-funded | mid-market EU coverage |
| Cortexa | EU enterprise | mid-market accessibility & price |
| Schneider EcoStruxure | peer (reporting + AI) | multi-protocol IoT + Fabric-native + mid-market price |
| Siemens Desigo | BMS / building automation | the analytics/intelligence layer, not a BMS |

**One-line position:** *the Microsoft Fabric-native energy-intelligence and EU-compliance platform for
the European mid-market, with an AI copilot that reasons over the Lakehouse via tool use — from under
€299/building/month.*

---

# 6. Product roadmap & future development

The technical foundation is broad and already built; the roadmap is about **depth, validation and new
revenue lines**, not rebuilding.

- **Execution marketplace (revenue line).** Evolve Phase 0 "request an installer" into a two-sided
  marketplace: vendor registry + matching, RFQ/quotes, and a **take-rate commission** on delivered
  retrofits — monetising the insight→action→execution loop beyond subscriptions.
- **Reporting engine.** Extend the 13-report engine toward **machine-readable filing (XBRL)**,
  additional standards and native Word/Excel output; deepen ESRS/VSME conformance as more client data
  arrives.
- **Residential expansion.** Grow the Hausverwaltung vertical: portfolio heat-cost automation,
  tenant-facing transparency, subsidy/retrofit ROI at scale.
- **Self-serve, fully automated onboarding.** Drive the Data-Score onboarding to a fully automated
  pipeline (customer data → reports with no founder in the loop) — a scale-economics step.
- **Innovation axes (A/P/O/M, §4.2).** Agentic planning copilot, ML predictive maintenance,
  closed-loop optimisation + demand response, and the published carbon methodology.
- **IoT depth.** BACnet + Modbus first (90 % of DACH BMS), then MQTT streaming and (premium) OPC-UA.
- **Geographic expansion.** Beyond DACH to BeNeLux + France (Décret Tertiaire, Erkende Maatregelen),
  with localisation.
- **Microsoft Partner Network.** Co-marketing and Cloud Marketplace distribution.

*Long-horizon vision:* by 2028, the leading Fabric-native energy-intelligence platform for European
real estate — turning every building into a self-diagnosing, decarbonising asset.

---

# 7. 12-month implementation plan

The technical foundation exists and the founder builds quickly; the genuine 12-month work is
**customer validation, sales, incorporation, regulatory/IP and research**. Milestones are therefore
expressed as business outcomes, with technical work in support. Because execution is fast, the plan is
front-loaded and milestones can be reached early.

**Q1 (months 1–3) — Validate.** First pilot live; 2–3 design partners engaged; pricing in test. Build:
production hardening; predictive-maintenance models in training; the carbon-methodology research
started with the academic host. *Metric:* ≥ 1 live pilot, ≥ 5 discovery conversations/week.

**Q2 (months 4–6) — Sell.** Convert pilots into 2–3 paying customers; pricing validated. Build: ship
the agentic copilot (propose-and-sequence) as the commercial wedge; harden the compliance engine for
real client data. *Metric:* first recurring revenue; ≥ 1 named case study.

**Q3 (months 7–9) — Incorporate & build the team.** Register the **UG (haftungsbeschränkt)**; first
hire (GTM / sales-engineering); pipeline toward 5 customers; launch marketplace matching as a pilot.
Build: closed-loop optimisation in production; security/GDPR review. *Metric:* company registered;
4–5 customers signed or in late stage.

**Q4 (months 10–12) — Fundable.** 5+ customers, €5–10k MRR; the **auditable-carbon methodology paper
submitted** with the academic host; Microsoft Partner Network track entered. Build: scale-readiness
(automated onboarding, reliability); seed/angel materials. *Metric:* sustainable MRR; a defensible,
demonstrable innovation; a credible seed story.

**Traction before the year begins.** First-pilot outreach, early sales conversations and freelance
income proceed in parallel now, so the venture enters the funded period **with traction already in
hand**.

---

# 8. Use of funds (≈ €45,000 over 12 months)

The 12-month budget is modest and focused, split between the founder's full-time commitment, a small
material budget and external coaching:

| Category | Amount | Purpose |
|----------|--------|---------|
| Stipend (living costs) | €30,000 | 12 months full-time (rent, living, insurance) |
| Software & cloud | €4,000 | Microsoft Fabric capacity (F-SKU), Power BI, AI inference, SaaS tooling |
| Hardware | €2,500 | Development laptop refresh, monitor, A/V for demos |
| Customer acquisition | €1,500 | Targeted outreach, events, content |
| Legal & administrative | €2,000 | UG incorporation, IP counsel, GDPR review |
| Coaching | €5,000 | Start-up mentor, sales coaching, technical advisory |
| **Total** | **≈ €45,000** | toward an incorporated, revenue-generating company |

*A founding team would expand the material budget and add a stipend per member; bringing on a
complementary commercial co-founder is an explicit option for the funded year (§9).*

---

# 9. Team, risks & mitigations

## 9.1 Team & hiring plan
The venture is currently led by a **single founder**. This is mitigated deliberately: the founder
already spans the two hardest-to-combine skill sets (**energy domain + data engineering**), reducing
early dependency on hires; an academic mentor and 1–2 advisors provide a visible support structure; a
**first GTM / sales-engineering hire is planned for Q3**, timed to first revenue; and a complementary
commercial **co-founder is an open option** once early traction de-risks equity.

## 9.2 Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Solo-founder bandwidth | First GTM hire in Q3; advisor network; onboarding automation |
| Pilot → paid conversion is slow | Free, low-risk pilots; quantified value reports; freelance runway buffer |
| "Integration, not innovation" perception | Four-axis agenda (agentic AI, predictive, optimisation, methodology IP) + an academic paper |
| Methodology / compliance over-claim | Honest labelling ("ESRS-E1-aligned support"; screening estimates flagged) reviewed before any "compliant" wording |
| Visa / residency | 18-month post-graduation Job-Search Visa; intent to incorporate (UG) and remain in Germany |
| Single-vendor (Microsoft) dependency | Provider-abstracted AI layer; standards-based IoT; data portable via open Delta/Parquet |
| Incumbent price pressure | EU-regulatory depth + Fabric-native lineage + mid-market focus as differentiation, not price |

## 9.3 Current limitations (stated openly)
A credible application is precise about maturity: Scope 3 is a labelled **screening estimate** (not
disclosure-grade); market-based Scope 2 needs supplier-contract data to differ from location-based;
**CRREM pathways are indicative** pending a License-Partner agreement; some HVAC splits are **modelled**
(HDD/CDD) rather than sub-metered; battery-ROI savings are currently **upper-bound** pending
hour-by-hour tariff matching; building consumption data is **synthetic** until the first real pilot.
Each has a concrete improvement on the roadmap. Naming exactly what is not yet real, and exactly how
to make it real, is a stronger signal than a polished claim of completeness.

---

# 10. Founder & academic anchor

**Ali Mert Özdemir.**

- **Education:** B.Sc. Energy Engineering (Yaşar University, İzmir); M.Sc. Energy Management (BSBI
  Berlin, June 2026).
- **Certification:** **Microsoft DP-600** (Implementing Analytics Solutions Using Microsoft Fabric) —
  a recent, in-demand certification rarely held by solo founders.
- **Demonstrated execution:** designed and built the **entire EnergyLens stack** — Fabric pipeline,
  10-page Power BI report, IoT/fault-detection layer, battery simulator, multi-tenant web app, AI
  copilot and a 13-report compliance engine — solo, end-to-end, accelerated by AI-assisted
  development.
- **Residency:** Berlin-based; 18-month Job-Search Visa runway post-graduation to incorporate and
  reach first revenue in Germany.

**Academic anchor.** EnergyLens originates directly from the founder's M.Sc. work, which gives the
venture a genuine **research-transfer character**: a **joint carbon-methodology publication** with the
academic host is planned during the funded year (innovation axis M, §4.2). *[Academic host and named
mentor — to be confirmed.]*

---

# 11. Timeline & next steps

- **Now:** confirm the academic host and named mentor; finalise this package with the host's start-up
  service.
- **In parallel:** first pilot, early customer outreach and freelance runway — building traction
  before the funded period begins.
- **On confirmation:** submit through the host institution; on approval, sign the funding agreement
  and begin the 12-month period (target Q1 2027).

---

*EnergyLens — turning every building into a self-diagnosing, decarbonising asset. Figures marked
illustrative or target are pre-revenue assumptions to be validated in pilots. energylens.eu ·
Microsoft DP-600.*
