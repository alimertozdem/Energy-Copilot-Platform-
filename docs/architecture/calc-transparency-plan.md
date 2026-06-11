# EnergyLens — Calculation Transparency Tooltips (app-wide plan)

> **Status:** PLAN for approval (Mert, 2026-06-11). Idea (Mert): show the user *how each number is
> calculated + key assumptions* in a tooltip, app-wide — to build trust in the figures.
> **Nature:** UX/architecture plan. No code yet; this document defines the design, the metric
> catalog (which metric, where), and a phased rollout. Build follows approval.

---

## 1. Goal & principle

Every calculated figure the app shows (EUI, payback, CO₂, stranding year, retrofit saving …) should
be able to answer, in one hover/focus: **"how is this computed, on what assumptions, and how
confident should I be?"** This is on-brand with the platform's existing honesty layer — the glossary
already states "rules of thumb… simple payback… no invented engineering thresholds" — and it
directly serves sales/audit trust: a number you can interrogate is a number a customer believes.

## 2. Why this is cheap: the infrastructure already exists

| Existing piece | What it does | Reuse |
|---|---|---|
| `lib/glossary.ts` | Single-source registry: `Record<TermKey,{label,short,full,category}>` (17 terms) | **Extend** with method/assumptions |
| `components/ui/info-tip.tsx` (`InfoTip`,`TermLabel`) | radix Tooltip "i" trigger; a11y (focus, Esc, aria) built-in; stops propagation in tables/links | **Reuse** as-is + a `method` section |
| `app/glossary/page.tsx` | Public reference page rendering each entry's `full` | **Extend** with a "How it's calculated" block |
| Mounted in 11+ components | KPITile, SolarDetail, ActionsTable, AlertsTable, BuildingsTable, compliance/* | Tooltips already on-screen → add method to the same anchors |

The work is **content + a small render change**, not new infrastructure.

## 3. Architecture — recommended: extend the existing registry (one source of truth)

Rather than a parallel `calcMethodology.ts` (which would drift from `glossary.ts`), **add optional
fields to the glossary entry** so each metric carries both its definition *and* its method:

```ts
export type GlossaryEntry = {
  label: string
  short: string                 // hover/focus definition (unchanged)
  full: string                  // /glossary definition (unchanged)
  category: GlossaryCategory
  method?: string               // NEW — one-line "how it's computed" (formula in words)
  assumptions?: string[]        // NEW — key inputs/assumptions (e.g. factor, period, basis)
  confidence?: "measured" | "indicative" | "screening"  // NEW — drives the disclaimer chip
  sourceRef?: string            // NEW — doc/section the method comes from (no drift)
}
```

- **`InfoTip`** renders the existing `short`, then — when `method` is present — a divider + a compact
  "**How it's calculated**" line + a confidence chip (`indicative` / `screening`). Long detail lives
  on `/glossary` (tooltip stays ≤ ~260px; it shows the one-liner + "details on /glossary").
- A new **`CalcTip`** thin wrapper = `InfoTip` defaulted to open on the method section, for figures
  that are *calculated values* rather than *terms* (same component, different default).
- **Non-term figures** (residential retrofit saving, MACC €/tCO₂, anomaly est. cost, GHG scopes) get
  **new registry entries** — the registry becomes the app's single "knowledge layer."

**One source, no drift:** each `method`/`assumptions` text is lifted from an authoritative doc
(`sourceRef`) — the residential calc doc, the GHG methodology doc, or the glossary caveats — so the
app, the /glossary page, and the docs always agree.

## 4. Metric catalog & rollout map (which metric, where, what it says)

> `confidence`: **M** measured · **I** indicative · **S** screening. Every entry ends with the
> matching disclaimer (e.g. screening → "not a compliance verdict / needs a building audit").

| Metric | Where (component) | Method (one-line) | Key assumptions | Conf | Phase |
|---|---|---|---|---|---|
| **EUI** | KPITile, BuildingsTable | annual energy ÷ heated floor area (kWh/m²·yr) | final energy; heated area; 12-mo window; "good" varies by type/climate | I | 1 |
| **Total energy** | KPITile | Σ metered/bill consumption over period | meter vs bill source; period normalised | M | 1 |
| **Energy cost (€)** | KPITile, portfolio | Σ(energy × tariff) | tariff = contract or default; excl/incl VAT stated | I | 1 |
| **CO₂ (t)** | KPITile, GHG | Σ(energy × emission factor) | grid 363 g/kWh (UBA 2024), gas 0.201 kg/kWh; location-based Scope 2 | I | 1 |
| **Payback (yr)** | ActionsTable, recommendations | net CapEx (after subsidy) ÷ annual € saving | **simple** payback; no financing/discounting (see NPV/IRR) | I | 1 |
| **Specific yield** | SolarDetail | annual generation ÷ installed kWp (kWh/kWp) | DC/AC basis; 12-mo | M | 2 |
| **Performance ratio** | SolarDetail | actual ÷ (kWp × irradiance) | irradiance source; ~0.75–0.85 healthy | I | 2 |
| **Self-consumption / -sufficiency** | SolarDetail | gen used on-site ÷ gen · gen used ÷ total load | interval data resolution | M | 2 |
| **Abatement cost €/tCO₂ (MACC)** | /decarbonisation | annualised net measure cost ÷ annual tCO₂ avoided | measure lifetime; carbon price; ranking only | I | 3 |
| **CRREM stranding year** | CrremStranding | first year building intensity > CRREM pathway | flat performance; chosen pathway | I | 3 |
| **MEPS renovation risk** | MepsRadar | EPC class vs EPBD worst-X% thresholds | national MEPS not final → **risk, not verdict** | S | 4 |
| **EU Taxonomy (7.7)** | TaxonomyScreen | EPC A or top-15% primary energy | climate-mitigation SC only; DNSH/safeguards out of scope | S | 4 |
| **ESRS-E1** | EsrsSummary | energy + Scope 1/2/3 GHG | Scope 3 estimated; reporting support, not audited | S | 4 |
| **Demand flexibility** | FlexibilityPanel | readiness signal from connected assets | battery/controls/sub-metering present; not a savings guarantee | I | 4 |
| **GHG Scope 1/2/3** | GHG / Page 6 | S1 on-site fuel × factor · S2 elec × grid · S3 estimated upstream | factor year; location-based; S3 partial | I | 5 |
| **Anomaly est. cost (€)** | AlertsTable | duration × power-waste kW × grid price | HVAC 2–5 kW/°C · CO₂ spike 1–3 kW · power spike = excess; DE €0.20 / TR €0.14 | S | 5 |
| **Residential retrofit saving** | residential plan view | ΔU×A×Gt÷η (fabric) · empirical % (operational) | per `residential-retrofit-calculations.md`; screening-grade | S | 5 |

*(Solar/compliance terms already have a definition InfoTip on these anchors — Phase 2–4 adds the
`method` section to the same tooltip, so no new placement work.)*

## 5. Content single-source (no drift)

| Metric group | `sourceRef` |
|---|---|
| Residential retrofit (Tier 0/1/2) | `docs/strategy/residential-retrofit-calculations.md` |
| GHG scopes, emission factors | `docs/ghg_methodology.md` |
| Compliance (MEPS/CRREM/Taxonomy/ESRS) | existing glossary `full` + `docs/.../compliance` notes |
| Payback / MACC | glossary `payback` caveat + decarbonisation doc |

## 6. Honesty & legal framing (per confidence tier)

- **measured (M):** state inputs (source, period) — no hedging needed beyond data provenance.
- **indicative (I):** "indicative — varies by building/climate; refine with your data."
- **screening (S):** "screening-grade, **not a compliance verdict**; a building-specific audit
  replaces this." Compliance copy keeps the approved legal wording ("ESRS-E1-aligned, not audited";
  "indicates a route, not a Taxonomy-aligned claim") — do **not** upgrade to "compliant".

## 7. Rollout phases (ship measure-by-measure; each is independently shippable)

1. **Pilot — core KPIs:** EUI, energy, cost, CO₂, payback (KPITile + portfolio). Proves the pattern.
2. **Solar:** specific yield, PR, self-consumption/-sufficiency (SolarDetail).
3. **Financial/Strategy:** savings, MACC abatement cost, CRREM stranding.
4. **Compliance:** MEPS, EU Taxonomy, ESRS-E1, flexibility (extend existing term tooltips).
5. **Residential + anomaly cost + GHG scopes.**

## 8. Acceptance criteria

- `tsc --noEmit` clean; `InfoTip` a11y preserved (focus/Esc/aria; stops propagation in tables).
- `/glossary` page renders the new "How it's calculated" block for every entry that has `method`.
- Every `method` has a `confidence` + a matching disclaimer and a `sourceRef` (no orphan numbers).
- No engineering threshold invented in-code — all trace to a `sourceRef`.

## 9. Open decisions (need product-owner input)

1. **Architecture:** extend `glossary.ts` (recommended — one source) vs a separate
   `calcMethodology.ts` registry?
2. **Tooltip vs page:** long methods — show a 1-line method in the hover tooltip + full detail on
   `/glossary` (recommended), or expand the tooltip itself?
3. **Phase order:** confirm 1→5 above, or reprioritise (e.g. compliance before solar for the
   EXIST/CSRD narrative)?
