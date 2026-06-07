# Microsoft for Startups — Master Application Plan

**Created:** 2026-05-15
**Owner:** Ali Mert Özdemir (alimertozdem@gmail.com)
**Application:** Microsoft Founders Hub (https://startups.microsoft.com)
**Target Tier:** Tier 2 (validated startup, $5k-$25k Azure credit + 12 months Power BI Premium)
**Future:** Tier 3 upgrade in 3-6 months ($150k Azure credit)

---

## 0. WHY this matters

- **Capacity throttle problem:** Fabric trial F4 SKU exhausts capacity → can't refresh models, run pipelines
- **Tier 2 solution:** $5k-25k Azure credit + 12 months Power BI Premium → capacity problem solved for 1 year
- **Trial ends:** 2026-06-12 (28 days from 2026-05-15) → must apply BEFORE
- **Strategic value:** "Microsoft-backed startup" credibility for sales/marketing

---

## 1. FOUNDER PROFILE (for application + bio)

### Personal
- **Full name:** Ali Mert Özdemir
- **Age:** ~30 (born ~1996, based on LinkedIn handle alimertozdemir96)
- **Location:** Berlin, Germany
- **Visa:** Currently temporary residence permit → 1 month later: Job Search Visa (18 months runway)
- **LinkedIn:** https://www.linkedin.com/in/alimertozdemir96/
- **GitHub:** https://github.com/alimertozdem

### Education
- **M.Sc.:** Energy Management — BSBI (Berlin School of Business and Innovation)
  - Expected graduation: **June 2026**
- **B.Sc.:** Energy Engineering — Yaşar University, İzmir (Turkey)

### Experience
- ~1 year engineering internship + brief professional engineering experience
- Prior entrepreneurial ventures in other sectors

### Certifications
- **Microsoft DP-600** (Implementing Analytics Solutions Using Microsoft Fabric) — recently obtained
  - Strategic value: rare for solo founders, Microsoft-recognized

### Microsoft relationships
- No prior Microsoft for Startups applications
- No Microsoft Partner Network membership
- No prior Microsoft sales contact

---

## 2. PRODUCT — EnergyLens

### Brand
- **Name:** EnergyLens
- **Tagline:** "Smart energy for smart buildings"
- **Identity:** "Emerald Pulse" — confirmed brand identity (logo, colors, wordmark) 2026-05-11
- **Domain:** energylens.eu (to be registered)

### What it does
**Energy Copilot Platform for Commercial Buildings** — Microsoft Fabric-native, EU regulatory-focused energy intelligence platform.

### Stack
- **Data layer:** Microsoft Fabric Lakehouse (Bronze/Silver/Gold medallion)
- **Pipeline:** Fabric Notebooks (PySpark), Pipelines
- **Visualization:** Power BI Premium (DirectLake)
- **App layer:** Next.js frontend + FastAPI backend (in design)
- **IoT:** BACnet, Modbus TCP, MQTT 5.0, OPC-UA adapters (Phase 2)
- **Pricing data:** EPEX Spot integration (dynamic German electricity prices)

### 9 Dashboard Pages + Live Web Application + AI Copilot (current state)

**Power BI dashboard (9 pages, DirectLake on Fabric Lakehouse):**
1. Portfolio Overview — Multi-building KPIs, scorecard
2. Building-Level Detail
3. Anomalies & Alerts
4. Forecast & Recommendations
5. Occupancy Analysis
6. Sustainability & Compliance (CRREM, EU Battery Reg)
7. HVAC & Building Envelope
8. IoT Real-Time Monitoring (final polish post-capacity)
9. Battery Strategy & Dispatch

**Web Application (Next.js + FastAPI, live since May 27-28, 2026):**
- 3-provider authentication (Microsoft Entra, Google, Email/Password)
- `/portfolio` — custom React reading directly from Fabric SQL Analytics Endpoint
- `/buildings/[id]` — embedded Power BI via service principal (V2 embed API, DirectLake)
- `/copilot` — AI chat with LLM tool use over Fabric Lakehouse + Postgres

**AI Copilot (live since May 28, 2026):**
- Six production tools: `query_kpi`, `compare_buildings`, `list_recommendations`, `get_anomalies`, `simulate_battery_scenario`, `update_action_status`
- Provider abstraction: Anthropic (Claude) / Azure OpenAI / Mock (currently active — credit-pending)
- Server-Sent Events streaming, conversation persistence, JWT auth, RLS at app layer

### Regulatory niche
- **CRREM** (Carbon Risk Real Estate Monitor) — pathway compliance scoring
- **EU 2023/1542** — Battery passport regulation
- **EnEfG** (Germany) — Energy efficiency law
- **GEG** (Germany) — Building Energy Act
- **EU CSRD** — Sustainability reporting
- **EU EPC** — Energy Performance Certificate

### Subscription Tier Architecture (feature tiers, not pricing)
| Tier | Name | Latency | Features |
|---|---|---|---|
| 1 | Insight | 1 hour batch | KPIs, trends, recommendations |
| 2 | Monitor | 5-15 min | Tier 1 + live alerts, HVAC optimization |
| 3 | Copilot | Real-time | Tier 2 + ML forecast, simulation, expert routing |

### Pricing draft (to be finalized in revenue model doc)
| Tier | €/building/month | Target segment |
|---|---|---|
| Insight | €99 | KOBİ ofis (<5,000 m²) |
| Monitor | €299 | Mid-market property mgmt (5,000-15,000 m²) |
| Copilot | €699-1,500 | Enterprise REIT, healthcare (>15,000 m² + IoT) |
| Portfolio Custom | €5k-50k/month | 10+ binalı portföyler |

---

## 3. MARKET POSITIONING

### Competitive landscape (proof market exists)
- **Measurabl** — $120M ARR, Series D, US/global
- **Aquicore** — $40M raised, Series C, US
- **Cortexa Intelligence** — $30M raised, Series B, EU
- **BuildingIQ** — Public on ASX
- **Carbonsight** — $20M raised, Series A, UK
- **Honeywell Forge, Schneider EcoStruxure, Siemens Desigo CC** — enterprise giants

### Differentiation (EnergyLens unique angle)
1. **Microsoft Fabric-native** — competitors use legacy Java/.NET, we're 2024-stack
2. **EU regulatory focus** — CRREM + EnEfG + EU Battery Reg natively
3. **Mid-market accessible** — €99-€699/month vs competitors' €5k+
4. **DACH market** — competitors are US-centric, we're EU-pricing + DE/AT/NL data
5. **IoT interoperability** — BACnet/Modbus/MQTT (Phase 2)

### Target market sizing (TAM/SAM/SOM)
- **TAM:** EU has ~5 million commercial buildings × ~€300/month average = **€18B/year**
- **SAM:** DACH region focus = ~1.2 million commercial buildings = **€4.3B/year**
- **SOM Year 1:** 5-10 pilot customers (€50k-100k ARR)
- **SOM Year 3:** 100-200 customers (€500k-1.5M ARR)

### GTM Strategy (bottom-up)
| Priority | Target | Pitch | Pilot timeline |
|---|---|---|---|
| 1 | University campuses (BSBI first) | Academic + sustainability angle, free pilot, case study | 2-4 weeks |
| 2 | Property Management firms (Berlin) | EU CRREM compliance, save €X/building | 1-3 months |
| 3 | Hotel chains (mid-size DACH) | Daily ops + ESG reporting | 3-6 months |
| 4 | REITs (Patrizia, Aroundtown) | Portfolio CRREM + carbon strategy | 6-12 months |
| 5 | Shopping malls (AVM) | Common area + tenant comparison | 6-12 months |

---

## 4. APPLICATION DELIVERABLES (9 documents to prepare)

### Documents I (Claude/Assistant) will prepare:

| # | Document | Format | Status | Purpose |
|---|---|---|---|---|
| 1 | **Executive Summary** (1-pager) | `.md` → `.pdf` | TODO | Application form `What is your startup?` |
| 2 | **Pitch Deck** (10 slides) | `.pptx` | TODO | Application form `Pitch deck` upload |
| 3 | **Architecture Document** | `.md` → `.pdf` | TODO | Microsoft Fabric stack emphasis |
| 4 | **Product Roadmap** (6/12/24 months) | `.md` → `.pdf` | TODO | Vision + milestones |
| 5 | **GTM Strategy** | `.md` → `.pdf` | TODO | EU CRE bottom-up sales motion |
| 6 | **Revenue Model + 3-yr projection** | `.xlsx` | TODO | Financial credibility |
| 7 | **Founder Bio** | `.md` | TODO | Ali Mert story + vision + future team plan |
| 8 | **Founder Video Script** (90-120 sec) | `.md` | TODO | User to record (Loom + Descript) |
| 9 | **Product Demo Video Script** (3-5 min) | `.md` | TODO | User to record (Loom + ElevenLabs voiceover) |
| 10 | **Application Form Draft** | `.md` | TODO | Every form field pre-filled |

### Tasks I (user) will execute:

| # | Task | Tool | Cost |
|---|---|---|---|
| 1 | Register **energylens.eu** | namecheap.com or hetzner.com | ~€15/year |
| 2 | Update LinkedIn headline: "Building EnergyLens — Energy intelligence for commercial buildings" | LinkedIn | Free |
| 3 | Clean up GitHub repo, write README highlighting Microsoft Fabric stack | GitHub | Free |
| 4 | Email BSBI facility manager + M.Sc. supervisor about pilot | Email | Free |
| 5 | Create ElevenLabs account (AI voiceover for demo video) | elevenlabs.io | Free tier |
| 6 | Create Loom account (screen recording) | loom.com | Free |
| 7 | Record founder intro video (90 sec) | Phone camera + Loom | €0-20 (optional lavalier mic) |
| 8 | Record product demo (Loom + AI voiceover) | Loom + ElevenLabs | Free tier OK |

---

## 5. VIDEO STRATEGY

### Video A — Founder Intro (90-120 seconds, user self-records)

**Tools:**
- Camera: phone (landscape), tripod
- Mic: phone OR lavalier (~€20)
- Light: window, daytime
- Edit: Loom + Descript (free tiers)

**3-part structure:**
1. **Hook (15 sec):** "Did you know commercial buildings produce 38% of global CO2?"
2. **Problem + Solution (40 sec):** Problem statement, EnergyLens solution
3. **Why me + Vision (35 sec):** Energy engineer + Microsoft Fabric + EU focus

### Video B — Product Demo (3-5 minutes)

**Recommended approach:**
- Loom screen recording of Power BI dashboard (silent walkthrough)
- AI voiceover via ElevenLabs (free tier $11/month, very natural voices)
- Background music from Pixabay (royalty-free)
- Final edit in Descript (free tier)

**Alternative:** Synthesia AI avatar ($30/month, more "corporate" feel)

---

## 6. APPLICATION SUBMISSION CHECKLIST (final stage)

Before clicking SUBMIT on Microsoft Founders Hub:

- [ ] energylens.eu domain registered + working
- [ ] LinkedIn updated with EnergyLens
- [ ] GitHub README professional
- [ ] All 9 documents (Executive Summary → Founder Bio) prepared
- [ ] Founder video recorded + uploaded (YouTube unlisted or Loom)
- [ ] Product demo video recorded + uploaded
- [ ] Pitch deck reviewed final
- [ ] Application form draft cross-referenced (no blank fields)
- [ ] Email confirmation from BSBI supervisor (optional but BIG plus)

---

## 7. POST-SUBMISSION TIMELINE

| Week | Event |
|---|---|
| 1 (submit) | Wait for auto-confirmation email |
| 1-2 | Tier 1 auto-approval (likely $1k credit + tools) |
| 2-3 | Tier 2 manual review (rejection or upgrade) |
| 3-4 | If Tier 2 approved: Azure credits + Power BI Premium activated |
| 3-4 | Migrate Fabric workload to Tier 2 capacity (F8 or higher) |
| 3-6 months later | Build pilot customer base (BSBI + 1-2 firms) |
| 6 months | Apply for Tier 3 upgrade ($150k) with traction proof |

---

## 8. RISK MITIGATIONS

### Risk: "Solo founder, no co-founder"
**Mitigation:** Frame as "actively evaluating co-founder fit, focused on technical validation first." Mention advisor relationships (M.Sc. supervisor) and future team build plan in pitch.

### Risk: "Student, not full-time"
**Mitigation:** "Final-semester M.Sc., transitioning to full-time post-June 2026. 18-month visa runway secured. Job Search Visa pending."

### Risk: "No customer pilots yet"
**Mitigation:** "BSBI campus pilot in active discussion. M.Sc. capstone project provides academic validation pathway."

### Risk: "No company registered"
**Mitigation:** "Pre-incorporation, UG mini-GmbH registration planned for Q3 2026 after first revenue commitment." (We can also fast-track registration in 1-2 days if Tier 3 requires it later.)

---

## 9. CURRENT STATUS — Where we are (updated 2026-05-28)

### ✅ Done
- 10 buildings realistic data, 3.5 years, 693K+ data points (DE/TR/AT/NL)
- 9 dashboard pages live (Page 8 IoT pending final polish post-capacity)
- Fabric medallion pipeline built (57 Lakehouse tables across Bronze/Silver/Gold)
- DAX measure library v56 (50+ measures, building-type aware thresholds)
- Battery dispatch simulator (12 countries × 8 chemistries × 7 strategies, EU 2023/1542)
- **Web app v1 LIVE (Next.js + FastAPI + Postgres, 3 auth providers, embed wrap, custom React /portfolio)**
- **AI Copilot LIVE (LLM tool use, 6 tools, SSE streaming, Anthropic + Mock providers)**
- **3 parallel Fabric data paths validated** (DirectLake embed, SQL Analytics Endpoint, LLM tool use)
- Brand identity finalized (EnergyLens "Emerald Pulse") + design system applied across web app
- Subscription tier architecture defined
- Domain energylens.eu registered + Azure subscription active
- 10 application documents v1.1 (this plan)

### 🔄 In progress
- Microsoft Startups portal submission (final video recording + form fill)
- Page 8 IoT dashboard polish (deferred post-capacity)

### ⏳ Pending (Mert)
- Email forwarding: alimert@energylens.eu → alimertozdem@gmail.com (Namecheap, ~15 min)
- ElevenLabs + Loom + Descript free-tier accounts (~10 min)
- Founder intro video recording (~30 min including takes)
- Product demo video recording (~60 min including Copilot scenes)
- BSBI pilot conversation

---

## 10. NEXT IMMEDIATE STEPS (2026-05-28)

1. Mert: Namecheap email forwarding `alimert@energylens.eu → alimertozdem@gmail.com` (~15 min)
2. Mert: ElevenLabs + Loom + Descript free-tier signups (~10 min total)
3. Mert: Record founder intro video using `08_founder_video_script.md` v1.1 (~30 min)
4. Mert: Record product demo video using `09_product_demo_script.md` v2.0 (~60 min, web app + Copilot + 3 PBI pages)
5. Mert: Upload videos to Loom unlisted, get share links
6. Mert: Submit at https://portal.startups.microsoft.com using `10_application_form_draft.md` v1.1
7. Wait 3-14 days for Microsoft review
8. Post-submission: polish Page 8 IoT (after capacity recovers or Tier 2 approved)

---

## DOCUMENT INDEX

- ✅ `00_MASTER_PLAN.md` — this file
- ✅ `01_founder_profile.md` — Founder background, profile, decisions
- ✅ `02_executive_summary.md` — 1-page pitch
- ✅ `03_pitch_deck.pptx` — 10-slide PowerPoint (EnergyLens brand)
- ✅ `04_architecture_document.md` — Microsoft Fabric stack deep-dive
- ✅ `05_product_roadmap.md` — 6/12/24 month roadmap
- ✅ `06_gtm_strategy.md` — Bottom-up GTM, customer segments, pricing
- ✅ `07_revenue_model.xlsx` — 3-year projection (7 sheets, zero formula errors)
- ✅ `08_founder_video_script.md` — Mert's recording script (90-120 sec)
- ✅ `09_product_demo_script.md` — Power BI demo + AI voiceover script (3-5 min)
- ✅ `10_application_form_draft.md` — Pre-filled application answers
- ✅ `ACTION_CHECKLIST.md` — Sequential task list

**Status (2026-05-28):** All 10 documents updated to v1.1, post-Day-16 reality. Awaiting:
1. Mert to set up Namecheap email forwarding (15 min)
2. Mert to record 2 videos (scripts v1.1 + v2.0 ready)
3. Mert to submit application at https://portal.startups.microsoft.com

Domain registered, Power BI dashboard 9-page complete (Page 8 polish post-capacity).

---

**Last updated:** 2026-05-28 (v1.1 — web app + AI Copilot live, ready for submission)
