# EnergyLens — Executive Summary

**Smart energy intelligence for commercial buildings**

---

## The Problem

European commercial buildings account for **40% of total energy consumption** and **36% of CO₂ emissions** in the EU. Yet most building portfolios still rely on **monthly utility bills and spreadsheets** to manage energy — making them blind to anomalies, regulatory risk, and decarbonization opportunities.

Meanwhile, EU regulation is tightening rapidly:
- **EU CRREM** (Carbon Risk Real Estate Monitor) pathways require every commercial building to decarbonize by 2030
- **EnEfG** (Germany, 2023) mandates energy efficiency audits for buildings >7.5 GWh/year
- **EU CSRD** forces sustainability reporting for all large enterprises (2024+)
- **EU Battery Regulation 2023/1542** requires battery passports for new installations

Property owners and managers face **€10B+/year in compliance risk** without modern energy intelligence tools.

---

## The Solution

**EnergyLens** is a Microsoft Fabric-native energy intelligence platform that unifies multi-building data into a single live dashboard, with built-in EU regulatory compliance scoring and AI-powered recommendations.

**Key capabilities:**
- **Multi-building portfolio view** — Real-time KPIs across 1 to 1,000+ buildings
- **EU compliance scoring** — Live CRREM, EnEfG, GEG, EPC tracking per building
- **HVAC optimization** — Heat pump COP monitoring, envelope retrofit prioritization
- **Battery dispatch simulation** — EU 2023/1542 compliant ROI scenarios
- **Anomaly detection** — Catches energy waste in real time, estimates € cost
- **IoT interoperability** — BACnet, Modbus, MQTT, OPC-UA adapters

Built on Microsoft Fabric medallion architecture, the platform scales from a single building to enterprise portfolios while keeping infrastructure costs predictable.

---

## Why Now

1. **Regulatory pressure** — EU climate regulations are binding from 2024-2030, creating €10B+ market urgency
2. **Energy crisis legacy** — Post-2022 spikes made energy a board-level priority
3. **Microsoft Fabric maturity** — Released GA in 2023, now enterprise-ready (cost-effective for SaaS)
4. **IoT cost collapse** — BACnet/Modbus sensors now €50-200 vs €500+ five years ago
5. **AI commodification** — Pattern recognition + forecasting now feasible at SaaS prices

---

## Why Us

**Ali Mert Özdemir** — Solo founder building EnergyLens from Berlin.

- **Energy Engineering** B.Sc. (Yaşar University, Turkey) + **Energy Management** M.Sc. (BSBI Berlin, expected June 2026)
- **Microsoft DP-600 certified** (Implementing Analytics Solutions Using Microsoft Fabric) — one of the most recent and demanded Microsoft certifications
- 1+ year engineering experience + prior entrepreneurial ventures
- Built full-stack EnergyLens MVP solo: Fabric medallion pipeline, 9-page Power BI dashboard, IoT adapter framework, battery dispatch simulator
- DACH-based with 18-month visa stability post-graduation

**Unique combination:** Deep domain expertise + Microsoft Fabric mastery + EU market access — rare in the energy SaaS space.

**Demonstrated execution:** In ~5 weeks (April–May 2026) shipped the 9-page Fabric dashboard, the live web application, three-provider authentication, and an AI Copilot with LLM tool use over the Lakehouse — solo, end-to-end.

---

## Market & Traction

### Total Addressable Market
- **EU commercial buildings:** ~5 million
- **Average software value:** €100-700/building/month
- **TAM (EU):** ~€18B/year
- **SAM (DACH focus):** ~€4.3B/year

### Competitive landscape
| Competitor | Funding | Focus | Gap EnergyLens fills |
|---|---|---|---|
| Measurabl | $200M+ | US enterprise | Mid-market EU |
| Aquicore | $40M | US offices | EU regulatory specifics |
| Cortexa | $30M | EU enterprise | Mid-market accessibility |
| BuildingIQ | Public | Enterprise BMS | SaaS pricing, Fabric-native |
| Honeywell Forge | Internal | Enterprise | Standalone product |

