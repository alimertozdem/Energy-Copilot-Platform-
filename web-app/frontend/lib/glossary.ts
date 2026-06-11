/**
 * Glossary — single source of truth for the domain terms AND calculation methods
 * surfaced across the app (InfoTip tooltips + the /glossary reference page both
 * read from here).
 *
 * `short` = hover/focus definition. `full` = longer /glossary definition.
 * `method` / `assumptions` / `confidence` / `sourceRef` (optional) describe HOW a
 * calculated figure is produced, so the user can interrogate any number.
 *
 * Energy-logic note: definitions + methods reviewed/approved with the product owner.
 * Numeric guides are rules of thumb; payback is simple payback (no discounting);
 * compliance figures are screening-grade (not a compliance verdict). No invented
 * engineering thresholds — every method traces to `sourceRef`.
 */

export type TermKey =
  | "eui"
  | "epc"
  | "anomaly"
  | "severity"
  | "performance_ratio"
  | "self_consumption"
  | "specific_yield"
  | "self_sufficiency"
  | "payback"
  | "crrem"
  | "eu_taxonomy"
  | "meps"
  | "epbd"
  | "esrs"
  | "dnsh"
  | "stranding"
  | "flexibility"
  | "energy_cost"
  | "co2_emissions"
  | "abatement_cost"
  | "anomaly_cost"
  | "retrofit_saving"

export type GlossaryCategory = "Portfolio" | "Solar" | "Financial" | "Strategy" | "Compliance"

/** How much to trust a figure — drives the tooltip's disclaimer line. */
export type Confidence = "measured" | "indicative" | "screening"

export type GlossaryEntry = {
  /** Display label, e.g. "EUI". */
  label: string
  /** Tight tooltip copy shown on hover/focus. */
  short: string
  /** Longer definition for the /glossary page (carries caveats). */
  full: string
  category: GlossaryCategory
  /** One-line "how it's computed" (formula in words). Present on calculated figures. */
  method?: string
  /** Key inputs / assumptions behind the number. */
  assumptions?: string[]
  /** Trust level; renders a matching disclaimer. */
  confidence?: Confidence
  /** Authoritative doc/section the method comes from (keeps app + docs in sync). */
  sourceRef?: string
}

/** Disclaimer copy per confidence tier (rendered under the method). */
export const CONFIDENCE_NOTE: Record<Confidence, string> = {
  measured: "Measured from your data.",
  indicative: "Indicative — varies by building and climate; refine with your data.",
  screening: "Screening-grade — not a compliance verdict; a building-specific audit replaces this.",
}

