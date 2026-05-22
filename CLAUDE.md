This project is a professional Energy Copilot Platform for Commercial Buildings.

GOAL:
Build a real energy intelligence and decision-support system using Microsoft Fabric.

WORKING APPROACH:
- Follow BMAD methodology:
  Business → Architecture → Data → Logic → Implementation
- Work step by step
- Do NOT implement everything at once
- Always explain decisions before implementing

MY ROLE:
- Product owner
- Energy domain reviewer
- I must approve important assumptions (especially energy logic)

YOUR ROLE:
- Act as a senior technical copilot
- Help design architecture, data model, and logic
- Explain Microsoft Fabric concepts clearly (DP-600 mindset)
- Ask for approval before major decisions

ENERGY LOGIC RULES:
- Do NOT invent unrealistic engineering logic
- Always state assumptions
- Prefer ranges instead of exact values
- Explain why recommendations are valid

FABRIC PRINCIPLES:
- Use medallion architecture (Bronze / Silver / Gold)
- Separate ingestion, transformation, and business logic
- Design clean and explainable data models

PROJECT STRUCTURE GOAL:
- GitHub-ready professional repository
- Clear documentation (README, architecture, data model, logic)
- Modular structure

IMPORTANT:
- Focus on one module at a time
- Do not jump ahead
- Do not overwrite previous design decisions without asking
- Teach me while building

---

## PHASE 2 ARCHITECTURE (Production-Grade Design, Day 1)

**Strategic Decision (2026-05-07):** Build Phase 2 = production-grade, not MVP.

### Why?
- MVP approach: rework when customer needs interoperability
- Production approach: ready to sell immediately
- Energy domain requires compliance (EU Battery Regulation, electrical standards)
- Same upfront design effort, saves rework later

### Three Pillars

#### 1. IoT Data Ingestion (Full Interoperability)

**Supported Protocols (Priority Order):**
- **P0:** BACnet/IP (ASHRAE 135 — Germany standard), Modbus TCP (IEC 61158 — widespread EU)
- **P1:** MQTT 5.0 (ISO/IEC 20922 — emerging, scalable), REST API (HTTP/JSON — catch-all)
- **P2:** OPC-UA (Phase 2.5 — premium automation)

**Architecture:** Protocol adapter pattern (Python classes)
```
bronze_iot_raw (protocol-native) 
  → silver_iot_normalized (standardized schema)
  → gold_iot_realtime (business logic)
```

Each protocol gets an adapter class that normalizes to standard units (°C, %, ppm, kW, kWh).

**Notebook:** `00_iot_adapter_framework.py` + `01_bronze_iot_ingestion.py`

#### 2. Dynamic Electricity Pricing (Regional APIs)

**Data Sources:**
- Germany + EU (EPEX Spot public REST API — hourly, day-ahead)
- Turkey (EXIST — daily, if API available)
- Fallback: EU-certified typical prices (2026 market rates)

**Architecture:**
```
gold_electricity_pricing (by date, country, hour)
  ├─ source (EPEX_SPOT, EXIST, FALLBACK_AVG)
  ├─ price_eur_per_mwh
  ├─ is_forecast (boolean)
  ├─ co2_intensity_g_per_kwh (grid carbon intensity)
  └─ last_updated_timestamp
```

**Notebook:** `00_fetch_electricity_prices.py` (scheduled daily @ 14:30 UTC)

**Impact on Page 9:** Battery dispatch ROI calculations use real prices, not static estimates.

#### 3. EU Battery Regulation (2023/1670 Compliance)

**Requirement:** All batteries sold in EU (Jan 2024+) must have:
- Carbon footprint label (Product Environmental Footprint, PEF)
- State of Health percentage
- Cycle durability warranty
- Recycled content disclosure

**Architecture:**
```
gold_battery_technologies (battery specs + EU compliance)
  ├─ battery_type (LFP, NCA, NMC, Solid-State)
  ├─ manufacturer (CATL, BYD, Panasonic, Tesla)
  ├─ regions_approved (DE, AT, FR, EU_avg)
  ├─ carbon_footprint_kg_co2_per_kwh (EU label)
  ├─ recycled_content_percent
  ├─ warranty_cycles
  ├─ eu_compliant (boolean — 2023/1670 check)
  └─ last_updated_date (when specs verified)
```

**Regional Strategy:**
- **Tier 1 (Primary):** Germany (EPEX pricing, LFP premium market, €140-180/kWh)
- **Tier 2 (Secondary):** EU-wide (regional averages, slight cost reduction)
- **Tier 3 (Fallback):** Turkey + SE Europe (NMC more common, EXIST pricing)

**Impact on Page 9:** Scenarios include only EU-compliant batteries, realistic regional pricing.

---

## PHASE 0: INFRASTRUCTURE & CAPACITY STRATEGY (2026-05-07)

### Trial Period (Days 1-14 from 2026-05-07)
**CRITICAL DEADLINE: 2026-05-21**

#### What MUST Complete Before Trial Ends:
1. ✅ All 9 Pages (1-7 complete, 8-9 design + DAX)
2. ✅ All gold tables (IoT, Battery schema finalized)
3. ✅ Fabric pipeline validated (01_bronze → 02_silver → 03_gold → Page 8-9)
4. ✅ Power BI measures (v42 + v43-v50 for Pages 8-9)
5. ✅ Microsoft for Startups application SUBMITTED
6. ✅ Backup: export all .pbix, notebooks, python scripts
7. ✅ Documentation: architecture, data model, DAX guide (GitHub-ready)

