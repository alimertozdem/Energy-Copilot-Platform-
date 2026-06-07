# Residential Segment & Resident Layer — Architecture Brief

**Status:** DRAFT — awaiting product-owner approval (Mert)
**BMAD layer:** Architecture (builds on the Business-layer brief)
**Builds on:** `docs/strategy/2026-06_growth_strategy.md`
**Date:** 2026-06-03

**Scope decisions locked this session:**
- **DE-first** (Turkey secondary)
- **Two segments:** Commercial (existing) + Residential (new)
- Residential has **two user layers** — Manager + **Resident (in V1)**
- **Hardware-optional** onboarding
- **Extend** the existing app/platform — do not rebuild

> Energy-logic and privacy assumptions in this brief are stated explicitly and marked
> **[ASSUMPTION]** / **[NEEDS APPROVAL]**. Nothing here is implemented yet.

---

## 1. Why now — the timing wedge

The EU Energy Efficiency Directive, implemented in Germany via the revised
**Heizkostenverordnung (HKVO, 1 Dec 2021)**, forces residential transparency on exactly
our timeline:

| Date | Obligation |
|---|---|
| since 2022 | Where remotely-readable meters exist → **monthly** consumption info to tenants |
| **31 Dec 2026** | All residential buildings must have remotely-readable metering devices |
| **1 Jan 2027** | **General obligation** to provide monthly consumption info (UVI) to tenants |
| § 12 HKVO | Tenant may **withhold 3%** of their heating-cost share if not informed |

**Implication:** managers are being legally pushed into monthly per-resident transparency
precisely as EnergyLens arrives. We **productize the obligation** — the resident layer is
both a compliance tool (manager avoids the 3% penalty, satisfies UVI) and a stickiness
driver. This is the resident layer's business case.

> Legal positioning (carry the compliance-hub rule): market this as
> **"EED/HKVO-aligned consumption-information support"**, *not* "guarantees legal
> compliance". DSGVO handling (§5) to be validated.

---

## 2. Architecture principles

**Carry-over (unchanged):** medallion Bronze/Silver/Gold · multi-tenant Row-Level Security ·
tier-aware ingestion (batch/stream) · modular technology-profile logic · extensible
regulation layer.

**New for residential:**
1. **Segment is derived from `building_type`** — not a parallel system. `Residential`
   becomes a building type alongside Office/Retail/etc.
2. **Add a `unit` grain** below building; preserve single-FK discipline:
   `org_id → building_id → unit_id`.
3. **Resident = lightweight, privacy-first, no Power BI license** (cost + data protection).
4. **Reuse the existing 3-layer access model** (RLS data + AppNav module gating + tier) —
   extend it, don't invent a new mechanism.

---

## 3. The four architecture blocks

### 3.1 Block 1 — User & Access model  **[V1-critical]**

**Personas:** existing B2B roles (Energy/Facility Manager, Owner, Consultant) **+ new
`Resident`** (the apartment occupant / tenant).

**Data model additions:**
- `dim_building`: add `building_type = Residential`, `unit_count`, `common_area_m2`.
- **NEW `dim_unit`** — `unit_id` (PK), `building_id` (FK), `floor`, `area_m2`,
  `unit_type`, and a reference to a resident identity (see below). No tenant names in the
  analytics tables — identity is held only in the Postgres control plane.

**RLS scopes (extend building-level RLS down to unit-level):**

| Scope | Sees |
|---|---|
| Platform admin | everything (existing) |
| Org / Manager | their org's buildings + **per-unit** consumption (legitimate for HKVO cost allocation) + common area |
| **Resident** | **own unit only** + **aggregated/anonymized** building benchmark + common-area share |

**Resident identity (scale + privacy):** residents are **not org members**. Default to a
**lightweight magic-link / invite token** bound to a `unit_id` (minimal PII: email + unit),
with an **optional full account** for residents who want one — separate from the paying
NextAuth B2B accounts. Rationale: N residents × M buildings = thousands of low-activity
users; we must not load them into the org-member model or pay per-user PBI licensing.

