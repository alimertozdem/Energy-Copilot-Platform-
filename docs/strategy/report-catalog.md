# Report Catalog — what each report is, who needs it, how it's delivered

**Purpose:** plain reference for the EnergyLens report family — what each report actually is,
who is obliged to produce it, to whom and how it is delivered, the real-world format, and
our build status. Use it to decide which report to build next and how to position it.
**Date:** 2026-06-12 · **Legal framing:** "reporting support", never "statutory filing on the customer's behalf".

> **Status snapshot:** 1 of 10 built. **CO₂ Cost Allocation (CO2KostAufG)** is live. The
> **ESG reports (ESRS E-1 / VSME / GHG inventory)** are NOT built yet — they are the next
> phase. So we are at the start of the German-mandatory set; ESG is still ahead.

---

## Tier A — German legally-mandatory (priority; producible from our data)

### 1. CO₂ Cost Allocation — CO2KostAufG ✅ BUILT
- **What:** splits the heating-fuel CO₂ price (national nEHS / from 2028 EU ETS2) between landlord and tenant by building efficiency.
- **Who must produce it:** every landlord renting out space with fossil heating (gas/oil).
- **To whom / how:** disclosed **inside the annual heating-cost statement (Heizkostenabrechnung)** handed to the tenant — *not* filed to any authority. The landlord bears their computed share. The fuel supplier must print the kg CO₂, emission factor (kg/kWh), energy content (kWh) and CO₂-cost (€) on the fuel bill; the landlord does the per-m² split.
- **Real format / required elements:** Brennstoffemissionen (kg CO₂) · Emissionsfaktor (kg CO₂/kWh) · Energiegehalt (kWh) · CO₂-Kostenanteil (€) · kg CO₂/m²·yr (living area) · step (1–10) · landlord/tenant % · split amounts. Residential = statutory 10-step model; non-residential = flat 50/50.
- **When:** annually, with the heating-cost statement.
- **Our status:** built; the report carries all four supplier-disclosure elements + the full split. Decision-support, not the legal Abrechnung.

### 2. GEG conformity — Gebäudeenergiegesetz
- **What:** the building energy law — new/replaced heating ≥ 65 % renewable (since 2024), envelope U-value minimums, retrofit duties (e.g. on ownership change).
- **Who:** building owners — new build, heating replacement, major renovation, post-purchase obligations.
- **To whom / how:** enforced via the building permit, the chimney sweep (Schornsteinfeger) heating check, and duties triggered on sale — not a periodic submission; it is conformity evidence held by the owner.
- **Real format:** per-measure Nachweis / conformity documentation.
- **When:** at trigger (build, heating change, sale).
- **Our status:** not built; we already compute GEG checks (screening) → a conformity summary is straightforward.

### 3. EnEfG energy audit + Umsetzungsplan — Energieeffizienzgesetz
- **What:** mandatory **energy audit (DIN EN 16247)** for mid-size consumers; **energy-management system (EnMS)** for large ones; plus **published, externally-reviewed implementation plans (Umsetzungspläne)** listing the *economic* saving measures.
- **Who:** non-SME companies above the consumption thresholds. Audit historically > 2.5 GWh/yr (2026 Novelle raising it to ~2.77 GWh); EnMS > 7.5 → raised to ~23.6 GWh; Umsetzungsplan publication for > 2.5 GWh consumers.
- **To whom / how:** the audit is kept and shown to **BAFA** on request; the **Umsetzungspläne must be published** (publicly) and externally reviewed. BAFA enforces — a nationwide control wave started March 2026 (formal Auskunftsersuchen + sample checks).
- **Real format:** DIN EN 16247 audit report + a published Umsetzungsplan. A measure is "economic" when its net present value turns positive within 50 % of its useful life.
- **When:** audit every 4 years (first under new rules ~Oct 2026); plan within 3 months of the audit/certification.
- **Our status:** not built; our `gold_recommendations` (measures + ROI + the same economic filter) **directly feed the Umsetzungsplan**. A full audit still needs a qualified auditor — we produce the supporting data + measure plan.

---

## Tier B — Mandatory at trigger (official issuer required)

