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
  | "scope_1"
  | "scope_2"
  | "scope_3"
  | "ghg_intensity"
  | "subsidy"
  | "uvi"
  | "cop"
  | "heating_demand"
  | "envelope_geg"
  | "retrofit_package"
  | "comfort"
  | "npv"
  | "scenario"
  | "value_uplift"
  | "isfp"
  | "carbon_price"
  | "data_basis"
  | "geg65"

export type GlossaryCategory = "Portfolio" | "Solar" | "HVAC" | "Financial" | "Strategy" | "Compliance"

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
      "Indicative € impact of an anomaly — the excess energy above baseline priced at the grid tariff.",
    full: "The estimated cost of an anomaly is an indicative euro impact of the excess energy it represents. For a consumption spike it prices the energy used above the alert's baseline at the local electricity tariff. It is always shown as an estimate — to size and prioritise alerts, not a billed figure — and only where the anomaly's metric is an energy quantity (other anomaly types show no cost).",
    category: "Portfolio",
    method: "Excess energy (reading − baseline, kWh) × electricity price.",
    assumptions: ["Shown only for energy anomalies (e.g. consumption spike)", "Excess measured above the alert threshold", "Electricity ≈ €0.20/kWh (DE default), €0.14 TR"],
    confidence: "screening",
    sourceRef: "anomaly_detection",
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
  scope_1: {
    label: "Scope 1 (direct)",
    short:
      "Direct on-site emissions — fuel combustion (gas / diesel) plus fugitive refrigerant.",
    full: "Scope 1 covers direct greenhouse-gas emissions from sources the building controls: on-site fuel combustion (gas, diesel) and fugitive refrigerant (F-gas) leakage. EnergyLens follows the GHG Protocol Corporate Standard; gas uses a metered or proxy factor, and refrigerant is 0 until an F-Gas logbook is loaded (method-correct, not yet populated).",
    category: "Compliance",
    method: "Σ(fuel kWh × fuel factor) + refrigerant leakage × GWP-100.",
    assumptions: ["Natural gas 0.201 kg/kWh (DESNZ/DEFRA)", "Gas metered where available, else proxy", "Refrigerant 0 until F-Gas logbook loaded"],
    confidence: "indicative",
    sourceRef: "ghg_methodology",
  },
  scope_2: {
    label: "Scope 2 (electricity)",
    short:
      "Indirect emissions from purchased electricity — reported both location- and market-based.",
    full: "Scope 2 covers indirect emissions from purchased electricity. Following the GHG Protocol Scope 2 Guidance, EnergyLens reports both location-based (the country-and-year grid-average factor) and market-based (supplier / residual-mix factor). Until supply contracts or Guarantees of Origin are loaded, the market-based figure uses the national residual mix.",
    category: "Compliance",
    method: "Electricity kWh × grid factor (location) or supplier / residual-mix factor (market).",
    assumptions: ["DE grid 0.363 kg/kWh (UBA 2024), TR 0.442 (TEİAŞ)", "DE residual mix 0.725 kg/kWh (AIB 2024)", "Market = residual mix until contracts / GoOs arrive"],
    confidence: "indicative",
    sourceRef: "ghg_methodology",
  },
  scope_3: {
    label: "Scope 3 (value chain)",
    short:
      "Estimated value-chain emissions (embodied carbon, downstream) — material categories only.",
    full: "Scope 3 covers value-chain emissions outside the building's direct control. EnergyLens estimates material categories only — Category 1 (embodied carbon, amortised from a building-type benchmark) and Category 13 (downstream leased assets). It is explicitly estimated, not disclosure-grade, and several buckets are 0 until pilot data arrives.",
    category: "Compliance",
    method: "Cat 1: floor area × embodied kgCO₂e/m² ÷ amortisation years. Cat 13: downstream estimate.",
    assumptions: ["Embodied benchmark by building type (RICS / LETI / DGNB)", "Estimated, not disclosure-grade", "Several categories 0 until pilot consumption data"],
    confidence: "screening",
    sourceRef: "ghg_methodology",
  },
  ghg_intensity: {
    label: "GHG intensity",
    short:
      "Total emissions per floor area — tCO₂e per m², for size-independent comparison.",
    full: "GHG intensity normalises total greenhouse-gas emissions (Scope 1 + 2 + 3) by floor area, giving tCO₂e/m². It lets buildings of different sizes be compared on a level field and tracks decarbonisation progress over time.",
    category: "Compliance",
    method: "Total tCO₂e ÷ floor area (m²).",
    assumptions: ["Total = Scope 1 + 2 (location) + 3", "Floor area = conditioned area"],
    confidence: "indicative",
    sourceRef: "ghg_methodology",
  },
  subsidy: {
    label: "Subsidy (BAFA/KfW)",
    short:
      "Indicative public grant a measure may attract — BAFA BEG or KfW programme; screening-grade.",
    full: "An indicative public subsidy is the grant a measure may attract under a German programme — BAFA BEG Einzelmaßnahme (envelope) or KfW (458 heat pump, 261 deep retrofit). EnergyLens maps each measure to its likely programme and an indicative grant from published rates. Eligibility and bonuses change, and you must apply BEFORE signing any contract — signing first forfeits the grant. Support, not financial advice.",
    category: "Financial",
    method: "Measure → eligible programme → grant % × eligible cost (per-programme cap).",
    assumptions: ["BAFA BEG EM envelope ~15% + iSFP 5%", "KfW heat-pump 30–70% (capped)", "Apply before contract; rates change — verify live"],
    confidence: "indicative",
    sourceRef: "residential-retrofit-calculations.md",
  },
  uvi: {
    label: "UVI (monthly info)",
    short:
      "Monthly consumption info residents must receive (HKVO §6a) — and the §12 3% penalty risk.",
    full: "Unterjährige Verbrauchsinformation (UVI) is the monthly consumption information German law (HKVO §6a, from the EU EED) requires landlords to give residents from 1 Jan 2027 where remote-readable meters exist. Breaching the duty lets a resident cut 3% of their consumption-based heating cost (§12). EnergyLens tracks readiness and an indicative penalty exposure — decision-support, not legal advice.",
    category: "Compliance",
    method: "Readiness = unit coverage + recency of the latest UVI month; penalty exposure = 3% × annual heating cost.",
    assumptions: ["Mandatory monthly UVI from 1 Jan 2027", "§12: resident may cut 3% if breached", "Heat tariff ≈ €0.12/kWh for the exposure estimate"],
    confidence: "screening",
    sourceRef: "residential-segment-architecture",
  },
  // --- HVAC (building-level heating, retrofit & comfort) ---
  cop: {
    label: "COP",
    short:
      "Coefficient of Performance — a heat pump's heat output ÷ electricity input. ~3 means 3 kWh of heat per kWh of power. Higher is better.",
    full: "Coefficient of Performance (COP) is a heat pump's delivered heat divided by the electricity it draws — a COP of 3 means three units of heat per unit of power. EnergyLens measures it from a heat meter plus an electricity sub-meter where both exist; without a heat meter it can't be derived (shown as “needs heat meter”), and a chiller's device-reported COP is labelled as such.",
    category: "HVAC",
    method: "Σ heat output (kWh_th) ÷ Σ heat-pump electricity (kWh_el) over the window.",
    assumptions: ["Needs a heat meter + electricity sub-meter", "Counter-delta when cumulative, else summed", "Device-reported COP labelled separately"],
    confidence: "measured",
    sourceRef: "glossary",
  },
  heating_demand: {
    label: "Heating demand",
    short:
      "How much heat a building needs per year (kWh, or kWh/m²·yr). The biggest cost and carbon lever in most older buildings.",
    full: "Heating demand is the annual heat a building needs for space heating. When a bill is on file it is the metered heating fuel; otherwise EnergyLens estimates it from a typical energy intensity for the building type × the heating share of energy. It is the dominant cost and carbon lever in most older commercial and residential stock.",
    category: "HVAC",
    method: "Metered heating fuel, or archetype EUI × heating-share (by building type) when no bill is on file.",
    assumptions: ["Heating share by type (office ~35%, residential ~60%)", "Estimated until consumption is uploaded", "Not weather-corrected"],
    confidence: "indicative",
    sourceRef: "residential-retrofit-calculations.md",
  },
  envelope_geg: {
    label: "Envelope vs GEG",
    short:
      "How well walls, roof and windows insulate (U-value, W/m²K) vs the German GEG component limits. Lower U = better.",
    full: "The building envelope's U-values (thermal transmittance, W/m²K — lower is better) compared with the limits in GEG Anlage 7 that apply when a component is renovated (wall ≤0.24, roof ≤0.20, window ≤1.30). Where a U-value isn't on file, EnergyLens assumes a 1970s-unrenovated value and labels it; adding the real value sharpens the retrofit figures.",
    category: "HVAC",
    method: "Compare each component U-value to its GEG Anlage 7 renovation limit.",
    assumptions: ["U from the building file, else a 1970s assumption (labelled)", "GEG limits apply on component renovation"],
    confidence: "screening",
    sourceRef: "glossary",
  },
  retrofit_package: {
    label: "Retrofit package",
    short:
      "A sequence of measures, each acting on the load the previous one left — so savings are NOT additive. A full package realistically reaches 50–65% heating reduction.",
    full: "A retrofit package sequences individual measures cheapest-payback-first, with each measure acting on the reduced load the previous one leaves — so the combined saving is less than the sum of the standalone measures. EnergyLens reports the cumulative reduction, net CapEx, blended payback and resulting EUI per step, capped at a realistic full-package ceiling (~50–65% heating reduction). Screening-grade; a building audit replaces it before commitment.",
    category: "HVAC",
    method: "Order measures by payback; each reduces the REMAINING demand; cumulative reduction capped ~72%.",
    assumptions: ["Measures NOT additive (sequential)", "Gain-utilisation applied to fabric savings", "Screening-grade"],
    confidence: "screening",
    sourceRef: "residential-retrofit-calculations.md",
  },
  comfort: {
    label: "Comfort & operation",
    short:
      "How well zones hold their setpoint (DIN EN 16798, 20–24°C), over-/under-heating share, supply–return ΔT and CO₂ air quality (good <800, poor >1200 ppm).",
    full: "Comfort & operation analytics turn live climate telemetry into operational insight: the share of zone-temperature readings inside the DIN EN 16798 comfort band (20–24°C), over- and under-heating share, supply–return ΔT, and CO₂ air quality (good <800, fair 800–1200, poor >1200 ppm). Significant over-heating flags a low/no-CapEx operational saving (setpoint, night setback, hydraulic balancing).",
    category: "HVAC",
    method: "Share of readings in / over / under the comfort band, from zone telemetry over the window.",
    assumptions: ["DIN EN 16798-1 Cat. II band (20–24°C)", "CO₂ 800 / 1200 ppm thresholds", "Live IoT data"],
    confidence: "measured",
    sourceRef: "glossary",
  },
  // --- Financial (added: NPV, scenarios, value uplift, iSFP) ---
  npv: {
    label: "NPV",
    short:
      "Net Present Value — today's value of an investment's future savings minus its upfront cost, discounted for time. Positive = it pays for itself over its life.",
    full: "Net Present Value (NPV) is the value today of an investment's future savings minus its upfront cost, with future cash flows discounted to reflect the time value of money. EnergyLens discounts at a stated real rate and escalates the savings with energy-price inflation and the rising carbon price, so a positive NPV means the measure pays back over its service life — a fuller picture than simple payback.",
    category: "Financial",
    method: "−Net CapEx + Σ (annual saving in year t) ÷ (1 + discount rate)^t, over the measure lifetime.",
    assumptions: ["Discount rate 4% real (stated)", "Savings escalate with energy + carbon price", "Net of subsidy"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  scenario: {
    label: "Scenario (low/base/high)",
    short:
      "Forward figures are shown as three scenarios — conservative, base and policy-tight — bracketing how energy and carbon prices might rise.",
    full: "Because future energy and carbon prices are uncertain, EnergyLens shows forward figures (e.g. lifetime NPV) as three scenarios rather than one false-precise number: conservative, base and policy-tight. They differ in how fast energy prices and the carbon price rise, so you see the range a decision sits in instead of a single point.",
    category: "Financial",
    method: "Each scenario escalates energy-price inflation + the carbon-price trajectory by its own assumptions.",
    assumptions: ["Energy inflation 1% / 3% / 5% real", "Carbon 2030 ≈ €80 / €120 / €180 per t", "Ranges, not forecasts"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  value_uplift: {
    label: "Value uplift (green premium)",
    short:
      "Indicative property-value increase from improving the EPC class — the “green premium / brown discount”. A % range, applied to your own valuation.",
    full: "Value uplift is the indicative increase in a building's value from improving its EPC class — the market's “green premium” for efficient buildings (and “brown discount” for poor ones). EnergyLens shows it as a conservative percentage range per EPC band improved, capped, and applied to the owner's own valuation. It is an estimate, not a guarantee — the premium is market- and location-specific.",
    category: "Financial",
    method: "≈1–2.5% value uplift per EPC band improved (capped ~15%), applied to the owner's valuation.",
    assumptions: ["Market- and location-specific", "Estimate, not a guarantee", "No € attached without the owner's valuation"],
    confidence: "screening",
    sourceRef: "glossary",
  },
  isfp: {
    label: "iSFP",
    short:
      "Individueller Sanierungsfahrplan — an Energieberater-certified renovation roadmap. Having one adds +5% to BAFA envelope grants and raises the eligible-cost cap.",
    full: "The individueller Sanierungsfahrplan (iSFP) is a German renovation roadmap drawn up by a certified Energieberater that stages a building's upgrades over time. Beyond the plan itself, it unlocks a +5% bonus on BAFA BEG envelope measures and raises the eligible-cost cap (e.g. €30k → €60k per unit) — improving both the sequencing and the economics of a retrofit.",
    category: "Financial",
  },
  // --- Strategy (added: carbon price) ---
  carbon_price: {
    label: "Carbon price (nEHS/ETS2)",
    short:
      "The cost per tonne of CO₂ under German/EU carbon pricing. It rises over time, raising the value of every tonne saved and shortening retrofit payback.",
    full: "Carbon pricing puts a cost on each tonne of CO₂ emitted. Germany's national scheme (BEHG/nEHS) runs a €55–65/t corridor through 2026–2027; the EU ETS2 (postponed) brings market-based pricing from 2028, with 2030 estimates ranging from the EU's ~€48–80/t up to higher figures under tighter-cap analyses. A rising carbon price increases the value of avoided emissions, improving retrofit and fuel-switch economics over time.",
    category: "Strategy",
    method: "Per-scenario trajectory: 2026–27 BEHG corridor, market-based ETS2 from 2028.",
    assumptions: ["2026 corridor €55–65/t", "ETS2 postponed to 2028", "2030 €80–180/t across scenarios"],
    confidence: "indicative",
    sourceRef: "glossary",
  },
  // --- Portfolio (added: data provenance) ---
  data_basis: {
    label: "Data basis",
    short:
      "Where a figure comes from: Measured (your real data), Estimated (model/archetype), Sample (demo building) or Simulated (test feed). Shown as a badge next to numbers.",
    full: "Every figure in EnergyLens carries its data basis so you always know what you're looking at: Measured (computed from your uploaded bills or live telemetry), Estimated (modelled from a building-type archetype before you have data), Sample (a demo building, not yours) or Simulated (a test/agent feed, not a real device). A consistent badge marks each, and estimated or sample figures invite you to add real data to sharpen them.",
    category: "Portfolio",
  },
  // --- Compliance (added: GEG section 71) ---
  geg65: {
    label: "GEG §71 (65% renewable)",
    short:
      "German rule (GEG §71): a newly installed or replaced heating system must run on ≥65% renewable energy — effectively a heat pump, district heat or biomass.",
    full: "Under the German Building Energy Act (GEG §71, the “Heizungsgesetz”), every newly installed or replaced heating system must run on at least 65% renewable energy — in practice a heat pump, district heating or biomass. EnergyLens flags buildings on fossil heating (gas/oil) where a boiler replacement will trigger this rule, so the switch can be planned with the replacement cycle rather than after a breakdown. Transition deadlines vary with municipal heat planning.",
    category: "Compliance",
    method: "Flag when the building's heating system is fossil (gas / oil).",
    assumptions: ["Applies on heating replacement, not immediately", "Transition deadlines vary by municipal heat planning"],
    confidence: "screening",
    sourceRef: "glossary",
  },
}

/** Stable display order for the /glossary page, grouped by category. */
export const GLOSSARY_CATEGORY_ORDER: GlossaryCategory[] = [
  "Portfolio",
  "Solar",
  "HVAC",
  "Financial",
  "Strategy",
  "Compliance",
]
