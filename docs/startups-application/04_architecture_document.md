# EnergyLens — Architecture Document

**Microsoft Fabric-native energy intelligence platform for commercial buildings**

---

## 1. Architecture Overview

EnergyLens is built **end-to-end on the Microsoft cloud stack**, with **Microsoft Fabric** as the central data and analytics fabric.

```
┌─────────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                                    │
│  Smart meters · BACnet · Modbus · MQTT · OPC-UA · Weather APIs  │
│  EPEX Spot · CRREM pathways · Manual CSV uploads                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  INGESTION LAYER                                                 │
│  ┌─────────────────────┐  ┌─────────────────────────┐          │
│  │ Fabric Data Factory │  │ Fabric Eventstream      │          │
│  │ (Tier 1: Batch)     │  │ (Tier 2-3: Streaming)   │          │
│  └─────────────────────┘  └─────────────────────────┘          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAKEHOUSE (Medallion Architecture)                              │
│  ┌─────────┐    ┌─────────┐    ┌──────────────────────────┐    │
│  │ BRONZE  │ →  │ SILVER  │ →  │ GOLD                     │    │
│  │ Raw     │    │ Clean   │    │ KPI / Analytics / Models │    │
│  └─────────┘    └─────────┘    └──────────────────────────┘    │
│                                                                  │
│  Bronze: 25+ tables (raw_*, bronze_iot_raw)                     │
│  Silver: 5 cleaned tables (energy, solar, battery, weather, BM) │
│  Gold:   15+ analytics tables (KPI, anomaly, GHG, CRREM, ...)   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ANALYTICS & ML                                                  │
│  ┌──────────────────────┐  ┌────────────────────────────┐      │
│  │ KQL Eventhouse       │  │ Fabric Notebooks (PySpark) │      │
│  │ (Real-time analytics)│  │ (ML, anomaly, forecasting) │      │
│  └──────────────────────┘  └────────────────────────────┘      │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  SEMANTIC LAYER                                                  │
│  Power BI Semantic Model (DirectLake)                            │
│  · 50+ DAX measures · RLS · Date/Time intelligence              │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTATION                                                    │
│  ┌──────────────────┐  ┌───────────────────────────────┐       │
│  │ Power BI         │  │ Next.js Web App (planned)     │       │
│  │ Reports (9 pgs)  │  │ Embedded reports + custom UI  │       │
│  └──────────────────┘  └───────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 Ingestion Layer

| Component | Used For | Tier |
|---|---|---|
| **Fabric Data Factory** | Batch ingestion from APIs, CSV uploads, smart meter exports | All tiers |
| **Fabric Eventstream** | Real-time IoT sensor data (BACnet/Modbus/MQTT) | Tier 2, Tier 3 |
| **Custom Python adapters** | Protocol normalization (BACnet/IP, Modbus TCP, MQTT 5.0, OPC-UA) | Tier 2, Tier 3 |

**Tier-aware design:** Batch for Insight tier, streaming for Monitor/Copilot tiers.

### 2.2 Lakehouse — Medallion Architecture

#### Bronze Layer (Raw)
Append-only landing zone for source data, **incremental loading with watermark tracking**:
- `bronze_raw_energy_readings` — 15-min interval kWh per building
- `bronze_raw_solar_generation` — PV inverter data
- `bronze_raw_battery_status` — SoC, charge/discharge events
- `bronze_raw_weather_data` — Temperature, humidity, irradiance, wind
- `bronze_building_master` — Reference table (overwrite mode)
- `bronze_iot_raw` — Streaming IoT sensor data (partitioned by building_id, event_date)
- `bronze_watermarks` — Per-(table, building) incremental tracking

#### Silver Layer (Cleaned)
Type-safe, validated, deduplicated data:
- `silver_energy_readings_clean` — Unit-normalized kWh, anomaly-flagged
- `silver_solar_generation_clean`
- `silver_battery_status_clean`
- `silver_weather_clean`
- `silver_building_master` — Joined with regulatory profile, climate zone
- `silver_iot_normalized` — Standardized sensor units (°C, %, ppm, kW, kWh)

#### Gold Layer (Analytics)
Pre-aggregated, business-ready:
- `gold_kpi_daily` — Per-building daily KPIs (consumption, EUI, cost, carbon)
- `gold_kpi_monthly` — Monthly rollups with YoY comparisons
- `gold_kpi_hourly` — Hourly granularity for trend analysis
- `gold_anomaly_log` — Detected anomalies with severity, action, € impact
- `gold_ghg_scope` — Scope 1/2 carbon accounting per building
- `gold_crrem_pathway` — Building × country × year stranding analysis
- `gold_hvac_analytics` — HVAC technology, COP, retrofit priority
- `gold_compliance_results` — EU regulatory scorecards (EnEfG, GEG, EPC, etc.)
- `gold_consumption_forecast` — ML-driven 30-day forecast
- `gold_occupancy_profile` — Occupancy pattern detection
- `gold_battery_dispatch` — Daily battery simulation results
- `gold_battery_simulation` — Strategy scenarios (self-consumption, peak-shaving, TOU, backup)
- `gold_battery_hourly_profile` — 4 strategies × 24 hours pattern templates
- `gold_battery_hourly_dispatch` — Per-building hourly dispatch (production)
- `gold_battery_technologies` — Battery product catalog with EU 2023/1670 compliance
- `gold_iot_realtime` — IoT KPIs for Page 8 dashboard
- `gold_iot_daily_summary` — Daily IoT aggregates
- `gold_recommendations` — AI-generated retrofit + operational recommendations

### 2.3 Analytics & ML

| Engine | Workload | Examples |
|---|---|---|
| **PySpark Notebooks** | Batch transformations, ML training | Anomaly detection, consumption forecasting, occupancy prediction |
| **KQL Eventhouse** | Real-time IoT analytics | Sensor uptime, zone compliance, live alerts |
| **Spark MLlib** | Pattern recognition | Heat pump fault detection, baseline drift |
| **Statistical methods** | Time-series modeling | Prophet-style decomposition, anomaly scoring |

### 2.4 Semantic Layer (Power BI)

- **Mode:** DirectLake (no data duplication, queries Delta files directly)
- **Tables:** 20+ (gold tables + date/dim tables)
- **Measures:** 50+ DAX measures with v52 versioning
- **RLS:** Building-level row-level security via `building_id` filtering
- **Date intelligence:** YearMonth sort-by-MonthIndex, PY/MoM/WoW comparisons
- **Refresh:** Automatic via DirectLake, no scheduled refresh needed

### 2.5 Presentation Layer

#### Power BI Reports (9 pages)
1. **Portfolio Overview** — Multi-building KPI scorecard, EUI benchmark
2. **Building-Level Detail** — Drill-down per building, time-series trends
3. **Anomalies & Alerts** — Severity heatmap, cost impact, action recommendations
4. **Forecast & Recommendations** — 30-day forecast, retrofit prioritization
5. **Occupancy Analysis** — Pattern detection, sensor utilization
6. **Sustainability & Compliance** — CRREM stranding, EPC distribution, regulatory status
7. **HVAC & Building Envelope** — System efficiency, COP monitoring, retrofit ROI
8. **IoT Real-Time Monitoring** — Live power, zone comfort, sensor uptime (Tier 2-3)
9. **Battery Strategy** — Dispatch simulation, scenario comparison, EU compliance

#### Web App (Next.js + FastAPI — planned Q3 2026)
- **Frontend:** Next.js on Azure Static Web Apps
- **Backend:** FastAPI on Azure Container Apps
- **Database:** Azure PostgreSQL (user mgmt, subscription state, custom dashboards)
- **Embedded Power BI:** User-owns-data or Premium capacity embedding

---

## 3. Access Control Architecture (3-layer model)

```
Layer 1 — Power BI RLS (DATA layer)
  → Controls: which buildings/data a user sees
  → "Customer A sees only their 3 buildings, not others"

