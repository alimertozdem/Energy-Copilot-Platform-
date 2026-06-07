# EnergyLens — Product Roadmap (6 / 12 / 24 months)

**Vision:** By 2028, EnergyLens is the leading Microsoft Fabric-native energy intelligence platform for European commercial real estate.

---

## Roadmap Overview

```
NOW (May 2026)    +6mo (Nov 2026)    +12mo (May 2027)    +24mo (May 2028)
    │                  │                    │                    │
    ▼                  ▼                    ▼                    ▼
  MVP            FIRST PILOTS        SCALE READY            MARKET LEADER
  9 pages        2-5 customers       15-30 customers        100-200 customers
  Sample data    Real data          AI + IoT live         DACH leadership
```

---

## PHASE 1 — Foundation (Q2 2026, COMPLETE)

### Status: ✅ Complete

**Data & analytics layer (April-May 2026):**
- ✅ 9-page Power BI dashboard MVP (Portfolio, Building, Anomalies, Forecast, Occupancy, Sustainability, HVAC, IoT, Battery)
- ✅ Microsoft Fabric medallion architecture (Bronze/Silver/Gold, 57 tables)
- ✅ Realistic data: 10 representative buildings (DE, TR, AT, NL), 3.5 years, 693k+ data points
- ✅ DAX measure library (v56, 50+ measures, building-type aware thresholds)
- ✅ Battery dispatch simulator (12 countries × 8 chemistries × 7 strategies, EU 2023/1542 compliant)
- ✅ CRREM pathway integration, Scope 1/2/3 GHG accounting
- ✅ Anomaly detection engine, HVAC analytics with envelope U-values

**Web application (May 24-27, 2026):**
- ✅ Next.js 16 + FastAPI + Azure PostgreSQL (10 tables, multi-provider auth)
- ✅ Three-provider authentication: Microsoft Entra ID + Google + Email/Password (bcrypt)
- ✅ `/portfolio` reading directly from Fabric Lakehouse SQL Analytics Endpoint (custom React + pyodbc + ODBC Driver 18)
- ✅ `/buildings/[id]` with embedded Power BI via service principal (V2 embed API, DirectLake compatible, app-owns-data)
- ✅ Brand-aligned design system (Tailwind v4 design tokens, shadcn/ui, EnergyLens "Emerald Pulse" applied across UI)

**AI Copilot (May 28, 2026):**
- ✅ LLM provider abstraction (Anthropic / Azure OpenAI / Mock)
- ✅ Six production tools: query_kpi, compare_buildings, list_recommendations, get_anomalies, simulate_battery_scenario, update_action_status
- ✅ Tool dispatcher routing to Fabric Lakehouse + PostgreSQL
- ✅ Server-Sent Events streaming, conversation persistence, JWT auth, org/building-level access control
- ✅ End-to-end smoke tested with real Fabric SQL queries

**Brand & domain:**
- ✅ Brand identity finalized (EnergyLens "Emerald Pulse")
- ✅ Domain energylens.eu registered

**What's remaining (this phase):**
- ⏳ Page 8 IoT dashboard polish (post-capacity)
- ⏳ Microsoft for Startups application submission

**Deliverables by July 2026:**
- Final dashboard MVP screenshot pack
- Founder + product demo videos
- Microsoft Startups Tier 2 approved (target)

---

## PHASE 2 — First Pilots & Azure Production Migration (Q3-Q4 2026)

### Status: 🎯 Starting Jul 2026 (post-Tier 2 approval)

**Note (May 28, 2026):** The web app + Copilot work originally scoped for Phase 2 was pulled into Phase 1 and shipped early. Phase 2 is now focused on pilot acquisition, Azure deployment migration, and the Azure OpenAI swap — not on building the app from scratch.

### 2A — Pilot Acquisition (Aug-Oct 2026)

**Target: 2-5 pilot customers**

| Pilot type | Source | Cost to customer | Value to EnergyLens |
|---|---|---|---|
| BSBI Campus (university) | M.Sc. capstone, supervisor advisory | Free pilot, 6 months | Case study, validation |
| Berlin property mgmt firm | Cold outreach, LinkedIn, BSBI alumni | Discounted (€199/building/mo) | First paid customer, GTM learning |
| Hotel chain (small DACH) | Industry event, intern referrals | Free 3-month then €299 | 24/7 operations validation |
| Healthcare facility | Yaşar Univ network | Discounted | Critical loads use case |
| Office portfolio | Microsoft Partner referral | Standard pricing | Reference case |

