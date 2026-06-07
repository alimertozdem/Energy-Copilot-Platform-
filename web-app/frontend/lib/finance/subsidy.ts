/**
 * Indicative German building-efficiency subsidy mapping (2026).
 *
 * SUPPORT, NOT ADVICE. Maps a recommendation's measure type → the likely public
 * programme and an indicative grant. Programmes change and bonuses depend on the
 * applicant — verify against the live programme, and ALWAYS apply BEFORE signing
 * a contract (signing first forfeits the subsidy).
 *
 * Sources (verified Jun 2026):
 *  - KfW 458 Heizungsförderung — renewable heating (heat pump, pellet, solar
 *    thermal…): 30% base, up to 70% with speed/income/efficiency bonuses; eligible
 *    cost cap ~€30k/unit. (KfW moved heating-replacement funding from BAFA in 2024.)
 *  - BAFA BEG EM (Einzelmaßnahmen) — building envelope / system tech (insulation,
 *    windows, controls; NOT heating): 15% base, +5% with an iSFP roadmap; cap
 *    €30k/unit (€60k with iSFP).
 *  - KfW 261 Wohngebäude-Kredit — full Effizienzhaus renovation: low-interest loan
 *    up to €150k/unit + repayment subsidy (handled as a loan referral, not a grant).
 *  - Solar PV: funded via EEG feed-in / separate schemes, not BEG.
 */

export type SubsidyEstimate = {
  program: string
  scheme: string
  ratePct: number
  maxRatePct: number
  capEurPerUnit: number | null
  grantEur: number | null
  note: string
  eligible: boolean
}

type MeasureClass = "heating" | "envelope" | "controls" | "renewables" | "other"

function classify(actionType: string | null): MeasureClass {
  const t = (actionType || "").toLowerCase()
  if (/(hvac|heat|boiler|pump|chiller|district)/.test(t)) return "heating"
  if (/(envelope|insul|window|glaz|facade|façade|roof|wall)/.test(t)) return "envelope"
  if (/(control|bms|automation|sensor)/.test(t)) return "controls"
  if (/(renew|solar|pv|photovolt)/.test(t)) return "renewables"
  return "other"
}

export function estimateSubsidy(
  actionType: string | null,
  capexEur: number | null
): SubsidyEstimate {
  const capex = capexEur ?? 0
  const cls = classify(actionType)

  if (cls === "heating") {
    const rate = 30
    const cap = 30000
    return {
      program: "KfW 458",
      scheme: "Heizungsförderung — renewable heating",
      ratePct: rate,
      maxRatePct: 70,
      capEurPerUnit: cap,
      grantEur: capex > 0 ? (rate / 100) * Math.min(capex, cap) : null,
      note: "Base 30%; up to 70% with speed/income/efficiency bonuses. Cap ~€30k/unit.",
      eligible: true,
    }
  }
  if (cls === "envelope" || cls === "controls") {
    const rate = 15
    const cap = 30000
    return {
      program: "BAFA BEG EM",
      scheme: "Building envelope / system tech",
      ratePct: rate,
      maxRatePct: 20,
      capEurPerUnit: cap,
      grantEur: capex > 0 ? (rate / 100) * Math.min(capex, cap) : null,
      note: "15% base (+5% with an iSFP roadmap). Cap €30k/unit (€60k with iSFP).",
      eligible: true,
    }
  }
  if (cls === "renewables") {
    return {
      program: "EEG / separate",
      scheme: "Solar PV",
      ratePct: 0,
      maxRatePct: 0,
      capEurPerUnit: null,
      grantEur: null,
      note: "PV is funded via EEG feed-in / separate schemes, not BEG.",
      eligible: false,
    }
  }
  return {
    program: "—",
    scheme: "Check eligibility",
    ratePct: 0,
    maxRatePct: 0,
    capEurPerUnit: null,
    grantEur: null,
    note: "No standard BEG match — assess case by case.",
    eligible: false,
  }
}
