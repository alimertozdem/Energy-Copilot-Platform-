# EnergyLens — Growth Strategy Brief
## Differentiation Layers + Residential Portfolio Expansion

> **Status:** DRAFT — awaiting product-owner approval (Mert)
> **Date:** 2026-06-03
> **BMAD layer:** Business (segments, value proposition, product boundaries) — precedes Architecture / Data / Logic
> **Nature:** Strategy synthesis from a brainstorming session. No code or schema changes yet.

---

## 0. Trigger

Two inputs prompted this brief:

1. **External critique:** "This project doesn't look attractive *today* — current energy prices and the high cost of smart-building tech infrastructure (sensors etc.) make the payback weak, especially for anything smaller than very large facilities."
2. **Product-owner question:** Can the platform be *scaled down* to smaller buildings (e.g. a 5–10 storey, 30–40 unit apartment block) with an investment + savings story strong enough to convince the owner? Is the platform really only profitable / green for large facilities?

This document evaluates the critique, then converts the four agreed directions into one coherent architecture with a dependency-ordered roadmap.

---

## 1. Evaluating the critique — myth vs. reality

The critique is a useful warning but is mostly a **positioning error**, not a fatal flaw. Split it into its two claims.

### 1.1 "Energy prices make efficiency unattractive"

For our target market (Germany / EU) energy is among the **most expensive** in the world, so the savings per kWh avoided are large — efficiency is *more* attractive here, not less. More importantly, the **cost of doing nothing is rising**, independent of today's tariff:

| Mechanism | 2025 | 2026 | Trajectory |
|---|---|---|---|
| German national CO₂ price (nEHS, heating + transport fuels) | €55/t (fixed) | €55–65/t auction corridor (max €68 in subsequent sales) | Converges into EU ETS2 |
| EU ETS2 (buildings + transport) | — | — | Launch postponed from 2027 → **2028** (agreed Nov 2025); corridor €55–65 kept through 2027; BloombergNEF forecasts **~€149/t by 2030** |

**Implication:** the business case *strengthens over time*. The valid kernel of the critique is that a **pure "save money on energy" pitch is weak** in cheap/subsidised-energy contexts (Turkey, US). The fix is to make the wedge **compliance + rising carbon cost + asset value**, none of which depend on today's tariff.

### 1.2 "Sensor / infrastructure cost is too high"

This is valid **only if** the product is framed as "install a full BMS with hundreds of sensors." EnergyLens is a **software intelligence layer; hardware is optional**:

- The architecture already separates a **minimum sensor set** (meter / bill data) from an **extended set** (full BMS). Report Pages 1–7 run on meter/bill data alone.
- The marginal cost of onboarding a building to a SaaS analytics layer is ≈ €0.
- The objection therefore applies to **hardware vendors** (Siemens Desigo, Schneider EcoStruxure retrofits), **not** to a layer that rides on data the building already produces.

**Implication:** being the **low-CapEx, no-hardware-required intelligence layer is the differentiator.** The answer to the critique is baked into a positioning choice — see §3.2.

---

## 2. The core reframe: the unit of sale is the PORTFOLIO, not the building

A single 35-unit apartment block cannot justify a bespoke platform — true. But we never sell to one building; we sell to **whoever manages 200 of them:**

- Property managers (*Hausverwaltung*)
- Housing companies & cooperatives (*Wohnungsunternehmen / Genossenschaften*)
- Institutional landlords (e.g. Vonovia ≈ 500k units)

The platform is **already portfolio-first and compliance-aware.** The single-building investment plan becomes a *drill-down* inside a portfolio CapEx-prioritisation tool. The buyer's real pain:

> "I manage 8,000 apartments. EPBD requires renovating the worst-performing stock, carbon cost is rising, my capital is constrained — **which buildings first, which measures, what is the ROI and the compliance payoff?**"

That is precisely what portfolio benchmarking + CRREM stranding + the recommendation engine + a marginal-abatement-cost curve answer.

---

## 3. Synthesis of the four agreed directions

The four selected directions are **not competing options** — they are one architecture: **two horizontal differentiator layers** (work in every segment) on top of which sit **two go-to-market verticals.**

```
   ┌─────────────────────── GO-TO-MARKET VERTICALS ───────────────────────┐
   │   D. Commercial (existing — deepen)      C. Residential (new segment) │
   └───────────────────────────────────────────────────────────────────────┘
   ┌─────────────────────── HORIZONTAL LAYERS (segment-agnostic) ─────────┐
   │   A. CO₂-forward ROI + auto MACC curve                                │
   │   B. No-hardware "bill/meter → insight" onboarding                    │
   └───────────────────────────────────────────────────────────────────────┘
   ┌─────────────────────── CORE ENGINE (already built) ──────────────────┐
   │   KPI engine · anomaly detection · simulation · recommendation ·      │
   │   compliance hub · portfolio benchmarking · Copilot                   │
   └───────────────────────────────────────────────────────────────────────┘
```

