---
title: "EnergyLens Master Study Guide"
subtitle: "From Niche to Client-Ready — Freelance Preparation"
author: "Ali Mert Özdemir"
date: "2026-05-26"
geometry: margin=2cm
fontsize: 11pt
documentclass: article
mainfont: "DejaVu Sans"
monofont: "DejaVu Sans Mono"
toc: true
toc-depth: 2
numbersections: true
colorlinks: true
linkcolor: "blue"
---

# How to Use This Guide

> **Reading guide (tr):** Bu doküman tek başına okursan müşteri toplantılarında EnergyLens'i ve enerji/ESG/Fabric jargonunu sağlam bilirsin. Sıra önemli — atlayarak gitme. Her bölümün sonunda "Drill phrases" kısmı varsa yüksek sesle 3-5 kere tekrar et, dilin alışsın. Türkçe ipuçları parantez içinde — anlamadığın İngilizce ifadeyi tanı, sonra anlamı pekiştir, sonra cümleyi kuran kalıbı içselleştir.

This is your complete preparation document. It merges three previously separate files (positioning, project technical reference, skill gap) into a single reading order. You can study it linearly, top to bottom, or jump to a Part using the table of contents.

**Time budget:** ~30 hours over 4 weeks at 1–1.5 hours/day. After Part III you are ready to send first proposals.

**Reading order (chronological):**

1. **Part I — Why This Niche** → understand the market opportunity and your value proposition (1 hour)
2. **Part II — Master Your Own Project** → know EnergyLens inside and out (3–5 hours)
3. **Part III — Regulatory Vocabulary** → learn CSRD, ESRS, GHG Protocol language (8 hours)
4. **Part IV — Microsoft Analytics Sales Language** → talk like a Fabric expert (6 hours)
5. **Part V — Discovery Calls** → structure your first sales conversations (3 hours)
6. **Part VI — Common Client Questions** → memorize the 7 answers you will get every time (1 hour)
7. **Part VII — Glossary** → reference; consult during real conversations (no study time)
8. **Appendix A** — 4-week study schedule
9. **Appendix B** — Free resource checklist

(tr: Sırayla git. Part II'de kendi projeni öğreniyorsun — bu en hızlı tamamlayacağın bölüm çünkü zaten kuruyorsun. Part III ve IV en yüksek yatırım — bu iki bölüm gerçek "yeni öğrenme". Part V ve VI uygulama. Glossary'i toplantı öncesi 10 dk tara.)

---

# PART I — WHY THIS NICHE

## 1. The Market Opportunity

Three forces stack at the same time. Almost nobody is positioned at their intersection:

