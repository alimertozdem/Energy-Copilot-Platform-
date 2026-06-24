# EnergyLens — Sample Package Build Recipe (from existing features)

> **Status:** DRAFT v1 — for product-owner (Mert) review
> **Date:** 2026-06-18
> **Companion to:** [`2026-06-18_sample-package-and-test-plan.md`](./2026-06-18_sample-package-and-test-plan.md)
> **Purpose:** assemble the two productized packages **using only features that already exist** —
> which is also how we *prove the system works*. Every row below was verified against the codebase
> on 2026-06-18 (frontend routes + backend services).

---

## 0. Decisions this round

- **Capacity:** current = **F4 trial, auto-renewing** → proceed treating it as available. ⚠️ One
  caution `[Muhtemel]`: don't let the *business model* depend on a free trial that can end without
  notice — for the **sample + test** it's perfectly fine to use now; just price the eventual paid
  capacity as a paused F2 (per the operating plan).
- **Building profile — widest reach = OFFICE**, shown as the headline drill-down inside a **mixed
  portfolio**. Why office (criterion now = *breadth*, not the wedge): most universal commercial
  type, clearest CRREM/EPBD stranding story, most mature demo data, lowest energy-logic risk, and it
  **transfers** to retail / schools / mixed-commercial prospects. *(Last turn I picked residential
  for **wedge** alignment; you changed the criterion to "widest probability of appearing" → office
  wins. Residential stays the wedge you grow into, shown as a second portfolio row.)*

---

## 1. Package A — Energy Analytics & BI Dashboard  *(cash engine)*

| Section | App route (exists) | Backend service | PDF route | Exists |
|---|---|---|---|---|
| Portfolio KPI overview (EUI · kWh · € · kgCO₂) | `/portfolio` | `portfolio_metrics` | `/portfolio/report` | ✅ |
| Cockpit / at-a-glance KPIs | `/dashboard` | `portfolio_metrics`, `baseline_kpi` | — | ✅ |
| Per-building benchmark + ranking | `/buildings/compare` | `portfolio_metrics` | — | ✅ |
| Consumption trend + anomalies | `/alerts` | `alerts_data`, `monitoring` | `/alerts/report` | ✅ |
| Solar performance (if PV) | `/solar` | `solar_detail` | — | ✅ |
| HVAC / comfort analytics (if data) | `/hvac` | `cop`, `comfort` | — | ✅ |
| Deep embedded report (10-page Power BI) | `/buildings/[id]/report`, `/buildings/[id]/reports` | Fabric gold (DirectLake) | embed | ✅ (demo bldgs already bridged) |

## 2. Package B — ESG / EPBD Decision-Support Report  *(wedge engine — headline)*

| Section | App route (exists) | Backend service | PDF route | Exists |
|---|---|---|---|---|
| Portfolio carbon (Scope 1/2, intensity) | `/compliance/ghg-report` | `esrs_metrics`, `co2_cost_allocation` | ✅ report | ✅ |
| CRREM stranding pathway | `/compliance/crrem-report` | CRREM gold | ✅ report | ✅ |
| EPBD / MEPS + GEG conformity | `/buildings/[id]/geg-report`, `/compliance/enefg-report` | `geg_conformity` | ✅ report | ✅ |
| ESRS-E1 / VSME report (+ editor) | `/compliance/esrs-report` · `/compliance/vsme-report` | `esrs_metrics` | ✅ report | ✅ |
| EPC + CO₂-cost split (CO2KostAufG) | `/buildings/[id]/epc-report` · `co2-report` | `co2_cost_allocation` | ✅ report | ✅ |
| Retrofit measures + **MACC** | `/decarbonisation` | `abatement` | `/decarbonisation/report` | ✅ |
| **BAFA/KfW subsidy-adjusted ROI** | `/financing` | `financing`, `finance_model` | `/financing/report` | ✅ |
| Prioritised action plan | `/actions` | `actions_data` | `/actions/report` | ✅ |
| GRESB prep (fund buyers, optional) | `/compliance/gresb-report` | `esrs_metrics` | ✅ report | ✅ |
| Assumptions / calc transparency | `/glossary` | glossary registry | — | ✅ |

*(Estimation engine — `services/estimation/{engine,archetypes,vintage,factors,assembler}` + `baseline_estimate` — fills gaps with ranges when data is missing; this is what the messy-data test in the test-plan exercises.)*

---

## 3. The proof: nothing new to build

Every row above is **✅ exists.** Assembling the sample = running existing routes on a demo office
building and exporting the existing report PDFs. There is **no new feature work** to produce the
listing asset — which is exactly the demonstration that the platform is real and works end-to-end.

---

## 4. Assembly steps — Track A (now, €0, no bridge)

1. Pick a demo **office** building (e.g. `B00x`) as the drill-down + 2–3 others for the portfolio frame.
2. **Dashboard package:** capture `/dashboard` + `/portfolio` + `/buildings/compare` (+ `/alerts`).
3. **Report package:** export the existing PDFs — `/compliance/crrem-report`, `ghg-report`,
   `enefg-report` (or per-building `geg-report`), `/decarbonisation/report`, `/financing/report`,
   `/actions/report`.
4. **Anonymise** building names/addresses; label every figure *indicative / screening, assumptions stated*.
5. Assemble one branded sample = a dashboard link/screens + a single combined PDF.
6. Publish on **Malt / freelance.de** as the two offers (Analytics dashboard · ESG/EPBD report).

---

## 5. Division of labour

- **I can produce:** the report narrative/copy, the freelance listing copy (both offers), the
  assembly + anonymisation checklist, and the acceptance/sanity checks on the numbers.
- **You run:** the routes / PDF exports / Power BI render (Claude cannot render Power BI), and the
  publish step.

---

## 6. Open / next

1. Confirm the demo **office building id** to headline (and 2–3 portfolio companions).
2. On confirm, I draft the **listing copy** (both offers) + the **report narrative template** so the
   exported PDF reads as a client deliverable, not an internal dashboard.

_All figures are indicative ranges. Energy logic per the project's "state assumptions, prefer ranges" rule._
