# ESG / Sustainability Report Engine — Design (BMAD)

**Status:** Design — awaiting approval to build Phase 1
**Date:** 2026-06-12
**Owner / domain reviewer:** Mert (energy + ESG reviewer)
**Anchor standard:** ESRS E-1 (Climate Change), generic engine for a wider report family
**Legal framing:** "ESRS-E1- / VSME-aligned reporting support". **Never** "CSRD-compliant filing".

---

## 0. Decisions locked (2026-06-12 session)

| # | Decision | Choice |
|---|----------|--------|
| D1 | Engine breadth | **Generic engine**, ship templates one by one; ESRS E-1 first |
| D2 | Narrative / qualitative layer | **Structured narrative editor** — guided forms + editable boilerplate; numbers auto-fill, human writes/approves narrative (no AI auto-draft of disclosures) |
| D3 | GHG scope positioning | **Scope 1+2 disclosure-grade core + Scope 3 separate "estimated" tier** (transparent, category-labelled) |
| D4 | Export | **Phased: PDF/DOCX first → XBRL digital template second** |
| D5 | Anchor + roadmap | ESRS E-1 quantitative core first; GHG Inventory is a near-free sibling |

These supersede nothing prior; they extend the existing `/compliance` hub (ESRS-E1 indicators, EU Taxonomy, MEPS, CRREM) from *screening* to *report deliverable*.

---

## 1. Business (B)

### 1.1 Why this, why now
The CSRD Omnibus (published 26 Feb 2026, in force 19 Mar 2026) cut mandatory CSRD scope by ~90% — now only > 1,000 employees **and** > €450m turnover; listed SMEs are fully out. ~50,000 → ~5,000 companies in scope. **EnergyLens's realistic customers (commercial building owners, Hausverwaltung, SMEs) are below the CSRD threshold.**

That is the opportunity, not a loss: out-of-scope SMEs still must supply ESG data — banks (lending), large clients (value-chain / VSME trickle-down), investors (real estate → GRESB). The EU's standard answer for them is **VSME** (EFRAG voluntary SME standard, Basic + Comprehensive, own digital template + XBRL taxonomy, expected to finalise as a delegated act ~summer 2026).

### 1.2 Report family = productized freelance services
One data spine → a library of templates. Each template is a sellable service:

1. **GHG Inventory** (GHG Protocol Corporate Standard) — Scope 1/2/3 inventory; the most common carbon-accounting gig. Maps `gold_ghg_scope` 1:1.
2. **ESRS E-1 (Climate)** — the deep one; E1-5/E1-6 auto + structured narrative. *(First build.)*
3. **VSME** (Basic / Comprehensive) — SME version; environmental module is a subset of E-1 data.
4. **EU Taxonomy** climate alignment — already screened in `/compliance`.
5. **CRREM / decarbonisation pathway** — asset stranding + retrofit roadmap (Page 5/9 simulation + CRREM); strong property-owner deliverable.
6. **GRESB** support — real-estate investor benchmark; building energy/GHG/EPC feeds it.

### 1.3 Positioning + guardrails
- Sell as **"ESG reporting support / VSME-aligned report preparation"** — not statutory filing.
- Every figure carries its **grade** (disclosure-grade real vs estimated) and a **methodology note** — this honesty is the credibility moat, and it is already in the data layer (`scope3_disclosure_grade`, `data_source="synthetic_demo"` flags).
- **Synthetic demo data must be swapped for real client data before any real-client report.** The Scope-3 demo generator emits the same schema as real activity tables, so the engine does not change when real data arrives.

---

## 2. Architecture (A)

### 2.1 Components
```
ESG DATA SPINE            TEMPLATE REGISTRY            AUTHORING + RENDER            EXPORT
(Fabric gold, flagged)    (per-standard specs)        (Next.js app)                 (phased)
─────────────────────     ───────────────────────     ──────────────────────────    ─────────────
gold_ghg_scope        →   esrs_e1.json            →   data-binding (auto fields) →   P1: PDF / DOCX
gold_kpi_*                vsme_basic.json             structured narrative editor    P2: XBRL (iXBRL
gold_compliance_*         ghg_inventory.json          (forms + boilerplate)              + VSME/ESRS
gold_recommendations      eu_taxonomy.json            live preview                        taxonomy)
EPC / CRREM / MEPS        crrem_pathway.json          (reuse /compliance + /reports)
```

