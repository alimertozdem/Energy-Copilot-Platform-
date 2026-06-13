/**
 * VSME (EFRAG Voluntary SME standard) — Basic Module narrative disclosures.
 *
 * Single source of the qualitative datapoints, used by the report as the guided
 * boilerplate fallback (and, once the narrative editor is extended to VSME keys,
 * the editor's form list + default text). B3 (Energy & GHG emissions) is the ONE
 * quantitative disclosure — it is auto-filled from Fabric (esrs_metrics) and is
 * therefore NOT in this list. The boilerplate is a guided draft with [bracketed
 * placeholders] the company completes — it is not a claim.
 *
 * Basic Module = B1–B11. The Comprehensive Module (C1–C9) is a later extension.
 * Titles per the EFRAG VSME Standard (Commission recommendation, 30 Jul 2025).
 */
export type VsmeDisclosure = {
  code: string
  title: string
  asks: string
  boilerplate: string
}

export const VSME_NARRATIVE: VsmeDisclosure[] = [
  {
    code: "B1",
    title: "Basis for preparation",
    asks: "Which module is used, the reporting basis (individual or consolidated), the scope of sites included, any omitted sensitive information, and any sustainability certifications or labels held.",
    boilerplate:
      "This report follows the VSME Basic Module (EFRAG Voluntary SME standard). It is prepared on a [individual / consolidated] basis for [legal entity] covering the financial year [20YY]. Reporting scope: [list the sites / buildings included]. [State any classified or sensitive information omitted, and any sustainability certifications or labels held — e.g. ISO 50001, EMAS, DGNB.]",
  },
  {
    code: "B2",
    title: "Practices, policies and future initiatives for transitioning towards a more sustainable economy",
    asks: "Whether the undertaking has practices, policies and future initiatives addressing the sustainability issues, and for which issues.",
    boilerplate:
      "[Company] maintains an energy & climate policy focused on reducing energy demand, deploying on-site renewables and phasing out fossil heating; EnergyLens provides the monitoring, anomaly detection and prioritised retrofit roadmap that operationalise it. [List any further environmental, social and governance policies, who owns them, and planned initiatives with timelines. State 'none' where a topic is not addressed.]",
  },
  {
    code: "B4",
    title: "Pollution of air, water and soil",
    asks: "Pollutants the undertaking is required to report (e.g. under an environmental permit or the E-PRTR register), with amounts.",
    boilerplate:
      "EnergyLens does not track regulated air, water or soil pollutant releases. [If the undertaking holds an environmental permit or is listed on the E-PRTR register, state the pollutants and quantities emitted; otherwise state that no such reporting obligation applies.]",
  },
  {
    code: "B5",
    title: "Biodiversity",
    asks: "Number and area of sites owned, leased or managed in or near biodiversity-sensitive areas, and total land use / soil sealing.",
    boilerplate:
      "[State whether any site is located in or near a biodiversity-sensitive area (e.g. Natura 2000), the number and area (ha) of such sites, and the total sealed / land-use area. For an urban building portfolio this is typically limited or not applicable.]",
  },
  {
    code: "B6",
    title: "Water",
    asks: "Total annual water withdrawal (m³) and, where applicable, withdrawal in areas of high water stress.",
    boilerplate:
      "Water withdrawal is not metered by EnergyLens. [Provide total annual water withdrawal (m³) from utility records, and indicate whether any site is located in an area of high water stress.]",
  },
  {
    code: "B7",
    title: "Resource use, circular economy and waste management",
    asks: "Whether circular-economy principles are applied, the total annual waste generated, and — where available — hazardous waste and recycled content.",
    boilerplate:
      "[Describe any circular-economy practices (e.g. retrofit-over-replace, material reuse during refurbishment, separated collection) and provide total annual waste generated (tonnes), split hazardous / non-hazardous where available.]",
  },
  {
    code: "B8",
    title: "Workforce — General characteristics",
    asks: "Number of employees (headcount or FTE) by contract type (permanent / temporary) and by gender, and the countries of employment.",
    boilerplate:
      "[State total employees by contract type and gender, and the countries of employment. For a small undertaking, headcount as at the reporting date is sufficient.]",
  },
  {
    code: "B9",
    title: "Workforce — Health and safety",
    asks: "Number of recordable work-related accidents, any fatalities, and the recordable accident rate.",
    boilerplate:
      "[Report the number of recordable work-related accidents and any fatalities during the period, and the accident rate. State 'zero' where applicable.]",
  },
  {
    code: "B10",
    title: "Workforce — Remuneration, collective bargaining and training",
    asks: "Whether all employees are paid at least the applicable minimum wage, the gender pay gap, collective-bargaining coverage, and average training hours.",
    boilerplate:
      "[Confirm that all employees are paid at or above the applicable minimum / adequate wage, and state the gender pay gap (%), the share of employees covered by collective bargaining, and the average training hours per employee.]",
  },
  {
    code: "B11",
    title: "Convictions and fines for corruption and bribery",
    asks: "Number of convictions and total amount of fines for violation of anti-corruption and anti-bribery laws.",
    boilerplate:
      "[State the number of convictions and the total amount of fines for breaches of anti-corruption / anti-bribery laws during the period. State 'none' where applicable.]",
  },
]

export const VSME_BY_CODE: Record<string, VsmeDisclosure> = Object.fromEntries(
  VSME_NARRATIVE.map((d) => [d.code, d])
)


