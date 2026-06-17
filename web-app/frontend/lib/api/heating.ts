/**
 * Heating & HVAC assessment (building grain) — server fetch.
 * Mirrors backend schemas/heating.py. Postgres-native (no Fabric); screening-grade.
 */
export type HeatingDemand = {
  heating_kwh: number
  heating_kwh_low: number
  heating_kwh_high: number
  heating_eui_kwh_m2: number | null
  heating_share_pct: number
  total_kwh: number
  basis: "measured" | "estimated" | "unknown"
  band_pct: number
}

export type HeatingSupply = {
  fuel_type: string
  fuel_assumed: boolean
  heat_cost_eur: number
  heat_co2_kg: number
  price_eur_kwh: number
  co2_factor_kg_kwh: number
}

export type EnvelopeElement = {
  element: "wall" | "roof" | "window" | string
  u_current: number | null
  u_target: number
  status: "pass" | "fail" | "unknown"
}

export type HeatingMeasure = {
  key: string
  label: string
  tier: string
  saving_kwh: number | null
  saving_kwh_gross: number | null
  saving_eur: number
  saving_co2_kg: number
  capex_gross: number
  capex_net: number
  payback_years: number | null
  note: string
}

export type HeatingPackageStep = {
  key: string
  label: string
  tier: string
  cumulative_reduction_pct: number
  cumulative_capex_net: number
  cumulative_saving_eur: number
  cumulative_co2_saved_kg: number
  heating_eui_after: number | null
  payback_years: number | null
}

export type HeatingPackageFull = {
  reduction_pct: number
  capex_net: number
  saving_eur: number
  co2_saved_kg: number
  payback_years: number | null
  eui_before: number | null
  eui_after: number | null
}

export type HeatingCarbon = {
  building_type: string
  total_co2_intensity_kg_m2: number | null
  total_co2_intensity_after_kg_m2: number | null
  heating_co2_kg: number
  heating_share_of_carbon_pct: number | null
  package_co2_saved_kg: number
  basis: "measured" | "estimated" | "unknown"
}

export type HeatingRegulation = {
  status: "applies" | "check_fuel" | "met"
  note: string
}

export type HeatingAssessment = {
  demand: HeatingDemand
  supply: HeatingSupply
  envelope: EnvelopeElement[]
  measures: HeatingMeasure[]
  package: {
    realistic_reduction_low_pct: number
    realistic_reduction_high_pct: number
    note: string
    steps: HeatingPackageStep[]
    full: HeatingPackageFull | null
  }
  carbon: HeatingCarbon
  regulation: HeatingRegulation
  assumptions: Record<string, string>
}

export async function fetchBuildingHeatingServer(
  accessToken: string,
  buildingId: string
): Promise<HeatingAssessment | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/heating`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    return (await res.json()) as HeatingAssessment
  } catch {
    return null
  }
}

/**
 * Comfort & operation analytics (GET /buildings/{id}/comfort). Mirrors
 * backend schemas/comfort.py. Standard comfort references.
 */
export type ComfortAssessment = {
  has_data: boolean
  window_hours: number
  simulated: boolean
  temperature: {
    avg: number
    in_band_pct: number
    under_pct: number
    over_pct: number
    samples: number
    band_low: number
    band_high: number
  } | null
  co2: { avg: number; good_pct: number; fair_pct: number; poor_pct: number; samples: number } | null
  humidity: { avg: number; in_band_pct: number; samples: number } | null
  delta_t: number | null
  operational_hint: string | null
}

export async function fetchBuildingComfortServer(
  accessToken: string,
  buildingId: string
): Promise<ComfortAssessment | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/comfort`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    return (await res.json()) as ComfortAssessment
  } catch {
    return null
  }
}
