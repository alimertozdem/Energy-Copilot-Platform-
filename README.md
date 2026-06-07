# Energy Copilot Platform — Commercial Buildings

> An intelligent, decision-support platform for energy management in commercial buildings.
> Built on **Microsoft Fabric** | Designed for **Germany & Turkey** | Multilingual: TR / DE / EN

---

## What Is This Platform?

This is **not a dashboard**. It is an energy intelligence and advisory system that answers:

- **What is happening?** — Real-time and near-real-time energy monitoring
- **Why is it happening?** — Anomaly detection with root-cause explanation
- **What should be done?** — Actionable, prioritized recommendations
- **What would happen if changes are made?** — Simulation engine for upgrades and scenarios

---

## Target Users

| User | Role | Primary Need |
|---|---|---|
| Energy Consultant | External advisor | Data-backed audit reports, ROI simulations |
| Facility Manager | On-site operator | Anomaly alerts, actionable guidance |
| Energy Manager | Strategic portfolio manager | KPI trends, compliance tracking, ESG reporting |
| Building Owner | Executive stakeholder | Investment cases, sustainability performance |

---

## Subscription Tiers

| Tier | Name | Data Latency | Key Features |
|---|---|---|---|
| 1 | Insight | 1 hour (batch) | KPIs, trends, recommendations, reporting |
| 2 | Monitor | 5–15 min (near real-time) | Tier 1 + live anomaly alerts, HVAC optimization |
| 3 | Copilot | Real-time streaming | Tier 2 + simulations, ML forecasting, human expert routing |

---

## Supported Building Technologies

- Standard HVAC (Chiller / AHU)
- Heat Pump systems — COP monitoring and optimization
- PV Solar systems — yield analysis, self-consumption optimization
- Battery Storage (BESS) — two dispatch strategies: Self-Consumption & Peak Shaving
- LED Lighting systems
- Building Automation Systems (BAS/BMS integration)

---

## Architecture Overview

```
Data Sources (IoT / Smart Meter / Weather API / CSV)
        │
        ├── Fabric Eventstream (Tier 2-3: Streaming)
        └── Fabric Data Factory (Tier 1: Batch)
                │
                ▼
    Microsoft Fabric — Lakehouse (Medallion Architecture)
    ┌──────────┐    ┌──────────┐    ┌──────────────────────┐
    │  BRONZE  │ ──►│  SILVER  │ ──►│        GOLD          │
    │  Raw     │    │ Cleaned  │    │  KPIs / Anomalies /  │
    │  Data    │    │ Modeled  │    │  Simulations / ESG   │
    └──────────┘    └──────────┘    └──────────────────────┘
                                            │
                                    Power BI Embedded
                                    (Branded Web App)
```

---

## Key Capabilities

### KPI Engine
- Energy Use Intensity (EUI) with climate adjustment
- Peak Demand & Load Factor
- Solar: Self-Consumption Rate, Self-Sufficiency Rate, Performance Ratio
- Battery: State of Charge, Cycle Count, Round-trip Efficiency
- Heat Pump: COP (Actual vs. Rated), SCOP
- Carbon Intensity (Scope 2), CO2 Net Emissions

### Anomaly Detection (Rule-Based, Phase 1)
- Consumption spikes (weather-adjusted)
- High base load (after-hours waste)
- COP degradation (heat pump maintenance alert)
- Solar underperformance (panel soiling / inverter fault)
- Battery anomalies (efficiency loss, over-discharge risk)
- Weekend/holiday overconsumption

### Simulation Engine
- Add PV Solar (kWp sizing with financial model)
- Add Battery Storage (with technology recommendation: LFP)
- Switch to Heat Pump (vs gas boiler comparison)
- Battery strategy change (Self-Consumption vs Peak Shaving)
- Insulation upgrade (wall / roof / window — U-value improvement)
- Window upgrade (thermal transmittance improvement)
- Air tightness improvement

### Sustainability & ESG
- CO2 consumption, CO2 avoided (via solar), Net CO2
- Carbon credit value estimation
- CSRD-ready ESG reporting
- EU Taxonomy alignment score
- LEED/BREEAM gap analysis

### Regulatory Compliance
- Germany: EnEfG, GEG (U-value checks), EEG
- European Union: EPBD (nZEB targets), EU ETS
- Turkey: BEP-TR energy certificate tracking
- Automatic incentive matching: KfW, BAFA, YEKA

---

## Web Application (EnergyLens)

Beyond the Fabric data platform, the repository contains **EnergyLens** — the
customer-facing SaaS application that turns the analytics into a product
(`web-app/`).

**Frontend** (`web-app/frontend/`) — Next.js (App Router) + Tailwind, multi-provider
auth (Microsoft / Google / Email via NextAuth), Power BI Embedded (app-owns-data).
Routes:

