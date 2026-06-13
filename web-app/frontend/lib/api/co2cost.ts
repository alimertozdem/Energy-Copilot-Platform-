/**
 * Server-only fetch for the per-building CO₂ cost-allocation (CO2KostAufG) report.
 *
 * Reads GET /compliance/co2-cost/{id} (B2B JWT). The landlord/tenant split of the
 * heating-fuel CO₂ price for one building the caller may see. Types mirror backend
 * app/schemas/co2_cost.py.
 */

export type Co2StairTier = {
  tier: number
  min_kg_m2: number
  max_kg_m2: number | null
  landlord_pct: number
  tenant_pct: number
}

export type Co2UnitAllocation = {
  unit_id: string
  area_m2: number | null
  area_share_pct: number | null
  co2_kg: number | null
  cost_eur: number | null
  landlord_cost_eur: number | null
  tenant_cost_eur: number | null
}

export type Co2CostAllocation = {
  fabric_building_id: string
  building_name: string
  building_type: string
  country_code: string | null
  is_residential: boolean
  reporting_year: number | null
  has_data: boolean
  floor_area_m2: number | null
  area_basis: string
  heating_co2_tonnes: number | null
  energy_content_kwh: number | null
  co2_intensity_kg_m2: number | null
  gas_emission_factor_kg_kwh: number
  co2_price_eur_t: number
  co2_price_eur_t_ets2: number
  ets2_year: number
  total_co2_cost_eur: number | null
  total_co2_cost_eur_ets2: number | null
  model: string
  tier: number | null
  landlord_pct: number | null
  tenant_pct: number | null
  landlord_cost_eur: number | null
  tenant_cost_eur: number | null
  landlord_cost_eur_ets2: number | null
  tenant_cost_eur_ets2: number | null
  stair: Co2StairTier[]
  note: string
  data_source: string
  units: Co2UnitAllocation[]
  unit_count: number | null
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

export async function fetchCo2CostAllocation(
  accessToken: string,
  fabricBuildingId: string
): Promise<FetchResult<Co2CostAllocation>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  try {
    const res = await fetch(
      `${backendUrl}/compliance/co2-cost/${encodeURIComponent(fabricBuildingId)}`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchCo2CostAllocation] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as Co2CostAllocation }
  } catch (err) {
    console.error("[fetchCo2CostAllocation] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}
