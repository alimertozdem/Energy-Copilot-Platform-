/**
 * CRREM-style stranding analysis for the /compliance page.
 *
 * Method = the CRREM standard: compare a building's annual operational carbon
 * intensity (kgCO2/m2.yr) against a declining 1.5C decarbonisation pathway;
 * the first year the (held-flat) intensity exceeds the pathway is the
 * "stranding year".
 *
 * IMPORTANT — the pathway values below are ILLUSTRATIVE, NOT the official
 * licensed CRREM dataset. Embedding the official CRREM pathways in commercial
 * software requires a CRREM License Partner agreement; these indicative curves
 * let us ship the capability now and swap in official values from THIS one
 * module later (decision approved with the product owner, 2026-06-02). Anchors
 * are rough 1.5C-aligned values by asset type and are clearly labelled in the
 * UI. Real curves also vary by country grid — out of scope for the indicative
 * version.
 *
 * Annualisation caveat (2026-06-16): intensity is scaled from a 30-day CO2
 * window (x365.25/30). A heating- or cooling-heavy 30-day window over- or
 * under-states the annual figure, so the stranding year is indicative. A full
 * trailing-year CO2 figure (a backend field) would remove this; surfaced in the
 * UI as a one-line caveat.
 */
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"

export const PATHWAY_START_YEAR = 2025
export const PATHWAY_END_YEAR = 2050

/** EPBD/CRREM milestone years worth marking on a pathway visual. */
export const MILESTONE_YEARS = [2030, 2033, 2040, 2050] as const

/** Indicative kgCO2/m2.yr anchors [start @2025, end @2050] per building type. */
const PATHWAY_ANCHORS: Record<string, [number, number]> = {
  Office: [45, 4],
  Retail: [50, 5],
  Logistics: [25, 3],
  Warehouse: [25, 3],
  Hotel: [75, 8],
  Healthcare: [100, 10],
  Education: [40, 4],
  Data_Center: [230, 25],
  Lab: [120, 12],
}
const DEFAULT_ANCHOR: [number, number] = [50, 5]

/** 30-day → annual scale factor. */
const ANNUALIZE = 365.25 / 30

function anchorFor(type: string): [number, number] {
  return PATHWAY_ANCHORS[type] ?? DEFAULT_ANCHOR
}

/** Linearly-interpolated pathway value (kgCO2/m2.yr) for a given year. */
export function pathwayValue(type: string, year: number): number {
  const [start, end] = anchorFor(type)
  if (year <= PATHWAY_START_YEAR) return start
  if (year >= PATHWAY_END_YEAR) return end
  const t = (year - PATHWAY_START_YEAR) / (PATHWAY_END_YEAR - PATHWAY_START_YEAR)
  return start + (end - start) * t
}

export type PathwayPoint = { year: number; value: number }

/**
 * Sampled pathway curve for a building type, for an inline sparkline.
 * Returns evenly-spaced {year, value} points from start to end (inclusive).
 */
export function pathwayPoints(type: string, step = 5): PathwayPoint[] {
  const pts: PathwayPoint[] = []
  for (let y = PATHWAY_START_YEAR; y <= PATHWAY_END_YEAR; y += step) {
    pts.push({ year: y, value: pathwayValue(type, y) })
  }
  if (pts[pts.length - 1]?.year !== PATHWAY_END_YEAR) {
    pts.push({ year: PATHWAY_END_YEAR, value: pathwayValue(type, PATHWAY_END_YEAR) })
  }
  return pts
}

/** Pathway start value (kgCO2/m2.yr @2025) for a type — sparkline y-scale. */
export function pathwayStart(type: string): number {
  return anchorFor(type)[0]
}

export type StrandingStatus = "stranded_now" | "stranding" | "on_track" | "unknown"

export type StrandingResult = {
  building: PortfolioBuildingRow
  /** Annualised operational carbon intensity, kgCO2/m2.yr. */
  intensity: number | null
  /** First year the pathway drops below the flat intensity, or null. */
  strandingYear: number | null
  status: StrandingStatus
}

/** Annualised operational carbon intensity (kgCO2/m2.yr) from recent data. */
export function carbonIntensity(b: PortfolioBuildingRow): number | null {
  if (!b.floor_area_m2 || b.floor_area_m2 <= 0) return null
  if (b.co2_30d_kg == null) return null
  return (b.co2_30d_kg * ANNUALIZE) / b.floor_area_m2
}

export function assessStranding(b: PortfolioBuildingRow): StrandingResult {
  const intensity = carbonIntensity(b)
  if (intensity == null) {
    return { building: b, intensity: null, strandingYear: null, status: "unknown" }
  }
  const type = b.building_type

  // Already above the 2025 pathway -> stranded today.
  if (intensity > pathwayValue(type, PATHWAY_START_YEAR)) {
    return { building: b, intensity, strandingYear: PATHWAY_START_YEAR, status: "stranded_now" }
  }
  // At or below the 2050 endpoint -> aligned through the horizon.
  if (intensity <= pathwayValue(type, PATHWAY_END_YEAR)) {
    return { building: b, intensity, strandingYear: null, status: "on_track" }
  }
  // Otherwise find the first year the (flat) intensity exceeds the pathway.
  for (let y = PATHWAY_START_YEAR + 1; y <= PATHWAY_END_YEAR; y++) {
    if (pathwayValue(type, y) < intensity) {
      return { building: b, intensity, strandingYear: y, status: "stranding" }
    }
  }
  return { building: b, intensity, strandingYear: null, status: "on_track" }
}

export type StrandingSummary = {
  results: StrandingResult[]
  assessed: number
  strandedNow: number
  strandedBy2030: number
  strandedBy2035: number
  avgStrandingYear: number | null
}

export function summarizeStranding(
  buildings: PortfolioBuildingRow[]
): StrandingSummary {
  const results = buildings.map(assessStranding)
  const assessed = results.filter((r) => r.intensity != null).length
  const strandedNow = results.filter((r) => r.status === "stranded_now").length
  const years = results
    .map((r) => r.strandingYear)
    .filter((y): y is number => y != null)
  const strandedBy2030 = years.filter((y) => y <= 2030).length
  const strandedBy2035 = years.filter((y) => y <= 2035).length
  const avgStrandingYear = years.length
    ? Math.round(years.reduce((a, b) => a + b, 0) / years.length)
    : null
  return {
    results,
    assessed,
    strandedNow,
    strandedBy2030,
    strandedBy2035,
    avgStrandingYear,
  }
}
