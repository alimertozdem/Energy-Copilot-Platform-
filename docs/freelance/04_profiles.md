# Platform Profiles — Copy-Paste Ready Text

**For:** Ali Mert Özdemir
**Date:** 2026-05-26
**Status:** Draft v1 — review and personalize before publishing

> **Reading guide (tr):** Aşağıdaki metinler doğrudan kopyala-yapıştır kullanım için hazır. Önce hepsini oku, sonra sırayla Malt → Contra → freelance.de → Toptal başvurusu yap. Her platforma özel ton ve format farklı (Malt detay sever, Contra kısa-vurucu, freelance.de daha kurumsal). Tüm hesaplarda **aynı 3 case study** kullanılıyor — bunlar EnergyLens'ten gelen kanıt. Profil fotoğrafı: profesyonel headshot, sade arkaplan, gülümseme var, kravat yok (data/tech freelancer beklentisi).

---

## SECTION 1 — MALT (Primary Channel)

**Why Malt is primary:** EU-focused, English profiles fully supported, premium daily rates, clients reach out to you instead of you bidding. Best ROI per hour of setup.

**URL to create profile:** https://www.malt.com/

### 1.1 Display Name
```
Ali Mert Özdemir
```

### 1.2 Headline / Title (max 80 characters)

Use this one (Recommended):
```
CSRD & ESG Reporting Expert | Microsoft Fabric & Power BI for Energy Data
```

Alternative if first feels too long:
```
Microsoft Fabric Specialist | CSRD-Ready Dashboards for Energy & Buildings
```

### 1.3 Location
```
Berlin, Germany
```

### 1.4 Languages
- English — Fluent (working language)
- Turkish — Native
- German — A2 / Conversational *(only add if you are comfortable with it — better to be honest than oversold)*

### 1.5 Hourly / Daily Rate
- **Daily:** €450/day (opening)
- **Hourly:** €60/hour (opening)
- **Availability:** "Open to projects" — set 3 days/week available

### 1.6 Skills Tags (add all of these — Malt uses tags for search match)

Primary:
```
Microsoft Fabric, Power BI, DAX, Data Engineering, Data Visualization,
ESG Reporting, CSRD, GHG Protocol, Sustainability Reporting,
Energy Analytics, Building Energy, Carbon Accounting, Scope 1 2 3 Emissions
```

Secondary:
```
Direct Lake, OneLake, Lakehouse, KQL, Real-Time Intelligence,
Python, PySpark, Azure Data Factory, Delta Lake,
Power BI Embedded, Tabular Editor, Semantic Modeling, EnPI, ISO 50001
```

### 1.7 Profile Summary (The Main Bio — Long Format)

> **Note (tr):** Bu uzun metin Malt'ın "About me" bölümüne gidiyor. Olduğu gibi yapıştır, sadece "10+ buildings" gibi sayıları kendi gerçek portföyüne göre güncelle.

