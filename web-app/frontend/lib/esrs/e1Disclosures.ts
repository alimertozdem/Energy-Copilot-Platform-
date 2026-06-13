/**
 * ESRS E-1 qualitative disclosures — single source of the narrative datapoints.
 *
 * Used by BOTH the report (boilerplate fallback when nothing is saved) and the
 * narrative editor (the form list + the default text). E1-5 (energy) and E1-6 (GHG)
 * are quantitative and auto-filled from Fabric, so they are NOT here. The boilerplate
 * is a guided draft with [bracketed placeholders] the company completes — not a claim.
 */
export type E1Disclosure = {
  code: string
  title: string
  asks: string
  boilerplate: string
}

export const E1_NARRATIVE: E1Disclosure[] = [
  {
    code: "E1-1",
    title: "Transition plan for climate change mitigation",
    asks: "Is there a transition plan aligned with limiting warming to 1.5°C, with targets, actions and financing?",
    boilerplate:
      "[Company] is developing a climate transition plan aligned with a 1.5°C pathway. EnergyLens CRREM analysis identifies the assets at stranding risk and a prioritised retrofit pathway (heat pumps, envelope insulation, on-site solar). [Add governance, milestones, decarbonisation levers and the financing plan.]",
  },
  {
    code: "E1-2",
    title: "Policies related to climate change mitigation and adaptation",
    asks: "What policies manage climate mitigation, adaptation, energy efficiency and renewable deployment?",
    boilerplate:
      "[Company]'s energy & climate policy commits to reducing energy demand, increasing on-site renewables and phasing out fossil heating across the portfolio. [State the policy owner, scope, and how it is monitored.]",
  },
  {
    code: "E1-3",
    title: "Actions and resources",
    asks: "What concrete actions and financial / operational resources support the targets?",
    boilerplate:
      "Planned actions include [the prioritised retrofit measures], with an estimated investment of [€…] and an expected reduction of [… tCO₂e/yr]. [Confirm which actions are committed, their budgets and timelines.]",
  },
  {
    code: "E1-4",
    title: "Targets related to climate change mitigation and adaptation",
    asks: "What measurable GHG-reduction targets (base year, scope, science-based?) are set?",
    boilerplate:
      "Base year [20YY]: [baseline] tCO₂e gross. Target: reduce gross Scope 1+2 emissions by [X]% by [20YY] against this base year. [State scope coverage, interim targets and whether the target is science-based (SBTi).]",
  },
  {
    code: "E1-7",
    title: "GHG removals and carbon credits",
    asks: "Are GHG removals or carbon credits used? Quantify and describe.",
    boilerplate:
      "No GHG removals or carbon credits are claimed for this reporting period. [Update if the company purchases credits or operates removal projects.]",
  },
  {
    code: "E1-8",
    title: "Internal carbon pricing",
    asks: "Is an internal carbon price applied in decision-making?",
    boilerplate:
      "No internal carbon price is currently applied. [If used, state the price (€/tCO₂e), scope, and how it informs investment decisions.]",
  },
  {
    code: "E1-9",
    title: "Anticipated financial effects from material climate risks",
    asks: "What are the anticipated financial effects of physical and transition risks?",
    boilerplate:
      "Transition risk: carbon pricing raises operating costs and assets at CRREM stranding risk require retrofit capex of [€…] to stay marketable / financeable. Physical risk: [assess heat / flood exposure]. [Quantify the effects on the company's financial position, performance and cash flows.]",
  },
]

export const E1_BY_CODE: Record<string, E1Disclosure> = Object.fromEntries(
  E1_NARRATIVE.map((d) => [d.code, d])
)