#### What Happens After Trial:
- **Notebooks:** STOP (compute = €0/month)
- **Lakehouse:** READ-ONLY, storage only (€5-15/month)
- **Power BI Premium:** STARTUP CREDITS (goal: €0) OR €32/month P1
- **App:** Embedded via user-owns-data OR Startup capacity

### Cost & Capacity Model

**Scenario A: Startup Credits Win** (Target)
- Premium capacity: $150k Azure credits (36 months)
- Power BI: 12 months free
- Embedded reports: UNLIMITED
- Monthly cost: €0
- Status: BEST CASE

**Scenario B: Self-funded P1** (Fallback)
- Premium capacity P1: €32/month
- Embedded reports: 20-25 concurrent users
- Monthly cost: €32
- Status: SUSTAINABLE

**Scenario C: Per-Capacity (Avoid)**
- Azure hourly billing: €1.26/hour
- Monthly equivalent: €920/month
- Status: TOO EXPENSIVE (use only for short demos)

### Embedded Report Management
- **Report** = locked, version-controlled template (read-only for embedded users)
- **UI changes** = App layer (custom filters, custom dashboards, custom charts)
- **Report changes** = Power BI Desktop → publish → auto-refresh embedded view
- **No real-time customization** in embedded view (design time only)

### Application Deployment Strategy
- **Frontend:** Next.js on Azure Static Web Apps (€0-20/month)
- **Backend:** FastAPI on Azure Container Apps (€10-30/month)
- **Database:** Azure PostgreSQL (€15-30/month)
- **Embedded Power BI:** Premium capacity (€0 or €32/month)
- **Total monthly minimum:** €25-80/month (excluding capacity)

---

## APP ARCHITECTURE: ACCESS CONTROL & MODULE VISIBILITY (2026-05-07)

### Three-Layer Access Model (CONFIRMED DECISION)

```
Layer 1 — Power BI RLS (DATA layer)
  → Controls: which buildings/data a user sees
  → "Customer A sees only their 3 buildings, not others"
  → Already designed in 03_rls_definition.md
  → CANNOT control page visibility — Power BI technical limitation

Layer 2 — Web App Navigation (MODULE layer)  [Next.js]
  → Controls: which pages/modules are accessible
  → Reads: user subscription + connected sensor inventory from DB
  → "Customer has no IoT sensors → Page 8 greyed out / hidden"
  → "Customer has no battery → Page 9 locked"
  → This is how enterprise BMS products work (Siemens Desigo, Schneider EcoStruxure)

Layer 3 — Subscription/Tier (COMMERCIAL layer)  [PostgreSQL + FastAPI]
  → Controls: feature gates based on plan
  → Future: could restrict historical depth, export, AI features
```

### Practical Module Access Examples
```
Customer A: 3 buildings, energy meters only, no IoT, no battery
→ Pages 1-7 active | Page 8 LOCKED | Page 9 LOCKED

Customer B: 1 building, energy + IoT sensors, no battery
→ Pages 1-8 active | Page 9 LOCKED

Customer C: 6 buildings, full package (energy + IoT + battery)
→ All 9 pages active
```
RLS always active regardless of tier — data never crosses customer boundaries.

### Data Isolation Between Pages
- Pages 1-7: `gold_kpi_daily`, `gold_hvac_analytics` (Delta/DirectLake)
- Page 8: `gold_iot_realtime`, `iot_hot_readings` (KQL + Delta) — ISOLATED by design
- Page 9: `gold_battery_dispatch`, `gold_battery_simulation` (Delta)
- All share `building_id` as FK — no cross-joins during trial period
- Post-trial roadmap: IoT data will enrich Pages 2 (real-time power) and 7 (live HVAC vs historical)

---

## PAGE 8: IoT MONITORING — CONFIRMED DESIGN DECISIONS (2026-05-07)

### Users
Both **Facility Manager** (daily ops) AND **Energy Manager** (strategic) use this page.

### Sensor Type Architecture
`sensor_type` is a **DIMENSION — NOT hardcoded**.
Each building exposes only its connected sensor types. Visuals adapt dynamically.

**Minimum sensor set (all buildings):**
- `HVAC_temp` (°C), `humidity` (%), `CO2` (ppm)
- `building_kwh` (kW) — total building power demand
- `hvac_kwh` (kW) — HVAC-only power (split from building total)

**Extended sensor set (full BMS buildings):**
- `HVAC_supply_temp`, `HVAC_return_temp` (delta-T efficiency)
- `lighting_kwh`, `plug_load_kwh` (sub-metering)
- `chiller_cop`, `boiler_eff`, `pump_pressure`, `fan_rpm`

### Confirmed KPI Cards
- C1: Real-time building power (kW) — green/amber/red vs baseline
- C2: Zone comfort compliance % — % zones within setpoint
- C3: CO₂ level — Good / Fair / Poor
- C4: Active high alerts + estimated daily cost ("3 Alerts — Est. €47 today")

### Confirmed Visuals
- V1: 24h power trend — `building_kwh` + `hvac_kwh` separate series + baseline reference line
- V2: Sensor uptime matrix — rows: zones, cols: sensor types
- V3: Zone setpoint compliance — which zones out of range and for how long
- V4: Alert table — location, sensor, reading, severity, action, est. €cost

### Anomaly Cost Estimation Logic (ASSUMPTION — always shown as "Est.")
```
cost_eur = duration_hours × power_waste_kw × grid_price_eur_per_kwh
HVAC_temp violation: 2-5 kW extra per °C deviation
CO2 spike >1500ppm: 1-3 kW extra ventilation
Power spike >120% baseline: actual excess kW
Grid price: DE €0.20/kWh, TR €0.14/kWh (building country from silver_building_master)
```

---