**Manager per-unit visibility — RESOLVED (purpose-based):** the manager sees per-unit
consumption in the **billing / cost-allocation** context (legitimate under HKVO), while
**comparative / benchmark** analytics are anonymized + aggregated. Org-configurable.

### 3.2 Block 2 — Data connectivity (hardware-free onboarding)

**Medallion mapping:**
```
Bronze  raw per source (bill CSV, heat-cost-allocation export/API, smart-meter feed)
  → Silver  normalized to {building_id, unit_id?, timestamp, energy_type, value, unit}
    → Gold   building EUI · heating kWh/m²/unit · common-area split · per-unit benchmark
```

**Source priority (DE residential) — RESOLVED: build bill CSV + heat-cost API in parallel:**

| # | Source | Grain | Note |
|---|---|---|---|
| 1 | Building bill / meter — **manual CSV upload** | building | Lowest friction, every building, instant value |
| 2 | Heat-cost-allocation API (**Techem / ista / Brunata**) | **unit + heating** | Foundation of the resident view; data already mandated |
| 3 | Smart-Meter Gateway / boiler-cloud API (Viessmann, Vaillant) | building/unit, sub-hourly | Later; enables near-real-time tier |

> Decision: deliver sources 1 and 2 **in parallel** (product owner wants full coverage).
> Risk to watch: parallel build splits effort and may extend V1 — sequence inside P2 if needed.

**Adapter pattern:** extend the existing Phase-2 adapter framework
(`00_iot_adapter_framework`) with a **submetering/billing adapter family**; each adapter
normalizes its source to the Silver contract. Same pattern that already serves IoT.

**Common-area vs. unit split — RESOLVED (HKVO-compliant, default 70/30):**
`building_total = Σ(unit consumption) + common_area (Allgemeinstrom)`. Shared heating/DHW is
split per HKVO: **default 70% consumption / 30% area**, per-building override to 50/50, and
the § 7 three-condition case (pre-1994 + oil/gas + insulated pipes ≈ 2.5% of stock) forces
70/30 automatically.

**Cadence → tier:** bills monthly, heat-cost monthly, smart-meter 15-min → maps to existing
Insight (batch) / Monitor (near-real-time) tiers.

### 3.3 Block 3 — Packaging & payment

**Existing:** Stripe self-serve, 4 tiers, **org pays** (Day 43).

**New — RESOLVED:**
- **Segment-based plans** — a Residential plan distinct from the Commercial plan.
- **Pricing unit = per-building base + per-unit band** (value scales with unit count;
  bands e.g. 1–20 / 21–50 / 51+). Exact price points are placeholders **[NEEDS APPROVAL]**.
- **Resident seats = FREE / included** in the manager subscription. **Never** a separate
  paywall — privacy, scale, and adoption all argue against it.
- **DE B2B:** add **SEPA / invoice** payment to Stripe (B2B managers rarely pay by card).

### 3.4 Block 4 — App information architecture

**Segment-aware navigation:** `building_type` selects the page set. A Residential building
shows heating-centric pages + the resident view; a Commercial building shows the existing
pages. Gating reuses the AppNav module-lock mechanism (already built).

**Manager app (reuse + extend):** portfolio / buildings / actions / alerts / compliance
(all reused) **+ residential KPIs** — heating kWh/m²/yr per unit, common-area consumption,
per-unit benchmark heatmap, UVI status per building.

**Resident app (new, lightweight):** a separate route (e.g. `/residence`) rendered as
**simple React — NO Power BI embed** (license + privacy + cost). 4–5 cards max:
1. My consumption (trend) 2. My unit vs. building average (anonymized) 3. Common-area share
4. (if PV) self-consumption 5. Saving tips (via `energy-insight-generator` skill / Copilot).

**EED artifact:** generate the **monthly consumption statement as a PDF** via the existing
`reportKit` — this *is* the UVI deliverable the manager must legally send. Reuses the
Day 39–42 PDF pipeline.

---

## 4. Data-model deltas (summary)