**Sales process:**
1. 30-min discovery call
2. 60-min product demo (Power BI walkthrough)
3. 2-week pilot setup
4. Monthly review for 3 months
5. Conversion to paid

### 2B — Azure Deployment Migration (Jul-Aug 2026)

**Web app already built — migrating from local dev to Azure (~3 hours of work, code unchanged):**
- Azure Static Web Apps (Next.js frontend, currently localhost:3000)
- Azure Container Apps (FastAPI backend, currently localhost:8000)
- Azure PostgreSQL Flexible (currently Supabase Frankfurt — pg_dump / pg_restore migration)
- Embed Power BI via Premium capacity (Startups credit)

**Net new for Phase 2:**
- Customer onboarding wizard (`/onboarding` route — building inventory + module flags)
- Subscription management (Stripe integration, deferred to V1.5 if pilots stay free)
- Basic admin dashboard (`/admin` — tenant overview)
- `/actions` page using existing `recommendation_status` Postgres table
- Public `/demo` page (kayıtsız, read-only, 6 sample binalar)
- **Azure OpenAI swap:** LLM_PROVIDER environment variable flip from Mock → Azure OpenAI. Tools, dispatcher, frontend unchanged.

### 2C — IoT Adapters Phase 1 (Sep-Nov 2026)

**Priority: BACnet + Modbus TCP** (90% of DACH BMS market)

- BACnet/IP adapter (ASHRAE 135 standard)
- Modbus TCP adapter (IEC 61158 standard)
- Sensor normalization library (°C, %, ppm, kW)
- Live data ingestion to Eventstream → Lakehouse
- Page 8 IoT dashboard with real customer data

**Validation target:** 1 pilot building with real IoT sensors connected.

### 2D — UG mini-GmbH Incorporation (Oct 2026)

After first 2-3 customer commitments:
- UG (haftungsbeschränkt) registration in Berlin
- €1 minimum capital
- 1-2 days process via Notar
- Sets foundation for VAT, invoicing, banking

**Deliverables by Dec 2026:**
- 3-5 pilot customers using EnergyLens
- Web app v1.0 deployed
- BACnet + Modbus adapters live
- UG mini-GmbH registered
- First MRR €500-2,000/month

---

## PHASE 3 — Scale & AI Layer (Q1-Q2 2027)

### Status: 🎯 Jan-Jun 2027

### 3A — Customer Growth (Jan-Mar 2027)
**Target: 5 → 15 customers**

- Sales playbook from Phase 2 learnings
- Customer success program (monthly QBRs)
- Reference customer testimonials → website
- 2-3 case studies published
- First DACH conference presentation (e.g., Light + Building Frankfurt 2027)

### 3B — AI Copilot V2 (Feb-Apr 2027)

The Copilot core (tool use + SSE streaming + provider abstraction) is already live (May 2026). V2 expansion:
- **Production Azure OpenAI** — running in production from Phase 2 (Jul 2026), with V2 focus on cost optimization and observability
- **Auto-generated weekly reports** — Customer-specific narratives (additional tool: `generate_weekly_report`)
- **Markdown + chart rendering** in chat output (react-markdown, embedded recharts)
- **Building context selector + conversation titles** (V1.5 polish, planned Feb 2027)
- **Predictive maintenance** — ML-based equipment fault prediction surfaced as a Copilot tool
- **Multi-turn analytical workflows** — Copilot can plan a sequence of 3-5 tool calls to answer compound questions ("Which buildings underperform CRREM AND have high recommendation backlog AND have not been audited?")

### 3C — MQTT 5.0 Streaming (Mar-May 2027)

For Copilot-tier customers with modern IoT:
- MQTT 5.0 broker integration (Mosquitto, Azure IoT Hub)
- Sub-minute latency anomaly detection
- Push notifications (email, SMS, Microsoft Teams)
- Real-time tenant dashboards (multi-tenant buildings)

### 3D — Enterprise Features (Apr-Jun 2027)