Layer 2 — Web App Navigation (MODULE layer) [Next.js]
  → Controls: which pages/modules are accessible
  → "Customer has no IoT → Page 8 hidden"
  → "Customer has no battery → Page 9 locked"

Layer 3 — Subscription Tier (COMMERCIAL layer) [PostgreSQL + FastAPI]
  → Controls: feature gates based on plan
  → Insight / Monitor / Copilot
```

**Practical examples:**
- Customer A (3 buildings, energy meters only) → Pages 1-7 active, 8-9 locked
- Customer B (1 building, energy + IoT, no battery) → Pages 1-8 active, 9 locked
- Customer C (6 buildings, full package) → All 9 pages active

RLS is always active regardless of tier — data never crosses customer boundaries.

---

## 4. Phase 2 — Production-Grade Components

### 4.1 IoT Adapter Framework

Protocol adapter pattern supporting:

| Protocol | Priority | Standard | Use case |
|---|---|---|---|
| BACnet/IP | P0 | ASHRAE 135 | Germany BMS standard |
| Modbus TCP | P0 | IEC 61158 | Widespread EU industrial |
| MQTT 5.0 | P1 | ISO/IEC 20922 | Emerging, scalable IoT |
| REST API | P1 | HTTP/JSON | Catch-all (cloud sensors) |
| OPC-UA | P2 | IEC 62541 | Premium automation |

Each adapter normalizes to standard units (°C, %, ppm, kW, kWh) and writes to `silver_iot_normalized`.

### 4.2 Dynamic Electricity Pricing

Real-time electricity prices from regional APIs:
- **Germany + EU:** EPEX Spot (hourly day-ahead)
- **Turkey:** EXIST (daily, if API available)
- **Fallback:** EU-certified typical prices (2026 rates)

Stored in `gold_electricity_pricing` (date, country, hour, price, source, CO2 intensity).

### 4.3 EU Battery Regulation Compliance

EU 2023/1670 mandates for batteries sold after Jan 2024:
- Carbon footprint label (Product Environmental Footprint)
- State of Health %
- Cycle durability warranty
- Recycled content disclosure

EnergyLens tracks via `gold_battery_technologies` with regional approval flags (DE, AT, FR, EU_avg).

---

## 5. Deployment Architecture

### Infrastructure (post-launch)
| Component | Service | Monthly cost (est.) |
|---|---|---|
| **Frontend** | Azure Static Web Apps | €0-20 |
| **Backend API** | Azure Container Apps | €10-30 |
| **Database** | Azure PostgreSQL Flexible | €15-30 |
| **Embedded Power BI** | Premium capacity (P1) | €0 (Startups credit) or €32 |
| **Fabric capacity** | F4-F8 | €0 (Startups credit) or €100-400 |
| **Total** | | **€25-510/month** |

### Multi-tenant strategy
- **Shared Fabric Lakehouse:** All customers in same Lakehouse, separated by `organization_id` partition
- **Shared Power BI Semantic Model:** RLS enforces organization boundary
- **Per-customer workspace (Enterprise):** Optional white-label deployment for large REITs

---

## 6. Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| Data Lake | Microsoft Fabric Lakehouse (Delta) | Cost-effective, no movement, OneLake catalog |
| ETL | PySpark Notebooks | Native, scalable, ML-ready |
| Streaming | Fabric Eventstream + KQL Eventhouse | Sub-second latency for IoT |
| Analytics | Power BI Premium (DirectLake) | No data duplication, fast queries |
| AI/ML | Spark MLlib + Azure OpenAI | Pattern detection + natural language insights |
| App Frontend | Next.js 14 (App Router) | Modern React, SSR, edge runtime |
| App Backend | FastAPI (Python) | Async, type-safe, integrates with Fabric SDK |
| Database | Azure PostgreSQL Flexible | Multi-tenant friendly, JSON support |
| Auth | Microsoft Entra ID + Azure AD B2C | Enterprise SSO + customer accounts |
| Monitoring | Azure Application Insights | End-to-end telemetry |

**100% Microsoft stack** — enables Microsoft Partner Network co-selling opportunities.

---

## 7. Why Microsoft Fabric (vs. alternatives)

| Concern | Alternative | Fabric advantage |
|---|---|---|
| Cost | AWS Redshift + S3 + Glue | OneLake = no movement charges |
| Skills | Databricks + Snowflake hybrid | One platform, one skill set |
| Microsoft alignment | Standalone tools | Strategic Microsoft partner positioning |
| Power BI integration | Manual semantic model build | DirectLake = zero refresh time |
| Time to market | Build custom pipeline | Pre-built medallion templates |

**Strategic bet:** Fabric is Microsoft's flagship data platform for 2024-2030. Energy/CRE vertical is currently underserved on Fabric → first-mover advantage.

---

## 8. Roadmap Alignment

| Quarter | Architectural milestone |
|---|---|
| Q2 2026 | MVP (9 pages, batch ingestion, sample data) ✅ |
| Q3 2026 | First pilot (BSBI campus), real data, web app skeleton |
| Q4 2026 | IoT adapters (BACnet/Modbus), 3-5 paying pilots |
| Q1 2027 | AI recommendations (Azure OpenAI), MQTT streaming |
| Q2 2027 | OPC-UA premium tier, white-label deployment option |
| Q4 2027 | 50+ buildings, F16 capacity, partner network |

---

*Document version 1.0 — May 2026*
*Author: Ali Mert Özdemir, Founder*
