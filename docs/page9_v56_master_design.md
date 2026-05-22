# Page 9 v56 — Master Design Document
**Battery Dispatch & Financial Simulation — production-grade architecture**
Date: 2026-05-21 · Author: Energy Copilot Platform team

---

## 1. Why this refactor

The original Page 9 (v47–v52) covered a single building's dispatch and a
13-scenario simulation table. After live data was added through Notebooks
12/14/15, six daily-flow measures (`V2 Charge kWh Daily` and siblings) were
orphaned by Power BI Service ("Move measure to another table" warnings) and
visuals broke at the same time.

Rather than patching v52 one more time, v56 is a **production-grade refactor**
aligned with the Phase 2 architecture decision (2026-05-07) — IoT
interoperability, EU 2023/1670 compliance, and dynamic pricing — and with the
DAX patterns learned in Pages 5–7 (self-contained measures, building-type aware
thresholds, country-aware logic).

## 2. Energy-domain logic — first principles

A commercial-building battery is a **time-shifting + power-buffering asset**.
It produces value through six economic mechanisms, and the right strategy is
the combination that maximizes the building's specific revenue stack.

| Mechanism | Driver | Sensitive to | Typical value range |
|---|---|---|---|
| Self-consumption (PV shift) | PV oversupply at noon, load demand at evening | PV size, load shape | €0.10–0.18/kWh shifted |
| Peak-shaving (kW reduction) | Demand charge structure | Local demand tariff | €60–180/kW/yr saved peak |
| Time-of-use arbitrage | Peak–off-peak spread | Tariff design | €0.06–0.18/kWh cycled |
| Backup capacity | Outage avoidance / SLA | Outage frequency, $loss/h | €5k–500k/yr avoided losses |
| Frequency reserve (FCR/aFRR) | Grid frequency control | TSO market design | €30–80/kW/yr (DE/DK lead) |
| Capacity market | Firm capacity to peak demand | UK/IT mechanisms | €15–35/kW/yr |
| V2G coordination | Bidirectional fleet integration | EV fleet size, grid code | €200–600/car/yr |

**Important assumption (always disclosed as a range):** every figure above is
sector-typical for 2026 EU markets and varies with year, location, and battery
spec. The dashboard always communicates *est. €X (range ±25%)* rather than
false precision.

## 3. Chemistry landscape — what we support and why

| Chemistry | Strength | Weakness | Sector context |
|---|---|---|---|
| **LFP** (LiFePO₄) | Cycles 5000-7000, low CO₂, full EU compliance, safe | Lower energy density (m³ footprint larger) | Default for commercial 2024+. Market share rising fast (>60% in EU 2026). |
| **LFP-V2G** | Bidirectional, ISO 15118-20 ready | +15-20% CAPEX | Critical for NL/UK/DE EV-fleet customers |
| **LFP-Supercap-Hybrid** | High power burst (FCR ideal), 1M+ effective cycles | Smaller usable kWh per €, niche | Frequency reserve revenue stack — Skeleton/Eaton |
| **NMC** | Higher energy density | High cobalt content, 68 kg CO₂/kWh, banned new installs DE/AT 2025+ | Legacy systems; not for new EU commercial |
| **NCA** | Premium energy density (Tesla 4680) | High Ni/Co, 60 kg CO₂/kWh near EU threshold | Premium niche; declining commercial use |
| **Second-Life NMC** | 60% lower CAPEX, 80% recycled (ESG win) | 7-yr life, ~2000 cycles | Sustainability-focused customers; pilot programs |
| **Sodium-Ion** (CATL Naxtra) | Cold tolerance -30 °C, lowest CO₂ (28 kg), no critical minerals | Energy density ~70% of LFP | 2026 Q3 entry; cold-climate winner (Nordics, AT) |
| **Solid-State** (QuantumScape) | 8000+ cycles, 96.5% RTE, ultra-high power density | Limited 2026 supply, premium pricing | Pilot programs; data-center early adopters |

## 4. Country coverage — 12 markets

The product targets commercial-building energy management across Western and
Central Europe with a Turkish reference (founder market) and a UK reference
(post-Brexit divergence).

```
DACH:     DE Germany     AT Austria       CH Switzerland (non-EU/EEA)
Benelux:  NL Netherlands BE Belgium       LU Luxembourg
Nordics:  DK Denmark     SE Sweden        FI Finland       NO Norway (non-EU/EEA)
Non-EU:   TR Turkey      UK United Kingdom
```

Each country row in `gold_country_regulations` carries 25 fields covering:
- EU membership / EEA alignment
- Chemistry permits (NMC/NCA/Sodium-Ion/Solid-State allowed flags)
- V2G grid-code readiness
- Frequency market eligibility (FCR/aFRR)
- Capacity market eligibility
- Submetering requirements
- Carbon footprint threshold, recycled content threshold
- Digital Battery Passport mandatory date
- Typical feed-in tariff, demand charge, peak/off-peak price
- Grid CO₂ intensity (g/kWh)
- Primary regulator + regulation reference + URL