| Layer | Change |
|---|---|
| `dim_building` | + `building_type=Residential`, `unit_count`, `common_area_m2` |
| **`dim_unit`** (new) | `unit_id` PK, `building_id` FK, `floor`, `area_m2`, `unit_type` |
| Silver | + `unit_id` grain for submetered sources |
| Gold | + per-unit KPIs, + common-area split, + UVI-ready monthly aggregates |
| Postgres control plane | + resident identity table, + unit↔resident mapping, + segment/plan fields |

---

## 5. Access & privacy model — the V1 crux

Because the resident layer is in V1, this is the highest-risk surface.

- **RLS dimensions:** `org_id → building_id → unit_id`.
- **Manager:** portfolio + per-unit (billing context, legitimate for HKVO cost allocation) +
  common area; comparative analytics anonymized (purpose-based, per §3.1).
- **Resident:** own unit + aggregated/anonymized building benchmark + common-area share —
  **never another named unit**.
- **DSGVO [NEEDS APPROVAL]:** consumption data is personal data. Apply data minimization
  (resident identity only in Postgres, not in analytics tables), purpose limitation
  (analytics beyond billing may need consent), and a retention policy. Treat like the
  compliance hub: provide "support", not legal guarantees.

---

## 6. Reuse vs. build-new (honesty check)

| Reuse (already built) | Build new |
|---|---|
| Medallion + Lakehouse + Delta | `Residential` building_type + `dim_unit` |
| RLS mechanism (extend to unit) | Unit-level RLS scope + resident identity (magic-link) |
| AppNav module gating | Segment-aware navigation |
| Stripe billing | Segment plans + per-unit band + SEPA |
| Adapter framework | Submetering/billing adapters |
| reportKit PDF | Resident UVI monthly statement |
| Recommendation / Copilot / energy-insight skill | Residential heating KPI set + common-area split |

The new surface is real but bounded — most of the platform is reused.

---

## 7. Phased delivery **within V1**

Even with the resident layer in V1, build in dependency order (resident UI ships last
because it depends on the model, the data, and access):

| Phase | Scope | Depends on |
|---|---|---|
| **P1** | Block 1 — `Residential` type + `dim_unit` + RLS scopes + resident identity | — |
| **P2** | Block 2 — ingestion: building bill CSV **+** heat-cost API (unit grain), in parallel | P1 |
| **P3** | Block 4 (manager) — residential KPIs + pages | P1, P2 |
| **P4** | Block 4 (resident) — `/residence` route + monthly UVI PDF + Block 3 packaging | P1–P3 |

---

## 8. Decisions — RESOLVED (2026-06-03 session)

All six items were decided with the product owner this session:

**Product / access**
1. **Manager per-unit visibility** = purpose-based — named per-unit in the billing /
   cost-allocation context (HKVO-legitimate), anonymized + aggregated in comparative
   analytics; org-configurable.
2. **Resident identity** = both — magic-link / invite by default + optional full account.
3. **Pricing** = per-building base + per-unit band (price points still to confirm).
4. **First ingestion** = bill CSV + heat-cost API **in parallel** (broader coverage; watch V1 scope).

**Energy logic**
5. **Shared-heating allocation** = HKVO-compliant, per-building, **default 70/30**
   (consumption-weighted; 50/50 override; § 7 three-condition auto-check).
6. **Heating KPI** = **climate-adjusted (HDD) kWh/m²/yr**, building + unit level.

---

## 9. Consultant / Partner layer  **[V1-critical — the unified-access foundation]**

> **Status:** design recorded for approval. The high-level GTM decision (sell to
> consultancies + commission; owner-direct secondary; founder dogfoods as a partner) is
> approved; the **schema choice in §9.3 is [NEEDS APPROVAL]** before any migration.

### 9.1 Why this layer is built first

The consultant layer is brought forward **ahead of** the residential data work because the
multi-tenant primitives it needs already exist and only have to be *composed*, not invented:

| Needed primitive | Already built |
|---|---|
| One principal reading **many** orgs | `/admin` cross-org repo + router (Day 23/25), platform-admin gate |
| Per-tenant data isolation | multi-tenant RLS (`org_id → building_id`) |
| White-label surface | `theme-factory` (logo / palette / wordmark scaffold) |
| Per-org billing | Stripe self-serve + tiers (Day 43) |
| Audited cross-org mutations | `audit_logs` + actor / IP capture (Day 25) |

**GTM (approved):** the **primary** motion is selling to consultancies / advisory firms and
taking a **commission** on the seats they resell; selling **owner-direct** stays secondary.
The founder uses the platform as a partner inside the existing freelance practice — this is
the **dogfood + first-validation** path and grants a **free partner subscription**.

### 9.2 The unified hierarchy (one model for two features)

P1 establishes a single 4-level access spine that serves **both** the consultant layer and
the residential resident layer — they are the top and bottom of the *same* hierarchy, so we
build it **once**:

```
partner_org (consultant)         ← Level 0  (advisory firm; manages many clients)
  └─ client_org (building owner)  ← Level 1  (the paying customer / Hausverwaltung)
       └─ building                ← Level 2  (existing grain)
            └─ unit (resident)     ← Level 3  (residential occupant — §3.1 / §5)
```

A partner is an **overlay above** existing orgs, not a replacement for them. A `client_org`
keeps **full ownership** of its own data; the partner receives a **delegated, revocable
grant** to act on the client's behalf — never silent ownership.

### 9.3 Schema choice  **[NEEDS APPROVAL — the one decision to confirm before migration]**

**Recommendation:** do **not** create a parallel partner hierarchy. Instead:

1. **Extend `organizations`** with `org_type ∈ {standalone, client, partner}`. A partner is
   *itself an organization* — so it inherits members, NextAuth auth, Stripe billing, and
   audit for free.
2. **Add one many-to-many grant table** `partner_client_link`
   (`partner_org_id`, `client_org_id`, `relationship_status`, `scope`, `commission_model`,
   `granted_by`, `revoked_at`, …). This is the *only* genuinely new control-plane table the
   consultant layer needs.

**Why this and not a new table family:** it reuses the `/admin` cross-org pattern almost
verbatim — that code is already "one principal authorized to read N orgs." We add an
**authorization edge** (the grant) rather than a second tenancy system. It preserves the
single-FK discipline (`org_id → building_id → unit_id`) and keeps one source of truth for
billing and audit. A partner managing many clients — and, rarely, a client served by more
than one partner — both fall out of the many-to-many edge naturally.

*Alternative considered & rejected:* a standalone `partner_orgs` table separate from
`organizations` — duplicates members / billing / audit, forks the RLS logic, and abandons
the already-working `/admin` cross-org code. Higher cost, no benefit.

### 9.4 Access — the 4-level RLS scopes

| Scope | Sees |
|---|---|
| **Platform admin** (founder) | everything (existing `/admin`) |
| **Partner** (consultant) | the **union of the buildings of the client_orgs it is actively linked to** (via `partner_client_link`), bounded by the granted `scope` (e.g. read-only advisory vs. full manage); **never** clients it is not linked to |
| **Client / Manager** | their own org's buildings + per-unit consumption (HKVO billing context) + common area — existing model, unchanged |
| **Resident** | own unit + aggregated / anonymized building benchmark + common-area share (§5) |

**Resolution continuity (carry the proven read path):** RLS is resolved in the **control
plane (Postgres)** → the backend filters Fabric reads by the **building_id set** the
principal may see. This is the same approach forced by the Day-15 `pyodbc + SQL Analytics
Endpoint` finding and the Day-29 result that **DirectLake embed tokens reject
`effectiveIdentity`** — so partner scope is *also* applied as a backend building_id filter,
not as a native Power BI RLS identity. No new read-path risk is introduced.

### 9.5 White-label & commercial

- **White-label:** each `partner_org` carries a `theme-factory` profile (logo, palette,
  wordmark). Already scaffolded — the partner layer just selects it per tenant / request.
- **Billing & commission [NEEDS APPROVAL]:** the partner pays the platform (or revenue-share);
  the commission terms live on `partner_client_link.commission_model`. The payout mechanism
  is a **design-time** choice — Stripe Connect (automated split) **vs.** manual invoice
  reconciliation — to confirm later; **not** on the P1 critical path.