### 2.2 Where each piece lives
- **Data spine:** existing Fabric gold tables (read via SQL Analytics Endpoint / ODBC, the proven backend path). No new heavy compute — the metrics already exist.
- **Template registry:** versioned JSON specs in repo (`/report-templates/`). A spec = ordered sections; each field tagged `AUTO-REAL | AUTO-ESTIMATED | FORM | NARRATIVE` + binding + methodology note key.
- **Authoring + preview:** Next.js, reusing `/compliance` (data fetch) and `/reports` (render/PDF) patterns. New: a per-datapoint narrative editor with editable boilerplate, persisted per org (Postgres).
- **Export:** P1 reuses the existing `window.print()` / DOCX path; P2 adds an XBRL/iXBRL packager against the EFRAG taxonomy.

### 2.3 Regulatory-flux handling (critical)
The revised ESRS (Omnibus simplification, ~−60% mandatory datapoints) is expected to finalise ~summer 2026. **Therefore the ESRS-E1 datapoint set is treated as a versioned, swappable template — never hardcoded.** The engine targets the *disclosure-requirement skeleton* (E1-1…E1-9, stable) and binds the datapoint list per template version, so a new delegated act = a new spec file, not an engine rewrite.

---

## 3. Data (D) — ESRS E-1 → EnergyLens field mapping

Grade legend: **AR** = auto, disclosure-grade real · **AE** = auto, estimated (flagged) · **F** = form input · **N** = narrative editor.

| ESRS E-1 disclosure | Grade | Source in EnergyLens |
|---------------------|:----:|----------------------|
| **E1-1** Transition plan | N (+AE) | Narrative; supported by CRREM pathway + MEPS stranding (auto evidence) |
| **E1-2** Policies | N / F | Narrative editor |
| **E1-3** Actions & resources | F (+AE) | Form; auto-suggested from `gold_recommendations` (retrofit actions + capex) |
| **E1-4** Targets | F (+AR) | Form; baseline auto from current GHG / energy |
| **E1-5** Energy consumption & mix | **AR** | `gold_kpi_*`: total MWh, by source, renewable/solar share, EUI (intensity per **revenue** needs F) |
| **E1-6** Scope 1 | **AR** | `scope1_gas + diesel + refrigerant_tco2` |
| **E1-6** Scope 2 (location + market) | **AR** | `scope2_location_tco2`, `scope2_market_tco2` (both, as ESRS requires) |
| **E1-6** Scope 3 | **AE** | `scope3_cat1_embodied + cat13_leased`; `disclosure_grade=False` → "estimated" tier |
| **E1-7** Removals & carbon credits | F / N | Form (default: none for buildings) |
| **E1-8** Internal carbon pricing | F | Form (default: none) |
| **E1-9** Anticipated financial effects | AE + N | CRREM stranding value + MEPS/retrofit capex (sim) + narrative |

**Known data gaps (honest):** (a) intensity-per-net-revenue needs a revenue input; (b) Scope 3 covers only Cat 1 + Cat 13 today and is synthetic-demo — must be labelled and, for real clients, replaced with real activity data; (c) Scope 2 market-based needs the client's actual supplier/GoO contracts (schema exists: `silver_supplier_contracts`).

---

## 4. Logic (L)

1. **Assembly:** pick template version → bind AUTO fields from spine → load org's saved FORM/NARRATIVE → assemble section tree.
2. **Grade propagation:** every rendered figure shows its grade; **estimated** figures get a badge + footnote; a **methodology appendix** is auto-generated from the ref/factor layer (already source-cited).
3. **Narrative editor:** per datapoint, a guided prompt + an editable boilerplate default; human edits/approves; versioned per org/reporting-period in Postgres. No figure is invented; no narrative is auto-published without human approval.
4. **Validation:** completeness check (required datapoints filled), methodology-note presence, scope-boundary statement, "estimated" disclosures flagged before export.

---

## 5. Implementation roadmap (phased — one gate at a time)

- **P1 — Engine spine + ESRS E-1 quantitative + narrative + PDF/DOCX**
  Template-registry abstraction; `esrs_e1.json` spec; auto-bind E1-5/E1-6 (S1+S2 grade, S3 estimated tier); structured narrative editor (forms + boilerplate, Postgres persistence); in-app preview; PDF/DOCX export with grade badges + methodology appendix.
- **P2 — XBRL digital template export**
  iXBRL/ESEF packager against EFRAG VSME/ESRS taxonomy; same report-spec → machine-readable output.
- **P3 — Sibling templates**
  GHG Inventory (near-free from E1-6) → VSME Basic → EU Taxonomy → CRREM pathway → GRESB. Each = a new spec + binding, reusing the engine.

Each phase ends with a review/approval gate before the next.

---

## 6. Open items to confirm (domain reviewer)