This is the source-of-truth for the V5 *Country × Chemistry* heatmap and for
the country-aware I2/I3 insight measures.

## 5. Building-type fitness — `gold_strategy_fitness`

49 rows = 7 building_types (office, retail, hotel, healthcare, education,
logistics, data_center) × 7 strategies. Each row carries:

- `fitness_score` 0-100 (matrix heat)
- `typical_annual_savings_eur_per_kwh` — sector benchmark
- `energy_logic_rationale` — one-paragraph explanation
- `risk_or_caveat` — what limits the case
- `is_primary` / `is_secondary` flags — pick top two strategies

The fitness rationales were calibrated against:
- ASHRAE 90.1 building load profiles
- EN 15232 occupancy assumptions
- DNV·GL EU storage outlook 2025
- Eurelectric battery strategy briefing 2024-Q4
- Public DSO tariff schedules (Stedin NL, Stromnetz DE, Energinet DK)

## 6. Innovation vs incumbents

Where competitors stop, this Page 9 keeps going:

| Capability | Siemens DEMS | Schneider EcoStruxure | **EnergyLens v56** |
|---|---|---|---|
| Multi-strategy what-if | One active strategy | One active strategy | **5 strategies side-by-side** |
| Chemistry recommender | LFP only | LFP + NMC | **8 chemistries (LFP/NMC/NCA/Sodium/Solid/V2G/2L/Hybrid)** |
| Country regulatory gating | DE only | EU avg | **12 countries with per-chemistry flags** |
| V2G integration | Roadmap | Pilot | **First-class — ISO 15118-20 modeled, BYD V2G product** |
| Frequency reserve revenue | External tool | External tool | **Native in V4 / I1 / I2** |
| Building-type aware recommendation | None | Generic | **49-row fitness matrix** |
| Prescriptive insight text | None | None | **Four LLM-grade insight measures** |

## 7. Implementation notes & energy-logic disclaimers

- **All revenue figures are ranges** (±25%). Sector benchmarks evolve quarterly.
- **Sodium-Ion** rows assume CATL Naxtra commercial availability Q3 2026 in
  DE/Nordics. If the rollout slips, the I2 fallback recommendation is LFP.
- **Solid-State** is pilot-only in DE for 2026. Treat as advisory until
  QuantumScape exits restricted release.
- **V2G** economics depend on EV fleet size ≥ 10 vehicles and aggregator
  contract. For buildings without EV fleets the V2G fitness score is ≤ 30 and
  the recommender skips it.
- **Second-Life NMC** has compliance subtleties: EU 2023/1670 second-life
  provisions allow repurposing but limit eligibility to non-critical loads.
  We flag this in the I3 measure for healthcare and data_center building types.
- **NMC ban** in DE/AT applies to new commercial installations from 2025-01.
  Existing systems are grandfathered through warranty period — the I3 insight
  reflects this (replacement window vs immediate non-compliance).

## 8. Maintenance plan

Quarterly updates that keep this Page 9 accurate:
1. **Pricing refresh** — Notebook `00_fetch_electricity_prices.py` (EPEX Spot)
   feeds `gold_electricity_pricing`. C1/V4/V6 read this.
2. **Regulation refresh** — manual edit of `gold_country_regulations.csv`
   when a country amends battery law. Targeted alerts (Bundesnetzagentur,
   ACM NL, Ofgem) inform this.
3. **Chemistry catalogue refresh** — `gold_battery_technologies.csv` adds new
   products as they reach EU commercial availability.

## 9. Files manifest

| Path | Purpose | Sprint |
|---|---|---|
| `sample-data/gold_country_regulations.csv` | 12-country regulation table | 1 |
| `sample-data/gold_strategy_fitness.csv` | 49-row fitness matrix | 1 |
| `sample-data/gold_battery_technologies.csv` | 15-row chemistry catalog (was 10) | 1 |
| `semantic-model/68_dax_v56_page9_master.dax` | DAX source-of-truth (26 measures) | 2 |
| `semantic-model/scripts/page9_v56_master_install.cs` | TE2 bulk install | 2 |
| `report-design/page9-v56-master-binding-guide.md` | Visual-by-visual binding | 3 |
| `docs/page9_v56_master_design.md` | This document | 4 |

## 10. References

- EU Regulation 2023/1670 — Batteries Regulation
- DNV·GL "European Energy Storage Outlook 2025"
- Eurelectric "Demand Response & Storage in Europe" Nov 2024
- IEA "Batteries and Secure Energy Transitions" 2024
- BYD Battery-Box HVS / HVM datasheets 2025-Q4
- CATL Naxtra commercial brief 2026-Q1
- QuantumScape pilot disclosure 2026-Q1 letter to investors
