/**
 * Compliance / renovation-risk logic for the /compliance page.
 *
 * Energy-logic (reviewed + approved with the product owner):
 *   - Primary signal = EPC class. Member states are expected to implement the
 *     revised EPBD's minimum energy performance standards (MEPS) largely via EPC
 *     thresholds, so EPC band is the most defensible proxy:
 *       F–G -> high (renovation priority), D–E -> watch, A–C -> lower.
 *   - Secondary signal = EUI > 200 kWh/m²·yr (the app's existing "poor" tier):
 *     a proxy when EPC is unknown, and an operational watch flag for otherwise
 *     well-rated buildings.
 *   - National MEPS thresholds are NOT finalised (EPBD transposition due
 *     2026-05, non-residential MEPS by 2027), and "worst 16/26%" is defined
 *     against the *national* stock, not a single portfolio. So this is an
 *     INDICATIVE renovation-risk view, never a compliance verdict.
 *
 * Pure + dependency-free so it can be unit-reasoned and reused by an export.
 */
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"

export type RiskBand = "high" | "watch" | "lower" | "epc_needed"

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

/** "High energy use" threshold — matches the portfolio EUI "poor" tier. */
export const HIGH_EUI_THRESHOLD = 200

export type BuildingRisk = {
  building: PortfolioBuildingRow
  band: RiskBand
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

  if (letter === "F" || letter === "G") {
    return {
      building: b,
      band: "high",
      reason: `EPC ${letter} — among the worst bands likely targeted by MEPS.`,
    }
  }
  if (letter === "D" || letter === "E") {
    return {
      building: b,
      band: "watch",
      reason: `EPC ${letter} — mid band; monitor as MEPS thresholds tighten.`,
    }
  }
  if (letter === "A" || letter === "B" || letter === "C") {
    if (euiHigh) {
      return {
        building: b,
        band: "watch",
        reason: `EPC ${letter} but high energy use (EUI > ${HIGH_EUI_THRESHOLD}) — operational review.`,
      }
    }
    return { building: b, band: "lower", reason: `EPC ${letter} — efficient band.` }
  }

  // No / unrecognised EPC.
  const euiNote = euiHigh
    ? ` High energy use (EUI > ${HIGH_EUI_THRESHOLD}) suggests elevated risk.`
    : ""
  return {
    building: b,
    band: "epc_needed",
    reason: `No EPC on file — required on sale/lease under the EPBD.${euiNote}`,
  }
}

export type ComplianceSummary = {
  total: number
  counts: Record<RiskBand, number>
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

  const priority = risks
    .filter((r) => r.band === "high" || r.band === "epc_needed")
    .sort((a, b) => {
      const w = RISK_BANDS[b.band].weight - RISK_BANDS[a.band].weight
      if (w !== 0) return w
      const ea = a.building.eui_kwh_m2_yr ?? -1
      const eb = b.building.eui_kwh_m2_yr ?? -1
      return eb - ea
    })

  return { total: buildings.length, counts, risks, priority }
}