1. **Reporting entity unit:** ESRS/VSME = organisation/group level; GHG inventory & property reports = portfolio or per-building. Proposed: org/portfolio for E-1/VSME, per-building for CRREM/EPC. *(Confirm.)*
2. **First sibling after E-1:** recommend **GHG Inventory** (cheapest, most common freelance gig). *(Confirm.)*
3. **Boilerplate authorship:** who drafts the editable default narrative per datapoint (Mert once, reused across clients)? *(Confirm — affects P1 content scope.)*
4. **Revenue input** for intensity metrics: collect in onboarding or per-report form? *(Confirm.)*

---

## 7. Legal / honesty guardrails (non-negotiable)

- Respect `disclosure_grade`; show "estimated" badges + methodology appendix on every report.
- Language: **"aligned / reporting support"**, never **"compliant / statutory filing"**.
- Synthetic/demo data (`data_source="synthetic_demo"`) must be replaced with real client data before any real-client report; the engine is unchanged when it is.
- No AI-auto-published narrative; human approval required on every qualitative disclosure.

---

## 8. German legal-mandatory report family (2026) — per-building priority

**Refinement (2026-06-12):** Reporting unit = **the building**. Each building the user is authorised to see (RLS-enforced) gets a **"Generate report"** action → pick report type → auto-fill from that building's gold data + minimal form inputs → preview → export (PDF/DOCX P1, XBRL P2). Portfolio rollup is secondary. **This resolves Open Item #1.**

Priority = currently German-mandatory reports producible from existing data, then high-demand voluntary ones.

### Tier A — Mandatory, data-ready (build first)
| Report | Legal basis (DE) | Mandatory when | EnergyLens data | Honesty caveat |
|--------|------------------|----------------|-----------------|----------------|
| **CO₂ cost allocation** | CO2KostAufG | Annually — every landlord with fossil heating; disclosed in the heating bill | emissions/m² (`gold_ghg_scope`), `co2_levy_cost_*` (05 already computes) | Residential/mixed = 10-stair (kg CO₂/m²/yr; ≥52→landlord 95%, <12→tenant 100%); **non-residential = flat 50/50** (NWG stair model planned 2025, not yet in force). 2026 price €55–65/t |
| **GEG conformity** | GEG §10 / §71 | Heating ≥65% renewable (since 2024), envelope/retrofit duties | GEG checks (`gold_compliance_*`) + retrofit sim | Screening; formal Nachweis is case-by-case |
| **EnEfG audit support + Maßnahmenplan** | EnEfG §8/§9 (2026 Novelle) | Audit > 2.77 GWh/yr; EnMS > 23.6 GWh/yr; first audit by 11 Oct 2026 | consumption, `enefg_audit_required`, `gold_recommendations` (measures + ROI = the required implementation plan) | Full DIN EN 16247 audit needs a qualified auditor; we produce the data + measure plan that supports it |

### Tier B — Mandatory at trigger (official-issuer caveat)
| Report | Basis | Trigger | Data | Caveat |
|--------|-------|---------|------|--------|
| **Energieausweis pre-assessment (EPC)** | GEG §79–88 / EPBD | Sale, lease, new build | EPC class, EUI | From ~July 2026 NWG must use **Bedarfsausweis** (Verbrauchsausweis → residential only); new A–G scale. A legally-valid certificate needs an authorised Aussteller (DIN V 18599). We produce a **pre-assessment / rating report**, not the registered Ausweis |

### Tier C — Voluntary, in-demand, data-ready
ESRS E-1 (definite, flagship) · VSME · GHG Inventory (GHG Protocol) · EU Taxonomy · CRREM decarbonisation pathway · GRESB. (Per §1.2 / §3.)

### Revised build sequence
- **P1:** per-building report button + RLS scoping + **CO₂ cost-allocation report** (mandatory, simplest, every landlord, ties to the residential/B011 vertical) + **building energy / GEG / EPC pre-assessment report**. Structured narrative editor + PDF/DOCX.
- **P2:** ESRS E-1 (flagship) on the same engine + XBRL export.
- **P3:** EnEfG Maßnahmenplan, VSME, GHG Inventory, EU Taxonomy, CRREM pathway, GRESB.

### Added legal guardrails
- CO2KostAufG: **non-residential = 50/50** until the NWG stair model is enacted — never apply the 10-stair to commercial.
- EPC: say **"energy pre-assessment / rating"**, never "Energieausweis" (official, issuer-bound).
- EnEfG: **"audit support / Maßnahmenplan"**, not "completed DIN EN 16247 audit".
