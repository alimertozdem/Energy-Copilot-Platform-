/**
 * Glossary — single source of truth for the domain terms surfaced across the
 * app (InfoTip tooltips + the /glossary reference page both read from here).
 *
 * `short` is the hover/focus tooltip copy (kept tight); `full` is the longer
 * /glossary-page definition that carries the assumptions and caveats.
 *
 * Energy-logic note: definitions reviewed/approved with the product owner.
 * Numeric guides (EUI bands, healthy PR range) are rules of thumb — real
 * "good" values vary by building type and climate. Payback figures are simple
 * payback (no financing/discounting). No invented engineering thresholds.
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

export type GlossaryCategory = "Portfolio" | "Solar" | "Financial" | "Strategy" | "Compliance"

export type GlossaryEntry = {
  /** Display label, e.g. "EUI". */
  label: string
  /** Tight tooltip copy shown on hover/focus. */
  short: string
  /** Longer definition for the /glossary page (carries caveats). */
  full: string
  category: GlossaryCategory
}

export const GLOSSARY: Record<TermKey, GlossaryEntry> = {
  eui: {
    label: "EUI",
    short:
      "Annual energy use per floor area (kWh/m²·yr). Lower is better. Rule of thumb: ≤100 good, 100–200 fair, >200 high.",
    full: "Energy Use Intensity — a building’s annual energy use divided by its floor area (kWh/m²·yr). Lower is better. As a rough guide this app flags ≤100 as good, 100–200 as fair and >200 as high, but a realistic “good” value depends heavily on building type and climate (a hospital or data centre runs far higher than an office).",
    category: "Portfolio",
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
  },
  self_consumption: {
    label: "Self-consumption",
    short:
      "Share of on-site solar generation used in the building rather than exported to the grid (%).",
    full: "Self-consumption is the share of on-site solar generation used within the building rather than exported to the grid (%). Higher self-consumption usually improves the economics, because using your own generation avoids buying grid electricity. Not to be confused with self-sufficiency.",
    category: "Solar",
  },
  specific_yield: {
    label: "Specific yield",
    short:
      "Annual solar generation per kW of installed capacity (kWh/kWp) — lets you compare systems of different sizes.",
    full: "Specific yield is annual solar generation per kW of installed capacity (kWh/kWp). Because it normalises for system size, it lets you compare the productivity of installations of different capacities or locations.",
    category: "Solar",
  },
  self_sufficiency: {
    label: "Self-sufficiency",
    short:
      "Share of the building’s total consumption covered by on-site solar (%). Differs from self-consumption.",
    full: "Self-sufficiency is the share of the building’s total energy consumption covered by on-site solar (%). It differs from self-consumption: self-sufficiency is measured against total consumption, while self-consumption is measured against total generation.",
    category: "Solar",
  },
  payback: {
    label: "Payback",
    short:
      "Years for cumulative savings to equal the upfront cost. Shorter = faster return. Simple payback (no financing or discounting).",
    full: "Payback is the number of years for an investment’s cumulative savings to equal its upfront cost — shorter means a faster return. This is a simple payback: it does not account for financing, inflation or discounting (see NPV/IRR for those).",
    category: "Financial",
  },
  crrem: {
    label: "CRREM",
    short:
      "Carbon Risk Real Estate Monitor — decarbonization pathways showing the year a building risks becoming “stranded”.",
    full: "CRREM (Carbon Risk Real Estate Monitor) provides science-based decarbonization pathways for real estate. Comparing a building’s emissions against its CRREM pathway shows the year it risks becoming “stranded” — exceeding the carbon budget aligned with climate targets.",
    category: "Strategy",
  },
  eu_taxonomy: {
    label: "EU Taxonomy",
    short:
      "EU classification of sustainable economic activities. For buildings, EPC class A (or top-15% national primary-energy) indicates the climate-mitigation route. Indicative here, not a compliance verdict.",
    full: "The EU Taxonomy classifies when an economic activity is environmentally sustainable. For acquisition and ownership of buildings (activity 7.7), an existing building substantially contributes to climate change mitigation if it has EPC class A or sits in the top 15% of the national or regional building stock by primary energy demand. EnergyLens screens this indicatively from EPC data only: full alignment also requires do-no-significant-harm (DNSH) and minimum-safeguards checks that are out of scope here, so the screen indicates a route rather than a Taxonomy-aligned or compliant claim.",
    category: "Compliance",
  },
  meps: {
    label: "MEPS",
    short:
      "Minimum Energy Performance Standards - the minimum efficiency a building must meet. Under the revised EPBD the worst performers must be renovated first.",
    full: "Minimum Energy Performance Standards (MEPS) are regulatory thresholds for the minimum energy efficiency a building must reach. Under the revised EPBD, member states must renovate the worst-performing non-residential buildings first (worst 16% by 2030, 26% by 2033). National MEPS are not yet finalised, so EnergyLens shows an indicative renovation-risk view from EPC class, not a compliance verdict.",
    category: "Compliance",
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
  },
  flexibility: {
    label: "Demand flexibility",
    short:
      "A building's ability to shift or reduce electricity use in time (battery, controls, sub-metering) to cut cost and carbon under dynamic pricing.",
    full: "Demand-side flexibility is a building's ability to shift or reduce electricity use in time - for example with a battery, smart controls or sub-metering - to benefit from dynamic tariffs and lower-carbon periods. EnergyLens shows an indicative readiness signal from the connected assets; it is not a guarantee of savings.",
    category: "Strategy",
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