/**
 * VSME Comprehensive Module — C1–C9 (the SME chooses Basic OR Comprehensive; the
 * Comprehensive level adds the information banks and investors typically request).
 * C3 (GHG targets) and C4 (climate risks) are backed by EnergyLens data in the report;
 * the rest are guided slots whose boilerplate PROMPTS for the specific datapoints the
 * company supplies, so the report becomes complete once those values are entered.
 */
export const VSME_COMPREHENSIVE: VsmeDisclosure[] = [
  {
    code: "C1",
    title: "Strategy: business model and sustainability-related initiatives",
    asks: "The business model, main markets, and how sustainability is embedded in the strategy.",
    boilerplate:
      "Business model: [what the company does and its main markets / customer groups]. Sustainability is embedded through [the energy-efficiency and decarbonisation programme operated via EnergyLens — monitoring, anomaly detection and a prioritised retrofit roadmap]. Key sustainability-related initiatives: [list, with owners].",
  },
  {
    code: "C2",
    title: "Description of practices, policies and future initiatives (transition)",
    asks: "Detail, beyond B2, of the practices, policies and future initiatives and how they are governed.",
    boilerplate:
      "Formalised policies: [environmental / energy management policy, sustainable procurement, …] — for each: [owner, scope, how monitored]. Future initiatives: [planned actions with timelines and budgets]. State 'not yet formalised' where a topic is not covered.",
  },
  {
    code: "C3",
    title: "GHG reduction targets and climate transition",
    asks: "GHG-reduction targets (base year, scope, science-based?) and the transition levers.",
    boilerplate:
      "Base year [20YY] gross emissions: [from the GHG inventory] tCO₂e (Scope 1+2 + 3). Target: reduce gross emissions by [X]% by [20YY] against the base year. Transition levers (from EnergyLens): heat-pump conversion, envelope insulation, on-site solar, LED / BMS — each with per-measure CO₂ and cost in the recommendations. [State interim targets and whether the target is science-based (SBTi-validated).]",
  },
  {
    code: "C4",
    title: "Climate risks",
    asks: "Material physical and transition climate risks and their anticipated financial effects.",
    boilerplate:
      "Transition risk: assets at CRREM stranding risk require retrofit capex to stay financeable; rising CO₂ pricing (national nEHS 2026, EU ETS2 2028) increases operating cost. Physical risk: [assess heat / flood / water-stress exposure of the portfolio]. Anticipated financial effects: [quantify the effect on costs, asset value and financing].",
  },
  {
    code: "C5",
    title: "Additional own workforce characteristics",
    asks: "Headcount by gender and contract type, country breakdown, turnover.",
    boilerplate:
      "Total employees (head count) at period end: [N]. By gender: women [N] / men [N] / other or not disclosed [N]. By contract: permanent [N] / temporary [N]. Countries of employment: [list]. Employee turnover rate: [X]%. [Add temporary-agency workers if material.]",
  },
  {
    code: "C6",
    title: "Additional own workforce information — human rights policies and processes",
    asks: "Human-rights policy, supplier code of conduct, due diligence and grievance mechanism.",
    boilerplate:
      "[State whether the company has: a human-rights policy [yes/no], a supplier code of conduct [yes/no], human-rights due diligence [yes/no], and a grievance / complaints mechanism [yes/no]. Describe each briefly, or state 'not yet formalised'.]",
  },
  {
    code: "C7",
    title: "Severe negative human rights incidents",
    asks: "Number of severe human-rights incidents in own operations / value chain and remediation.",
    boilerplate:
      "Severe human-rights incidents confirmed during the period (e.g. forced labour, child labour, discrimination): [N]. [Describe any incident and the remediation taken, or state 'none identified'.]",
  },
  {
    code: "C8",
    title: "Revenues from certain sectors and exclusion from EU reference benchmarks",
    asks: "Share of revenue from fossil fuels, chemicals, controversial weapons and tobacco.",
    boilerplate:
      "Share of revenue from: fossil fuels (coal / oil / gas) [X]%; chemicals production [X]%; controversial weapons [X]%; tobacco cultivation or production [X]%. [State '0% / none' where not applicable, and confirm whether the company is excluded from the EU Paris-aligned / Climate-Transition benchmarks.]",
  },
  {
    code: "C9",
    title: "Gender diversity ratio in the governance body",
    asks: "Composition of the highest governance body by gender.",
    boilerplate:
      "Highest governance body (board / managing directors): [N] members — women [N] / men [N] → women [X]%. [Provide as at the reporting date.]",
  },
]

export const VSME_COMPREHENSIVE_BY_CODE: Record<string, VsmeDisclosure> =
  Object.fromEntries(VSME_COMPREHENSIVE.map((d) => [d.code, d]))

/** Basic (B1–B11) + Comprehensive (C1–C9) narrative disclosures, for the editor. */
export const VSME_ALL_NARRATIVE: VsmeDisclosure[] = [
  ...VSME_NARRATIVE,
  ...VSME_COMPREHENSIVE,
]

/** Combined lookup used by the report's narrative slots (Basic + Comprehensive). */
export const VSME_ALL_BY_CODE: Record<string, VsmeDisclosure> = {
  ...VSME_BY_CODE,
  ...VSME_COMPREHENSIVE_BY_CODE,
}
