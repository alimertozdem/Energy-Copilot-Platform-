/**
 * Heating & HVAC assessment (building grain) — server fetch.
 * Mirrors backend schemas/heating.py. Postgres-native (no Fabric); screening-grade.
 */
export type HeatingDemand = {
  heating_kwh: number
  heating_eui_kwh_m2: number | null
  heating_share_pct: number
  total_kwh: number
  basis: "measured" | "estimated" | "unknown"
}

export type HeatingSupply = {
  fuel_type: string
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
  saving_eur: number
  saving_co2_kg: number
  capex_gross: number
  capex_net: number
  payback_years: number | null
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
  }
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