export const GLOSSARY: Record<TermKey, GlossaryEntry> = {
  eui: {
    label: "EUI",
    short:
      "Annual energy use per floor area (kWh/m²·yr). Lower is better. Rule of thumb: ≤100 good, 100–200 fair, >200 high.",
    full: "Energy Use Intensity — a building’s annual energy use divided by its floor area (kWh/m²·yr). Lower is better. As a rough guide this app flags ≤100 as good, 100–200 as fair and >200 as high, but a realistic “good” value depends heavily on building type and climate (a hospital or data centre runs far higher than an office).",
    category: "Portfolio",
    method: "Annual energy use ÷ heated floor area (kWh/m²·yr).",
    assumptions: ["Final (site) energy", "Heated/conditioned area", "12-month window"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  epc: {
    label: "EPC",
    short:
      "EU Energy Performance Certificate rating, A (most efficient) to G (least efficient).",
    full: "Energy Performance Certificate — the EU’s standardised building energy rating, from A (most efficient) to G (least efficient). Required for most commercial buildings that are sold or let.",
    category: "Portfolio",
  },
  anomaly: {
    label: "Anomaly",
    short:
      "A reading that deviates significantly from the building’s expected baseline (e.g. a consumption spike or solar performance drop), flagged for review.",
    full: "An anomaly is a reading that deviates significantly from the building’s expected baseline — for example a consumption spike, an out-of-range zone, or a drop in solar performance. EnergyLens flags anomalies automatically so they can be triaged and resolved.",
    category: "Portfolio",
  },
  severity: {
    label: "Severity",
    short:
      "How far an anomaly exceeds its threshold: Critical / High / Medium / Low. Drives triage order.",
    full: "Severity ranks how far an anomaly exceeds its threshold — Critical, High, Medium or Low. It drives the order in which alerts should be triaged; Critical and High are surfaced first.",
    category: "Portfolio",
  },
  performance_ratio: {
    label: "Performance Ratio",
    short:
      "Solar quality metric: actual generation ÷ theoretical generation (capacity × irradiance). ~0.75–0.85 is healthy; below ~0.65 suggests soiling, shading or faults.",
    full: "Performance Ratio (PR) measures how close a solar system gets to its theoretical output: actual generation divided by (installed capacity × irradiance). A healthy system sits around 0.75–0.85; a value below roughly 0.65 points to soiling, shading or equipment faults.",
    category: "Solar",
    method: "Actual generation ÷ (installed kWp × irradiance).",
    assumptions: ["Irradiance from the reference source", "~0.75–0.85 healthy", "12-month window"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  self_consumption: {
    label: "Self-consumption",
    short:
      "Share of on-site solar generation used in the building rather than exported to the grid (%).",
    full: "Self-consumption is the share of on-site solar generation used within the building rather than exported to the grid (%). Higher self-consumption usually improves the economics, because using your own generation avoids buying grid electricity. Not to be confused with self-sufficiency.",
    category: "Solar",
    method: "On-site solar used in the building ÷ total solar generation (%).",
    assumptions: ["Measured against generation (not load)", "Interval data resolution matters"],
    confidence: "measured",
    sourceRef: "glossary",
  },
  specific_yield: {
    label: "Specific yield",
    short:
      "Annual solar generation per kW of installed capacity (kWh/kWp) — lets you compare systems of different sizes.",
    full: "Specific yield is annual solar generation per kW of installed capacity (kWh/kWp). Because it normalises for system size, it lets you compare the productivity of installations of different capacities or locations.",
    category: "Solar",
    method: "Annual solar generation ÷ installed kWp (kWh/kWp).",
    assumptions: ["12-month generation", "Nameplate DC kWp"],
    confidence: "measured",
    sourceRef: "glossary",
  },
  self_sufficiency: {
    label: "Self-sufficiency",
    short:
      "Share of the building’s total consumption covered by on-site solar (%). Differs from self-consumption.",
    full: "Self-sufficiency is the share of the building’s total energy consumption covered by on-site solar (%). It differs from self-consumption: self-sufficiency is measured against total consumption, while self-consumption is measured against total generation.",
    category: "Solar",
    method: "On-site solar used ÷ total building consumption (%).",
    assumptions: ["Measured against load (not generation)", "Interval data resolution matters"],
    confidence: "measured",
    sourceRef: "glossary",
  },
  payback: {
    label: "Payback",
    short:
      "Years for cumulative savings to equal the upfront cost. Shorter = faster return. Simple payback (no financing or discounting).",
    full: "Payback is the number of years for an investment’s cumulative savings to equal its upfront cost — shorter means a faster return. This is a simple payback: it does not account for financing, inflation or discounting (see NPV/IRR for those).",
    category: "Financial",
    method: "Net CapEx (after subsidy) ÷ annual € saving.",
    assumptions: ["Simple payback — no financing/discounting", "Saving at today's tariff", "Net of subsidy"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  crrem: {
    label: "CRREM",
    short:
      "Carbon Risk Real Estate Monitor — decarbonization pathways showing the year a building risks becoming “stranded”.",
    full: "CRREM (Carbon Risk Real Estate Monitor) provides science-based decarbonization pathways for real estate. Comparing a building’s emissions against its CRREM pathway shows the year it risks becoming “stranded” — exceeding the carbon budget aligned with climate targets.",
    category: "Strategy",
    method: "First year the building's carbon intensity rises above its CRREM pathway.",
    assumptions: ["Performance assumed flat", "Chosen CRREM pathway (use/country)"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  eu_taxonomy: {
    label: "EU Taxonomy",
    short:
      "EU classification of sustainable economic activities. For buildings, EPC class A (or top-15% national primary-energy) indicates the climate-mitigation route. Indicative here, not a compliance verdict.",
    full: "The EU Taxonomy classifies when an economic activity is environmentally sustainable. For acquisition and ownership of buildings (activity 7.7), an existing building substantially contributes to climate change mitigation if it has EPC class A or sits in the top 15% of the national or regional building stock by primary energy demand. EnergyLens screens this indicatively from EPC data only: full alignment also requires do-no-significant-harm (DNSH) and minimum-safeguards checks that are out of scope here, so the screen indicates a route rather than a Taxonomy-aligned or compliant claim.",
    category: "Compliance",
    method: "Flag if EPC = A or building is in the top 15% of stock by primary energy (activity 7.7).",
    assumptions: ["Climate-mitigation substantial-contribution only", "DNSH + minimum safeguards out of scope"],
    confidence: "screening",
    sourceRef: "glossary",
  },
  meps: {
    label: "MEPS",
    short:
      "Minimum Energy Performance Standards - the minimum efficiency a building must meet. Under the revised EPBD the worst performers must be renovated first.",
    full: "Minimum Energy Performance Standards (MEPS) are regulatory thresholds for the minimum energy efficiency a building must reach. Under the revised EPBD, member states must renovate the worst-performing non-residential buildings first (worst 16% by 2030, 26% by 2033). National MEPS are not yet finalised, so EnergyLens shows an indicative renovation-risk view from EPC class, not a compliance verdict.",
    category: "Compliance",
    method: "Rank EPC class against the EPBD worst-performing thresholds (16% by 2030, 26% by 2033).",
    assumptions: ["National MEPS not yet finalised", "Risk view from EPC class only"],
    confidence: "screening",
    sourceRef: "glossary",
  },
  epbd: {
    label: "EPBD",
    short:
      "EU Energy Performance of Buildings Directive - the law driving building efficiency, EPCs and minimum standards (MEPS).",
    full: "The Energy Performance of Buildings Directive (EPBD) is the EU's main law for building energy performance. The 2024 recast brings stricter EPCs, minimum energy performance standards (MEPS) and a path to zero-emission buildings, with national transposition due in 2026 and non-residential MEPS expected by 2027.",
    category: "Compliance",
  },
  esrs: {
    label: "ESRS-E1",
    short:
      "The climate standard of the EU sustainability reporting rules (CSRD): energy use plus Scope 1, 2 and 3 GHG emissions.",
    full: "ESRS-E1 is the climate-change standard within the European Sustainability Reporting Standards (ESRS) under the CSRD. It covers energy consumption and Scope 1, 2 and 3 greenhouse-gas emissions. EnergyLens produces an ESRS-E1-aligned summary as reporting support - not an audited disclosure, and Scope 3 is estimated.",
    category: "Compliance",
    method: "Aggregate energy + Scope 1/2/3 GHG into the ESRS-E1 datapoints.",
    assumptions: ["Scope 3 estimated", "Reporting support, not an audited disclosure"],
    confidence: "screening",
    sourceRef: "ghg_methodology",
  },
  dnsh: {
    label: "DNSH",
    short:
      "Do No Significant Harm - an EU Taxonomy test: an activity must not significantly harm other environmental objectives to count as sustainable.",
    full: "Do No Significant Harm (DNSH) is an EU Taxonomy principle: an activity that substantially contributes to one environmental objective must not significantly harm the others (water, circular economy, pollution, biodiversity). EnergyLens screens only the climate-mitigation substantial-contribution criterion, so DNSH and the minimum safeguards are out of scope in the Taxonomy view.",
    category: "Compliance",
  },
  stranding: {
    label: "Stranding",
    short:
      "When a building's carbon intensity exceeds its decarbonisation pathway, risking value loss or costly retrofits. The year it happens is the stranding year.",
    full: "A building becomes stranded when its carbon intensity rises above the level allowed by a science-based decarbonisation pathway (see CRREM). Beyond that point it risks falling out of step with climate targets, losing value or needing costly retrofits. The stranding year is when this is projected to occur if performance stays flat.",
    category: "Strategy",
    method: "The year the building's carbon intensity first crosses its CRREM pathway (flat performance).",
    assumptions: ["Performance assumed flat", "Same pathway as the CRREM view"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  flexibility: {
    label: "Demand flexibility",
    short:
      "A building's ability to shift or reduce electricity use in time (battery, controls, sub-metering) to cut cost and carbon under dynamic pricing.",
    full: "Demand-side flexibility is a building's ability to shift or reduce electricity use in time - for example with a battery, smart controls or sub-metering - to benefit from dynamic tariffs and lower-carbon periods. EnergyLens shows an indicative readiness signal from the connected assets; it is not a guarantee of savings.",
    category: "Strategy",
    method: "Readiness signal from connected flexibility assets (battery, controls, sub-metering).",
    assumptions: ["Presence of assets, not a measured response", "Not a savings guarantee"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  energy_cost: {
    label: "Energy cost",
    short:
      "Total energy spend over the period: the sum of consumption priced at your tariff.",
    full: "Energy cost is the building's (or portfolio's) total energy spend over the period — the sum of metered/billed consumption priced at the applicable tariff. Where a contract tariff is not set, a regional default is used; VAT treatment is labelled where shown.",
    category: "Financial",
    method: "Σ(energy consumed × tariff) over the period.",
    assumptions: ["Tariff = your contract rate, or a regional default if unset", "VAT as labelled", "Same period as consumption"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  co2_emissions: {
    label: "CO₂ emissions",
    short:
      "Operational carbon: each energy carrier multiplied by its emission factor, summed.",
    full: "Operational CO₂ emissions are the building's energy use converted to carbon by multiplying each carrier by its emission factor and summing. EnergyLens uses a location-based grid factor for electricity and standard fuel factors; this is operational (Scope 1 + 2) carbon, with Scope 3 handled separately and estimated.",
    category: "Strategy",
    method: "Σ(energy × carrier emission factor).",
    assumptions: ["Grid electricity ≈ 363 g/kWh (UBA 2024, falling)", "Natural gas 0.201 kg/kWh", "Location-based Scope 2"],
    confidence: "indicative",
    sourceRef: "ghg_methodology",
  },
  abatement_cost: {
    label: "Abatement cost",
    short:
      "Cost-effectiveness of a measure: euros spent per tonne of CO₂ avoided (drives the MACC ranking).",
    full: "Abatement cost is the cost-effectiveness of a decarbonisation measure — its annualised net cost divided by the annual CO₂ it avoids (€/tCO₂). Ranking every measure low-to-high produces the Marginal Abatement Cost Curve (MACC): cheap, high-impact measures come first.",
    category: "Strategy",
    method: "Annualised net measure cost ÷ annual tCO₂ avoided; measures ranked low→high (MACC).",
    assumptions: ["Measure lifetime for annualisation", "Net of subsidy", "Carbon price not in the ranking itself"],
    confidence: "indicative",
    sourceRef: "decarbonisation",
  },
  anomaly_cost: {
    label: "Est. anomaly cost",
    short:
      "Indicative € impact of an anomaly while it persists — always shown as an estimate.",
    full: "The estimated cost of an anomaly is an indicative euro impact of the wasted energy while the anomaly persists. It multiplies the duration by an estimated power-waste and the local electricity price. It is always shown as an estimate, to size and prioritise alerts — not as a billed figure.",
    category: "Portfolio",
    method: "Duration × estimated power-waste (kW) × electricity price.",
    assumptions: ["HVAC temp: 2–5 kW per °C deviation", "CO₂ spike >1500 ppm: 1–3 kW extra ventilation", "Power spike: measured excess", "Grid price DE €0.20 / TR €0.14 per kWh"],
    confidence: "screening",
    sourceRef: "CLAUDE.md (Page-8 anomaly cost logic)",
  },
  retrofit_saving: {
    label: "Retrofit saving",
    short:
      "Indicative energy / cost / CO₂ saving from a retrofit measure (screening-grade).",
    full: "A retrofit saving is the indicative reduction in energy, cost and CO₂ from a measure. Fabric measures (insulation, windows) use the transmission method (ΔU × area × Gradtagzahl); operational measures use empirical field-study percentages. Savings are screening-grade and not additive across measures — a building-specific audit replaces them before any commitment.",
    category: "Strategy",
    method: "Fabric: ΔU × area × Gradtagzahl × 24 ÷ boiler η. Operational: empirical study %.",
    assumptions: ["Gradtagzahl 3,500 Kd (DE reference)", "Condensing-gas η 0.90", "Savings NOT additive across measures"],
    confidence: "screening",
    sourceRef: "residential-retrofit-calculations.md",
  },
}

/** Stable display order for the /glossary page, grouped by category. */
export const GLOSSARY_CATEGORY_ORDER: GlossaryCategory[] = [
  "Portfolio",
  "Solar",
  "Financial",
  "Strategy",
  "Compliance",
]