### 3.1 Layer A — CO₂-forward ROI + automatic MACC curve
- **What:** bake the rising carbon-cost trajectory (§1.1) into *every* ROI/payback, and auto-generate a **Marginal Abatement Cost Curve** — rank every measure across the portfolio by €/tCO₂ avoided and €/kWh saved.
- **Why it differentiates:** almost no competing tool prices the *cost of doing nothing* forward, or produces a portfolio MACC automatically. It is the CFO / sustainability-lead view.
- **Reuses:** existing simulation + recommendation engine outputs; we add a carbon-price curve table and a ranking measure layer.

### 3.2 Layer B — No-hardware onboarding
- **What:** a "bill/meter → insight" fast path: ingest utility bills, smart-meter exports, and (for residential) existing heat-cost-allocation data, with zero new hardware.
- **Why it differentiates:** directly neutralises the sensor-cost objection (§1.2) and slashes the adoption barrier. It is also a **prerequisite** for the residential vertical, where sensors are absent but billing/sub-metering data exists.

### 3.3 Vertical C — Residential portfolio (new) — see §4.

### 3.4 Vertical D — Commercial (existing) — deepen
- Continue the current commercial line (office / retail / hotel / healthcare / education / logistics). It carries today's revenue and reference customers. Layers A + B strengthen it immediately.
- High-fit commercial sub-segments to target: **branch/retail chains, public sector (schools, municipalities)** — many near-identical small buildings, compliance pressure, no in-house energy manager.

---

## 4. Residential vertical — deep dive

### 4.1 Why residential is structurally different
- **Heating + domestic hot water dominate** (~60–70% of energy use in Central-European apartment blocks — *assumption, range, to validate*). Value is **heating-centric**, not chiller/HVAC-centric.
- **Split-incentive problem:** the landlord funds the CapEx, the tenant captures the savings (or vice versa). This is *the* classic barrier — software can model "who pays / who saves" and structure it.
- **Regulatory tailwind specific to residential:** EPBD residential target (≈ −16% average primary energy by 2030, −20–22% by 2035, with ≥55% from the worst-performing 43% of stock), German GEG (heating law), and the rising fuel CO₂ price.

### 4.2 Data sources — no new sensors required
- Existing **heat-cost allocators / sub-meters** (Techem, ista, Brunata — already legally mandated; EU now requires monthly consumption info → a data feed exists).
- Central heat meter, common-area electricity meter, smart-meter rollout.
- Modern boiler / heat-pump **cloud APIs** (Viessmann, Vaillant, Buderus).

### 4.3 Illustrative investment plan — ~35-unit, 6–8 storey block
> **All figures are indicative ranges and ASSUMPTIONS pending energy-domain review (Mert).** Do not present as exact.

| Tier | Measures | Indicative CapEx | Payback | Heating/energy saving |
|---|---|---|---|---|
| **0 — Operational** | Heating-curve / weather compensation, hydraulic balancing (often legally required for gas-heated MDUs in DE), DHW circulation scheduling, common-area LED + presence sensors | low / near-zero | < 2 yr | ~10–20% heating |
| **1 — Moderate** | Roof / basement-ceiling insulation, smart radiator thermostats, rooftop PV for common-area / *Mieterstrom* | moderate | 3–8 yr | varies by measure |
| **2 — Structural (regulation-driven)** | Central heat-pump retrofit (replace gas boiler), façade insulation, window replacement | high | longer | largest absolute |

### 4.4 The "convince them" story = three numbers, not one
1. **€/yr energy saving** at today's tariff.
2. **€/yr rising CO₂-cost avoidance** — show the 2026 → 2030 curve; this is the strongest slide because it *grows*.
3. **Asset & compliance value:** avoid EPBD stranding, preserve rentability, and **subsidy eligibility** that re-shapes payback:
   - **BAFA heat-pump grant (2026):** base **30%**, stackable bonuses (speed +20% until 2028, income +30%, efficiency +5%), **capped at 70%** of eligible cost. *(Caps are per-residential-unit for multi-family buildings — exact MFH cap to confirm.)*
   - **Mieterstrom / tenant-electricity (post-Solarpaket I, 2024):** simplified supply models, ~2–3.8 ct/kWh subsidy, tenants ~10–30% below standard tariff; meter-cabinet conversion ≈ €2–6k. Turns rooftop PV into a revenue/retention lever for the landlord.

> Subsidies are the most under-used lever: a 30–70% grant is often what turns a "no" into a "yes." The platform already lists *incentive matching: KfW, BAFA* in scope — residential should lean on it hard.