```markdown
## What I Do

I help mid-market property portfolios and ESG/sustainability consultancies turn raw building energy data into CSRD-ready Power BI dashboards on Microsoft Fabric — with auditable Scope 1/2/3 numbers and regulator-grade data lineage.

Most Power BI consultants know finance dashboards. Most ESG consultants know spreadsheets. I sit at the intersection: Microsoft Fabric engineering + EU energy regulation + Power BI analytics. There are very few of us in Europe right now.

## Who I Work With

- **ESG and sustainability consultancies** building productized CSRD reporting offerings for their clients
- **Property and portfolio managers** (50–500 buildings) needing energy benchmarking, EnPI tracking, and EPC compliance dashboards
- **Mid-cap sustainability teams** with Microsoft Fabric already in-house, missing the dashboard layer

## What Sets Me Apart

I have already built and operate an end-to-end energy intelligence platform — EnergyLens — across 10 buildings, with:

- A 9-page production Power BI report suite
- Scope 1/2/3 GHG emissions model mapped to ESRS E1 disclosures (area-weighted EPC scoring, market-based and location-based Scope 2)
- Real-time IoT monitoring via Microsoft Fabric EventStream + KQL Eventhouse (BACnet / Modbus ingestion)
- Battery dispatch and ROI scenario simulation aligned with EU Battery Regulation 2023/1542
- A production DAX measure library (v56) optimized for Direct Lake mode

This is not a tutorial portfolio. It is a live system, built from raw silver/gold medallion ingestion to Power BI semantic model.

## My Productized Offerings

**P1 — CSRD Scope 1/2/3 Quickstart** — 2 weeks, €3,200 fixed
Connect 2–3 data sources, deliver a Scope 1/2/3 dashboard mapped to ESRS E1 datapoints, in your Power BI tenant. Includes methodology documentation.

**P2 — Building Energy KPI Dashboard** — 1 week, €1,800 fixed (≤5 buildings)
Ingest utility bills + EPC + optional BMS exports. EnPI, kWh/m², EPC compliance heat map, baseline comparison.

**P3 — Microsoft Fabric Audit & Roadmap** — 3 days, €1,200 fixed
Review of your Fabric setup, written recommendations on Direct Lake / Real-Time Intelligence / capacity sizing.

**P4 — Power BI Performance Tune-up** — 2 days, €800 fixed
DAX profiling, model optimization, before/after benchmark. Quick win for slow reports.

For non-productized work, I work at €450/day or €60/hour.

## Credentials

- Microsoft Certified: Fabric Data Engineer Associate
- MSc Sustainable Energy Systems (BSBI Berlin)
- Native energy domain — boiler/HVAC/IoT operations, not just spreadsheets

## Working Style

- I write before I code. Every engagement starts with a one-page scope memo.
- I deliver in your tenant, in your stack — no lock-in.
- I document for handover from day one. Your team can maintain what I build.

Available for engagements across the EU. Working language is English. Based in Berlin, available for on-site days in Germany / Austria / Netherlands.

Send me your brief and I'll respond with a scoped proposal within 48 hours.
```

### 1.8 Featured Projects (Case Studies)

Malt has a "Realizations" / "Projects" section. Add **3 case studies** as separate entries:

---

**Case Study 1 — "10-Building Energy Intelligence Platform on Microsoft Fabric"**

*Client type:* Mid-market property portfolio (internal project / EnergyLens demonstrator)
*Duration:* 8 months
*Stack:* Microsoft Fabric, Power BI, Python (PySpark), Delta Lake, EventStream, KQL

**Situation:** A multi-building portfolio across Germany, Turkey, and broader EU lacked unified visibility into energy consumption, cost, comfort, and carbon. Data lived in utility bills, EPC certificates, BMS exports, and manual Excel tracking — five siloed sources.

**Action:**
- Designed a medallion architecture (Bronze → Silver → Gold) on Fabric Lakehouse
- Built 9 Power BI pages: portfolio overview, building drill-down, anomaly detection, energy forecasting (Prophet), decision support, sustainability/GHG, hourly profiles, real-time IoT, battery dispatch ROI
- Implemented Scope 1/2/3 emissions model with EPC area-weighted portfolio scoring, mapped to ESRS E1 disclosures
- Configured EventStream + KQL Eventhouse for sub-second IoT telemetry from BACnet sensors
- Production DAX library (v56) with self-contained, building-type-aware measures

**Result:**
- Portfolio-level kWh/m² visibility down from "no answer in 4 weeks" to "live dashboard"
- ESRS E1 disclosure data traceable from raw bill row to disclosed kg CO₂e
- Real-time HVAC anomaly detection across 10 buildings with €cost estimation per alert
- Used as the reference architecture for ESG consultancies needing a productized CSRD offering

---

**Case Study 2 — "CSRD Scope 1/2/3 Emissions Dashboard with ESRS E1 Mapping"**

