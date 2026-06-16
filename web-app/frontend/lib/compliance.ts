/**
 * Compliance / renovation-risk logic for the /compliance page.
 *
 * Energy-logic (reviewed + approved with the product owner; refined 2026-06-16):
 *   - Primary signal = EPC class. Member states are expected to implement the
 *     revised EPBD's minimum energy performance standards (MEPS) largely via EPC
 *     thresholds, so EPC band is the most defensible proxy:
 *       G -> renovation priority, EPBD "worst ~16%" 2030 milestone scope.
 *       F -> renovation priority, EPBD "~26%" 2033 milestone scope.
 *       D-E -> watch, A-C -> lower.
 *   - Secondary signal = high ABSOLUTE energy use (EUI > 200 kWh/m2.yr, the app's
 *     existing flat ASHRAE-style "poor" tier). Used only as a proxy when EPC is
 *     unknown, and as an operational watch flag for otherwise well-rated
 *     buildings. NOT type-normalised: for high-intensity types (healthcare, labs,
 *     data centres) a high EUI is expected, so read it as context, not waste.
 *   - National MEPS thresholds are NOT finalised (EPBD transposition due
 *     2026-05, non-residential MEPS by 2027), and "worst 16/26%" is defined
 *     against the *national* stock, not a single portfolio. So this is an
 *     INDICATIVE renovation-risk view, never a compliance verdict. The
 *     G->2030 / F->2033 split maps EPC bands to the EPBD milestones for triage
 *     only; the actual national cut-offs may differ.
 *
 * Pure + dependency-free so it can be unit-reasoned and reused by an export.
 */
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"

export type RiskBand = "high" | "watch" | "lower" | "epc_needed"

/** EPBD renovation milestone an at-risk building maps to (triage only). */
export type MepsMilestone = "2030" | "2033" | null

export type RiskBandMeta = {
  key: RiskBand
  label: string
  blurb: string
  textClass: string
  dotClass: string
  badgeClass: string
  /** Surfacing weight — higher shows first in the priority list. */
  weight: number
}

export const RISK_BANDS: Record<RiskBand, RiskBandMeta> = {
  high: {
    key: "high",
    label: "Renovation priority",
    blurb: "Worst EPC bands (F–G) — most likely targeted by future MEPS.",
    textClass: "text-red-300",
    dotClass: "bg-red-400",
    badgeClass: "bg-red-500/15 text-red-200 border-red-500/40",
    weight: 3,
  },
  epc_needed: {
    key: "epc_needed",
    label: "EPC needed",
    blurb: "No EPC on file — itself required on sale or lease under the EPBD.",
    textClass: "text-sky-300",
    dotClass: "bg-sky-400",
    badgeClass: "bg-sky-500/15 text-sky-200 border-sky-500/30",
    weight: 2,
  },
  watch: {
    key: "watch",
    label: "Watch",
    blurb: "Mid EPC bands (D–E), or a good rating with high measured energy use.",
    textClass: "text-amber-300",
    dotClass: "bg-amber-400",
    badgeClass: "bg-amber-500/15 text-amber-200 border-amber-500/30",
    weight: 1,
  },
  lower: {
    key: "lower",
    label: "Lower risk",
    blurb: "Efficient EPC bands (A–C) with no high-use flag.",
    textClass: "text-emerald-300",
    dotClass: "bg-emerald-400",
    badgeClass: "bg-emerald-500/15 text-emerald-200 border-emerald-500/30",
    weight: 0,
  },
}

/** EPBD milestone metadata for the renovation-priority split. */
export const MEPS_MILESTONES: Record<
  "2030" | "2033",
  { year: string; label: string; blurb: string }
> = {
  "2030": {
    year: "2030",
    label: "2030 scope",
    blurb: "EPC G — first EPBD milestone (worst ~16% of the stock).",
  },
  "2033": {
    year: "2033",
    label: "2033 scope",
    blurb: "EPC F — second EPBD milestone (~26% of the stock).",
  },
}

