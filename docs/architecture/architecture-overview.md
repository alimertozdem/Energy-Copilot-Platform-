# Architecture Overview — Energy Copilot Platform

## Design Principles

1. **Medallion Architecture** — Bronze / Silver / Gold separation of concerns
2. **Multi-tenant by design** — Row-Level Security (RLS) per building
3. **Tier-aware ingestion** — Batch for Tier 1, Streaming for Tier 2-3
4. **Modular logic** — Technology profile activates relevant KPI modules
5. **Extensible regulation layer** — New countries added without architecture change

---

## Component Map

### Ingestion Layer

| Component | Role | Used By |
|---|---|---|
| Fabric Eventstream | Real-time IoT / sensor data ingestion | Tier 2, Tier 3 |
| Fabric Data Factory | Batch ingestion (API, CSV, smart meter) | All tiers |

### Storage Layer — Microsoft Fabric Lakehouse (OneLake)

All data lives in a single Lakehouse using Delta Lake format.
Multi-tenancy is enforced via `building_id` partitioning + Row-Level Security.

### Processing Layer

All transformations are written as PySpark notebooks.
Orchestration is handled by Fabric Data Factory pipelines.

### Output Layer

- **Power BI Semantic Model** (Direct Lake connection to Gold tables)
- **Power BI Embedded** (white-labeled in the customer-facing web application)
- **Fabric Activator (Reflex)** — rule-based alert and notification engine

---

## Medallion Architecture Detail

### Bronze — Raw Data
- Data is written as-is. No transformations.
- Purpose: auditability, error recovery, reprocessing capability
- Partitioned by: `building_id / year / month / day`
- Format: Delta Lake

### Silver — Cleaned & Modeled
- Units normalized (all kWh, °C, m²)
- Timestamps aligned to UTC and local time
- Missing values handled: interpolated or flagged
- Data quality flags applied: OK / INTERPOLATED / MISSING / ANOMALY
- Building metadata joined

### Gold — Business-Ready
- KPIs calculated and stored as aggregations
- Anomaly detection results stored
- Simulation outputs stored
- Recommendations generated
- ESG and compliance outputs
- Directly consumed by Power BI Semantic Model

---

## Subscription Tier Architecture

```
TIER 1 — Insight (Batch)
Smart Meter API / CSV ──► Data Factory ──► Bronze ──► Silver ──► Gold ──► Power BI
Latency: ~1 hour

TIER 2 — Monitor (Near Real-Time)
IoT Gateway ──► Eventstream ──► Bronze (streaming)
                                      +
                              Batch (weather, static)
                                      │
                              Silver ──► Gold ──► Power BI + Activator Alerts
Latency: 5–15 minutes

TIER 3 — Copilot (Full Intelligence)
All of Tier 2
+ Simulation engine (on-demand)
+ Phase 2: ML models
+ Phase 2: Human expert routing
Latency: <5 minutes
```

---

## Multi-Tenant Design

```
ORGANIZATION
    └── BUILDING (building_id)
            ├── Technology Profile (PV, Battery, Heat Pump, etc.)
            ├── Subscription Tier
            ├── Country / Regulatory Profile
            └── All data partitioned by building_id

Row-Level Security (RLS):
    - Facility Manager → sees only their building(s)
    - Energy Manager → sees all buildings in their organization
    - Platform Admin → sees all
```

---

## IoT Integration

For Tier 2-3 buildings with existing smart sensors:

```
Building Sensors (BACnet / Modbus / MQTT / OPC-UA)
        │
        ▼
IoT Gateway (edge device — translates protocols to MQTT/JSON)
        │
        ▼
Fabric Eventstream (real-time ingestion)
        │
        ▼
Bronze Layer (raw stream landing)
```

Supported protocols: BACnet, Modbus, MQTT, OPC-UA
Gateway examples: Azure IoT Edge, Advantech, Siemens SIMATIC

---

## Technology Profile — Modular Logic Activation

When a building is onboarded, its technology profile determines which KPI modules are active:

```
building.has_pv = True        → Solar KPI module activated
building.has_battery = True   → Battery KPI + Dispatch module activated
building.has_heat_pump = True → COP monitoring module activated
building.country_code = 'DE'  → EnEfG, GEG, EEG compliance rules activated
building.country_code = 'TR'  → BEP-TR, EPDK rules activated
```

---

## Key Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Streaming technology | Fabric Eventstream (native) | No external dependency, cost-effective, Fabric-native |
| Multi-tenant isolation | Single Lakehouse + RLS | Simpler management, scalable, security via RLS |
| Output layer (Phase 1) | Power BI Embedded | Fast to market, Fabric-native, brandable |
| Output layer (Phase 2) | REST API for mobile | Planned but not in Phase 1 scope |
| Simulation engine | Physics-based formulas | Transparent, explainable, no data requirement |
| ML anomaly detection | Phase 2 only | Requires 6–12 months historical data to train |
| Regulation data | Static reference tables | Regulations change rarely; annual manual update sufficient |
