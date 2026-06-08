---
title: "EnergyLens — Campus Pilot: Data Request Checklist"
author: "Ali Mert Özdemir"
date: "2026-06-08"
---

# EnergyLens — Campus Pilot: Data Request Checklist

**Prepared by:** Ali Mert Özdemir  
**For:** University facilities / estates & energy team, with academic supervisor  
**Date:** 8 June 2026

## Purpose

Run a real pilot of **EnergyLens** on the university's own buildings — turning the platform
from a synthetic demonstration into a **real, auditable energy-and-carbon analysis** of the
campus. In return, the university receives a working energy & carbon dashboard of its estate
**at no cost**, as part of the pilot.

**What I already provide myself — you do *not* need to send these:** weather data, grid
emission factors, electricity-market prices and regulatory reference data, all from free
official sources (DWD / EEA / Umweltbundesamt / ENTSO-E). **Your effort is only the
building-specific data listed below.**

**Privacy:** data can be fully anonymised (building codes instead of names); I am happy to
sign a data-sharing agreement / NDA; **no personal data is required** — only building and
energy data.

---

## Tier 0 — Minimum to start (a real pilot within days)

*Unlocks: portfolio overview, energy-use intensity (kWh/m²) benchmarking, energy cost, and
Scope 1 + 2 carbon footprint (location-based).*

| Data needed | Why it is needed | Format |
|-------------|------------------|--------|
| Building list: name/code, address, **floor area — gross + heated (m²)**, use type, year built | Energy intensity (EUI), benchmarking, the core of the data model | Excel / CSV |
| **Electricity bills — at least 12 months** (kWh + €), all meters | Consumption, cost, Scope 2 CO₂ | PDF / CSV / Excel |
| **Gas or district-heating bills — at least 12 months** (kWh or m³) | Heating analysis, Scope 1 CO₂ | PDF / CSV / Excel |
| Energy Performance Certificate (Energieausweis), if available | Compliance, EPC benchmarking | PDF |

---

## Tier 1 — Solid pilot (the full reporting story)

*Adds: hourly load profiles, peak-demand & load-factor analysis, anomaly detection,
consumption forecasting, market-based Scope 2, and decision-support recommendations.*

| Data needed | Why it is needed | Format |
|-------------|------------------|--------|
| **Interval electricity data** — half-hourly or hourly (kWh), as much history as possible (ideally 2–3 years) | 24-hour profiles, peak demand, load factor, forecasting, anomaly detection | CSV / Excel / energy-system export |
| Interval gas / heating data (if metered) | Heating efficiency and anomalies | CSV / Excel |
| Electricity tariff & supply contract: price (€/kWh), demand charge (€/kW), supplier name | Real cost and savings calculations | PDF / summary |
| **Guarantees of Origin / green-electricity certificates** (if the contract has any) | Market-based Scope 2 (the dual reporting auditors require) | PDF / summary |
| Occupancy & calendar: typical headcount, opening hours, term and holiday dates | Fair normalisation; weekend/holiday waste detection | Summary / Excel |

---

## Tier 2 — Full / advanced pilot (the complete platform)

*Adds: HVAC efficiency, real-time IoT monitoring, automated fault detection, solar/battery
ROI, refrigerant Scope 1, and Scope 3.*

| Data needed | Why it is needed | Format |
|-------------|------------------|--------|
| Sub-meter data (per floor or system: HVAC, lighting, plug loads) | Real HVAC energy split instead of a modelled estimate | CSV / energy-system export |
| Building Management System (BMS/BAS) export or read access — BACnet / Modbus: temperatures, setpoints, CO₂, humidity, occupancy | Real-time monitoring, comfort compliance, fault detection | Export / read access |
| HVAC equipment list + specs (chillers, boilers, air handlers, heat pumps: rated COP, capacity) | COP / efficiency analysis, fault diagnostics | List / spec sheets |
| **Refrigerant / F-Gas logbook** — refrigerant type (e.g. R-410A) and top-up kg per service | Refrigerant Scope 1 — the emission source most often missed | Logbook / Excel |
| On-site generation: solar PV capacity (kWp) + generation data, battery, EV charging | Solar & battery KPIs and investment ROI | CSV / spec sheets |
| Tenant / leased-space energy (if the campus leases to cafés, shops, partners) | Scope 3, Category 13 (downstream leased assets) | Summary / Excel |
| Building-envelope details (U-values, window-to-wall ratio, insulation year) — usually inside the EPC | Insulation and retrofit simulations | EPC / building docs |

---

## How to start (the simple version)

**Even just Tier 0** — floor areas plus 12 months of electricity and gas bills — produces a
real, presentable result. Everything above Tier 0 makes the pilot progressively richer; it
does not have to arrive all at once.

**What the university gets back:** a working energy-and-carbon dashboard of its own buildings
— EUI benchmarking, cost breakdown, Scope 1/2 footprint, anomaly flags, and prioritised
improvement recommendations — produced as part of the pilot at no cost.

**Format & contact:** CSV, Excel, PDF, or read access to the energy-management system all
work equally well. A single point of contact in the facilities / estates / energy team is
ideal to keep the exchange simple.

---

*EnergyLens — a Microsoft Fabric-based energy intelligence and ESG-reporting platform for
commercial buildings. Pilot data is used solely to validate the platform on real buildings
and to produce the university's own energy & carbon analysis.*
