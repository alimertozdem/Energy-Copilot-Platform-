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

/** 30-day → annual scale factor. */
const ANNUALIZE = 365.25 / 30

/**
 * A pathway curve. Either 2-point anchors [start @startYear, end @endYear] — the
 * current ILLUSTRATIVE shape — or explicit year-indexed `points` (the official
 * licensed dataset). `points` take precedence when present.
 */
export type CrremCurve = { anchors?: [number, number]; points?: Record<number, number> }

export type CrremDataset = {
  source: "illustrative" | "official"
  version: string
  scenario: string
  metric: string
  startYear: number
  endYear: number
  defaultRegion: string
  /** region (ISO country code or "DEFAULT") -> asset type -> curve; "_default" = fallback type. */
  regions: Record<string, Record<string, CrremCurve>>
}

/**
 * The ACTIVE pathway dataset — ILLUSTRATIVE 1.5C anchors until an official licensed
 * set is loaded (see loadOfficialCrrem). Values are indicative kgCO2/m2.yr by asset
 * type; the official data adds per-country curves and exact year-by-year shape.
 */
export let CRREM_DATASET: CrremDataset = {
  source: "illustrative",
  version: "indicative-2026-06",
  scenario: "1.5C",
  metric: "carbon_kgco2_m2",
  startYear: PATHWAY_START_YEAR,
  endYear: PATHWAY_END_YEAR,
  defaultRegion: "DEFAULT",
  regions: {
    DEFAULT: {
      Office: { anchors: [45, 4] },
      Retail: { anchors: [50, 5] },
      Logistics: { anchors: [25, 3] },
      Warehouse: { anchors: [25, 3] },
      Hotel: { anchors: [75, 8] },
      Healthcare: { anchors: [100, 10] },
      Education: { anchors: [40, 4] },
      Data_Center: { anchors: [230, 25] },
      Lab: { anchors: [120, 12] },
      _default: { anchors: [50, 5] },
    },
  },
}

/**
 * Swap point: replace the active pathway data with the official licensed dataset
 * (per-country, year-indexed, source:"official"). Requires a CRREM License Partner
 * agreement. Nothing else in this module changes. See docs/compliance/crrem-official-swap.md.
 */
export function loadOfficialCrrem(dataset: CrremDataset): void {
  CRREM_DATASET = dataset
}
/** "illustrative" | "official" — the UI labels the curve from this. */
export function crremSource(): "illustrative" | "official" {
  return CRREM_DATASET.source
}
export function crremVersion(): string {
  return CRREM_DATASET.version
}

function curveFor(type: string, region?: string): CrremCurve {
  const reg =
    CRREM_DATASET.regions[region ?? CRREM_DATASET.defaultRegion] ??
    CRREM_DATASET.regions[CRREM_DATASET.defaultRegion]
  return reg[type] ?? reg._default ?? { anchors: [50, 5] }
}

/** Linearly-interpolated pathway value (kgCO2/m2.yr) for a year (+ optional region). */
export function pathwayValue(type: string, year: number, region?: string): number {
  const curve = curveFor(type, region)
  // Official year-indexed points: interpolate between the surrounding years.
  if (curve.points) {
    const years = Object.keys(curve.points).map(Number).sort((a, b) => a - b)
    if (years.length) {
      if (year <= years[0]) return curve.points[years[0]]
      if (year >= years[years.length - 1]) return curve.points[years[years.length - 1]]
      for (let i = 0; i < years.length - 1; i++) {
        const y0 = years[i]
        const y1 = years[i + 1]
        if (year >= y0 && year <= y1) {
          const t = (year - y0) / (y1 - y0)
          return curve.points[y0] + (curve.points[y1] - curve.points[y0]) * t
        }
      }
    }
  }
  // Illustrative 2-point anchors.
  const [start, end] = curve.anchors ?? [50, 5]
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

/** Pathway start value (kgCO2/m2.yr @ start year) for a type — sparkline y-scale. */
export function pathwayStart(type: string): number {
  return pathwayValue(type, PATHWAY_START_YEAR)
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

/**
 * Stranding year + status for a raw annual carbon intensity (kgCO2/m2.yr) and a
 * building type. Shared primitive: the portfolio path (assessStranding) and the
 * building-level Heating & HVAC path both use it, so the curve logic lives once.
 */
export function strandingYearForIntensity(
  type: string,
  intensity: number | null
): { strandingYear: number | null; status: StrandingStatus } {
  if (intensity == null) return { strandingYear: null, status: "unknown" }
  // Already above the 2025 pathway -> stranded today.
  if (intensity > pathwayValue(type, PATHWAY_START_YEAR)) {
    return { strandingYear: PATHWAY_START_YEAR, status: "stranded_now" }
  }
  // At or below the 2050 endpoint -> aligned through the horizon.
  if (intensity <= pathwayValue(type, PATHWAY_END_YEAR)) {
    return { strandingYear: null, status: "on_track" }
  }
  // Otherwise find the first year the (flat) intensity exceeds the pathway.
  for (let y = PATHWAY_START_YEAR + 1; y <= PATHWAY_END_YEAR; y++) {
    if (pathwayValue(type, y) < intensity) {
      return { strandingYear: y, status: "stranding" }
    }
  }
  return { strandingYear: null, status: "on_track" }
}

export function assessStranding(b: PortfolioBuildingRow): StrandingResult {
  const intensity = carbonIntensity(b)
  const { strandingYear, status } = strandingYearForIntensity(b.building_type, intensity)
  return { building: b, intensity, strandingYear, status }
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