### 9.6 Reuse vs. build-new (honesty check)

| Reuse (already built) | Build new (bounded) |
|---|---|
| `/admin` cross-org repo + router | `org_type` column on `organizations` |
| multi-tenant RLS + building_id filtering | `partner_client_link` grant table + scope resolution |
| theme-factory white-label | partner-scoped theme selection |
| Stripe billing + audit_logs | commission fields + (later) payout integration |

---

## 10. Financing bridge  **[capability layer — post-residential, not in P1]**

> **Status:** scope recorded for approval. Sequenced **after** the residential vertical
> (post-P4); documented here so the access model is designed with it in mind — **not** built now.

### 10.1 What it is

A capability layer that converts the platform's existing **recommendation** and
**compliance** outputs into **financing actions**:

1. **Subsidy-application automation** — pre-fill and assemble **KfW / BAFA** application
   packages from data the platform already holds (building, measure, ROI, EPC, CRREM).
2. **Green-loan / partner-bank referral** — route a qualified, subsidy-stacked CapEx plan to
   a financing partner as a **referral**, not as lending.

### 10.2 Why it belongs to the consultant GTM

Subsidy capture is the single biggest "no → yes" lever in the residential business case
(BAFA 30–70%, growth-brief §4.4). Consultants live on getting clients **funded**; an
origination / commission fee on financing aligns cleanly with the §9 partner-commission
model. It deepens the moat without new sensors or hardware.

### 10.3 Architecture sketch (build-time, later)

- **Eligibility** reuses the **compliance hub** (MEPS / CRREM / EU-Taxonomy screens) + the
  **recommendation engine** — no new analytics primitives.
- **Document generation** reuses **reportKit** (the Day 39–42 PDF pipeline) for the
  application pack and the financing one-pager.
- **State** is tracked like `actions` / `alerts` — a `financing_application` control-plane
  entity with status + audit, mirroring the existing overlay pattern.
- **Gold** adds only thin `gold_financing_*` aggregates if needed; most logic is
  control-plane + document assembly.

### 10.4 Guardrails  **[ASSUMPTION / NEEDS APPROVAL]**

- **Positioning (carry the compliance-hub legal rule):** market as **"subsidy-application
  support"**, *never* "financial advice" or "guaranteed approval." A bank partnership is a
  **referral**, not a lending product.
- Subsidy rules (BAFA MFH per-unit caps, KfW programme numbers) are **time-sensitive
  assumptions** — verify against the live programme at build time, not from cached values.

### 10.5 Explicitly parked (horizon — do not build now)

Benchmark data product · public API / embed · tenant gamification · installer marketplace.
These remain deferred (positioning risk); recorded here so they are not accidentally pulled
into V1 scope.

---

## 11. References

- HKVO / EED monthly consumption info (UVI), 2026/2027 deadlines, § 12 rule:
  [Haufe](https://www.haufe.de/immobilien/verwaltung/unterjaehrige-verbrauchsinformation-fristen-fuer-verwalter_258_644426.html) ·
  [ista — HKVO 2026](https://www.ista.com/de/gesetze-und-verordnungen/heizkostenverordnung/) ·
  [Techem — Verbrauchsinformation / EED](https://www.techem.com/de/de/immobilienservices/verbrauchsinformation)
- Distribution key (Verteilerschlüssel) 50–70% rule, § 7:
  [Haufe](https://www.haufe.de/recht/deutsches-anwalt-office-premium/heizkv-heizkostenabrechnung-33-verteilerschluessel-und-anteil-des-nutzers_idesk_PI17574_HI2118432.html) ·
  [Minol](https://www.minol.de/en/blog/verteilerschlussel-in-der-heizkostenabrechnung/)
- Business-layer brief: `docs/strategy/2026-06_growth_strategy.md`
- Existing architecture: `docs/architecture/architecture-overview.md`,
  `docs/architecture/iot-page8-fdd-architecture.md`