/** "High energy use" threshold — matches the portfolio EUI "poor" tier (flat). */
export const HIGH_EUI_THRESHOLD = 200

export type BuildingRisk = {
  building: PortfolioBuildingRow
  band: RiskBand
  /** EPBD milestone this building maps to (only for renovation-priority). */
  milestone: MepsMilestone
  reason: string
}

function epcLetter(epc: string | null): string | null {
  if (!epc) return null
  const c = epc.trim().charAt(0).toUpperCase()
  return /^[A-G]$/.test(c) ? c : null
}

/** Indicative renovation / MEPS-readiness band for a single building. */
export function assessBuilding(b: PortfolioBuildingRow): BuildingRisk {
  const letter = epcLetter(b.epc_class)
  const euiHigh =
    b.eui_kwh_m2_yr != null && b.eui_kwh_m2_yr > HIGH_EUI_THRESHOLD

  if (letter === "G") {
    return {
      building: b,
      band: "high",
      milestone: "2030",
      reason: `EPC G — worst class; first EPBD milestone (worst ~16% by 2030).`,
    }
  }
  if (letter === "F") {
    return {
      building: b,
      band: "high",
      milestone: "2033",
      reason: `EPC F — second EPBD milestone (~26% of the stock by 2033).`,
    }
  }
  if (letter === "D" || letter === "E") {
    return {
      building: b,
      band: "watch",
      milestone: null,
      reason: `EPC ${letter} — mid band; monitor as MEPS thresholds tighten.`,
    }
  }
  if (letter === "A" || letter === "B" || letter === "C") {
    if (euiHigh) {
      return {
        building: b,
        band: "watch",
        milestone: null,
        reason: `EPC ${letter} but high absolute energy use (EUI > ${HIGH_EUI_THRESHOLD}) — operational review; expected for high-intensity types.`,
      }
    }
    return {
      building: b,
      band: "lower",
      milestone: null,
      reason: `EPC ${letter} — efficient band.`,
    }
  }

  // No / unrecognised EPC.
  const euiNote = euiHigh
    ? ` High absolute energy use (EUI > ${HIGH_EUI_THRESHOLD}) suggests elevated risk.`
    : ""
  return {
    building: b,
    band: "epc_needed",
    milestone: null,
    reason: `No EPC on file — required on sale/lease under the EPBD.${euiNote}`,
  }
}

export type ComplianceSummary = {
  total: number
  counts: Record<RiskBand, number>
  /** Renovation-priority buildings mapping to the 2030 EPBD milestone (EPC G). */
  scope2030: number
  /** Renovation-priority buildings mapping to the 2033 EPBD milestone (EPC F). */
  scope2033: number
  risks: BuildingRisk[]
  /** Actionable buildings (renovation priority + missing EPC), worst first. */
  priority: BuildingRisk[]
}

export function summarizeCompliance(
  buildings: PortfolioBuildingRow[]
): ComplianceSummary {
  const risks = buildings.map(assessBuilding)
  const counts: Record<RiskBand, number> = {
    high: 0,
    watch: 0,
    lower: 0,
    epc_needed: 0,
  }
  for (const r of risks) counts[r.band] += 1

  const scope2030 = risks.filter((r) => r.milestone === "2030").length
  const scope2033 = risks.filter((r) => r.milestone === "2033").length

  const priority = risks
    .filter((r) => r.band === "high" || r.band === "epc_needed")
    .sort((a, b) => {
      const w = RISK_BANDS[b.band].weight - RISK_BANDS[a.band].weight
      if (w !== 0) return w
      // Within renovation priority, 2030 scope (G) before 2033 scope (F).
      const ma = a.milestone === "2030" ? 1 : 0
      const mb = b.milestone === "2030" ? 1 : 0
      if (ma !== mb) return mb - ma
      const ea = a.building.eui_kwh_m2_yr ?? -1
      const eb = b.building.eui_kwh_m2_yr ?? -1
      return eb - ea
    })

  return { total: buildings.length, counts, scope2030, scope2033, risks, priority }
}