*Client type:* Sustainability reporting use case (internal module of EnergyLens)
*Duration:* 4 weeks
*Stack:* Power BI, DAX, Microsoft Fabric Lakehouse, GHG Protocol methodology

**Situation:** Producing ESRS E1 disclosure data is a compliance bottleneck for most mid-cap European companies. Auditors require traceable methodology behind every Scope 1, 2, and 3 number. Existing Excel-based approaches fail audit because there is no row-level lineage.

**Action:**
- Implemented the GHG Protocol Corporate Standard calculation engine in the gold layer
- Modeled Scope 1 (boilers, fleet, refrigerants), Scope 2 (location-based and market-based electricity), and material Scope 3 categories
- Built a dedicated Power BI page (Page 6) with Scope donut, year-over-year comparison, building drill-down, and EPC compliance scoring
- Used LOOKUPVALUE for cross-table EPC area-weighting (avoiding common "average of averages" errors)
- Documented mapping from each visual to its ESRS E1 disclosure code (E1-1, E1-5, E1-6, E1-9)

**Result:**
- Single-click drill from disclosed total to raw utility bill row
- Audit-ready data lineage via Fabric medallion architecture
- Both market-based and location-based Scope 2 reported (ESRS E1-6 requirement many companies miss)

---

**Case Study 3 — "Real-Time IoT Monitoring for Commercial Buildings on Microsoft Fabric"**

*Client type:* Smart building / facility management use case (EnergyLens Page 8)
*Duration:* 3 weeks
*Stack:* Microsoft Fabric EventStream, KQL Eventhouse, Power BI Direct Lake, Python adapter framework

**Situation:** Facility managers needed live visibility into HVAC performance, zone comfort, CO₂ levels, and energy demand across 10 buildings. Scheduled refreshes (every 15 minutes) were too slow; importing all sensor data into Power BI would have blown out memory.

**Action:**
- Designed a protocol adapter framework in Python supporting BACnet/IP, Modbus TCP, MQTT 5.0, and REST APIs
- Built a Bronze → Silver → Gold IoT pipeline with normalized units (°C, %, ppm, kW)
- Configured EventStream feeding both a KQL Eventhouse (for sub-second queries) and a Lakehouse (for historical analysis)
- Power BI Direct Lake semantic model for near-import performance on live data
- Implemented anomaly cost estimation (kW excess × duration × country grid price)

**Result:**
- Sub-second telemetry latency from sensor to dashboard
- Live alert table with estimated daily €cost per anomaly
- Dynamic sensor inventory — buildings with minimal BMS see appropriate dashboard layout, full BMS buildings get extended views

---

### 1.9 Sectors of Expertise (Malt has a dropdown)
- Energy
- Sustainable Development / CSR
- Real Estate
- Industry / Manufacturing (secondary)

### 1.10 Tools (Malt has a tool tag picker)
- Microsoft Power BI
- Microsoft Azure
- Microsoft Fabric
- Python
- Apache Spark
- DAX
- Tabular Editor
- Git / GitHub

---

## SECTION 2 — CONTRA (Replaces Upwork)

**Why Contra:** Free for freelancers (no commission), modern interface, English-only EU market growing, supports productized "services" beautifully. Faster to set up than Toptal, less competitive than Upwork.

**URL:** https://contra.com/

### 2.1 Display Name + Tagline
```
Ali Mert Özdemir
CSRD-Ready Power BI Dashboards on Microsoft Fabric
```

### 2.2 Bio (short — Contra is concise-friendly, max ~300 words)