**EnergyLens unique angle:** Microsoft Fabric-native + EU regulatory niche + mid-market pricing (€99-€699/building/month).

### Current Traction
- **MVP complete** — 9-page Power BI dashboard with realistic data from 10 representative buildings (Germany, Turkey, Austria, Netherlands), 3.5 years, 693K+ data points
- **Architecture proven** — Bronze/Silver/Gold medallion in Microsoft Fabric (57 Lakehouse tables across layers)
- **Web application live (v1)** — Next.js + FastAPI + Azure PostgreSQL, three-provider authentication (Microsoft Entra ID, Google, Email/Password), embedded Power BI viewer, custom React portfolio and building pages reading directly from Fabric Lakehouse SQL Analytics Endpoint
- **AI Copilot live** — Conversational analytics over Microsoft Fabric using LLM tool use (six tools spanning gold KPI tables, anomalies, recommendations, battery simulation, and recommendation status); production-ready with provider abstraction (Anthropic / Azure OpenAI / Mock) and Server-Sent Events streaming
- **Three parallel data paths into Fabric** validated end-to-end: Power BI DirectLake embed, custom React via SQL Analytics Endpoint, and LLM tool use through backend dispatcher
- **Domain registered** — energylens.eu live, Azure subscription active
- **First pilot in discussion** — BSBI Berlin campus as M.Sc. capstone validation
- **Brand identity finalized** — EnergyLens "Emerald Pulse" design system, applied across the web app (Tailwind v4 design tokens + shadcn/ui)

---

## Business Model

**SaaS subscription, per building per month:**

| Tier | Price | Target |
|---|---|---|
| **Insight** | €99/building/month | SME offices (<5,000 m²) |
| **Monitor** | €299/building/month | Mid-market property mgmt (5-15k m²) |
| **Copilot** | €699-1,500/building/month | Enterprise REIT, healthcare, IoT-equipped |
| **Portfolio Custom** | €5k-50k/month | 10+ building portfolios |

**Revenue path:**
- Year 1: 5-10 pilot customers → €30k-100k ARR
- Year 2: 30-50 customers → €300k-600k ARR
- Year 3: 100-200 customers → €1M-2M ARR

---

## Microsoft Partnership Ask

We are applying to Microsoft for Startups Founders Hub to:

1. **Solve immediate infrastructure capacity** — Fabric Trial F4 SKU is insufficient for production workloads
2. **Access Azure credits** to scale Fabric capacity, Power BI Premium, and Azure container hosting for the web app
3. **Build on Microsoft-native stack** — Already DP-600 certified, planning Microsoft Partner Network membership
4. **Co-marketing potential** — EnergyLens is a strong reference case for Fabric in the energy vertical (currently underserved)

**Specific resource needs:**
- Microsoft Fabric F8+ capacity (~$2,500/month value)
- Power BI Premium per Capacity (12-month license)
- Azure compute for FastAPI backend + PostgreSQL (web app already operating locally, ready to migrate)
- **Azure OpenAI credits to switch the live AI Copilot from the current Mock provider to production GPT-4o (provider abstraction already in place, single environment variable to flip)**

---

## Vision (3-year)

By 2028, EnergyLens is the **leading Microsoft Fabric-native energy intelligence platform** for European commercial real estate, serving 200+ buildings across DACH, expanding to BeNeLux and Southern Europe. We are the **defaut choice** for property managers seeking EU regulatory compliance + operational energy optimization, positioned as a strategic Microsoft partner in the climate-tech vertical.

---

## Contact

**Ali Mert Özdemir**
Founder, EnergyLens
- Email: alimertozdem@gmail.com
- LinkedIn: https://www.linkedin.com/in/alimertozdemir96/
- GitHub: https://github.com/alimertozdem
- Domain: energylens.eu *(registered; production deployment pending Azure migration)*

*Document version 1.1 — May 2026 (updated after Day 16: live web app + AI Copilot)*