### 4.5 Mapping to existing platform
| Need | Status |
|---|---|
| Portfolio benchmarking & prioritisation | ✅ exists |
| Recommendation engine (insulation / windows / heat pump / PV / battery) | ✅ exists |
| Compliance hub (MEPS radar, CRREM stranding, EU Taxonomy) | ✅ exists |
| Action tracking | ✅ exists |
| **Residential building type + heating KPIs** (kWh/m²/yr heating, per-unit benchmark) | ❌ new |
| **Heat-cost-allocation data ingestion** | ❌ new |
| **Split-incentive + subsidy-aware ROI** | ❌ new |
| **Common-area vs. unit energy split** | ❌ new |

---

## 5. Is it only green / profitable for large facilities?

- **Profitability:** SaaS economics scale with portfolio energy spend — bigger is easier, true. But the sweet spot is not "big facility"; it is **many buildings + compliance pressure + no in-house energy manager + a capital-allocation decision.** That includes residential portfolios, retail/branch chains, and the public sector.
- **Environmental impact:** the **largest aggregate carbon savings in the EU are in the residential stock** (biggest share of building emissions, worst average efficiency). Moving into residential is therefore *more* green in aggregate — a strong narrative for EXIST / grant funding.

---

## 6. Proposed roadmap (dependency-ordered) — FOR APPROVAL

Per BMAD and the "one module at a time" rule, build in this order. Rationale: do the **segment-agnostic horizontal layers first** (they lift the existing commercial product immediately *and* are prerequisites for residential), then open the new vertical.

| Phase | Scope | Why this order | Primary output |
|---|---|---|---|
| **A** | CO₂-forward ROI + MACC curve | Highest horizontal leverage; lowest new-data requirement; sits directly on the existing simulation/recommendation engine | A carbon-price curve + a portfolio abatement ranking, surfaced in app + report |
| **B** | No-hardware onboarding (bill/meter ingestion) | Speeds commercial sales *and* is the prerequisite for residential (no sensors there) | A bill/meter ingestion path → Bronze/Silver |
| **C** | Residential vertical (building type + heating KPIs + split-incentive/subsidy ROI) | Depends on A + B | New `Residential` type, heating KPI set, residential investment-plan view |
| **D** | Commercial deepening | Continuous / parallel — carries current revenue | Vertical sub-segment templates (retail chain, public sector) |

Suggested first move: **Phase A**, because it is the cheapest to build, improves the product for *every* existing customer, and produces the most differentiated artefact (the forward-priced MACC).

---

## 7. Open decisions (need product-owner input)

1. **Residential buyer:** professional portfolio (*Hausverwaltung* / housing company) — *recommended* — vs. single owner / *WEG*? This changes the whole UX and sales motion.
2. **First geography for residential:** Germany only (strongest regulation + subsidies + carbon price) — *recommended* — or include Turkey (weak carbon/subsidy signal → weak residential case)?
3. **Energy-logic validation:** all saving ranges in §4.3 are assumptions awaiting your domain review.
4. **Roadmap order:** confirm A → B → C with D continuous, or re-order.

---

## 8. Sources

- German national CO₂ price corridor 2026: [ICAP](https://icapcarbonaction.com/en/ets/german-national-emissions-trading-system) · [Clean Energy Wire](https://www.cleanenergywire.org/factsheets/germanys-planned-carbon-pricing-system-transport-and-buildings) · [Umweltbundesamt](https://www.umweltbundesamt.de/en/press/pressinformation/co2-pricing-for-emissions-in-heating-transport)
- ETS2 postponement to 2028 & price path: [Clean Energy Wire](https://www.cleanenergywire.org/news/germany-freeze-national-co2-price-2027-eu-delays-emissions-trading) · [BloombergNEF (~€149/t by 2030)](https://about.bnef.com/insights/commodities/europes-new-emissions-trading-system-expected-to-have-worlds-highest-carbon-price-in-2030-at-e149-bloombergnef-forecast-reveals/)
- EPBD 2024 MEPS (residential & non-residential targets): [European Commission](https://energy.ec.europa.eu/topics/energy-efficiency/energy-performance-buildings/energy-performance-buildings-directive_en) · [Longevity Partners](https://longevity-partners.com/exclusive/existing-buildings-the-revised-epbd-minimum-energy-performance-standards-renovation-requirements/)
- BAFA heat-pump subsidy 2026: [Rechenportal](https://rechenportal.de/en/heat-pump-calculator/blog/bafa-heat-pump-subsidy-2026-bonuses/) · [BAFA](https://www.bafa.de/EN/Energy/energy_node.html)
- Mieterstrom / Solarpaket I: [BMWE FAQ](https://www.bundeswirtschaftsministerium.de/Redaktion/EN/FAQ/landlord-to-tenant-electricity/faq-mieterstrom.html) · [heise](https://www.heise.de/en/news/Fuer-Mieterstrom-und-Balkonkraftwerke-Solarpaket-I-tritt-in-Kraft-9718947.html)