```markdown
I build CSRD-ready energy dashboards on Microsoft Fabric & Power BI for European mid-market companies and ESG consultancies.

I'm one of the few freelancers globally combining all three:
→ Microsoft Fabric Data Engineer (certified)
→ Production Power BI / DAX (v56 measure library)
→ EU energy regulation (CSRD, ESRS E1, GHG Protocol, EU Battery Regulation 2023/1542)

I built EnergyLens — a 9-page production analytics platform across 10 buildings — and now help clients build similar Scope 1/2/3 dashboards in 2-4 week sprints.

If you have utility bills, EPCs, BMS data, or fragmented ESG spreadsheets and need to translate them into auditor-ready dashboards, that's exactly what I do.

Based in Berlin. Working language: English. Available EU-wide.
```

### 2.3 Contra "Services" (productized — Contra calls these "Services")

Create **4 services**, one per package:

**Service 1 — CSRD Scope 1/2/3 Quickstart**
- Price: €3,200 fixed
- Duration: 2 weeks
- Description (short): Get an auditor-ready Scope 1/2/3 dashboard mapped to ESRS E1 disclosures. I connect 2-3 data sources (utility bills, fleet log, refrigerant data), build the dashboard in your Power BI tenant, and deliver methodology documentation. Includes both market-based and location-based Scope 2.
- Deliverables: Power BI report, methodology PDF, data model documentation, 1-hour handover session.

**Service 2 — Building Energy KPI Dashboard**
- Price: €1,800 fixed for up to 5 buildings (+€250 each additional, up to 10)
- Duration: 1 week
- Description: For property portfolios. EnPI, kWh/m², EPC compliance heatmap, anomaly detection, baseline comparison. Works from your existing utility bills, EPC certificates, and optional BMS exports.
- Deliverables: Power BI report, refreshable data model, walkthrough video.

**Service 3 — Microsoft Fabric Audit & Roadmap**
- Price: €1,200 fixed
- Duration: 3 days
- Description: For teams who bought Fabric and don't know if they're using it correctly. I review your setup, identify Direct Lake and Real-Time Intelligence opportunities, recommend capacity sizing, and deliver a written 90-day roadmap.
- Deliverables: 15-page audit report with findings, prioritized recommendations, ROI estimates.

**Service 4 — Power BI Performance Tune-up**
- Price: €800 fixed
- Duration: 2 days
- Description: For slow Power BI reports. DAX profiling with DAX Studio, semantic model optimization, before/after benchmark. Usually delivers 3-10x query speed improvement.
- Deliverables: Optimized .pbix file, performance benchmark report, list of best practices applied.

### 2.4 Skills Tags
```
Microsoft Fabric • Power BI • DAX • ESG Reporting • CSRD • GHG Protocol
Scope 1 2 3 Emissions • Energy Analytics • Carbon Accounting • Python
Data Engineering • Direct Lake • Real-Time Intelligence • Sustainability
```

### 2.5 Portfolio (use same 3 case studies as Malt — Contra has a Portfolio section)

Use Case Studies 1, 2, 3 from Section 1.8 above, condensed to ~150 words each on Contra (it favors shorter text).

---

## SECTION 3 — FREELANCE.DE (Secondary, English Projects Only)

**Why:** German Mittelstand market, kurumsal (corporate) clients, higher per-project budgets when match found. But ~70% of projects are German-language. We will filter aggressively for English-only and keep this profile lower priority.

**URL:** https://www.freelance.de/

### 3.1 Title / Headline
```
Microsoft Fabric & Power BI Specialist — ESG / CSRD / Energy Analytics
```

### 3.2 Profile Description (English, more formal tone than Malt — German clients value formality)

