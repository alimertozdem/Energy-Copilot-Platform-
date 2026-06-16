/**
 * Flexibility / dynamic-tariff readiness (indicative).
 *
 * The EU is scaling demand-side flexibility: dynamic retail tariffs + the
 * Demand Response Network Code (rules expected from ~2027). Buildings that can
 * shift load to low-price / low-carbon hours stand to cut those costs and
 * emissions (studies cite materially lower bills on the shifted portion).
 *
 * Energy-logic (refined 2026-06-16): flexibility = the ability to SHIFT load in
 * time, which needs BOTH (a) something to shift or store and (b) controls to
 * orchestrate it. So readiness is gated on controls:
 *   ready   = IoT controls AND battery storage (orchestrated, dispatchable)
 *   partial = exactly one of IoT controls / battery (an enabler, not orchestrated)
 *   limited = neither (meters only, or on-site solar with no controls/storage)
 * On-site PV is generation, not a demand-shift mechanism, so it is shown as a
 * minor enabler but NEVER makes a building "ready" on its own.
 *
 * This is an INDICATIVE readiness signal from the portfolio's asset inventory
 * plus a typical shiftable-load share by building type. It is NOT a metered
 * load-shift or savings calculation — price/carbon-aware optimisation for
 * battery sites is modelled separately (battery dispatch / Page 9).
 * Shiftable-share values are illustrative and conservative.
 */
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"

export type FlexReadiness = "ready" | "partial" | "limited"

export const FLEX_META: Record<
  FlexReadiness,
  { label: string; badge: string; dot: string }
> = {
  ready: {
    label: "Flexibility-ready",
    badge: "bg-emerald-500/15 text-emerald-200 border-emerald-500/30",
    dot: "bg-emerald-400",
  },
  partial: {
    label: "Partial",
    badge: "bg-amber-500/15 text-amber-200 border-amber-500/30",
    dot: "bg-amber-400",
  },
  limited: {
    label: "Limited",
    badge: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
    dot: "bg-zinc-500",
  },
}

/** Indicative share of load that is typically time-flexible, by building type. */
const SHIFTABLE_SHARE: Record<string, number> = {
  Logistics: 30,
  Warehouse: 30,
  Data_Center: 25,
  Office: 20,
  Education: 18,
  Retail: 18,
  Hotel: 15,
  Lab: 15,
  Healthcare: 8,
}
const DEFAULT_SHIFTABLE = 15

export type FlexResult = {
  building: PortfolioBuildingRow
  readiness: FlexReadiness
  enablers: string[]
  shiftable_share_pct: number
  /** True when the only enabler is PV (generation, not demand-shift). */
  pvOnly: boolean
}

export function assessFlex(b: PortfolioBuildingRow): FlexResult {
  const enablers: string[] = []
  if (b.has_battery) enablers.push("Battery storage")
  if (b.has_iot) enablers.push("IoT controls")
  if (b.has_pv) enablers.push("On-site solar")

  // Controls are the gate: orchestration (IoT) + something to dispatch (battery).
  let readiness: FlexReadiness
  if (b.has_iot && b.has_battery) readiness = "ready"
  else if (b.has_iot || b.has_battery) readiness = "partial"
  else readiness = "limited"

  const pvOnly = b.has_pv && !b.has_iot && !b.has_battery
  const share = SHIFTABLE_SHARE[b.building_type] ?? DEFAULT_SHIFTABLE
  return { building: b, readiness, enablers, shiftable_share_pct: share, pvOnly }
}

export type FlexSummary = {
  results: FlexResult[]
  ready: number
  partial: number
  limited: number
  with_battery: number
  with_iot: number
  with_pv: number
  avg_shiftable_pct: number | null
}

export function summarizeFlex(buildings: PortfolioBuildingRow[]): FlexSummary {
  const results = buildings.map(assessFlex)
  const ready = results.filter((r) => r.readiness === "ready").length
  const partial = results.filter((r) => r.readiness === "partial").length
  const limited = results.filter((r) => r.readiness === "limited").length
  const with_battery = buildings.filter((b) => b.has_battery).length
  const with_iot = buildings.filter((b) => b.has_iot).length
  const with_pv = buildings.filter((b) => b.has_pv).length
  const avg_shiftable_pct = results.length
    ? Math.round(
        results.reduce((a, r) => a + r.shiftable_share_pct, 0) / results.length
      )
    : null
  return {
    results,
    ready,
    partial,
    limited,
    with_battery,
    with_iot,
    with_pv,
    avg_shiftable_pct,
  }
}