- `/demo` — public, no-signup showcase (sample buildings)
- `/onboarding` — building setup wizard
- `/portfolio` — portfolio KPIs + buildings table (custom React over Fabric SQL)
- `/buildings`, `/buildings/[id]/reports/[page]` — per-building embed of the 9 Power BI pages, with route-level module gating
- `/actions` — recommendation tracking (Fabric catalog + Postgres status overlay)
- `/alerts` — portfolio-wide anomaly triage (acknowledge / dismiss overlay)
- `/solar` — dedicated on-site solar detail
- `/copilot` — AI chat over the portfolio (tool-using LLM)
- `/settings`, `/admin` — org / member management + platform admin, with audit logging

**Backend** (`web-app/backend/`) — FastAPI service: Power BI embed-token generation
(service principal via MSAL), direct Fabric Lakehouse reads over the SQL Analytics
Endpoint (ODBC / pyodbc), and a PostgreSQL control plane (SQLAlchemy + Alembic:
organizations, buildings, recommendation / alert status, copilot history, audit log).

**Two data paths over one Lakehouse:** Power BI Embedded (DirectLake semantic model)
for the rich report pages, and direct Fabric SQL for the app's custom React views —
each joined to a Postgres overlay holding customer-side operational state. See
`web-app/README.md` to run it locally.

---

## Repository Structure

```
energy-copilot-platform/
│
├── docs/
│   ├── architecture/          # System architecture diagrams and decisions
│   ├── data-model/            # Table schemas, ERD, data dictionary
│   ├── business-logic/        # KPI formulas, anomaly rules, simulation logic
│   └── assumptions/           # Stated assumptions and data sources
│
├── fabric/
│   ├── bronze/                # Raw ingestion table definitions
│   ├── silver/                # Cleaned and modeled table definitions
│   ├── gold/                  # Business-ready KPI and analytics tables
│   ├── streaming/             # Eventstream configuration
│   └── semantic-model/        # Power BI semantic model definitions
│
├── notebooks/
│   ├── ingestion/             # Bronze layer ingestion notebooks
│   ├── transformation/        # Bronze → Silver transformation
│   ├── kpi-engine/            # Silver → Gold KPI calculation
│   ├── anomaly-detection/     # Anomaly detection rules
│   ├── simulation/            # What-if scenario simulations
│   ├── sustainability/        # CO2 and ESG calculations
│   └── compliance/            # Regulatory compliance checks
│
├── pipelines/
│   ├── batch/                 # Data Factory batch pipeline definitions
│   └── streaming/             # Eventstream pipeline definitions
│
├── web-app/                   # EnergyLens SaaS application
│   ├── frontend/              # Next.js (App Router) + Tailwind + NextAuth + PBI embed
│   └── backend/               # FastAPI + SQLAlchemy/Alembic + Fabric SQL + Copilot LLM
│
├── semantic-model/            # Power BI semantic model + RLS definitions
├── report-design/             # Power BI page design guides (9 report pages)
├── branding/                  # EnergyLens brand assets
├── ml-models/                 # Phase 2: ML model training and serving
├── sample-data/               # Synthetic building data for development/testing
└── scripts/                   # Utility scripts
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Data Platform | Microsoft Fabric (Lakehouse, Eventstream, Data Factory, Activator) |
| Storage Format | Delta Lake (OneLake) |
| Processing | Apache Spark (PySpark) via Fabric Notebooks |
| Orchestration | Fabric Data Factory Pipelines |
| Semantic Layer | Power BI Semantic Model (Direct Lake) |
| Visualization | Power BI Embedded |
| App Frontend | Next.js (App Router), Tailwind CSS, NextAuth, powerbi-client-react |
| App Backend | FastAPI, SQLAlchemy + Alembic, pyodbc (Fabric SQL endpoint), MSAL |
| App Database | PostgreSQL (Supabase) — multi-tenant control plane |
| Copilot | Tool-using LLM (Anthropic / Azure OpenAI) |
| Version Control | GitHub (Fabric Git Integration) |
| Languages | Python, PySpark, SQL, DAX |

---

## Regulatory Coverage

| Country | Regulations |
|---|---|
| Germany | EnEfG, GEG, EEG, KfW/BAFA incentives |
| European Union | EPBD, EU ETS, CSRD, EU Taxonomy |
| Turkey | BEP-TR, EPDK tariffs, YEKA incentives |

---

## Development Approach

This platform is built following the **BMAD methodology**:

1. **Business** — Use cases, users, product boundaries
2. **Architecture** — Microsoft Fabric components, Medallion design
3. **Data** — Table schemas, data model, ingestion strategy
4. **Logic** — KPI formulas, anomaly rules, simulation engine
5. **Implementation** — Notebooks, pipelines, deployment

> Development is incremental. Phase 1 covers core KPI engine, rule-based anomaly detection, and simulation fundamentals. Phase 2 adds ML forecasting and mobile API.

---

## Phase Roadmap

### Phase 1 (Current)
- Medallion architecture setup
- Batch and near-real-time ingestion
- Full KPI engine
- Rule-based anomaly detection
- Simulation engine (physics-based)
- Power BI Embedded output
- Germany + Turkey regulatory compliance

### Phase 2
- ML-based anomaly detection (adaptive thresholds)
- Consumption forecasting model
- Occupancy prediction
- REST API for mobile application
- Additional country regulatory profiles

---

*Built with Microsoft Fabric | Designed for energy intelligence, not just reporting.*
