/**
 * EU Taxonomy alignment-indication screen for the /compliance page.
 *
 * Scope (approved with the product owner, 2026-06-02): EU Taxonomy Climate
 * Delegated Act, activity 7.7 "Acquisition and ownership of buildings",
 * substantial-contribution (SC) criterion for climate change mitigation ONLY.
 *
 * Energy-logic & assumptions (approved):
 *   1. Only activity 7.7 (operational ownership lens). Construction (7.1),
 *      renovation (7.2) and equipment (7.3-7.6) need CapEx/project data we do
 *      not hold, so they are out of scope.
 *   2. EPC band drives the indication:
 *        A           -> SC criterion met via the "EPC class A" route.
 *        B-C         -> potentially met via the "top 15% of the national stock
 *                       by primary energy demand (PED)" route — needs national
 *                       verification (we do not hold national PED percentiles).
 *        D-G / none  -> not met as-is / EPC missing.
 *   3. EUI (final energy, kWh/m2.yr) is shown as operational context only and is
 *      NEVER used for the top-15% test: the Taxonomy uses *primary* energy
 *      demand, which differs from final energy by primary-energy factors
 *      (~1.8-2.5x for electricity). Treating EUI as PED would overstate.
 *   4. Construction year is not in the dataset, so the pre-2021 existing-stock
 *      route (EPC-A / top-15%) is assumed. The post-2020 "PED >= 10% below NZEB"
 *      route cannot be evaluated and is flagged as such in the UI.
 *   5. Output is an "alignment indication on the SC-mitigation criterion" only.
 *      DNSH (do-no-significant-harm) and the minimum safeguards are NOT assessed
 *      here, so the screen NEVER asserts a building is "Taxonomy-aligned" or
 *      "Taxonomy-compliant". The portfolio share is a count and a
 *      floor-area-weighted proxy — NOT a turnover/CapEx/OpEx Taxonomy KPI.
 *   6. EPC validity (added 2026-06-16): under the EPBD an EPC is valid for 10
 *      years. An expired certificate is not valid evidence for any Taxonomy
 *      route, so we flag stale/expiring EPCs ("renew") rather than silently
 *      crediting a decade-old rating. The flag is advisory and does NOT change
 *      the route counts (the recorded class is still shown, just caveated).
 *
 * Indicative, swappable: national PED top-15% tables / NZEB values would be
 * added in this one module once licensed/sourced. Pure + dependency-free so it
 * can be unit-reasoned and reused by the PDF export.
 */
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"

export type TaxonomyRoute = "epc_a" | "top15_potential" | "not_met" | "epc_needed"

export type TaxonomyRouteMeta = {
  key: TaxonomyRoute
  label: string
  blurb: string
  textClass: string
  dotClass: string
  badgeClass: string
  /** Surfacing weight — higher shows first in the highlights list. */
  weight: number
}

export const TAXONOMY_ROUTES: Record<TaxonomyRoute, TaxonomyRouteMeta> = {
  epc_a: {
    key: "epc_a",
    label: "On the EPC-A route",
    blurb:
      "EPC class A — meets the activity 7.7 substantial-contribution route for existing buildings.",
    textClass: "text-emerald-300",
    dotClass: "bg-emerald-400",
    badgeClass: "bg-emerald-500/15 text-emerald-200 border-emerald-500/40",
    weight: 3,
  },
  top15_potential: {
    key: "top15_potential",
    label: "Potential (top-15%)",
    blurb:
      "EPC B-C — may qualify via the top-15% primary-energy route; needs national verification.",
    textClass: "text-teal-300",
    dotClass: "bg-teal-400",
    badgeClass: "bg-teal-500/15 text-teal-200 border-teal-500/30",
    weight: 2,
  },
  not_met: {
    key: "not_met",
    label: "Not met as-is",
    blurb:
      "EPC D-G — unlikely to meet the substantial-contribution criterion without renovation.",
    textClass: "text-amber-300",
    dotClass: "bg-amber-400",
    badgeClass: "bg-amber-500/15 text-amber-200 border-amber-500/30",
    weight: 1,
  },
  epc_needed: {
    key: "epc_needed",
    label: "EPC needed",
    blurb: "No EPC on file — required before any Taxonomy route can be evaluated.",
    textClass: "text-sky-300",
    dotClass: "bg-sky-400",
    badgeClass: "bg-sky-500/15 text-sky-200 border-sky-500/30",
    weight: 0,
  },
}

/** EPBD EPC validity period (years). */
export const EPC_VALIDITY_YEARS = 10

export type EpcValidity = "valid" | "expiring" | "expired" | "unknown"

/**
 * Large non-residential floor-area proxy for the ">290 kW HVAC" monitoring
 * criterion. The Taxonomy criterion is an HVAC effective rated-output threshold,
 * not a floor area — we do not hold rated output, so floor area is a rough proxy
 * used ONLY to decide whether to show the BACS/monitoring note. It is never a
 * determinant of alignment.
 */
export const LARGE_BUILDING_AREA_M2 = 5000

/** Building types treated as residential (Taxonomy distinguishes the two). */
const RESIDENTIAL_TYPES = new Set(["Residential", "Apartment", "Housing"])

function epcLetter(epc: string | null): string | null {
  if (!epc) return null
  const c = epc.trim().charAt(0).toUpperCase()
  return /^[A-G]$/.test(c) ? c : null
}