### 4. Energieausweis (EPC)
- **What:** the energy-performance certificate (demand- or consumption-based), class A–G.
- **Who:** owners selling, letting, or constructing.
- **To whom / how:** only a **qualified Aussteller** (Energieberater / architect / certified expert) may issue it; the Aussteller registers each certificate with the **DIBt (GEG-Registrierstelle)** for a Registriernummer (€6.30). The owner must show it at viewings, hand it over on sale/lease, and quote its data (incl. Registriernummer) in property ads (§ 87 GEG). DIBt runs sample checks (§ 99). Fines up to €10,000.
- **Real format:** the official Energieausweis form. From ~July 2026 non-residential buildings must use the **Bedarfsausweis**; new A–G scale.
- **When:** at sale / lease / new build.
- **Our status:** not built; we can produce a **pre-assessment / energy rating** — **not** the legally-registered certificate (that needs the registered Aussteller). Position as screening/preparation only.

---

## Tier C — ESG / sustainability (voluntary for most post-Omnibus, or large-company mandatory)

### 5. ESRS E-1 / CSRD — the flagship "ESG report"
- **What:** the **climate chapter** of the CSRD sustainability statement (E1-1…E1-9: transition plan, policies, targets, energy, Scope 1/2/3 GHG, anticipated financial effects).
- **Who:** post-Omnibus, only **large companies (> 1,000 employees AND > €450M turnover)**. Most SMEs are out of scope.
- **To whom / how:** filed **inside the annual management report (Lagebericht)**, subject to (limited) **assurance by an auditor**, published in the **Unternehmensregister**, **digitally tagged (iXBRL/ESEF)** per the ESRS taxonomy, and from 2028 filed to the EU **ESAP**.
- **Real format:** iXBRL / XHTML (ESEF package) — machine-readable + human-readable.
- **When:** annually with the financial report (Wave 1 continues; Wave 2 from 2028 / FY 2027).
- **Our status:** **not built.** E1-5 (energy) + E1-6 (Scope 1/2/3) data is ready/auto; E1-1…E1-4 need the structured narrative editor. This is the planned flagship.

### 6. VSME — Voluntary SME Standard (EFRAG)
- **What:** a streamlined ESG report for non-listed SMEs (Basic + Comprehensive modules).
- **Who:** SMEs voluntarily — usually because a **bank** (lending), a **large customer** (value-chain / CSRD trickle-down) or an **investor** asks for ESG data.
- **To whom / how:** handed directly to the bank / customer / investor on request — **no authority filing**. A digital template + XBRL taxonomy is in development (delegated act expected ~summer 2026).
- **Real format:** the VSME template (PDF/structured; XBRL coming).
- **When:** on request / annually.
- **Our status:** not built; the environmental module is a subset of our E-1 data → cheap once the engine exists.

### 7. GHG Inventory (GHG Protocol Corporate Standard)
- **What:** a Scope 1/2/3 corporate carbon inventory.
- **Who:** any company voluntarily (carbon accounting, CDP, customer requests).
- **To whom / how:** internal use, or shared with customers / CDP / investors — no authority filing.
- **Real format:** GHG Protocol Corporate Standard report.
- **Our status:** not built; maps `gold_ghg_scope` 1:1 → **near-free** once the engine exists. The most common freelance carbon-accounting deliverable.

### 8. EU Taxonomy alignment
- **What:** turnover / capex / opex alignment KPIs against the EU green taxonomy.
- **Who:** part of CSRD for in-scope companies; voluntary screening otherwise.
- **Our status:** not built; we already screen taxonomy in `/compliance`.

### 9. CRREM decarbonisation pathway
- **What:** asset-level stranding risk + retrofit roadmap vs the 1.5 °C pathway.
- **Who:** property owners / funds voluntarily (investor-driven).
- **Our status:** not built; we have CRREM + simulation data.

### 10. GRESB
- **What:** the real-estate investor ESG benchmark.
- **Who:** funds / portfolio owners submit annually to GRESB B.V.
- **To whom / how:** annual portfolio submission to GRESB (investor benchmark, scored).
- **Our status:** not built; building energy/GHG/EPC data feeds it.

---

## How to read this for the business

- **Authority-filed vs party-to-party.** Only a few are filed to an authority (ESRS/CSRD → Unternehmensregister/ESAP; EnEfG Umsetzungsplan → published, BAFA-checked; Energieausweis → DIBt registration). Most are **delivered directly** to a tenant (CO2KostAufG), a bank/customer (VSME), or investors (GRESB, CRREM). That shapes the product: we mostly produce **a document the customer hands to someone**, not a government e-filing.
- **Where an official issuer is required** (Energieausweis Aussteller; ESRS auditor assurance), we produce **supporting/pre-assessment** material, not the legally-binding artifact — stated on every such report.
- **Build order so far:** German-mandatory, data-ready first (CO2KostAufG ✅). Natural next steps: GHG Inventory (near-free, a real ESG deliverable), then ESRS E-1 (flagship) / VSME, or the remaining German set (GEG, EnEfG).