1. **CSRD enforcement wave** — The first wave of EU companies (large public-interest) filed FY2024 reports in 2025. The second wave — ~50,000 EU companies — must file FY2025 reports in 2026. They are *behind* and *panicking*. Demand is structural, not a fad. (tr: Bu dalga gerçek. Şu an Avrupa'da ESG müdürlerinin %70'inin uykuları kaçıyor, çünkü Excel'le yetişemiyorlar.)

2. **Microsoft Fabric is new** — GA in May 2024, still a small specialist pool. DP-600/DP-700 holders globally are in the low tens of thousands. Most Power BI consultants haven't migrated yet. (tr: Fabric uzmanı dünyada çok az. Sen sertifikalısın, gerçek bir production sistem işlettin. Bu pozisyon nadir.)

3. **Energy domain literacy is rare in BI** — Most Power BI freelancers know finance dashboards, not kWh/m², EnPI, Scope 2 market-based vs location-based, or EPC weighting.

A freelancer at the intersection of these three (Fabric + BI + EU energy regulation) faces near-zero direct competition on Malt / freelance.de / Contra. Pricing power follows.

## 2. One-Line Positioning

Memorize this. Every profile, every proposal, every cold message must support this sentence:

> **"I help mid-market property portfolios and ESG/sustainability consultancies turn raw building energy data into CSRD-ready Power BI dashboards on Microsoft Fabric — with auditable Scope 1/2/3 numbers and regulator-grade data lineage."**

(tr: Bu cümleyi telefonun ekranına yapıştır. Her 30 dakikalık discovery call'da ilk 3 dakikada bu cümleyi söylemen lazım — kelime kelime.)

## 3. Who Buys (Ideal Customer Profiles)

We hunt three customer types, in order of fit:

### ICP-A — ESG / Sustainability Consultancies (PRIMARY)
- **Size:** 10–150 employees, EU-based (DACH first)
- **Pain:** Their client needs ESRS E1 disclosure in 8 weeks. The consultancy has Excel-based methodology but no productized dashboard. They lose deals to bigger firms who have one.
- **Buyer:** Partner / ESG Director
- **Project type:** Build a productized CSRD dashboard template they resell to *their* clients
- **Deal size:** €5,000–€20,000 initial, often retainer follow-up

### ICP-B — Property / Portfolio Managers
- **Size:** 50–500 building portfolio, €50M–€500M assets under management
- **Pain:** Has energy data in 5 systems (BMS, utility bills, EPCs, manual Excel, sometimes Power BI). Cannot answer "which buildings are dragging our portfolio score down" in under 30 minutes.
- **Buyer:** Head of Asset Management / Sustainability Officer
- **Project type:** Multi-building energy KPI dashboard, EnPI tracking, EPC compliance heat map
- **Deal size:** €2,500–€8,000 initial, monthly retainer plausible

### ICP-C — Internal Sustainability Teams (mid-cap)
- **Size:** €100M–€1B revenue, 1–3 person sustainability team
- **Pain:** Company invested in Microsoft Fabric for finance/sales, but the sustainability team is locked out — builds Scope 1/2/3 in Excel manually each quarter.
- **Buyer:** Head of Sustainability
- **Project type:** A "sustainability layer" on top of their existing Fabric lakehouse — Scope 1/2/3 model + dashboard
- **Deal size:** €8,000–€25,000, often leads to long retainer

### Anti-ICPs (we say no)
- Tableau-only shops
- "Build me a full ESG SaaS for $500" requests
- Renewable energy *project finance* clients (different niche, not analytics)
- Anyone using "ESG" loosely without naming a framework (CSRD / GRI / SASB)

## 4. Pain Points We Sell To (the exact language clients use)

Memorize these. Every proposal must hit one of these in the first paragraph:

- "Our auditor flagged our Scope 2 calculation"
- "We have data in 5 systems and can't reconcile ESRS E1 disclosures"
- "Our ESG report takes 6 weeks to compile — regulators want it quarterly"
- "We built a Power BI dashboard but it's slow, wrong, or nobody opens it"
- "We bought Microsoft Fabric and don't know how to use it"
- "We need to benchmark our portfolio against EPC requirements"
- "Our CFO wants one dashboard for energy cost + carbon"

(tr: Müşteri kendi cümlesini sana geri okur gibi proposal aç. Bu cümlelerden birini neredeyse aynı kelimelerle kullanmaya çalış. "Generic professional opener" yazma — direkt acıya gir.)

## 5. What We Sell (Productized Packages)

We open *below* market to win the first 5–10 deals, build reviews, then raise rates aggressively. Velocity over margin for the first 90 days.

### P1 — "CSRD Scope 1/2/3 Quickstart"
- **Scope:** 2-week sprint. Connect 2–3 data sources (utility bills CSV, fleet log, refrigerant data), build Scope 1/2/3 dashboard with ESRS E1 mapping, deliver in client's Power BI tenant.
- **Opening price:** €3,200 fixed | **After 3 closes:** €4,500
- **Margin:** Reusable EnergyLens Scope template — 60% of work pre-built

### P2 — "Building Energy KPI Dashboard"
- **Scope:** 1-week sprint. Ingest energy bills + EPC + (optional) BMS exports, build EnPI / kWh/m² / EPC compliance dashboard.
- **Opening price:** €1,800 fixed for ≤5 buildings, +€250 per additional building up to 10 | **After 3 closes:** €2,500
- **Margin:** EnergyLens Pages 1–5 template

### P3 — "Microsoft Fabric Audit & Roadmap"
- **Scope:** 3 days. Review existing Fabric setup, identify Direct Lake / Real-Time Intelligence opportunities, deliver written roadmap.
- **Opening price:** €1,200 fixed | **After 3 closes:** €1,800
- **Margin:** Pure consulting, no delivery — high margin, low time

### P4 — "Power BI Performance Tune-up"
- **Scope:** 2 days. Profile a slow Power BI report, fix DAX, optimize model, deliver before/after benchmark.
- **Opening price:** €800 fixed | **After 3 closes:** €1,200
- **Margin:** Pure expertise — quick wins, satisfied client, easy upsell

### Hourly fallback (for work outside packages)
- Malt: open at €450/day, raise to €650 after 3 satisfied clients, target €850 by month 6
- freelance.de: €60/hr or €450/day (English-language projects only)
- Contra: open at $50/hr (USD), raise to $75 after 5 jobs
- Toptal (if accepted): $80–100/hr right out of the gate

## 6. Why Pick Us Over a Cheaper Freelancer (Differentiation)

Order of arguments, by power:

1. **"I have already built and operate the platform you are trying to build"** — Show 1–2 EnergyLens screenshots in every proposal. This is the single biggest weapon.
2. **Microsoft Fabric + energy domain + EU regulation** — no other freelancer combines these three. Search results show fewer than 10 freelancers worldwide claiming Fabric + ESG.
3. **Regulation-first thinking** — we don't just build dashboards, we cite EU 2023/1542, ESRS E1, GHG Protocol Corporate Standard, ISO 50001. Clients need that confidence.
4. **Productized offerings** — fixed scope, fixed price, fixed timeline. No "I'll think about it and get back to you."

## 7. The 5 Ingredients of a Winning Proposal

Every proposal you send must contain — in this order:

1. **Pain mirror** — opening line repeats their pain in their language
2. **EnergyLens artifact** — one concrete relevant proof point (Page 6 Scope dashboard, Page 8 IoT, etc.)
3. **Specific question** — proves you read the brief, not copy-paste
4. **Productized package match** — name the package, the price, the duration. Offer two options when possible (forces choice between A and B, not yes/no)
5. **Domain jargon paragraph** — two sentences that prove CSRD / Fabric literacy (market-based Scope 2, Direct Lake mode, ESRS E1 datapoints, OneLake medallion lineage)

Sign off with one CTA sentence + Calendly link. 220–320 words total. Closing: "Best, Mert"

(tr: Bu 5 madde sırayı bozma. Bot da bu sırayı izleyerek draft üretiyor. Müşteri reply rate'in en azından %8 olsun istiyoruz — bu yapı onu sağlar.)

## 8. Success Metrics (Track Monthly)

- Proposals sent / week — target 15–25 with automation
- Reply rate — target ≥ 8%
- Booked meetings / week — target 2–4 by week 6
- Closed deals / month — target 1 by month 1, 3 by month 3
- Revenue / month — target €2k month 1, €5k month 3, €8k+ month 6

(tr: Bunlar gerçekçi hedefler, agresif değil. Bot Sunday akşamları haftalık digest atacak, bu metrikler oradan gelir.)

---

# PART II — MASTER YOUR OWN PROJECT

This is your home turf. You built EnergyLens. The client doesn't need you to learn it — they need you to *talk* about it in their language with zero hesitation. This Part is your reminder of every formula, every visual, every standard your platform implements.

(tr: Burada yeni bir şey öğrenmiyorsun. Sadece bildiğin şeyleri müşteri diline tercüme ediyorsun. Bir formül sorulduğunda 3 saniyede çıkarman lazım — kekelersen güvenini kaybedersin.)

## 9. Project Anatomy

### What EnergyLens is, in one paragraph

EnergyLens is a production-grade energy intelligence platform for commercial buildings, built on Microsoft Fabric. It ingests data from utility bills, EPC certificates, BMS sensors (BACnet / Modbus / MQTT), weather APIs, and battery telemetry; processes it through a Bronze → Silver → Gold medallion architecture in OneLake; and surfaces 9 Power BI pages covering consumption, anomalies, forecasting, decision support, sustainability (CSRD/ESRS-aligned), HVAC profiles, real-time IoT, and battery dispatch ROI. It supports multiple buildings, multiple tenants, and multiple regulatory regions through a single semantic model with Row-Level Security.

### Why this design

- **Medallion architecture** so every disclosed kg of CO₂ can be traced back to its raw bill row — audit-ready
- **Technology profile gating** (`has_pv`, `has_battery`, `has_heat_pump`) so each building only sees its relevant analytics — no "N/A" cells everywhere
- **Tier-aware ingestion** (batch for Tier 1, streaming for Tier 2/3) so we don't pay for streaming when a smart meter delivers data hourly
- **Static regulation tables** because rules like GEG / EnEfG / BEP-TR change ~once a year — overengineering as live API would burn time

### Architecture in words

```
SOURCES
  Smart meters, utility bills (CSV / API)
  BMS sensors (BACnet, Modbus, MQTT, OPC-UA)
  Weather APIs (OpenWeather / DWD / MGM)
  Battery telemetry, solar inverters
                  │
                  ▼
INGESTION (Microsoft Fabric)
  Data Factory pipelines   →  batch    (Tier 1)
  EventStream              →  real-time (Tier 2/3)
                  │
                  ▼
STORAGE — Microsoft Fabric Lakehouse (OneLake)
  BRONZE  raw, as ingested
     └─►  SILVER  cleaned, normalized, validated
                └─►  GOLD  business-ready (KPIs, anomalies, simulations)
                              │
                              ▼ Direct Lake mode
                       SEMANTIC MODEL (Power BI)
                       9-page report + DAX v56 library
                              │
                              ▼
                       OUTPUT
                       Embedded Power BI in web app
                       Activator (Reflex) alerts
```

### Three subscription tiers

| Tier | Name | Latency | Data sources | Active modules |
|---|---|---|---|---|
| **1** | Insight | ~1 hour | Smart meter (hourly), bills (monthly) | KPI dashboard, basic anomaly detection, compliance, recommendations |
| **2** | Monitor | 5–15 min | Tier 1 + IoT sensors (BACnet/Modbus/MQTT) | + Real-time monitoring, HVAC optimization, peak shaving |
| **3** | Copilot | < 5 min | Tier 2 + battery / heat pump telemetry | + Battery dispatch simulation, ML anomaly detection (Phase 2), scenario simulation |

### Multi-tenant access (3-layer model)

```
ORGANIZATION
  └── BUILDING (building_id — primary partition key)
        ├── Technology Profile (has_pv, has_battery, has_heat_pump…)
        ├── Country (DE / TR / …)
        ├── Subscription Tier
        └── All time-series data partitioned by building_id

LAYER 1 — Power BI RLS (DATA layer):
  Facility Manager → only their building(s)
  Energy Manager   → all buildings in organization
  Platform Admin   → everything

LAYER 2 — Web App Navigation (MODULE layer, Next.js):
  Customer has no IoT  → Page 8 hidden
  Customer has no battery → Page 9 locked

LAYER 3 — Subscription / Tier (COMMERCIAL layer):
  Tier 1 vs Tier 2 vs Tier 3 unlocks features
```

(tr: Müşteri "page visibility nasıl çalışıyor?" diye sorarsa cevap: RLS verinin kim göreceğini, App Navigation hangi sayfanın açılacağını, Subscription hangi özelliklerin aktif olacağını kontrol eder. Üç farklı katman, üç farklı görev.)

## 10. The 9 Power BI Pages — Every Visual Explained

### Page 1 — Portfolio Overview
- **Reader:** Energy Manager, C-suite — "how is the portfolio doing this month?"
- **Time scope:** Last 30 days vs prior period
- **Visuals:** Portfolio kWh consumption (bar by building); kWh/m² heat map across buildings (KPI 1 — EUI); total energy cost €; total CO₂ kg; top 3 underperforming buildings (highest EUI vs type benchmark)
- **Source:** `gold.kpi_daily` aggregated to portfolio level

### Page 2 — Building Deep-Dive
- **Reader:** Facility Manager — "what's my building doing right now?"
- **Time scope:** Selectable (today / week / month)
- **Visuals:** 24-hour consumption profile (line, hourly demand kW); today's peak demand vs baseline; cost-to-date this month; climate-adjusted EUI
- **Source:** `gold.kpi_hourly` + `gold.kpi_daily` filtered by `building_id`

### Page 3 — Anomaly Detection
- **Reader:** Facility Manager, Energy Manager
- **Visuals:** Anomaly count by severity (LOW / MEDIUM / HIGH / CRITICAL); type breakdown (consumption_spike, cop_drop, solar_underperformance, base_load_high, battery_anomaly, holiday_overconsumption, insulation_degradation); anomaly table with timestamp, type, severity, affected system, recommended action, estimated loss €; resolution status (`is_resolved`)
- **Source:** `gold.anomaly_log` — 23 P3 measures, 4 anomaly types active in production

### Page 4 — Forecasting
- **Reader:** Energy Manager, Sustainability Manager — "what will next month cost?"
- **Visuals:** 7 / 30 / 90-day forward consumption forecast (Prophet-based); forecast cost €; forecast CO₂; confidence band (in v54 backlog, deferred)
- **Source:** `gold.kpi_daily` + Prophet model output. Building-type-aware thresholds applied (Hotel / Healthcare 130, Logistics 60, Office 35)

### Page 5 — Decision Support
- **Reader:** Energy Manager, Sustainability Manager
- **Visuals:** Recommended actions ranked by priority_score; estimated savings (€/year, kWh/year, CO₂ kg/year); implementation effort (LOW / MEDIUM / HIGH); payback years; matching incentive programs (KfW, BAFA, YEKA, EEG)
- **Source:** `gold.recommendations` + `gold.incentive_matches`
- **Self-contained measures:** 6 v54 measures designed without chain dependencies — safer DAX

### Page 6 — Sustainability (ESG / GHG)
- **Reader:** Sustainability Manager, ESG consultant, Auditor
- **Visuals:** Scope 1 / 2 / 3 donut (current month); year-over-year Scope total bar; EPC compliance heatmap (A+ → G across buildings, area-weighted); CSRD readiness flag (`csrd_ready`); ESG Score 0–100 (40% EUI / 30% CO₂ intensity / 20% renewable share / 10% compliance); carbon credit potential €
- **Source:** `gold.sustainability_metrics` + `gold.ghg_scope`
- **Mapped to ESRS E1:** E1-1 (transition plan), E1-5 (energy mix), E1-6 (GHG totals, both location-based and market-based), E1-9 (financial effects)
- **EPC area-weighting:** uses `LOOKUPVALUE` across building dimension to compute area-weighted portfolio compliance — not "average of building averages" (a common audit failure)

### Page 7 — HVAC & Hourly Profile
- **Reader:** Facility Manager, building owner
- **Visuals:** Hourly heat-pump COP (actual vs rated); supply / return air temperature delta (HVAC efficiency proxy); HVAC runtime hours/day; HVAC share of total consumption (bug fixed in v54); 10-building portfolio including B007 Copenhagen Net-Plus, B008 Leipzig Plattenbau, B009 Frankfurt DC, B010 Stockholm Lab
- **Source:** `gold.hvac_analytics` + `silver.hvac_data`

### Page 8 — Real-Time IoT Monitoring
- **Reader:** Facility Manager (operations) + Energy Manager (strategic)
- **KPI Cards:**
  - C1 — Real-time building power (kW), green/amber/red vs baseline
  - C2 — Zone comfort compliance % (zones within HVAC setpoint)
  - C3 — CO₂ level (Good / Fair / Poor)
  - C4 — Active alerts + estimated daily €cost
- **Visuals:**
  - V1 — 24h power trend (`building_kwh` + `hvac_kwh` separated series, baseline reference)
  - V2 — Sensor uptime matrix (rows = zones, cols = sensor_type — DYNAMIC, not hardcoded)
  - V3 — Zone setpoint compliance (which zones out of range and for how long)
  - V4 — Alert table (location, sensor, reading, severity, action, est. €cost)
- **Source:** `gold.iot_realtime` + KQL Eventhouse hot path (`iot_hot_readings`)
- **Architecture:** Event Hub → EventStream → KQL Eventhouse + Lakehouse → DAX v44
- **sensor_type is a DIMENSION** — each building shows only its connected sensor types

#### Anomaly cost estimation (always labelled "Est.")
```
cost_eur = duration_hours × power_waste_kw × grid_price_eur_per_kwh

HVAC_temp violation:    2–5 kW extra per °C deviation
CO2 spike >1500 ppm:    1–3 kW extra ventilation
Power spike >120% base: actual excess kW

Grid price: DE €0.20/kWh, TR €0.14/kWh
(country from silver_building_master)
```

### Page 9 — Battery Dispatch & ROI
- **Reader:** Energy Manager, CFO, Investor
- **Visuals:**
  - Battery technology matrix (LFP / NCA / NMC / Solid-State × 12 countries) → 49 fitness scores
  - 7 dispatch strategies compared (self-consumption, peak shaving, arbitrage, frequency regulation, demand response, time-of-use, hybrid)
  - Country-specific electricity pricing (EPEX Spot for DE / EU, EXIST for TR, fallback to EU certified averages)
  - Investment cost €/kWh by country and chemistry
  - Payback years, NPV (5% discount, 10-year), IRR
  - EU Battery Regulation 2023/1542 compliance flag (carbon footprint, recycled content, warranty cycles, cycle durability)
- **Source:** `gold.battery_simulation` + `gold.battery_technologies` + `gold.country_regs` + `gold.strategy_fitness`
- **Data:** 12 countries × 8 chemistries × 7 strategies = 672 simulation rows, plus 49 fitness matrix scores

## 11. KPI Formulas Master List

Memorize the formulas. When a client asks "how do you calculate EnPI?" you should rattle the formula off without breaking eye contact.

### KPI 1 — Energy Use Intensity (EUI / EnPI)

```
EUI = Total Annual Consumption (kWh) / Conditioned Area (m²)
Unit: kWh/m²/year

Climate-Adjusted EUI:
EUI_adj = EUI × (Reference HDD+CDD / Actual HDD+CDD)
```

**Why climate-adjusted?** A Berlin building burns more heating energy than an Istanbul building of identical efficiency. Normalize by Heating + Cooling Degree Days to compare fairly.

**Base temperatures (per EN ISO 15927-6):**
- HDD base = 15°C
- CDD base = 22°C

**Office benchmarks:**
| Class | EUI (kWh/m²/yr) | Comparable to |
|---|---|---|
| Excellent | < 80 | LEED Platinum |
| Good | 80–130 | Above sector average |
| Average | 130–200 | Typical commercial |
| Poor | > 200 | Urgent action |

Separate benchmark sets exist for Hotel, Retail, Logistics, Hospital.

### KPI 2 — Peak Demand

```
Peak_Demand_kW = MAX(demand_kw) over the period

If battery present:
Peak_Shaved_kW = Peak_Without_Battery − Peak_With_Battery
Demand_Charge_Saving_€ = Peak_Shaved_kW × demand_charge_rate (€/kW/month)
```

Demand charges are billed on the highest 15-minute average kW — one bad spike at 10:00 sets the bill for the whole month. Battery peak shaving directly cuts this.

### KPI 3 — Load Factor

```
Load_Factor = Average_Demand_kW / Peak_Demand_kW
Range: 0 to 1
```

1.0 = perfectly flat (ideal). 0.3 = highly spiky (pays max demand charges, equipment short-cycles). Office target > 0.70.

(tr: Bina elektrik tüketiminin "ne kadar düz" olduğunu ölçer. Düşük load factor = "tarife mahkumu" = net €kayıp.)

### KPI 4 — Base Load (Sleep Consumption)

```
Base_Load_kW = MIN(demand_kw) during 02:00–04:00 local time

Alert if Base_Load / Peak_Demand > 0.35
→ Equipment not entering standby properly
```

(tr: Gece 2-4 bina "uyumalı". Hâlâ peak'in %35'inden fazla çekiyorsa bir şey kapanmıyor — server, lighting, HVAC scheduling, ısrarlı standby cihazlar.)

### KPI 5 — Solar KPIs (when `has_pv = True`)

```
Self_Consumption_Rate = self_consumed_kwh / generated_kwh
Target: > 70%
Low → battery needed OR load scheduling optimization needed

Self_Sufficiency_Rate = self_consumed_kwh / total_consumption_kwh
Target: 20–60%

Solar_Yield = generated_kwh / pv_capacity_kwp
Germany: 900–1050 kWh/kWp/year
Turkey:  1300–1600 kWh/kWp/year

Performance_Ratio (PR) = actual_yield / theoretical_yield
theoretical_yield = irradiance_kwh_m² × pv_capacity_kwp × 0.80
Target PR > 0.75
Low PR → panel soiling, shading, inverter fault
```

**Critical distinction clients always confuse:**
- **Self-Consumption Rate** = "of my generation, how much did I use myself?" (vs exported)
- **Self-Sufficiency Rate** = "of my total need, how much came from my own generation?" (vs grid imported)

### KPI 6 — Battery KPIs (when `has_battery = True`)

```
Round_Trip_Efficiency = discharged_kwh / charged_kwh
Target: > 0.90 (LFP lithium-ion)

Cycle_Count_Daily = charged_kwh / battery_capacity_kwh
Lifetime estimate = total_cycles / guaranteed_cycles

Battery_Utilization = average_soc_used / battery_capacity_kwh
Recommended SoC band: 20% – 80%
(outside this band accelerates degradation)
```

### KPI 7 — Heat Pump COP (when `has_heat_pump = True`)

```
COP_actual = Heat_Energy_Produced_kWh / Electricity_Consumed_kWh

SCOP (Seasonal COP) = Total_Season_Heat / Total_Season_Electricity

COP_Performance_Ratio = COP_actual / COP_rated
< 0.80 → MEDIUM maintenance alert
< 0.60 → HIGH critical fault alert

Always compare COP at equivalent outdoor temperature bands
(COP drops naturally as outdoor temp falls)
```

(tr: COP düşüyorsa **mevsim değişti mi** önce bak. Sonra alarmı yorumla. EnergyLens kodu zaten outdoor temp band karşılaştırması yapıyor.)

### KPI 8 — Carbon & Cost

```
CO2_Consumption_kg = consumption_kwh × emission_factor_kg_kwh

CO2_Avoided_kg = solar_generated_kwh × emission_factor_kg_kwh
(grid electricity NOT consumed because solar produced it)

CO2_Net_kg = CO2_Consumption_kg − CO2_Avoided_kg

Carbon_Intensity = CO2_Net_kg / conditioned_area_m²
Unit: kg CO₂/m²/year

Grid emission factors (static reference, updated annually):
  Germany 2024: 0.380 kg CO₂/kWh — source: Umweltbundesamt (UBA)
  Turkey 2024:  0.442 kg CO₂/kWh — source: TEİAŞ

Energy_Cost_€ =
  (grid_import_kwh × energy_price_€_kwh)
  + (peak_demand_kw × demand_charge_€_kw_month)
  − (grid_export_kwh × feed_in_tariff_€_kwh)
```

### ESG Composite Score

```
Monthly ESG Score (0–100):
  40% — EUI vs sector benchmark
  30% — CO₂ intensity vs country average
  20% — Renewable share (solar self-sufficiency)
  10% — Compliance status (regulatory gaps closed)

Carbon Credit Value:
  carbon_credit_value_€ = co2_avoided_kg / 1000 × eu_ets_price_€_ton
  EU ETS 2024 range: €60 – €80/ton CO₂
```

## 12. Anomaly Detection Logic (7 Types)

### A1 — Consumption Spike (MEDIUM)
```
consumption_kwh(t) > rolling_avg(last 30d, same hour, same day-type) × 1.5
AND outdoor_temp_change < 5°C
```
Causes: equipment fault, setpoint drift, unauthorized after-hours use.

### A2 — High Base Load (LOW → MEDIUM)
```
base_load_kw > peak_demand_kw × 0.35
AND time between 01:00–05:00 local
```
Causes: servers, lighting, HVAC scheduling not engaging.

### A3 — COP Degradation (HIGH)
```
COP_actual < COP_rated × 0.80
AND outdoor_temp > design_temp − 3°C
```
Causes: filter fouling, refrigerant leak, missed maintenance.

### A4 — Solar Underperformance (MEDIUM)
```
PR_actual < 0.70
AND irradiance > 400 W/m²
```
Causes: panel soiling, shading, inverter fault.

### A5 — Battery Anomaly (variable)
- A5a — `round_trip_efficiency < 0.85` → MEDIUM (cell degradation / temperature)
- A5b — `SoC ≥ 95% continuously` → LOW (oversized capacity, schedule loads)
- A5c — `SoC < 10% repeatedly` → HIGH (over-discharge, battery life at risk)

### A6 — Weekend / Holiday Overconsumption (MEDIUM)
```
consumption(weekend/holiday) > avg_weekday_consumption × 0.60
```
Causes: HVAC not switching to holiday mode, standby loads.

### A7 — Insulation Performance Degradation (MEDIUM)
```
climate_adjusted_EUI increased > 15% vs prior year
AND weather comparable AND HVAC unchanged
```
Recommended action: Blower Door Test (per EN 13829 / ISO 9972).

## 13. Battery Dispatch Strategies

### Strategy A — Self-Consumption Mode (every 15 min, Tier 2/3)

```
net_load = consumption(t) − solar_generation(t)

IF net_load < 0 (solar surplus):
  IF SoC < 90%: charge battery
  ELSE: export to grid

IF net_load > 0:
  IF SoC > 15%: discharge battery
  ELSE: import from grid

Optimization target: maximize Self_Consumption_Rate
```

### Strategy B — Peak Shaving Mode

```
peak_threshold = operator-defined (default: 90th percentile of last 12 months demand)

IF demand(t) > peak_threshold:
  discharge_power = demand(t) − peak_threshold
  IF SoC > 15%: discharge
  ELSE: alert (insufficient capacity)

IF demand(t) < peak_threshold × 0.50:
  charge opportunity
  IF SoC < 80%: charge from grid or solar
  Preference: charge during off-peak tariff

Optimization target: minimize peak_demand_kw → reduce demand charges
```

(tr: Müşteri "neden 15%–90% SoC bandı?" diye sorabilir. Cevap: aşağıya inince hücre kimyası bozuluyor, yukarıya çıkınca elektrod stres yiyor. LFP için EU regülasyonu cycle durability garantisi bunu varsayar. **20%–80% optimal band** — extended lifetime için.)

## 14. Simulation Engines

### S1 — Add PV Solar

```
Inputs:
  pv_capacity_kwp (user input or auto-suggested from roof_area_m²)
  Auto-suggest: max_kwp = roof_area_m² / 7   (1 kWp ≈ 7 m² of panel)

Step 1 — Estimate generation:
  hourly_generation = pv_capacity_kwp × irradiance_kwh_m² × 0.80 (PR)

Step 2 — Self-consumption split:
  self_consumed = MIN(hourly_generation, hourly_consumption)
  exported = hourly_generation − self_consumed

Step 3 — Financial:
  annual_saving = (self_consumed × energy_price) + (exported × feed_in_tariff)

Step 4 — Carbon:
  co2_avoided = hourly_generation × emission_factor

Step 5 — Investment return:
  investment = pv_capacity_kwp × installed_cost_per_kwp
  payback_years = investment / annual_saving
  npv = NPV(discount_rate=0.05, cashflows=10 years)
  irr = IRR(cashflows)

Default cost assumptions:
  Germany 2024: 1,000–1,400 €/kWp
  Turkey 2024:  600–900 USD/kWp
```

### S2 — Add Battery Storage

```
Inputs: battery_capacity_kwh, battery_strategy
Default tech: LFP (LiFePO₄)

Technology specs (LFP, 2024 EU market):
  cost: 600–900 €/kWh (installed system)
  cycle life: 4,000 cycles
  warranty: 10 years
  round-trip efficiency: 0.92
  operating temp: −10°C to 45°C
  safety: IEC 62619 compliant

Output: peak charge saving + arbitrage saving vs investment
```

### S3 — Switch to Heat Pump

```
Current heating cost (gas boiler baseline):
  existing_cost = heating_kwh / 0.90 (boiler efficiency) × gas_price_€_kwh

Heat pump cost:
  hp_electricity = heating_kwh / cop_rated
  hp_cost = hp_electricity × electricity_price_€_kwh

Saving = existing_cost − hp_cost
CO2_reduction = existing_co2 − (hp_electricity × emission_factor)

Germany GEG compliance:
  Heat pump auto-satisfies 65% renewable requirement
  → Flag KfW/BAFA Wärmepumpe incentives
```

### S4 — Insulation Upgrade

```
Heat loss reduction:
  Q_saved = ΔU × surface_area × HDD × 24 / 1000
  ΔU = current_u_value − target_u_value (W/m²K)

Cost (Germany 2024):
  Wall insulation (100mm EPS):     80–120 €/m²
  Roof insulation (mineral wool):  60–100 €/m²
  Triple glazing windows:         400–700 €/m²

KfW BEG / KfW 261 grants: typically 15–20% of investment
```

## 15. Data Model

### Bronze layer — raw, as ingested
Tables: `raw_energy_readings`, `raw_solar_generation`, `raw_battery_status`, `raw_weather_data`, `raw_hvac_data`. All store `building_id`, raw values, source system, timestamps. Partitioned by `building_id / year / month / day`. Delta Lake format.

### Silver layer — cleaned and validated

#### silver.building_master (spine of the data model)

Every dimension column that drives logic gating:
- **Identity:** `building_id`, `organization_id`, `building_name`
- **Geography:** `country_code`, `city`, `climate_zone` (Köppen — Cfb, BSk, etc.)
- **Area:** `gross_floor_area_m²`, `conditioned_area_m²`
- **Type:** `building_type` (Office / Retail / Hotel / Logistics)
- **Subscription:** `subscription_tier` (Insight / Monitor / Copilot)
- **Technology flags:** `has_pv`, `has_battery`, `has_heat_pump`, `has_hvac_traditional`, `has_ev_charging`, `has_led_lighting`
- **PV details:** `pv_capacity_kwp`, `roof_area_m²`, `roof_orientation`, `roof_tilt_deg`
- **Battery details:** `battery_capacity_kwh`, `battery_technology`, `battery_strategy`
- **Heat pump:** `heat_pump_cop_rated`, `heat_pump_capacity_kw`
- **Envelope:** `wall_u_value`, `roof_u_value`, `floor_u_value`, `window_u_value`, `window_to_wall_ratio`, `air_tightness_ach`, `thermal_mass_level`, `insulation_year`
- **Compliance:** `energy_certificate` (A+ → G), `iso50001_certified`, `regulatory_profile_id`

#### Other silver tables
- `energy_readings_clean`, `solar_generation_clean`, `battery_status_clean`, `weather_clean`
- `grid_emission_factors` — country × year × emission_factor
- `electricity_tariffs` — peak / off-peak / demand charge / feed-in tariff per country
- `incentive_programs` — KfW / BAFA / YEKA / etc.
- `regulatory_rules` — EnEfG / GEG / EPBD / BEP-TR

### Gold layer — business-ready
- `kpi_hourly` (primary Tier 2/3 fact)
- `kpi_daily` (primary Tier 1 fact — 32 columns)
- `kpi_monthly` (ESG + billing analysis)
- `anomaly_log` (type, severity, action, estimated_loss, acknowledged, resolved)
- `sustainability_metrics`, `ghg_scope`, `compliance_status`, `incentive_matches`, `recommendations`
- `simulation_add_pv`, `simulation_add_battery`, `simulation_switch_hvac`, `simulation_add_insulation`, `simulation_window_upgrade`, `simulation_battery_strategy`
- `iot_realtime`, `iot_hot_readings` (Page 8 — KQL Eventhouse hot path)
- `hvac_analytics` (Page 7)
- `battery_simulation`, `battery_technologies`, `country_regs`, `strategy_fitness` (Page 9)
- `data_health_log`

## 16. Stated Assumptions

If a client asks "why 5%?" you point to this list.

### Data
- Minimum resolution Tier 1: hourly | Tier 2/3: 15-minute
- HDD base 15°C, CDD base 22°C (EN ISO 15927-6)
- Missing data interpolated up to 2 consecutive hours; beyond that flagged MISSING

### Grid emission factors
- Germany 2024: 0.380 kg CO₂/kWh (UBA)
- Turkey 2024: 0.442 kg CO₂/kWh (TEİAŞ)
- Reviewed annually

### Solar PV
- Performance Ratio default: 0.80
- 7 m² roof area per kWp (400W panels, 1.7 m² each)
- South orientation default; tilt 30° (Germany), 25° (Turkey)
- NPV discount 5%, period 10 years
- Germany cost €1,000–1,400/kWp; Turkey $600–900/kWp
- Panel lifetime 25 years

### Battery
- LFP recommended
- Cost €600–900/kWh (2024 EU installed)
- Round-trip efficiency 0.92
- Cycle life 4,000; system lifetime 15 years
- Operating band 15%–90% mandatory, 20%–80% optimal
- EU ETS €60–80/ton CO₂

### Heat Pump
- Gas boiler baseline efficiency 0.90
- COP alert at 80% rated, HIGH alert at 60%
- COP comparison band ±3°C of design

### HVAC
- Heating 20°C (EN 16798-1), cooling 24°C
- ~6% excess energy per °C deviation
- Preheat 6 min per °C diff
- Winter setback 16°C, summer setback 28°C

### Building benchmarks (Office)
| Class | EUI (kWh/m²/yr) | Source |
|---|---|---|
| Excellent | < 80 | ASHRAE 90.1 + EU Building Stock Observatory |
| Good | 80–130 | |
| Average | 130–200 | |
| Poor | > 200 | |

### Building-type aware thresholds (DAX patterns)
- Hotel / Healthcare: 130 kWh/m²/yr
- Logistics: 60 kWh/m²/yr
- Office (default): 35 kWh/m²/yr (specific monitoring KPI)

### Financial
- Electricity (commercial): DE ~€0.22/kWh, TR ~€0.08/kWh (2024)
- Gas (DE): ~€0.07/kWh
- Feed-in tariff PV (DE small commercial): ~€0.08/kWh (EEG 2024)

### What we DO NOT assume
- Sensor data always accurate (quality flags handle this)
- Energy prices fixed (per-tenant tariff table)
- All buildings have all technologies (tech profile gates modules)
- Roof characteristics always known (PV sims note when estimates used)
- Compliance is binary (gap analysis provides gradations)

---

# PART III — REGULATORY VOCABULARY

This is where your freelance pricing power comes from. A client paying €4,500 for a CSRD Quickstart does not pay for SQL — they pay for the confidence that you understand their disclosure obligation.

(tr: Müşteri SQL yazabilen 100 kişi bulur. Senin CSRD konuştuğunu görünce parayı sorgusuz öder. Bu bölüm İngilizce dilini test ettiğin yer — kelimeleri tanıdığında anlamı pekişir, sonra cümleyi içselleştirirsin.)

Each section has: **What it is** • **Why the client cares** • **Talking points** • **Drill phrases** • **Where to study (free)** • **Time budget**.

## 17. CSRD — Corporate Sustainability Reporting Directive

**What it is:**
An EU law in force since January 2024. Forces companies to publish sustainability reports using ESRS (European Sustainability Reporting Standards). Replaces the older NFRD (Non-Financial Reporting Directive).

**Who must comply, and when (memorize):**
- **Wave 1** — Large public-interest companies, FY2024 → filed 2025 (already happening)
- **Wave 2** — Other large companies, FY2025 → filed 2026 (your prime market — they are scrambling right now)
- **Wave 3** — Listed SMEs, FY2026 → filed 2027
- **Wave 4** — Non-EU companies with EU turnover > €150M, from FY2028

(tr: Wave 2 = altın madenin. 2026'da rapor verecekler, çoğu Excel'de boğuluyor.)

**Why the client cares:**
- Penalties (Germany Lieferkettengesetz precedent: up to 2% of global turnover)
- Investor pressure — funds will not buy non-CSRD-compliant company shares
- Bank lending tied to ESG scores (taxonomy regulation)
- They have to produce a report and **they don't know how**

**Talking points:**
> "Are you in Wave 1, Wave 2, or still waiting for Wave 3?" — this single question tells you their urgency
> "Which assurance level are you targeting — limited or reasonable?" — limited is mandatory now, reasonable mandatory from FY2028
> "Have you completed your double materiality assessment yet?" — foundation of CSRD; if not done, they cannot file

**Drill phrases (repeat aloud):**
1. "CSRD is the EU directive; ESRS is the standard; double materiality is the methodology — they sit together but they are different things."
2. "Your reporting obligation depends on which wave you fall under. Most mid-cap companies I work with are Wave 2, filing FY2025 numbers in 2026."
3. "I help clients translate ESRS datapoints into Power BI dashboards their auditor can sign off on."

**Where to study (free):**
- EFRAG ESRS landing page (search "EFRAG ESRS")
- KPMG / PwC / Deloitte CSRD readiness guides (free PDF)
- IFRS Foundation summary

**Time:** 3 hours

## 18. ESRS E1 — Climate Change Standard

**What it is:**
The most important of the 12 ESRS topical standards. E1 is the climate disclosure. If you sell *one* product, it sells ESRS E1 compliance.

E1 has **9 disclosure requirements, E1-1 through E1-9.** Memorize at least these four:

| Code | What it discloses | Maps to EnergyLens |
|---|---|---|
| **E1-1** | Transition plan for climate mitigation | Pages 4–5 (forecast, decision support) |
| **E1-5** | Energy consumption and mix | Pages 1–3 (consumption breakdown) |
| **E1-6** | Gross Scope 1, 2, 3 and Total GHG emissions | Page 6 (GHG dashboard) |
| **E1-9** | Anticipated financial effects of climate risks | Page 9 (battery ROI, scenario analysis) |

(tr: Bu tabloyu ezberle. Müşteri "ESRS E1-6 yapabiliyor musun?" diye sorduğunda kafanda direkt Page 6 belirsin. Bu refleks olmalı.)

**Why the client cares:**
- E1 is the most data-heavy ESRS standard — they need a *tool*, not a Word document
- Auditors demand traceable data lineage (every kg CO₂ traceable to a source row)
- This is *exactly* where your Fabric medallion architecture becomes the selling point — full lineage is a Fabric superpower

**Talking points:**
> "E1-6 requires Scope 1, 2, and 3 separately, both market-based and location-based for Scope 2. Are your current numbers in that format?"
> "ESRS demands traceable methodology. My medallion architecture gives your auditor row-level lineage from raw bill to disclosed kg CO₂e."
> "We can pre-populate the E1-1 transition plan visualization from your historical baseline and target trajectory."

**Drill phrases:**
1. "Scope 2 must be reported both location-based and market-based. Most companies forget this and get flagged in audit."
2. "ESRS E1-6 is the disclosure; the GHG Protocol is the methodology. They reference each other but they are different documents."
3. "I do not just build a dashboard — I build a dashboard with traceable lineage from raw data to disclosed number."

**Where to study (free):**
- EFRAG ESRS E1 final standard PDF (~80 pages, skim disclosure requirements section)
- Deloitte "ESRS E1 Implementation Guide" PDF
- CDP one-pager comparing E1 to TCFD recommendations

**Time:** 5 hours

## 19. GHG Protocol Corporate Standard

**What it is:**
The **methodology** for calculating greenhouse gas emissions. Published by World Resources Institute (WRI) + WBCSD. Defines Scope 1, 2, 3 rules.

Critically: ESRS E1 *references* the GHG Protocol. They go together but are not the same.

(tr: ESRS sana **ne** raporlayacağını söyler, GHG Protocol **nasıl** hesaplayacağını söyler. İki farklı seviyede çalışır.)

**The three scopes — memorize cold:**

- **Scope 1 — Direct emissions** from owned/controlled sources
  - Examples: Natural gas boilers, fleet vehicles, refrigerant leaks (HVAC), industrial process emissions
- **Scope 2 — Indirect from purchased energy**
  - Electricity, steam, heating, cooling purchased from utilities
  - Reported **two ways**: location-based (grid average) and market-based (supplier-specific, often green certificates)
- **Scope 3 — All other indirect** across the value chain
  - 15 categories. Most relevant for buildings: Category 1 (purchased goods), 6 (business travel), 7 (employee commuting), 13 (downstream leased assets)

**Why the client cares:**
- They have Scope 1 + 2 *roughly* in Excel
- Scope 3 is where they get stuck — 15 categories, many data sources
- They have *no idea* about market-based vs location-based Scope 2 — auditor will flag this

**Talking points:**
> "Have you calculated market-based Scope 2 yet? Mandatory under ESRS E1-6 starting FY2025 reports."
> "Which Scope 3 categories are material for your business? Most building portfolios need at least Category 13 modeled."
> "Refrigerant leaks are Scope 1 and they're routinely missed. Have your facility teams reported R-410A or R-32 refills?" — power move; shows HVAC operations understanding

**Drill phrases:**
1. "Scope 1 is owned, Scope 2 is purchased, Scope 3 is everything else."
2. "Market-based Scope 2 uses your supplier's actual fuel mix. Location-based uses your country's grid average."
3. "Scope 3 has 15 categories. Most clients only need to model 4 or 5 that are material to their business."

**Where to study (free):**
- GHG Protocol Corporate Standard PDF (ghgprotocol.org, ~110 pages, very readable)
- Scope 3 Standard (separate PDF — only read Chapter 5 listing the 15 categories)
- One-pager: search "Location-based vs Market-based Scope 2"

**Time:** 4 hours

## 20. EU Taxonomy + EPC + ISO 50001 (lighter touch)

You need to recognize and reference these, not master them.

**EU Taxonomy** — A list of economic activities counting as "environmentally sustainable" for investor reporting. Comes up when clients talk about *which buildings qualify for green financing*.
> *Quick line:* "Your taxonomy alignment percentage depends on building EPC ratings — A and B are typically aligned, C and below need substantial renovation."

**EPC — Energy Performance Certificate** — National rating A+ to G based on kWh/m²/year. Required at sale/rent across EU. Different methodologies per country (DENA in Germany, BREEAM/BER in Ireland).
> *Power line:* "I work with EPC ratings as area-weighted portfolio scores. EnergyLens Page 6 uses LOOKUPVALUE across the building dimension to weight by floor area, not just count buildings."

**ISO 50001 — Energy Management System** — Industrial framework. Defines **EnPI** (Energy Performance Indicator) and **EnB** (Energy Baseline) — terms in many job postings.
> *Power line:* "Your EnPI should normalize for occupancy, weather (heating/cooling degree days), and production volume. Without that, kWh/m² alone is misleading."

**Time:** 2 hours (recognition and namedrop level)

## 21. Country-Specific Regulations

### Germany

**EnEfG — Energiedienstleistungsgesetz / Energy Efficiency Act**
- Applies if organization has ≥ 250 employees
- Requires **ISO 50001 certification** OR equivalent energy audit
- Checked in EnergyLens against `organization.employee_count` and `building.iso50001_certified`

**GEG — Gebäudeenergiegesetz / Building Energy Act**
- For HVAC replacements from 2024 onward: **≥ 65% renewable energy source required** (§71)
- Minimum U-values: wall ≤ 0.24 W/m²K, roof ≤ 0.20, windows ≤ 1.30

**EEG — Erneuerbare-Energien-Gesetz / Renewable Energy Act**
- Sets feed-in tariff rates for PV grid exports
- 2024 small commercial PV: ~€0.08/kWh

**KfW & BAFA grant programs** (referenced in `gold.incentive_matches`):
- KfW 261 / BEG — building efficiency grants (insulation, windows)
- BAFA Wärmepumpe — heat pump grants
- BAFA energy audit — audit cost subsidy

### Turkey

**BEP-TR — Binalarda Enerji Performansı (Building Energy Performance)**
- Requires EPC certificate; renewal every 10 years

**EPDK** — Turkish energy market regulator; affects tariff structure

**YEKA — Yenilenebilir Enerji Kaynak Alanları** — Renewable energy zones, PV incentives

## 22. Technical / Engineering Standards

**ISO 50001** — International EnMS standard. Defines EnPI and EnB. Required under German EnEfG for ≥250 employees.

**EN ISO 15927-6** — Degree Day methodology. EnergyLens uses base 15°C (HDD), 22°C (CDD) per this standard.

**EN 16798-1** — Indoor Environmental Input Parameters. Comfort categories I–IV; 20°C heating / 24°C cooling setpoints from this standard.

**ASHRAE 90.1** — US energy efficiency standard, widely cited in EU. Source of "Excellent / Good / Average / Poor" EUI thresholds.

**ASHRAE 135** — BACnet protocol. Germany BMS market standard. P0-priority protocol adapter in EnergyLens.

**IEC 61158** — Modbus protocol. Widespread EU. P0-priority adapter.

**ISO/IEC 20922** — MQTT 5.0 protocol. P1-priority adapter.

**IEC 62541 — OPC-UA** — Premium industrial protocol. P2 (Phase 2.5) adapter.

**IEC 62619** — Lithium-ion battery safety for industrial applications. LFP recommendation is IEC 62619 compliant.

**EN 13829 / ISO 9972** — Blower Door Test methodology. Cited in EnergyLens A7 anomaly action.

---

# PART IV — MICROSOFT ANALYTICS SALES VOCABULARY

This is the language that makes a client say "this person is technically credible and current."

## 23. Microsoft Fabric Elevator Pitch

You know Fabric internally. Now memorize how to *sell* it in one paragraph.

**The elevator pitch (memorize verbatim, English):**

> "Microsoft Fabric is a unified analytics platform — it combines data engineering, data warehousing, real-time analytics, data science, and Power BI on a single SaaS foundation. The big deal is OneLake — every workload reads and writes the same data layer, so you stop copying data between systems. For sustainability reporting, this matters because your ESRS audit trail stays in one place."

(tr: Bu paragrafı ezberle. Aynen söyle. Boğazından çıkana kadar tekrar et. Müşteri toplantısının ilk 3 dakikasında bunu söyleyince "vay bu adam Fabric biliyor" diyecek.)

**Key terms to drop naturally:**

- **OneLake** — the unified storage layer (one logical data lake across the org)
- **Lakehouse** — Fabric's table store; combines lake flexibility + warehouse semantics
- **Medallion architecture** — Bronze (raw) → Silver (cleaned, conformed) → Gold (business-ready)
- **DirectLake mode** — Power BI reads Parquet files directly from OneLake, no import, no DirectQuery latency
- **Capacity (F-SKU)** — Fabric pricing unit (F2, F4, F8... F64). Mention F2 as "smallest viable for production POC."

## 24. DP-600 / DP-700 Certifications

You hold DP-700 (Data Engineer). DP-600 (Analytics Engineer) is the *more sellable* cert for client-facing BI work — it covers Power BI, semantic modeling, DAX, plus Fabric.

**Do you need to take it?** Only if you have time. Studying for it (without taking the exam) gives you a confidence boost. Actual cert adds maybe 15% to perceived credibility on Malt.

**Free study path:**
- Microsoft Learn DP-600 Learning Path (100% free, official)
- Practice exam: Whizlabs / MeasureUp samples
- YouTube: "Pragmatic Works DP-600 study guide"

**Time:** 8–12 hours if sitting the exam. 3–4 hours skim for sales credibility.

(tr: Sertifikayı almasak bile öğrenme yolundaki içeriği gez. Müşteri "DAX optimization yapıyor musun?" diye sorduğunda "evet, semantic model best practices'i tüm projelerde uyguluyorum" diyebilmen lazım.)

## 25. Direct Lake Mode — The Headline Feature

This is *the* Fabric talking point because almost nobody understands it yet.

**One-sentence definition:**
> "Direct Lake lets Power BI query data directly from Delta Parquet files in OneLake — no import, no DirectQuery — so you get near-import performance with real-time data freshness."

**Why clients love it:**
- They've been stuck between slow DirectQuery and stale Import mode for years
- Direct Lake gives them both: fast and fresh
- It's a *visible* upgrade — they will pay for someone who configures it correctly

**Drill phrase:**
> "Most teams default to Import mode out of habit. Direct Lake gives you the same performance without the refresh schedule headache — and it's free if you're already on Fabric."

**Time:** 1 hour (2 Microsoft Learn pages + one Patrick LeBlanc video on Guy in a Cube)

## 26. Power BI Embedded + App-Owns-Data

If you sell to ESG consultancies (ICP-A), they want to *resell* your dashboard to their clients. That means embedding.

**Two flavors — know the difference:**

- **User-owns-data** — Each end user needs their own Power BI license. Simple, but client pays per user.
- **App-owns-data** — Service principal authenticates on behalf of users. End users do **not** need Power BI licenses. *This is what consultancies and SaaS resellers need.* Requires a Premium capacity (or PPU + workspace).

(tr: Müşterin başka müşterilerine dashboard satıyorsa **app-owns-data** lazım. Aksi halde her son kullanıcı için Power BI lisansı ödemek zorunda. Bu konuyu bilmek = consultancy müşteri kazanmak.)

**Drill phrase:**
> "If you're white-labeling this dashboard to your clients, you'll want app-owns-data with a service principal — that way your clients don't need Power BI licenses. We need a Premium capacity or PPU workspace for the embed to work."

**Time:** 2 hours (Microsoft Learn "Embed Power BI content" + "Service principal authentication")

## 27. Copilot in Fabric / Power BI

Every client asks. You don't need to be a Copilot expert — you need to know what it does and where it doesn't.

**What it does (today, 2026):**
- Generates DAX measures from natural language ("show me YoY growth for revenue")
- Summarizes report pages
- Generates Q&A insights ("which customer segment grew most this quarter?")
- Helps write semantic model documentation

**What it does NOT do (be honest):**
- Replace a real semantic model designer — makes mistakes on complex relationships
- Build dashboards end-to-end from a CSV without curation
- Understand business context — still needs a human to validate

**Drill phrase:**
> "I use Copilot to accelerate measure scaffolding, then refine manually. It's good at 70% of the work but the last 30% is where the value sits."

**Time:** 1 hour (any recent Microsoft Reactor Copilot demo + Guy in a Cube episode)

## 28. Real-Time Intelligence (EventStream, Eventhouse, KQL)

You already built this for Page 8 (EnergyLens IoT). Memorize the *sales* angle.

**Sales angle:**
> "Most Power BI consultants stop at scheduled refreshes. With Fabric Real-Time Intelligence — EventStream feeding KQL Eventhouse plus a Power BI Direct Lake semantic model — you can show building energy data with sub-second latency. I built one for a 10-building portfolio with BACnet ingestion."

This is a flex that <0.1% of freelancers can pull off. Use it on Malt profile prominently.

**Time:** 0 hours of new study (you built it). Just memorize the sales line.

---

# PART V — DISCOVERY CALL FRAMEWORK

Knowing vocabulary is necessary but not sufficient. You also need structure for the first call.

## 29. The 30-Minute Discovery Call Structure

```
0–5 min   — Build rapport. Find out their role and what triggered the project.
5–15 min  — Diagnose. Ask the 6 questions below.
15–25 min — Educate (briefly) + position your offering.
25–30 min — Define next step. Either propose or schedule scoping call.
```

## 30. The Six Diagnostic Questions (Memorize)

Ask in this order in every discovery call. Each is calibrated.

1. **"Walk me through what you have today — what tools, what data sources, what's working and what's painful?"**
   *(Lets them vent. You learn the landscape. 3-4 minutes of their talking.)*

2. **"What triggered you to start looking for help right now?"**
   *(Reveals urgency. "Audit in 6 weeks" — high urgency, premium price. "Exploring options" — low urgency, longer cycle.)*

3. **"Are you in CSRD Wave 1, Wave 2, or not yet in scope?"** *(only ask if ESG context)*
   *(Quickly calibrates regulatory pressure.)*

4. **"Who is the end consumer of this report — the CFO, the sustainability officer, your auditor, your investors?"**
   *(Different consumers need different dashboards. CFO wants €cost. Auditor wants lineage. Investor wants trend.)*

5. **"What's your timeline and budget range?"**
   *(Ask directly. Most freelancers chicken out of this. If you don't ask, you'll quote in the dark.)*

6. **"What does 'done' look like for you in this engagement?"**
   *(Forces them to define success. Protects you from scope creep.)*

## 31. The "Position-and-Propose" Move (Last 10 Minutes)

Once you've diagnosed, transition with this exact sentence:

> "Based on what you've described, I think the best fit is one of two paths..."

Then offer two productized packages from positioning brief (P1–P4). **Always two** — not one, not three. Two options force a choice rather than yes/no.

(tr: Sadece bir teklif sunma — "evet/hayır" psikolojisine sürüklenir. İki teklif sun — müşteri "A mı B mi?" diye düşünür. Pazarlama psikolojisi temel taktiği. Genelde A'yı seçerler — onu da senin tercihin yap.)

---

# PART VI — COMMON CLIENT QUESTIONS & PRE-BUILT ANSWERS

Memorize these. You will get every one of them eventually.

### "What's your hourly rate?"
> "I work on fixed-scope packages where possible — that gives you cost certainty. For ad-hoc work, my opening rate is €60/hour. I'm flexible based on project scope and duration."

### "Do you have CSRD certification?"
> "There is no official 'CSRD certification' that exists today — the regulation is too new. I work with the actual EFRAG ESRS standards and the GHG Protocol methodology. I'm Microsoft Fabric Data Engineer certified, which is what underpins the technical delivery."

### "Can you do this in Tableau / Looker?"
> "I specialize in the Microsoft Fabric and Power BI stack. If you're locked into Tableau, I'd recommend a Tableau specialist — happy to refer one. If you have flexibility on the BI tool, I can show you why Fabric is significantly stronger for the lineage requirements CSRD demands."

### "We need this in 2 weeks. Can you do it?"
> "For a Scope 1/2/3 baseline dashboard with 2-3 data sources, 2 weeks is realistic with my P1 Quickstart package. If you need full ESRS E1 mapping across all 9 disclosures, that's a 4-week engagement. Let's scope what 'done' means for the 2-week version."

### "Can you work on our existing Power BI?"
> "Yes — I do a lot of remediation work. Typical pattern: 2-day audit, then a fixed-scope improvement sprint based on the audit findings. The audit alone is €1,200 and includes a written roadmap you keep regardless of next steps."

### "We have no Microsoft Fabric — should we get it?"
> "Not necessarily. Power BI Premium Per User is enough for many CSRD use cases. Fabric pays off when you have real-time data, multi-source integration, or you need OneLake's audit lineage. Let me look at your data sources before recommending."

### "We're a small company — can you make this affordable?"
> "I have a starter package — P2 Building KPI Dashboard at €1,800 for up to 5 buildings. That covers EnPI, kWh/m², and EPC mapping. If that's still too high, we can talk about a 1-day audit at €500 to scope something narrower."

(tr: Bu hazır cevapları ezberle. Müşteri telefonda sorduğunda hiç tereddüt etmemen lazım — fiyat sorusunda 3 saniye duraklamak güvensizlik sinyali verir. Aynayla pratik et.)

---

# PART VII — GLOSSARY (Alphabetical Reference)

Quick reference for every term used in the project and in conversations. Consult during real calls — 5-second lookup.

**ABFS** — Azure Blob File System; storage path scheme used by Fabric Lakehouse.

**Activator (Reflex)** — Microsoft Fabric's rule-based alert engine.

**App-Owns-Data** — Power BI Embedded mode using a service principal — end users do NOT need Power BI licenses. Required for SaaS / consultancy reselling.

**ASHRAE 90.1** — US energy efficiency standard for non-residential buildings; widely used for benchmark thresholds globally.

**ASHRAE 135** — BACnet protocol standard (data communication for building automation).

**BACnet/IP** — Building Automation and Control Networks over IP. Standard for BMS communication in commercial buildings. Germany default protocol.

**Baseline / EnB (Energy Baseline)** — Reference energy performance under specified conditions (per ISO 50001). The number against which improvements are measured.

**Base Load** — Minimum consumption during unoccupied hours (02:00–04:00). High base load = equipment not entering standby properly.

**BAFA** — Bundesamt für Wirtschaft und Ausfuhrkontrolle (German federal economic office). Runs heat-pump and energy-audit grants.

**BEG** — Bundesförderung für effiziente Gebäude. Germany's central efficient-buildings grant program.

**BEP-TR** — Binalarda Enerji Performansı (Turkish Building Energy Performance regulation). Requires EPC every 10 years.

**BMS** — Building Management System. Centralized control of HVAC, lighting, security, etc.

**Bronze layer** — Medallion architecture tier for raw, untransformed data.

**Capacity (F-SKU)** — Fabric's pricing/compute unit. F2 is the smallest viable for production POC.

**CDD — Cooling Degree Days** — Sum over period of `MAX(0, daily_avg_temp − CDD_base)`. Base 22°C in EnergyLens.

**Climate-Adjusted EUI** — EUI normalized by HDD+CDD to allow fair comparison across climates.

**COP — Coefficient of Performance** — Heat energy output ÷ electrical input. A heat-pump KPI.

**CSRD — Corporate Sustainability Reporting Directive** — EU law mandating sustainability disclosures via ESRS.

**Data Factory** — Microsoft Fabric pipeline orchestrator (batch ETL).

**DAX — Data Analysis Expressions** — Power BI's modeling and measure language.

**Demand Charge** — Per-month billing component based on peak kW. Often the largest line item on commercial bills.

**Direct Lake** — Power BI mode where reports read Parquet files directly from OneLake — no import, no DirectQuery — combining near-import performance with real-time freshness.

**DirectQuery** — Power BI mode where queries hit the source database live. Real-time but slow on complex queries.

**Double Materiality** — CSRD methodology: report both how sustainability affects company (financial materiality) AND how company affects sustainability (impact materiality).

**EEG — Erneuerbare-Energien-Gesetz** — German Renewable Energy Act. Sets feed-in tariffs for grid-exported PV.

**EFRAG — European Financial Reporting Advisory Group** — Body that develops the ESRS standards.

**EnB — Energy Baseline** — see Baseline.

**EnEfG — Energiedienstleistungsgesetz** — German Energy Services Act. Requires ISO 50001 or audit for organizations ≥ 250 employees.

**EnPI — Energy Performance Indicator** — ISO 50001 term. Quantifies energy performance, typically normalized by output, occupancy, or weather.

**EPBD — Energy Performance of Buildings Directive** — EU directive targeting nZEB and minimum building energy standards.

**EPC — Energy Performance Certificate** — National rating A+ to G based on kWh/m²/year. Required at building sale/rent across EU.

**EPEX Spot** — European Power Exchange. Source of day-ahead electricity pricing data for Germany / Central EU.

**ESG Score** — Composite environmental/social/governance metric. In EnergyLens: 40% EUI vs benchmark, 30% CO₂ intensity, 20% renewable share, 10% compliance.

**ESRS — European Sustainability Reporting Standards** — The standards CSRD references. 12 topical standards; E1 (Climate) most important.

**ESRS E1** — The climate-change standard within ESRS. 9 disclosure requirements, E1-1 to E1-9.

**EU ETS** — EU Emissions Trading System. Carbon market with current pricing €60–80/ton CO₂ (2024).

**EU Taxonomy** — Classification of "environmentally sustainable" economic activities for investor reporting.

**EU 2023/1542** — EU Battery Regulation. Requires carbon footprint label, recycled content disclosure, warranty cycles for batteries sold in EU after Jan 2024.

**EUI — Energy Use Intensity** — kWh/m²/year. Primary efficiency KPI.

**EventStream** — Microsoft Fabric real-time data ingestion service.

**Eventhouse / KQL** — Fabric's real-time analytics database, queried with Kusto Query Language.

**EXIST** — Energy Exchange Istanbul. Turkish day-ahead electricity pricing reference.

**Fabric (Microsoft Fabric)** — Microsoft's unified analytics platform. GA May 2024. Combines data engineering, warehousing, real-time analytics, data science, Power BI on a single SaaS foundation.

**Feed-in Tariff** — Per-kWh price utility pays for grid-exported energy.

**GEG — Gebäudeenergiegesetz** — German Building Energy Act. Defines minimum U-values and §71 65% renewable heating requirement.

**GHG Protocol** — World Resources Institute / WBCSD methodology defining Scope 1/2/3 emissions calculation.

**Gold layer** — Medallion architecture tier for business-ready, aggregated data — what Power BI directly reads.

**HDD — Heating Degree Days** — Sum over period of `MAX(0, HDD_base − daily_avg_temp)`. Base 15°C in EnergyLens.

**IEC 61158** — Modbus communication protocol standard.

**IEC 62541 — OPC-UA** — Premium industrial automation protocol.

**IEC 62619** — Lithium-ion battery safety standard for industrial applications.

**Insulation U-Value** — Heat-transfer coefficient through a building element. Lower = better. W/m²K.

**IoT — Internet of Things** — Network of physical sensors/devices reporting data centrally.

**IRR — Internal Rate of Return** — Discount rate at which NPV equals zero.

**ISO 50001** — International standard for Energy Management Systems. Defines EnPI and EnB. Required under German EnEfG.

**ISO/IEC 20922** — MQTT 5.0 protocol standard.

**KfW** — Kreditanstalt für Wiederaufbau (German state development bank). Runs efficiency grant programs.

**KPI — Key Performance Indicator** — Any measurable value used to track performance.

**KQL — Kusto Query Language** — Microsoft's query language for time-series and log analytics.

**Lakehouse** — Storage paradigm combining data lake flexibility with warehouse structure. Fabric's Lakehouse uses Delta Lake on OneLake.

**LFP — Lithium Iron Phosphate (LiFePO₄)** — Battery chemistry. Recommended in EnergyLens for commercial buildings.

**Load Factor** — Average demand ÷ peak demand (0 to 1). Higher = flatter, more efficient consumption.

**Location-based Scope 2** — Method: country grid average emission factor. Mandatory for ESRS E1-6.

**Market-based Scope 2** — Method: supplier-specific emission factor. Also mandatory for ESRS E1-6.

**Medallion Architecture** — Bronze (raw) → Silver (cleaned) → Gold (business-ready) tier model. Fabric standard.

**Modbus TCP** — Industrial communication protocol over Ethernet. Widespread in EU. IEC 61158.

**MQTT 5.0** — Lightweight pub/sub IoT messaging protocol. ISO/IEC 20922.

**NMC — Nickel Manganese Cobalt** — Battery chemistry. More energy-dense than LFP but lower cycle life. Common in Turkey.

**NPV — Net Present Value** — Future cash flows discounted to present value. EnergyLens uses 5% discount rate, 10-year horizon.

**nZEB — Nearly Zero-Energy Building** — EPBD target for new buildings.

**OneLake** — Microsoft Fabric's unified data lake — single logical lake across the entire organization.

**OPC-UA** — Open Platform Communications Unified Architecture (IEC 62541). Phase 2.5 priority adapter.

**PEF — Product Environmental Footprint** — EU methodology for carbon footprint labeling of products (referenced by EU Battery Regulation).

**Performance Ratio (PR)** — actual PV yield ÷ theoretical PV yield. Target > 0.75. Industry default: 0.80.

**PPU — Power BI Premium Per User** — Per-user Premium license. Allows Premium features without full capacity purchase.

**Power BI Embedded** — Embedding Power BI reports in custom applications. Two flavors: user-owns-data and app-owns-data.

**Prophet** — Time-series forecasting library by Meta. Used for Page 4 forecasts.

**RLS — Row-Level Security** — Power BI feature restricting data visibility per user role. EnergyLens uses RLS on `building_id`.

**Round-trip Efficiency** — Battery: kWh discharged ÷ kWh charged. Target > 0.90 for LFP.

**Scope 1** — Direct GHG emissions from owned/controlled sources.

**Scope 2** — Indirect emissions from purchased electricity/heat. Report both location-based and market-based.

**Scope 3** — All other value-chain GHG emissions. 15 categories.

**SCOP — Seasonal COP** — COP averaged over a heating season.

**Self-Consumption Rate** — Of generated PV energy, percentage used on-site. Target > 70%.

**Self-Sufficiency Rate** — Of total consumption, percentage supplied by own PV. 20–60% typical.

**Semantic Model** — Power BI's modeling layer. Tables, relationships, measures, calculated columns.

**SoC — State of Charge** — Battery charge level 0–100%.

**SoH — State of Health** — Battery capacity vs nominal (declines with age). Required disclosure under EU 2023/1542.

**TEİAŞ** — Türkiye Elektrik İletim A.Ş. Turkish grid operator. Source of TR emission factor.

**Tier 1 / 2 / 3** — Subscription tiers in EnergyLens. Insight / Monitor / Copilot.

**UBA — Umweltbundesamt** — German Federal Environment Agency. Source of DE emission factor.

**U-Value** — Heat-transfer coefficient (W/m²K). Building element insulation quality. Lower = better.

**Window-to-Wall Ratio (WWR)** — Window area ÷ exterior wall area. Affects heat loss and daylighting.

**YEKA** — Yenilenebilir Enerji Kaynak Alanları (Turkish renewable energy zone designations).

---

# APPENDIX A — 4-Week Study Schedule

| Week | Daily time | Focus | Deliverable to yourself |
|---|---|---|---|
| **Week 1** | 1.5 hr | Part I (positioning) + Part II (project) + Part III §17–19 (CSRD / ESRS E1 / GHG Protocol) | Can answer any client question about Scope 1/2/3 unprompted |
| **Week 2** | 1.5 hr | Part III §20–22 (Taxonomy/EPC/ISO 50001 + country regs + tech standards) + Part IV §23–24 (Fabric pitch + DP-600) | Can deliver the Fabric elevator pitch in 60 seconds without notes |
| **Week 3** | 1.5 hr | Part IV §25–28 (Direct Lake + Embedded + Copilot + Real-Time) | Can demo each on screen-share if asked |
| **Week 4** | 1 hr | Part V (Discovery Calls) + Part VI (Q&A) + 3 mock calls | Run 3 mock discovery calls with yourself or a friend. Record. Listen back. |

**Total: ~30 hours over 4 weeks**, but **you only need Week 1+2 before sending first proposals.** Week 3+4 happen in parallel with the first applications.

---

# APPENDIX B — Free Resource Checklist

### Regulatory (free PDFs)
- EFRAG ESRS E1 final standard
- GHG Protocol Corporate Standard
- GHG Protocol Scope 3 Standard
- KPMG / PwC / Deloitte CSRD readiness guides

### Microsoft (free)
- Microsoft Learn DP-600 path
- Microsoft Learn DP-700 path (refresh)
- Guy in a Cube YouTube channel
- Pragmatic Works YouTube
- Microsoft Fabric documentation (docs.microsoft.com/fabric)

### Industry context (free)
- IEA Buildings Tracker (annual buildings energy outlook)
- BPIE (Buildings Performance Institute Europe) reports
- CDP disclosure guides

### Practice (free)
- Reddit /r/PowerBI for live job questions
- Stack Overflow [microsoft-fabric] tag
- LinkedIn ESG/CSRD groups (read, don't post yet)

---

# Final Note

You don't need to finish everything in this document before sending the first proposal. You need:

- **Day 1:** Part I + Part II §9–10 + Part III §17, 18, 19 + Part V §30 (6 diagnostic questions)
- **Day 7:** Add Part III §20–22 + Part IV §23, 25, 28
- **Day 14:** Everything else in passing fluency

Send the first proposals at Day 7. Refine the rest while live in the market. Don't wait to be perfect — perfect is the enemy of paid.

(tr: Hazırlık vs uygulamayı karıştırma. 7 gün ön çalışma yeterli — sonra teklif göndermeye başla. Eksiklerini canlı işlerde tamamlarsın.)

Good luck. You have everything you need in your head and on the page. Now go convert it into invoices.

— Mert