```markdown
Microsoft Certified Fabric Data Engineer specializing in CSRD-compliant sustainability reporting and energy analytics on the Microsoft data platform.

I help mid-market European companies and ESG consultancies build production-grade Power BI dashboards on Microsoft Fabric — with verifiable Scope 1/2/3 emissions, EPC portfolio scoring, and real-time building telemetry.

**Background:**
- Microsoft Certified: Fabric Data Engineer Associate
- MSc Sustainable Energy Systems (BSBI Berlin)
- Built EnergyLens, a 9-page production analytics platform spanning 10 buildings, with ESRS E1-aligned GHG reporting and EU Battery Regulation 2023/1542-compliant battery dispatch modeling

**Service Focus:**
- CSRD / ESRS E1 reporting dashboards (Scope 1, 2, 3 + EPC + transition plan)
- Building portfolio energy KPI dashboards (EnPI, kWh/m², ISO 50001 framework)
- Microsoft Fabric architecture audits and Direct Lake migration
- Power BI performance optimization and DAX modeling

**Working Language:** English (German projects considered if technical scope is clear and stakeholder interaction is limited)

**Availability:** Currently accepting new engagements. Remote-first, available for on-site days in Berlin / DACH region.

**Productized Engagements:**
- CSRD Scope 1/2/3 Quickstart — 2 weeks, €3,200
- Building Energy KPI Dashboard — 1 week, €1,800
- Fabric Audit & Roadmap — 3 days, €1,200
- Power BI Performance Tune-up — 2 days, €800

Hourly rate: €60. Daily rate: €450.
```

### 3.3 Skills (freelance.de uses skill picker — add these)
```
Microsoft Power BI, Microsoft Fabric, DAX, ESG Reporting, CSRD,
GHG Protocol, Energy Management, ISO 50001, Python, PySpark,
Data Engineering, Data Visualization, Azure, Delta Lake, Power Query
```

### 3.4 Rates
- **Hourly:** €60
- **Daily:** €450

### 3.5 Filter setup (important — only see English-language projects)
- Set "Project language" filter to **English only**
- Set "Remote work" preference to **Remote possible**
- Set notification frequency: **Daily digest** (we will pipe these into our automation tool)

---

## SECTION 4 — TOPTAL (Apply Once, Premium Floor)

**Why:** If you get in, baseline rates are $80-150/hr, clients are pre-vetted, no competitive bidding. **Application is brutal** (4 stages: language, personality, technical screen, live test project). Many fail. Worth trying ONCE while you build other channels.

**URL:** https://www.toptal.com/freelance-jobs

### 4.1 Application Pitch (the initial 200-word self-introduction)

```markdown
I'm a Microsoft Certified Fabric Data Engineer specializing in CSRD-compliant sustainability reporting and energy analytics on Microsoft Fabric and Power BI. I'm one of the few freelancers globally combining three rare skills: production Microsoft Fabric (Direct Lake, EventStream, KQL Eventhouse), EU energy regulation (CSRD, ESRS E1, GHG Protocol, EU Battery Regulation 2023/1542), and senior-level Power BI semantic modeling (production DAX library at v56).

I built EnergyLens — an end-to-end 9-page production Power BI report across a 10-building portfolio — with Scope 1/2/3 emissions modeling, EPC area-weighted compliance scoring, real-time IoT monitoring via BACnet/Modbus/MQTT, and battery dispatch ROI simulation. Stack: Microsoft Fabric Lakehouse, EventStream, KQL, Python/PySpark, Direct Lake semantic model, Tabular Editor.

I hold an MSc in Sustainable Energy Systems (BSBI Berlin) and a B.Eng in Mechanical Engineering. I work primarily with mid-market European ESG consultancies and property portfolio managers. Working language is English; I am based in Berlin.

I'm applying to Toptal because the EU CSRD wave creates structural demand for the exact intersection I serve, and your client pool aligns with the mid-cap and consultancy segment I focus on. Looking forward to the screening process.
```

### 4.2 Technical Screen Prep (when invited)

Toptal's technical screen for data engineers typically covers:
- SQL deep dive (window functions, CTEs, query optimization)
- Python data manipulation (Pandas / PySpark)
- Data modeling questions (star schema, normalization, slowly changing dimensions)
- Live system design (e.g., "design an ETL for X")

**Your prep:** Practice 5 medium/hard SQL window function problems on StrataScratch (free). Refresh PySpark basics. Walk through your medallion architecture out loud as your live system design example.

