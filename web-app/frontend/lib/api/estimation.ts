/**
 * Tier-A estimation engine result — server fetch helper.
 *
 * The screening estimate band (EUI / energy / cost / CO₂ as low–point–high) plus
 * a confidence tier and the method that produced it, refined by whatever the
 * building exposes (archetype → vintage → climate → EPC → partial bill). Unlike
 * the legacy baseline estimate it works at every stage: it anchors to uploaded
 * bills and returns basis='actual' once ≥12 months exist.
 * Mirrors backend schemas/estimation.py::EngineEstimate.
 */
export type EngineEstimate = {
  basis: string // estimated | actual
  confidence: string // high | medium | low | very_low
  method: string
  building_type: string | null
  area_m2: number | null
  area_basis: string | null // user | gold | footprint | none
  eui_low: number | null
  eui_point: number | null
  eui_high: number | null
  annual_kwh_low: number | null
  annual_kwh_point: number | null
  annual_kwh_high: number | null
  annual_cost_eur_low: number | null
  annual_cost_eur_point: number | null
  annual_cost_eur_high: number | null
  annual_co2_kg_low: number | null
  annual_co2_kg_point: number | null
  annual_co2_kg_high: number | null
  cost_basis: string
  editable_fields: string[]
}

/** Server-side fetch (direct to the backend with the session token). Returns
 *  null on any failure or when the type can't be modelled (e.g. Datacenter), so
 *  the detail page degrades gracefully. */
export async function fetchBuildingEstimateServer(
  accessToken: string,
  buildingId: string
): Promise<EngineEstimate | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/estimate`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    const data = (await res.json()) as { available: boolean; estimate: EngineEstimate | null }
    return data?.available && data.estimate ? data.estimate : null
  } catch {
    return null
  }
}

/**
 * Portfolio screening — the Tier-A engine across EVERY visible building, so a
 * manager sees the whole portfolio scored even when most buildings have no
 * uploads. Mirrors backend schemas/estimation.py::PortfolioEstimatesResponse.
 */
export type PortfolioEstimateRow = {
  building_id: string
  name: string | null
  city: string | null
  building_type: string | null
  area_m2: number | null
  available: boolean
  basis: string // estimated | actual
  confidence: string
  has_real_data: boolean
  eui_low: number | null
  eui_point: number | null
  eui_high: number | null
  annual_cost_eur_point: number | null
  annual_co2_kg_point: number | null
}

export type PortfolioEstimates = {
  total: number
  scored: number
  estimated_count: number
  actual_count: number
  rows: PortfolioEstimateRow[]
}

export async function fetchPortfolioEstimatesServer(
  accessToken: string
): Promise<PortfolioEstimates | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(`${backendUrl}/portfolio/estimates`, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) return null
    return (await res.json()) as PortfolioEstimates
  } catch {
    return null
  }
}
