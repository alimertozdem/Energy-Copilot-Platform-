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

## PHASE 1 — Foundation (Q2 2026, NOW)

### Status: ✅ Mostly complete

**What's done:**
- ✅ 9-page Power BI dashboard MVP (Portfolio, Building, Anomalies, Forecast, Occupancy, Sustainability, HVAC, IoT, Battery)
- ✅ Microsoft Fabric medallion architecture (Bronze/Silver/Gold)
- ✅ Sample data: 6 representative buildings (DE, TR, AT, NL), 3.5 years, 693k+ data points
- ✅ DAX measure library (v52, 50+ measures)
- ✅ Brand identity finalized (EnergyLens "Emerald Pulse")
- ✅ Battery dispatch simulator (4 strategies, EU 2023/1670 compliant)
- ✅ CRREM pathway integration
- ✅ Anomaly detection engine
- ✅ HVAC analytics with envelope U-values

**What's remaining (this phase):**
- ⏳ Page 1-9 final review + polish
- ⏳ Production-grade Fabric capacity (currently throttled on trial)
- ⏳ Microsoft for Startups application
- ⏳ Domain registration (energylens.eu)

**Deliverables by July 2026:**
- Final dashboard MVP screenshot pack
- Founder + product demo videos
- Microsoft Startups Tier 2 approved (target)

---

## PHASE 2 — First Pilots & Production Stack (Q3-Q4 2026)

### Status: 🎯 Starting Aug 2026 (post-graduation)

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

### 2B — Production Infrastructure (Aug-Sep 2026)

**Web app build (Next.js + FastAPI + PostgreSQL):**
- Customer onboarding flow
- User management (Microsoft Entra ID auth)
- Embedded Power BI viewer
- Per-customer building inventory
- Subscription management (Stripe integration)
- Basic admin dashboard

**Infrastructure setup:**
- Azure Static Web App (frontend)
- Azure Container App (backend)
- Azure PostgreSQL Flexible (database)
- Embed Power BI via Premium capacity (Startups credit)

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

### 3B — AI Recommendation Engine (Feb-Apr 2027)

Azure OpenAI integration:
- **Natural language insights** — "Your hospital's HVAC is using 12% more than peers; investigate boiler #3"
- **Auto-generated weekly reports** — Customer-specific narratives
- **Conversational dashboard** — "Show me Berlin buildings underperforming vs CRREM 2030"
- **Predictive maintenance** — ML-based equipment fault prediction

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

*Document version 1.0 — May 2026*
*Author: Ali Mert Özdemir, Founder*
