# EnergyLens — Project Technical Reference

**For:** Ali Mert Özdemir
**Date:** 2026-05-26
**Purpose:** Master your own project before client calls. Every KPI, every standard, every visual, every assumption — explained in English, with Turkish help notes for the hardest concepts.

> **Reading guide (tr):** Bu doküman EnergyLens'i baştan sona açıklıyor — kendi projenin bilmediğin yanı kalmasın. Müşteri "şu sayfada nasıl hesapladın?" diye sorduğunda 3 saniyede cevap verebilmen lazım. Önce Bölüm 1'i (proje anatomisi) oku — büyük resim. Sonra Bölüm 2 (9 sayfa). Bölüm 3 (formüller) referans amaçlı — toplantı öncesi tarayabilirsin. Bölüm 4 (standartlar) ve Bölüm 10 (glossary) en çok döneceğin yerler.

---

## Table of Contents

1. [Project Anatomy — The Big Picture](#1-project-anatomy)
2. [The 9 Power BI Pages — Every Visual Explained](#2-the-9-power-bi-pages)
3. [KPI Formulas Master List](#3-kpi-formulas-master-list)
4. [Standards and Regulations Cited](#4-standards-and-regulations)
5. [Anomaly Detection Logic](#5-anomaly-detection-logic)
6. [Battery Dispatch Strategies](#6-battery-dispatch-strategies)
7. [Simulation Engines](#7-simulation-engines)
8. [Data Model — Bronze / Silver / Gold](#8-data-model)
9. [Stated Assumptions](#9-stated-assumptions)
10. [Glossary — Every Technical Term Used](#10-glossary)

---

## 1. Project Anatomy

### What EnergyLens is, in one paragraph

EnergyLens is a production-grade energy intelligence platform for commercial buildings, built on Microsoft Fabric. It ingests data from utility bills, EPC certificates, BMS sensors (BACnet / Modbus / MQTT), weather APIs, and battery telemetry; processes it through a Bronze→Silver→Gold medallion architecture in OneLake; and surfaces 9 Power BI pages covering consumption, anomalies, forecasting, decision support, sustainability (CSRD/ESRS-aligned), HVAC profiles, real-time IoT, and battery dispatch ROI. It supports multiple buildings, multiple tenants, and multiple regulatory regions through a single semantic model with Row-Level Security.

### Why this design

- **Medallion architecture** so every disclosed kg of CO₂ can be traced back to its raw bill row — audit-ready
- **Technology profile gating** (`has_pv`, `has_battery`, `has_heat_pump`) so each building only sees its relevant analytics — no "N/A" cells everywhere
- **Tier-aware ingestion** (batch for Tier 1, streaming for Tier 2/3) so we don't pay for streaming when a smart meter delivers data hourly
- **Static regulation tables** because rules like GEG / EnEfG / BEP-TR change ~once a year — overengineering them as live API would burn time

### Architecture diagram (in words)

```
SOURCES (data in)
  Smart meters, utility bills (CSV / API)         ─┐
  BMS sensors (BACnet, Modbus, MQTT, OPC-UA)      ─┤
  Weather APIs (OpenWeather / DWD / MGM)          ─┤
  Battery telemetry, solar inverters              ─┤
                                                   │
                                                   ▼
INGESTION LAYER (Microsoft Fabric)
  Data Factory pipelines  ──  batch (Tier 1)
  Eventstream            ──  real-time (Tier 2/3)
                                                   │
                                                   ▼
STORAGE — Microsoft Fabric Lakehouse (OneLake)
  ┌──────────────────────────────────────────────┐
  │ BRONZE — raw, as ingested                    │
  │   raw_energy_readings, raw_solar_generation, │
  │   raw_battery_status, raw_weather_data,      │
  │   raw_hvac_data                              │
  └──────────────────┬───────────────────────────┘
                     │ PySpark transformations
                     ▼
  ┌──────────────────────────────────────────────┐
  │ SILVER — cleaned, normalized, validated      │
  │   building_master, energy_readings_clean,    │
  │   solar/battery/weather_clean,               │
  │   grid_emission_factors, tariffs,            │
  │   incentive_programs, regulatory_rules       │
  └──────────────────┬───────────────────────────┘
                     │ KPI calculation, anomaly detection
                     ▼
  ┌──────────────────────────────────────────────┐
  │ GOLD — business-ready                        │
  │   kpi_hourly, kpi_daily, kpi_monthly         │
  │   anomaly_log, sustainability_metrics,       │
  │   compliance_status, incentive_matches,      │
  │   recommendations, simulation_* tables       │
  └──────────────────┬───────────────────────────┘
                     │ Direct Lake mode
                     ▼
SEMANTIC MODEL (Power BI)
  9-page report + DAX v56 measure library
                     │
                     ▼
OUTPUT
  Embedded Power BI in customer-facing web app
  Activator (Reflex) rule-based alerts
```

### Three subscription tiers — what they unlock

| Tier | Name | Latency | Data sources | Active modules |
|---|---|---|---|---|
| **1** | Insight | ~1 hour | Smart meter (hourly), bills (monthly) | KPI dashboard, basic anomaly detection, compliance, recommendations |
| **2** | Monitor | 5–15 min | Tier 1 + IoT sensors (BACnet/Modbus/MQTT) | + Real-time monitoring, HVAC optimization, peak shaving |
| **3** | Copilot | < 5 min | Tier 2 + battery / heat pump telemetry | + Battery dispatch simulation, ML anomaly detection (Phase 2), scenario simulation |

(tr: Bu üç katman ürün paketlemesi için kritik. Müşteriye "Tier 2'ye geçtiğinizde şunlar açılır" diye somut konuşabiliyorsun.)

### Multi-tenant access model

```
ORGANIZATION
  └── BUILDING (building_id — primary partition key)
        ├── Technology Profile (has_pv, has_battery, has_heat_pump…)
        ├── Country (DE / TR / …)
        ├── Subscription Tier
        └── All time-series data partitioned by building_id

ROW-LEVEL SECURITY (RLS) roles:
  Facility Manager  → sees only their building(s)
  Energy Manager    → sees all buildings in their organization
  Platform Admin    → sees all organizations
```

This is enforced **in Power BI** (data layer) and is independent of the **App Navigation** layer (which controls which pages a user can open) and the **Subscription** layer (which controls which features the tier unlocks). Three-layer access model.

---

## 2. The 9 Power BI Pages

Each page below: **who reads it**, **what each visual shows**, **what calculation feeds it**.

(tr: Sayfa sayfa demoyu içselleştir. Müşteri "Page 6'nın V3 visual'ı ne hesaplar?" diye sorabilir. Cevabını ezberle.)

### Page 1 — Portfolio Overview
- **Reader:** Energy Manager, C-suite — "how is the portfolio doing this month?"
- **Time scope:** Last 30 days vs prior period
- **Visuals:**
  - Portfolio-level kWh consumption (bar by building)
  - kWh/m² heat map across buildings (KPI 1: EUI)
  - Total energy cost €
  - Total CO₂ emissions kg
  - Top 3 "underperforming" buildings (highest EUI relative to type benchmark)
- **Source:** `gold.kpi_daily` aggregated to portfolio level

### Page 2 — Building Deep-Dive
- **Reader:** Facility Manager — "what's my building doing right now?"
- **Time scope:** Selectable (today / week / month)
- **Visuals:**
  - 24-hour consumption profile (line chart, hourly demand kW)
  - Today's peak demand vs baseline
  - Cost-to-date this month
  - Climate-adjusted EUI for selected period
- **Source:** `gold.kpi_hourly` + `gold.kpi_daily` filtered by `building_id`

### Page 3 — Anomaly Detection
- **Reader:** Facility Manager, Energy Manager
- **Visuals:**
  - Anomaly count by severity (LOW / MEDIUM / HIGH / CRITICAL)
  - Anomaly type breakdown (consumption_spike, cop_drop, solar_underperformance, base_load_high, battery_anomaly, holiday_overconsumption, insulation_degradation)
  - Anomaly table with: timestamp, type, severity, affected system, recommended action, estimated loss €
  - Resolution status tracking (is_resolved flag)
- **Source:** `gold.anomaly_log` — 23 measures, 4 anomaly types active in production
- **Detection logic:** see Section 5

### Page 4 — Forecasting
- **Reader:** Energy Manager, Sustainability Manager — "what will next month cost?"
- **Visuals:**
  - 7/30/90-day forward consumption forecast (Prophet-based)
  - Forecast cost €
  - Forecast CO₂
  - Confidence band (in v54 backlog — not in current pbix)
- **Source:** `gold.kpi_daily` + Prophet model output. Building-type-aware thresholds (Hotel/Healthcare 130, Logistics 60, Office 35) applied to flag forecast outliers.

### Page 5 — Decision Support
- **Reader:** Energy Manager, Sustainability Manager
- **Visuals:**
  - Recommended actions ranked by priority_score
  - Estimated savings (€/year, kWh/year, CO₂ kg/year)
  - Implementation effort (LOW / MEDIUM / HIGH)
  - Payback years
  - Matching incentive programs (KfW / BAFA / YEKA / EEG / etc.)
- **Source:** `gold.recommendations` + `gold.incentive_matches`
- **Self-contained measures:** Page 5 uses 6 v54 measures designed without chain dependencies — safer in DAX

### Page 6 — Sustainability (ESG / GHG)
- **Reader:** Sustainability Manager, ESG consultant, Auditor
- **Visuals:**
  - Scope 1 / 2 / 3 donut breakdown (current month)
  - Year-over-year Scope total bar comparison
  - EPC compliance heatmap (A+ → G across buildings, area-weighted)
  - CSRD readiness flag (`csrd_ready` boolean)
  - ESG Score 0–100 (40% EUI / 30% CO₂ intensity / 20% renewable share / 10% compliance)
  - Carbon credit potential value (€)
- **Source:** `gold.sustainability_metrics` + `gold.ghg_scope`
- **Mapped to ESRS E1 disclosures:** E1-1 (transition plan), E1-5 (energy mix), E1-6 (GHG totals — both location-based and market-based), E1-9 (financial effects)
- **EPC area-weighting:** uses `LOOKUPVALUE` across building dimension to compute area-weighted portfolio compliance — not "average of building averages" (a common audit failure)

### Page 7 — HVAC & Hourly Profile
- **Reader:** Facility Manager, building owner
- **Visuals:**
  - Hourly heat-pump COP (actual vs rated)
  - Supply / return air temperature delta (HVAC efficiency proxy)
  - HVAC runtime hours per day
  - HVAC share of total consumption (was bug — fixed in v54)
  - 10-building portfolio includes B007 Copenhagen Net-Plus, B008 Leipzig Plattenbau, B009 Frankfurt DC, B010 Stockholm Lab
- **Source:** `gold.hvac_analytics` + `silver.hvac_data`

### Page 8 — Real-Time IoT Monitoring
- **Reader:** Facility Manager (operations) + Energy Manager (strategic)
- **Visuals:**
  - C1: Real-time building power (kW) with green/amber/red status vs baseline
  - C2: Zone comfort compliance % (zones within HVAC setpoint)
  - C3: CO₂ level (Good / Fair / Poor)
  - C4: Active alerts count + estimated daily €cost
  - V1: 24h power trend (building_kwh + hvac_kwh separated series, baseline reference)
  - V2: Sensor uptime matrix (rows = zones, cols = sensor_type — DYNAMIC, not hardcoded)
  - V3: Zone setpoint compliance — which zones out of range and for how long
  - V4: Alert table — location, sensor, reading, severity, action, est. €cost
- **Source:** `gold.iot_realtime` + KQL Eventhouse hot path (`iot_hot_readings`)
- **Architecture:** Event Hub → EventStream → KQL Eventhouse + Lakehouse → DAX v44
- **Sensor_type is a DIMENSION** — each building shows only its connected sensor types

#### Anomaly cost estimation on Page 8 (always shown as "Est.")
```
cost_eur = duration_hours × power_waste_kw × grid_price_eur_per_kwh

HVAC_temp violation: 2-5 kW extra per °C deviation
CO2 spike >1500ppm: 1-3 kW extra ventilation
Power spike >120% baseline: actual excess kW

Grid price: DE €0.20/kWh, TR €0.14/kWh
(building country from silver_building_master)
```

### Page 9 — Battery Dispatch & ROI
- **Reader:** Energy Manager, CFO, Investor
- **Visuals:**
  - Battery technology matrix (LFP / NCA / NMC / Solid-State × 12 countries) — 49 fitness scores
  - 7 dispatch strategies compared (self-consumption, peak shaving, arbitrage, frequency regulation, demand response, time-of-use, hybrid)
  - Country-specific electricity pricing (EPEX Spot for DE/EU, EXIST for TR, fallback to EU certified averages)
  - Investment cost €/kWh by country and chemistry
  - Payback years, NPV (5% discount, 10-year), IRR
  - EU Battery Regulation 2023/1542 compliance flag (carbon footprint, recycled content, warranty cycles, cycle durability)
- **Source:** `gold.battery_simulation` + `gold.battery_technologies` + `gold.country_regs` + `gold.strategy_fitness`
- **Data:** 12 countries × 8 chemistries × 7 strategies = 672 simulation rows, plus 49 fitness matrix scores

---

## 3. KPI Formulas Master List

Memorize the formulas. When a client asks "how do you calculate EnPI?" you should rattle the formula off without breaking eye contact.

(tr: Bunlar EnergyLens'in matematik temeli. Müşteri formülü sorduğunda kekelersen güvenini kaybedersin. Aşağıdaki formüllerin her birini ezberle ve günlük dilde açıklayabil.)

### KPI 1 — Energy Use Intensity (EUI / EnPI)

```
EUI = Total Annual Consumption (kWh) / Conditioned Area (m²)
Unit: kWh/m²/year

Climate-Adjusted EUI:
EUI_adj = EUI × (Reference HDD+CDD / Actual HDD+CDD)
```

**Why climate-adjusted?** A Berlin building burns more heating energy than an Istanbul building of identical efficiency. To compare fairly, normalize by Heating + Cooling Degree Days.

**Base temperatures (per EN ISO 15927-6):**
- HDD base = 15°C — heating required below this outdoor temp
- CDD base = 22°C — cooling required above this

**Office benchmarks:**
| Class | EUI (kWh/m²/yr) | Comparable to |
|---|---|---|
| Excellent | < 80 | LEED Platinum |
| Good | 80–130 | Above sector average |
| Average | 130–200 | Typical commercial |
| Poor | > 200 | Urgent action |

Separate sets exist for Hotel, Retail, Logistics, Hospital — see Section 9 for thresholds.

### KPI 2 — Peak Demand

```
Peak_Demand_kW = MAX(demand_kw) over the period

If battery present:
Peak_Shaved_kW = Peak_Without_Battery − Peak_With_Battery
Demand_Charge_Saving_€ = Peak_Shaved_kW × demand_charge_rate (€/kW/month)
```

Demand charges are billed on the highest 15-minute average kW — even one bad spike at 10:00 sets the bill for the whole month. Battery peak shaving directly cuts this.

### KPI 3 — Load Factor

```
Load_Factor = Average_Demand_kW / Peak_Demand_kW
Range: 0 to 1
```

- 1.0 = perfectly flat load (impossible in reality, but ideal)
- 0.3 = highly spiky — pays max demand charges, equipment short-cycles
- Office building target: > 0.70

(tr: Bina elektrik tüketiminin "ne kadar düz" olduğunu ölçer. Düşük load factor = "tarife mahkumu". Müşteri için bu **net €kaybı** demek.)

### KPI 4 — Base Load (Sleep Consumption)

```
Base_Load_kW = MIN(demand_kw) during 02:00–04:00 local time

Alert if Base_Load / Peak_Demand > 0.35
→ Equipment not entering standby properly
```

(tr: Gece 2-4 arası bina "uyuyor olmalı". Hâlâ peak'in %35'inden fazla çekiyorsa bir şey kapanmıyor demektir — server, lighting, HVAC scheduling, ısrarlı standby cihazlar.)

### KPI 5 — Solar KPIs (when `has_pv = True`)

```
Self_Consumption_Rate = self_consumed_kwh / generated_kwh
Target: > 70%
Low value → battery needed, OR load scheduling optimization needed

Self_Sufficiency_Rate = self_consumed_kwh / total_consumption_kwh
Target: 20–60% (depends on PV size relative to load)

Solar_Yield = generated_kwh / pv_capacity_kwp
Germany: 900–1050 kWh/kWp/year
Turkey: 1300–1600 kWh/kWp/year

Performance_Ratio (PR) = actual_yield / theoretical_yield
theoretical_yield = irradiance_kwh_m² × pv_capacity_kwp × 0.80
Target PR: > 0.75
Low PR → panel soiling, shading, inverter fault
```

**Important distinction** clients always confuse:
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
(operating outside this accelerates degradation)
```

### KPI 7 — Heat Pump COP (when `has_heat_pump = True`)

```
COP_actual = Heat_Energy_Produced_kWh / Electricity_Consumed_kWh

SCOP (Seasonal COP) = Total_Season_Heat_kWh / Total_Season_Electricity_kWh

COP_Performance_Ratio = COP_actual / COP_rated
< 0.80 → MEDIUM maintenance alert
< 0.60 → HIGH critical fault alert

Always compare COP at equivalent outdoor temperature bands
(COP drops naturally as outdoor temp falls)
```

(tr: COP düşüyorsa **mevsim değişti mi** önce bak. Sonra alarmı yorumla. Mert'in kodu zaten outdoor temp band karşılaştırması yapıyor.)

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
  EU ETS price 2024 range: €60 – €80/ton CO₂
```

---

## 4. Standards and Regulations

Each entry: **what it is**, **why clients care**, **what to say in a meeting**.

### EU-level frameworks

#### CSRD — Corporate Sustainability Reporting Directive
EU law in force since January 2024. Requires large EU companies to publish ESRS-compliant sustainability reports. Replaces NFRD. Penalties for non-compliance vary by member state (Germany: up to 2% of global turnover — Lieferkettengesetz precedent).

**Waves (memorize):**
- Wave 1 — Large public-interest companies, FY2024 → filed 2025
- **Wave 2 — Other large companies, FY2025 → filed 2026 (your primary market)**
- Wave 3 — Listed SMEs, FY2026 → filed 2027
- Wave 4 — Non-EU companies with EU turnover > €150M, from FY2028

#### ESRS — European Sustainability Reporting Standards
The detailed standards CSRD references. 12 topical standards total. **ESRS E1 (Climate Change)** is the most important for you.

**ESRS E1 disclosure requirements (9 total — memorize E1-1, E1-5, E1-6, E1-9):**
- E1-1 — Transition plan for climate change mitigation
- E1-5 — Energy consumption and mix
- E1-6 — Gross Scope 1, 2, 3 and total GHG emissions
- E1-9 — Anticipated financial effects of climate risks

(tr: Bu 4 kod = sayfa 6'nın direkt çıktı tablosu. Hangi visual hangi koda çıkar, ezberle.)

#### GHG Protocol Corporate Standard
The **methodology** behind Scope 1/2/3 calculations. Published by WRI + WBCSD. ESRS E1 *references* GHG Protocol but doesn't replace it.

- Scope 1 — Direct emissions from owned/controlled sources (boilers, fleet, refrigerants)
- Scope 2 — Indirect from purchased energy (electricity, steam) — must report **both** location-based and market-based starting FY2025
- Scope 3 — All other value-chain emissions (15 categories — most relevant for buildings: 1, 6, 7, 13)

#### EU Taxonomy Regulation
Classification of "environmentally sustainable" economic activities for investor reporting. Building EPC rating heavily affects taxonomy alignment — A/B typically aligned, C and below need renovation.

#### EPBD — Energy Performance of Buildings Directive
EU directive that targets nZEB (nearly zero-energy buildings) for new construction. Sets minimum energy performance standards per member state.

#### EU Battery Regulation 2023/1542
In force January 2024. All batteries sold in EU must have:
- Carbon footprint label (PEF — Product Environmental Footprint)
- Recycled content disclosure
- State of Health (SoH) percentage
- Cycle durability warranty
- Recycled content percentage

Page 9 of EnergyLens flags battery technologies that are EU-compliant via the `eu_compliant` boolean.

#### EU ETS — Emissions Trading System
EU carbon market. Used in EnergyLens to value avoided CO₂ as a "carbon credit potential." 2024 price range: €60 – €80/ton CO₂.

### Germany-specific

#### EnEfG — Energiedienstleistungsgesetz / Energy Efficiency Act
- Applies if organization has ≥ 250 employees
- Requires either **ISO 50001 certification** OR equivalent energy audit
- Mert's `gold.compliance_status` checks this against `organization.employee_count` and `building.iso50001_certified`

#### GEG — Gebäudeenergiegesetz / Building Energy Act
- For HVAC replacements from 2024 onward: **≥ 65% renewable energy source required**
- Defines minimum U-values: wall ≤ 0.24 W/m²K, roof ≤ 0.20, windows ≤ 1.30
- §71 is the renewable heating requirement most commonly cited

#### EEG — Erneuerbare-Energien-Gesetz / Renewable Energy Act
- Sets feed-in tariff rates for solar exports to grid (PV)
- Germany 2024 small commercial PV: ~€0.08/kWh feed-in

#### KfW & BAFA grant programs (referenced in `gold.incentive_matches`)
- KfW 261 / BEG — building efficiency grants (insulation, windows)
- BAFA Wärmepumpe — heat pump installation grants
- BAFA energy audit — audit cost subsidy

### Turkey-specific

#### BEP-TR — Binalarda Enerji Performansı (Building Energy Performance)
- Requires EPC certificate for buildings; renewal every 10 years
- Tracked in EnergyLens via `energy_certificate` and `energy_certificate_year`

#### EPDK — Energy Market Regulatory Authority
- Turkish energy market regulator; affects tariff structure
- Reflected in `silver.electricity_tariffs` with `country_code = 'TR'`

#### YEKA — Yenilenebilir Enerji Kaynak Alanları
- Renewable energy zone designations and PV incentive programs

### Technical / engineering standards

#### ISO 50001 — Energy Management Systems
- The framework for systematic energy management in organizations
- Defines **EnPI** (Energy Performance Indicator — same family as EUI but normalized to operational variables)
- Defines **EnB** (Energy Baseline) — the reference performance against which improvements are measured
- Certification matters legally under German EnEfG

#### EN ISO 15927-6 — Degree Day Methodology
- Defines how HDD and CDD are calculated
- EnergyLens uses base 15°C for HDD, 22°C for CDD per this standard

#### EN 16798-1 — Indoor Environmental Input Parameters
- The European standard for indoor environmental design
- Defines comfort categories (I, II, III, IV) and recommended setpoints
- 20°C heating / 24°C cooling targets in EnergyLens come from this standard

#### ASHRAE 90.1 — Energy Standard for Buildings
- US energy efficiency standard, widely cited globally including EU
- Source of "Excellent / Good / Average / Poor" EUI thresholds

#### ASHRAE 135 — BACnet protocol
- The data communication protocol for building automation
- BACnet/IP is the German market standard; EnergyLens P0-priority protocol adapter

#### IEC 61158 — Modbus protocol
- Industrial communication protocol, very widespread across EU
- EnergyLens P0-priority protocol adapter

#### ISO/IEC 20922 — MQTT 5.0
- Lightweight pub/sub messaging protocol for IoT
- EnergyLens P1-priority protocol adapter

#### OPC-UA — IEC 62541
- Industrial automation protocol, premium BMS systems
- EnergyLens P2 (Phase 2.5) protocol adapter

#### IEC 62619 — Battery Safety Standard
- Lithium-ion battery safety for industrial applications
- Referenced in battery technology specs (LFP recommendation is IEC 62619 compliant)

---

## 5. Anomaly Detection Logic

EnergyLens detects 7 distinct anomaly types. Each rule = trigger condition + severity + probable cause + recommended action.

### A1 — Consumption Spike (MEDIUM)
```
consumption_kwh(t) > rolling_avg(last 30d, same hour, same day-type) × 1.5
AND outdoor_temp_change < 5°C   (rules out weather as cause)
```
Causes: equipment fault, setpoint drift, unauthorized after-hours use.

### A2 — High Base Load / After-Hours Waste (LOW → MEDIUM)
```
base_load_kw > peak_demand_kw × 0.35
AND time between 01:00–05:00 local
```
Causes: servers, lighting, HVAC scheduling not engaging.

### A3 — COP Degradation (HIGH)
```
COP_actual < COP_rated × 0.80
AND outdoor_temp > design_temp − 3°C   (rules out cold as cause)
```
Causes: filter fouling, refrigerant leak, missed maintenance.

### A4 — Solar Underperformance (MEDIUM)
```
Performance_Ratio < 0.70
AND irradiance > 400 W/m²   (sufficient sunlight)
```
Causes: panel soiling, shading, inverter fault.

### A5 — Battery Anomaly (LOW / MEDIUM / HIGH)
- A5a — `round_trip_efficiency < 0.85` → MEDIUM (cell degradation / temperature)
- A5b — `SoC ≥ 95% continuously` → LOW (oversized capacity, schedule loads)
- A5c — `SoC < 10% repeatedly` → HIGH (over-discharge, battery life at risk)

### A6 — Weekend / Holiday Overconsumption (MEDIUM)
```
consumption(weekend or holiday) > avg_weekday_consumption × 0.60
```
Causes: HVAC not switching to holiday mode, standby loads.

### A7 — Insulation Performance Degradation (MEDIUM)
```
climate_adjusted_EUI increased > 15% vs prior year
AND weather comparable AND HVAC unchanged
```
Recommended action: schedule a Blower Door Test (air-tightness test, standard EN 13829 / ISO 9972).

---

## 6. Battery Dispatch Strategies

Two strategies are coded today; Page 9 simulates 7 hypothetically (self-consumption, peak shaving, arbitrage, frequency regulation, demand response, time-of-use, hybrid).

### Strategy A — Self-Consumption Mode

Runs every 15 minutes (Tier 2/3):
```
net_load = consumption(t) − solar_generation(t)

IF net_load < 0 (solar surplus):
  IF SoC < 90%: charge battery
  ELSE: export to grid

IF net_load > 0 (consumption > solar):
  IF SoC > 15%: discharge battery
  ELSE: import from grid

Optimization target: maximize Self_Consumption_Rate
```

### Strategy B — Peak Shaving Mode

```
peak_threshold = operator-defined (default suggestion: 90th percentile of last 12 months demand)

IF demand(t) > peak_threshold:
  discharge_power = demand(t) − peak_threshold
  IF SoC > 15%: discharge battery
  ELSE: alert (insufficient capacity)

IF demand(t) < peak_threshold × 0.50:
  Charge opportunity period
  IF SoC < 80%: charge from grid or solar
  Preference: charge during off-peak tariff hours

Optimization target: minimize peak_demand_kw → reduce demand charges
```

(tr: Müşteri "neden 15%–90% bandı?" diye sorabilir. Cevap: aşağıya inince hücre kimyası bozuluyor, yukarıya çıkınca elektrod stres yiyor. LFP için EU regülasyonu cycle durability garantisi bunu varsayar. **20%–80% optimal band** — extended lifetime için.)

---

## 7. Simulation Engines

Four simulation modules. Each takes building data + a hypothetical intervention and returns financial / carbon outcomes.

### S1 — Add PV Solar

```
Inputs:
  pv_capacity_kwp (user input or auto-suggested from roof_area_m²)
  Auto-suggest: max_kwp = roof_area_m² / 7   (1 kWp ≈ 7 m² panel area)

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
  Germany 2024: 1,000–1,400 €/kWp (range displayed, not point estimate)
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
  existing_cost = heating_kwh / boiler_efficiency × gas_price_€_kwh
  (default boiler efficiency: 0.90 for modern condensing boiler)

Heat pump cost:
  hp_electricity = heating_kwh / cop_rated
  hp_cost = hp_electricity × electricity_price_€_kwh

Saving = existing_cost − hp_cost
CO2_reduction = existing_co2 − (hp_electricity × emission_factor)

Germany GEG compliance note:
  Heat pump auto-satisfies 65% renewable requirement
  → Flag applicable KfW/BAFA Wärmepumpe incentives
```

### S4 — Insulation Upgrade

```
Heat loss reduction:
  Q_saved = ΔU × surface_area × HDD × 24 / 1000

  where ΔU = current_u_value − target_u_value (in W/m²K)

Cost assumptions (Germany 2024):
  Wall insulation (100mm EPS):     80–120 €/m²
  Roof insulation (mineral wool):  60–100 €/m²
  Triple glazing windows:         400–700 €/m²

Match KfW BEG / KfW 261 grants: typically 15–20% of investment
```

---

## 8. Data Model

### Bronze layer — raw, as ingested

Tables: `raw_energy_readings`, `raw_solar_generation`, `raw_battery_status`, `raw_weather_data`, `raw_hvac_data`. All store `building_id`, raw values, source system, timestamps, ingestion timestamps. Partitioned by `building_id / year / month / day`. Delta Lake format.

### Silver layer — cleaned, validated

#### silver.building_master (the spine of the data model)

Has every dimension column that drives logic gating:
- Identity: `building_id`, `organization_id`, `building_name`
- Geography: `country_code`, `city`, `climate_zone` (Köppen — Cfb, BSk, etc.)
- Area: `gross_floor_area_m²`, `conditioned_area_m²`
- Type: `building_type` (Office / Retail / Hotel / Logistics)
- Subscription: `subscription_tier` (Insight / Monitor / Copilot)
- Technology flags: `has_pv`, `has_battery`, `has_heat_pump`, `has_hvac_traditional`, `has_ev_charging`, `has_led_lighting`
- PV details: `pv_capacity_kwp`, `roof_area_m²`, `roof_orientation`, `roof_tilt_deg`
- Battery details: `battery_capacity_kwh`, `battery_technology`, `battery_strategy`
- Heat pump: `heat_pump_cop_rated`, `heat_pump_capacity_kw`
- Envelope: `wall_u_value`, `roof_u_value`, `floor_u_value`, `window_u_value`, `window_to_wall_ratio`, `air_tightness_ach`, `thermal_mass_level`, `insulation_year`
- Compliance: `energy_certificate` (A+ → G), `iso50001_certified`, `regulatory_profile_id`

#### Other silver tables
- `energy_readings_clean` — kWh, demand_kw, quality_flag, interpolated
- `solar_generation_clean` — generated, exported, self_consumed, irradiance
- `battery_status_clean` — SoC, charge_kw, discharge_kw, cycle_count, active_strategy
- `weather_clean` — temperature, humidity, irradiance, HDD, CDD
- `grid_emission_factors` — country × year × emission_factor
- `electricity_tariffs` — peak / off-peak / demand charge / feed-in tariff per country
- `incentive_programs` — KfW / BAFA / YEKA / etc.
- `regulatory_rules` — EnEfG / GEG / EPBD / BEP-TR

### Gold layer — business-ready

- `kpi_hourly` — primary Tier 2/3 fact table
- `kpi_daily` — primary Tier 1 fact table (32 columns covering Core KPIs / Solar / Battery / Heat Pump / Cost / Carbon / Climate)
- `kpi_monthly` — ESG reporting + billing analysis
- `anomaly_log` — type, severity, affected_system, descriptions (EN/DE/TR), probable_cause, action, estimated_loss, acknowledged, resolved
- `sustainability_metrics` — CO₂ in / out / net, vs baseline, carbon credit value, ESG score, csrd_ready flag
- `ghg_scope` — Scope 1/2/3 breakdown with ESRS E1 mapping
- `compliance_status` — rule_id × building_id × compliant + gap description + action + deadline + priority
- `incentive_matches` — auto-matched grant programs per building
- `recommendations` — type, system, savings, payback, effort, priority_score, applicable_incentives
- `simulation_add_pv`, `simulation_add_battery`, `simulation_switch_hvac`, `simulation_add_insulation`, `simulation_window_upgrade`, `simulation_battery_strategy`
- `iot_realtime`, `iot_hot_readings` — Page 8 (KQL Eventhouse hot path)
- `hvac_analytics` — Page 7
- `battery_simulation`, `battery_technologies`, `country_regs`, `strategy_fitness` — Page 9
- `data_health_log` — data freshness, quality rate, dead sensor detection, overall health

---

## 9. Stated Assumptions

These assumptions are explicitly documented so they can be challenged and updated. If a client asks "why 5%?" you point to this list.

### Data
- Minimum resolution Tier 1: hourly | Tier 2/3: 15-minute
- HDD base 15°C, CDD base 22°C — per EN ISO 15927-6
- Missing data interpolated up to 2 consecutive hours; beyond that flagged MISSING

### Grid emission factors
- Germany 2024: 0.380 kg CO₂/kWh (UBA — Umweltbundesamt)
- Turkey 2024: 0.442 kg CO₂/kWh (TEİAŞ)
- Reviewed and updated annually

### Solar PV
- Default Performance Ratio: 0.80 (industry standard for well-maintained systems)
- 7 m² roof area per kWp (assumes 400W panels, 1.7 m² each)
- Default orientation: South (180°); default tilt: 30° (Germany), 25° (Turkey)
- NPV discount rate: 5%; analysis period: 10 years
- Germany cost: €1,000–1,400/kWp; Turkey cost: $600–900/kWp
- Panel lifetime: 25 years (warranty)

### Battery
- Recommended technology: LFP (LiFePO₄) — best safety/cost/lifetime balance
- Cost: €600–900/kWh (2024 EU market, installed)
- Round-trip efficiency: 0.92 (LFP at room temp)
- Cycle life: 4,000 cycles (warranty); system lifetime: 15 years
- Operating SoC band: 15%–90% mandatory, 20%–80% optimal
- Carbon credit valuation: EU ETS €60–80/ton CO₂

### Heat Pump
- Gas boiler baseline efficiency: 0.90 (modern condensing)
- COP performance alert threshold: 80% of rated
- Critical alert threshold: 60% of rated
- COP comparison temperature band: ±3°C of design

### HVAC
- Heating setpoint: 20°C (EN 16798-1)
- Cooling setpoint: 24°C
- ~6% excess energy per °C deviation
- Preheat: 6 min per °C difference (simplified — actual varies by thermal mass)
- Winter unoccupied setback: 16°C (frost protection)
- Summer unoccupied setback: 28°C

### Building benchmarks (Office — separate sets for other types)
| Class | EUI (kWh/m²/yr) | Source |
|---|---|---|
| Excellent | < 80 | ASHRAE 90.1 + EU Building Stock Observatory |
| Good | 80–130 | |
| Average | 130–200 | |
| Poor | > 200 | |

### Building-type aware thresholds (DAX patterns)
- Hotel / Healthcare: 130 kWh/m²/yr threshold
- Logistics: 60 kWh/m²/yr
- Office (default): 35 kWh/m²/yr (a conservative threshold tied to specific monitoring KPI)

### Financial
- Electricity price (commercial): Germany ~€0.22/kWh, Turkey ~€0.08/kWh (2024)
- Gas price (Germany): ~€0.07/kWh (2024)
- Feed-in tariff PV (Germany small commercial): ~€0.08/kWh (EEG 2024)

### Regulatory
- Static reference tables, manually reviewed annually
- EnEfG: ≥250 employees → ISO 50001 or equivalent audit required
- GEG: from 2024, new/replacement heating must use ≥65% renewable
- CSRD: Phase 1 threshold ≥500 employees (Wave 2 main market)

### What we explicitly DO NOT assume
- That sensor data is always accurate (quality flags handle this)
- That energy prices are fixed (tariff table per-tenant)
- That all buildings have all technologies (tech profile gates modules)
- That roof characteristics are always known (PV sims note when estimates used)
- That regulatory compliance is binary (gap analysis provides gradations)

---

## 10. Glossary

Quick reference for every term used in the project. When a client throws jargon at you, look it up here in 5 seconds.

**ABFS** — Azure Blob File System; storage path scheme used by Fabric Lakehouse.

**Activator (Reflex)** — Microsoft Fabric's rule-based alert engine.

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

**ESRS E1** — The climate-change standard within ESRS. 9 disclosure requirements (DR), E1-1 to E1-9.

**EU ETS** — EU Emissions Trading System. Carbon market with current pricing €60–80/ton CO₂ (2024).

**EU Taxonomy** — Classification of "environmentally sustainable" economic activities for investor reporting.

**EU 2023/1542** — EU Battery Regulation. Requires carbon footprint label, recycled content disclosure, warranty cycles for batteries sold in EU after Jan 2024.

**EUI — Energy Use Intensity** — kWh/m²/year. Primary efficiency KPI.

**EventStream** — Microsoft Fabric real-time data ingestion service.

**Eventhouse / KQL** — Fabric's real-time analytics database, queried with Kusto Query Language (KQL).

**EXIST** — Energy Exchange Istanbul. Turkish day-ahead electricity pricing reference.

**Fabric (Microsoft Fabric)** — Microsoft's unified analytics platform. GA May 2024. Combines data engineering, warehousing, real-time analytics, data science, Power BI on a single SaaS foundation.

**Feed-in Tariff** — Per-kWh price utility pays for grid-exported energy (e.g., from PV).

**GEG — Gebäudeenergiegesetz** — German Building Energy Act. Defines minimum U-values and §71 65% renewable heating requirement.

**GHG Protocol** — World Resources Institute / WBCSD methodology defining Scope 1/2/3 emissions calculation.

**Gold layer** — Medallion architecture tier for business-ready, aggregated data — what Power BI directly reads.

**HDD — Heating Degree Days** — Sum over period of `MAX(0, HDD_base − daily_avg_temp)`. Base 15°C in EnergyLens.

**IEC 61158** — Modbus communication protocol standard.

**IEC 62619** — Lithium-ion battery safety standard for industrial applications.

**Insulation U-Value** — Heat-transfer coefficient through a building element. Lower = better insulation. Units: W/m²K.

**IoT — Internet of Things** — Network of physical sensors/devices reporting data to centralized systems.

**IRR — Internal Rate of Return** — Discount rate at which NPV equals zero. Used to compare investment alternatives.

**ISO 50001** — International standard for Energy Management Systems. Defines EnPI and EnB. Required under German EnEfG for large organizations.

**ISO/IEC 20922** — MQTT 5.0 protocol standard.

**KfW** — Kreditanstalt für Wiederaufbau (German state development bank). Runs efficiency grant programs (KfW 261, BEG).

**KPI — Key Performance Indicator** — Any measurable value used to track performance.

**KQL — Kusto Query Language** — Microsoft's query language for time-series and log analytics.

**Lakehouse** — Storage paradigm combining data lake flexibility with warehouse structure. Fabric's Lakehouse uses Delta Lake format on OneLake.

**LFP — Lithium Iron Phosphate (LiFePO₄)** — Battery chemistry. Recommended in EnergyLens for commercial buildings: best safety/cost/lifetime balance.

**Load Factor** — Average demand ÷ peak demand (0 to 1). Higher = flatter, more efficient consumption.

**Location-based Scope 2** — Method: use country grid average emission factor. Mandatory for ESRS E1-6.

**Market-based Scope 2** — Method: use supplier-specific emission factor (e.g., green certificates). Also mandatory for ESRS E1-6.

**Medallion Architecture** — Bronze (raw) → Silver (cleaned) → Gold (business-ready) tier model. Microsoft Fabric standard.

**Modbus TCP** — Industrial communication protocol over Ethernet. Widespread in EU. Standard: IEC 61158.

**MQTT 5.0** — Lightweight pub/sub IoT messaging protocol. Standard: ISO/IEC 20922.

**NMC — Nickel Manganese Cobalt** — Battery chemistry. More energy-dense than LFP but lower cycle life. Common in Turkey market.

**NPV — Net Present Value** — Future cash flows discounted to present value. EnergyLens uses 5% discount rate, 10-year horizon.

**nZEB — Nearly Zero-Energy Building** — EPBD target for new buildings.

**OneLake** — Microsoft Fabric's unified data lake — single logical lake across the entire organization.

**OPC-UA** — Open Platform Communications Unified Architecture (IEC 62541). Premium industrial protocol; EnergyLens Phase 2.5 priority.

**PEF — Product Environmental Footprint** — EU methodology for carbon footprint labeling of products (referenced by EU Battery Regulation).

**Performance Ratio (PR)** — actual PV yield ÷ theoretical PV yield. Target > 0.75. Industry default assumption: 0.80.

**PPU — Power BI Premium Per User** — Per-user Power BI Premium license. Allows Premium features without buying full capacity.

**Power BI Embedded** — Embedding Power BI reports in custom applications. Two flavors: user-owns-data (per-user license) and app-owns-data (service principal — no end-user licenses).

**Prophet** — Time-series forecasting library by Meta. Used for Page 4 consumption forecasts.

**RLS — Row-Level Security** — Power BI feature restricting data visibility per user role. EnergyLens uses RLS on `building_id`.

**Round-trip Efficiency** — Battery: kWh discharged ÷ kWh charged. Target > 0.90 for LFP.

**Scope 1** — Direct GHG emissions from owned/controlled sources.

**Scope 2** — Indirect emissions from purchased electricity/heat. Report both location-based and market-based.

**Scope 3** — All other value-chain GHG emissions. 15 categories.

**SCOP — Seasonal COP** — COP averaged over a heating season.

**Self-Consumption Rate** — Of generated PV energy, percentage used on-site. Target > 70%.

**Self-Sufficiency Rate** — Of total consumption, percentage supplied by own PV. 20–60% typical.

**Semantic Model** — Power BI's modeling layer. Contains tables, relationships, measures, calculated columns.

**SoC — State of Charge** — Battery charge level 0–100%.

**SoH — State of Health** — Battery capacity vs nominal (declines with age). Required disclosure under EU 2023/1542.

**TEİAŞ** — Türkiye Elektrik İletim A.Ş. Turkish grid operator. Source of TR emission factor.

**Tier 1 / 2 / 3** — Subscription tiers in EnergyLens. Insight (batch) / Monitor (near-real-time) / Copilot (full intelligence).

**UBA — Umweltbundesamt** — German Federal Environment Agency. Source of DE emission factor.

**U-Value** — Heat-transfer coefficient (W/m²K). Building element insulation quality. Lower = better.

**Window-to-Wall Ratio (WWR)** — Window area ÷ exterior wall area. Affects heat loss and daylighting.

**YEKA** — Yenilenebilir Enerji Kaynak Alanları (Turkish renewable energy zone designations).

---

## Closing notes

This document covers everything Mert needs to walk into any CSRD/ESG / Microsoft Fabric / energy analytics client meeting and answer questions about EnergyLens without hesitation. Read sections 1, 2, 4, and 10 first — those carry the most weight in calls.

When the project changes (DAX bumped to v57, new pages added, new countries supported), this file should be updated alongside `docs/business-logic/kpi-formulas.md`, `docs/architecture/architecture-overview.md`, and `docs/data-model/data-dictionary.md`. Those are the source-of-truth files; this one is the meeting-ready synthesis.