/** EPC validity status from its issue year against the 10-year EPBD window. */
export function epcValidity(
  epcYear: number | null | undefined,
  nowYear: number = new Date().getFullYear()
): EpcValidity {
  if (epcYear == null || epcYear < 1900) return "unknown"
  const age = nowYear - epcYear
  if (age > EPC_VALIDITY_YEARS) return "expired"
  if (age >= EPC_VALIDITY_YEARS - 1) return "expiring"
  return "valid"
}

export type BuildingTaxonomy = {
  building: PortfolioBuildingRow
  route: TaxonomyRoute
  reason: string
  /** Show the large-non-residential BACS/monitoring note for this building. */
  bacsRelevant: boolean
  /** has_iot satisfies the monitoring note (only meaningful if bacsRelevant). */
  bacsMet: boolean
  /** EPC issue year (from the certificate), if known. */
  epcYear: number | null
  /** EPC validity vs the 10-year EPBD window. */
  validity: EpcValidity
}

/** Indicative activity-7.7 SC-mitigation route for a single building. */
export function assessTaxonomy(
  b: PortfolioBuildingRow,
  nowYear: number = new Date().getFullYear()
): BuildingTaxonomy {
  const letter = epcLetter(b.epc_class)
  const isResidential = RESIDENTIAL_TYPES.has(b.building_type)
  const bacsRelevant = !isResidential && (b.floor_area_m2 ?? 0) >= LARGE_BUILDING_AREA_M2
  const bacsMet = bacsRelevant && b.has_iot
  const epcYear = b.epc_year ?? null
  const validity = letter ? epcValidity(epcYear, nowYear) : "unknown"

  let route: TaxonomyRoute
  let reason: string
  if (letter === "A") {
    route = "epc_a"
    reason =
      "EPC A — meets the substantial-contribution criterion via the EPC-A route for existing buildings."
  } else if (letter === "B" || letter === "C") {
    route = "top15_potential"
    reason = `EPC ${letter} — may meet the criterion via the top-15% primary-energy route; requires national PED verification.`
  } else if (letter === "D" || letter === "E" || letter === "F" || letter === "G") {
    route = "not_met"
    reason = `EPC ${letter} — unlikely to meet substantial contribution without renovation.`
  } else {
    route = "epc_needed"
    reason = "No EPC on file — required before any Taxonomy route can be evaluated."
  }

  if (validity === "expired") {
    reason += ` EPC issued ${epcYear} is past its 10-year validity — renew before it counts as Taxonomy evidence.`
  } else if (validity === "expiring") {
    reason += ` EPC issued ${epcYear} is nearing its 10-year expiry — plan a renewal.`
  }

  return { building: b, route, reason, bacsRelevant, bacsMet, epcYear, validity }
}

export type TaxonomySummary = {
  total: number
  counts: Record<TaxonomyRoute, number>
  results: BuildingTaxonomy[]
  /** Count of buildings on the EPC-A route. */
  onRouteCount: number
  /** Share of buildings on the EPC-A route (0-1). */
  onRouteShare: number
  /** Floor-area-weighted EPC-A share (0-1) — a proxy, not a turnover/CapEx KPI. */
  onRouteAreaShare: number
  /** Count of buildings where the large-building monitoring criterion applies. */
  bacsRelevantCount: number
  /** Of those, how many already have monitoring (has_iot). */
  bacsMetCount: number
  /** Buildings with an EPC that is past (or near) its 10-year validity. */
  staleEpcCount: number
  /** Buildings to surface (EPC-A first, then potential), best first. */
  highlights: BuildingTaxonomy[]
}

export function summarizeTaxonomy(
  buildings: PortfolioBuildingRow[],
  nowYear: number = new Date().getFullYear()
): TaxonomySummary {
  const results = buildings.map((b) => assessTaxonomy(b, nowYear))
  const counts: Record<TaxonomyRoute, number> = {
    epc_a: 0,
    top15_potential: 0,
    not_met: 0,
    epc_needed: 0,
  }
  for (const r of results) counts[r.route] += 1

  const total = buildings.length
  const onRouteCount = counts.epc_a
  const onRouteShare = total > 0 ? onRouteCount / total : 0

  const totalArea = buildings.reduce((a, b) => a + (b.floor_area_m2 || 0), 0)
  const onRouteArea = results
    .filter((r) => r.route === "epc_a")
    .reduce((a, r) => a + (r.building.floor_area_m2 || 0), 0)
  const onRouteAreaShare = totalArea > 0 ? onRouteArea / totalArea : 0

  const bacsRelevantCount = results.filter((r) => r.bacsRelevant).length
  const bacsMetCount = results.filter((r) => r.bacsMet).length
  const staleEpcCount = results.filter(
    (r) => r.validity === "expired" || r.validity === "expiring"
  ).length

  const highlights = results
    .filter((r) => r.route === "epc_a" || r.route === "top15_potential")
    .sort(
      (a, b) => TAXONOMY_ROUTES[b.route].weight - TAXONOMY_ROUTES[a.route].weight
    )

  return {
    total,
    counts,
    results,
    onRouteCount,
    onRouteShare,
    onRouteAreaShare,
    bacsRelevantCount,
    bacsMetCount,
    staleEpcCount,
    highlights,
  }
}