### 4.3 Live Test Project

If you reach this stage, expect a 2-3 day mini-project graded on code quality, documentation, communication. Your EnergyLens code style (notebook patterns, error handling, documentation) is already at this level — show that quality.

---

## SECTION 5 — Cross-Platform Setup Tasks

### 5.1 Photo
Take a professional headshot:
- Plain neutral background (white, light grey, or muted blue)
- Soft natural light, no flash
- Smile, eye contact with camera
- Smart casual (button-up shirt, no tie, no t-shirt)
- High resolution (>1500x1500 px for cropping flexibility)

(tr: Profil fotoğrafı çok önemli. Telefonun timer'ıyla çekme. Bir arkadaşına çektir veya €40 verip bir foto stüdyosunda çek. Bu €40 ilk işte geri döner.)

### 5.2 LinkedIn — Mirror These Profiles

After publishing on Malt/Contra, update LinkedIn:
- Headline matches Malt headline
- About section matches Malt summary (slightly shorter)
- Add EnergyLens as a "Project" with same case study
- Pin a post showing one EnergyLens screenshot

### 5.3 GitHub
- Make EnergyLens GitHub repository public OR create a sanitized "EnergyLens-public" repo with:
  - Architecture diagrams
  - Sample notebooks (no proprietary data)
  - README that mirrors your positioning
- Pin this repo on GitHub profile

### 5.4 Personal Domain (optional, high-leverage)
Buy `energylens.eu` or `mertozdemir.com` (cheap, ~€10/year). Single landing page with:
- The one-line positioning
- 3 case studies
- 4 productized packages with prices
- "Book a discovery call" Calendly link

This becomes the link you put in every cold email.

(tr: Bu opsiyonel ama getirisi yüksek. Müşteri toplantıdan sonra senin profesyonelliğini ölçmek için Google'a "Ali Mert Özdemir" yazıp baksa, kendi sitesi olan bir freelancer ile bağımsız hesabı olan freelancer arasındaki fark çok büyük. Bir hafta sonu çalışmasıyla halledilebilir.)

---

## SECTION 6 — Order of Operations (next 5 days)

| Day | Task | Time |
|---|---|---|
| **Day 1** | Take + edit profile photo. Set up Malt account, paste profile, upload 3 case studies | 3 hours |
| **Day 2** | Set up Contra. Create 4 services. Add portfolio. Polish bio. | 2 hours |
| **Day 3** | Set up freelance.de. Translate any German UI as needed. Filter English-only projects. | 1.5 hours |
| **Day 4** | Submit Toptal application. Update LinkedIn to mirror. | 2 hours |
| **Day 5** | Polish, screenshot 5 EnergyLens views, add to all profiles. Buy domain if going that route. | 2 hours |

After Day 5, you start receiving and responding to inbound. The automation tool (Step 5) handles the outbound.

---

## SECTION 7 — Pre-Publish Checklist

Before pressing "Publish" on Malt and Contra, verify:

- [ ] Profile photo is sharp and professional
- [ ] Headline contains: "Microsoft Fabric" + "CSRD" or "ESG" + "Power BI"
- [ ] Bio leads with pain you solve, not with your CV
- [ ] All 4 productized packages have fixed prices visible
- [ ] At least 3 case studies are written and visible
- [ ] EnergyLens screenshots are in the gallery (blur any proprietary data)
- [ ] Skills tags include both regulatory (CSRD, ESRS, GHG) and technical (Fabric, DAX, Direct Lake) terms
- [ ] Hourly + daily rates set conservatively (we raise later)
- [ ] Availability set to "Open to projects" / "Available"
- [ ] Languages: English fluent at minimum
- [ ] LinkedIn URL added (Malt allows this)
- [ ] GitHub URL added if you have a public repo

When all boxes are ticked, publish. Then start the automation tool work.