For REIT/large customers:
- White-label deployment option
- Custom branding per customer
- Portfolio-level CRREM stranding heatmaps
- ESG reporting export (CSRD XBRL format)
- API access (REST endpoints for data export)

**Deliverables by Jun 2027:**
- 15-20 customers (€10k+ MRR)
- AI-powered insights live
- MQTT streaming for Copilot tier
- 1-2 enterprise reference customers
- First hire (junior developer or sales)

---

## PHASE 4 — Market Leadership (Q3 2027 - Q2 2028)

### Status: 🎯 Jul 2027 - May 2028

### 4A — Geographic Expansion (Jul-Dec 2027)

- Beyond DACH: BeNeLux + France
- Localization: French + Dutch interface
- Regulatory profile additions: Decret Tertiaire (FR), Erkende Maatregelen (NL)
- Partnership with local property management associations

### 4B — Microsoft Partner Network (Aug-Oct 2027)

- Apply for Microsoft Partner status
- Co-marketing opportunities (Microsoft Cloud Marketplace)
- Joint webinars on "Fabric for Energy"
- Microsoft Build / Ignite presence

### 4C — OPC-UA + Premium Tier (Oct 2027-Mar 2028)

Premium customers in advanced automation:
- OPC-UA adapter (Siemens, Rockwell compatibility)
- Industrial-grade integration (factories, hospitals, data centers)
- Custom rule engine (SCADA-grade alerts)
- 24/7 SLA support tier

### 4D — Team Building (continuous)

| Role | When | Why |
|---|---|---|
| Junior Full-Stack Dev | Q2 2027 (post first €10k MRR) | Web app feature velocity |
| Sales/BD | Q3 2027 | Scale customer acquisition |
| Customer Success | Q4 2027 | Retention focus, 15+ customers |
| Senior Data Engineer | Q1 2028 | Scale Fabric architecture |
| CTO / Co-founder | Q2 2028 (if right person) | Long-term strategic |

**Deliverables by May 2028:**
- 50-100 customers
- €25k-50k MRR
- DACH + BeNeLux + FR coverage
- 4-5 person team
- Microsoft Partner status
- Series-A ready (or profitable bootstrap continuation)

---

## PHASE 5 — Vision Realized (2028+)

- 200+ buildings across Europe
- €1M+ ARR
- 10+ team
- Strategic exit options: VC funding for global expansion, OR acquisition by Microsoft/Siemens/Schneider, OR sustainable independent business

---

## Key Milestones Summary

| Date | Milestone | Why critical |
|---|---|---|
| **Jun 2026** | M.Sc. graduation, full-time on EnergyLens | Founder commits |
| **Jul 2026** | Microsoft Startups Tier 2 approved | Infrastructure unlocked |
| **Sep 2026** | First paying pilot customer | Market validation |
| **Oct 2026** | UG mini-GmbH registered | Commercial foundation |
| **Dec 2026** | 3-5 customers, €500-2k MRR | Product-market fit signal |
| **Mar 2027** | Microsoft Startups Tier 3 upgrade ($150k) | Scaling fuel |
| **Jun 2027** | 15-20 customers, €10k+ MRR | Repeatable GTM |
| **Q4 2027** | First hire | Beyond solo |
| **May 2028** | 50-100 customers, €25k+ MRR | Market leadership tier |

---

## Risk-Adjusted View

### What could derail this?

| Risk | Mitigation |
|---|---|
| Pilot acquisition slower than expected | Pivot to consultancy revenue while building product |
| Fabric capacity costs spiral | Optimize pipelines, stay on Startups credit |
| Competitor copies model | Speed + EU regulatory depth as moat |
| Founder solo burnout | Hire support early (Q2 2027) |
| Regulatory shift away from EU focus | Add UK/CH coverage, diversify |

### What if it goes faster?

| Acceleration trigger | Action |
|---|---|
| Pilot converts in <1 month | Hire sales by Q4 2026 |
| Microsoft co-marketing offered | Allocate 30% time to partnership |
| Enterprise lead (50+ buildings) | Custom enterprise feature sprint |
| Investor inbound | Evaluate seed round in 2027 |

---

*Document version 1.1 — May 28, 2026 (updated after Day 16: web app + AI Copilot pulled into Phase 1)*
*Author: Ali Mert Özdemir, Founder*
