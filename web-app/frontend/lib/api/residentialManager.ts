/**
 * Server-only fetch helper for the MANAGER residential dashboard.
 *
 * Reads GET /residential/buildings/{id} (B2B JWT). Per-unit, NAMED data for one
 * building the manager may see — distinct from /lib/api/residence.ts (the
 * resident's own anonymized-benchmark view). Types mirror backend
 * app/schemas/residential.py.
 */

export type ResidentialUnitRow = {
  unit_id: string
  area_m2: number | null
  is_heated: boolean | null
  eui_kwh_m2_yr: number | null
  eui_climate_adjusted_kwh_m2_yr: number | null
  epc_band: string | null
  vs_building_pct: number | null
  heating_dhw_kwh_annual: number | null
  common_allocated_kwh: number | null
  cov_days: number | null
}

export type UviStatus = {
  latest_year: number | null
  latest_month: number | null
  units_covered: number
}

export type ResidentialBuildingRollup = {
  units_with_data: number
  building_avg_eui_kwh_m2_yr: number | null
  climate_adjustment_factor: number | null
  epc_distribution: Record<string, number>
  uvi: UviStatus
}

export type ResidentialBuildingResponse = {
  fabric_building_id: string
  rollup: ResidentialBuildingRollup
  units: ResidentialUnitRow[]
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

export async function fetchBuildingResidential(
  accessToken: string,
  fabricBuildingId: string
): Promise<FetchResult<ResidentialBuildingResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  try {
    const res = await fetch(
      `${backendUrl}/residential/buildings/${encodeURIComponent(fabricBuildingId)}`,
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
      console.error(`[fetchBuildingResidential] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    const data = (await res.json()) as ResidentialBuildingResponse
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchBuildingResidential] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}


export type ResidentialPortfolioRow = {
  fabric_building_id: string
  name: string
  city: string | null
  country_code: string | null
  rollup: ResidentialBuildingRollup
}

export type ResidentialPortfolioResponse = {
  buildings: ResidentialPortfolioRow[]
}

// --- UVI / HKVO compliance readiness (R1) ---

export type UviComplianceRow = {
  fabric_building_id: string
  name: string
  total_units: number
  units_covered: number
  coverage_pct: number | null
  latest_year: number | null
  latest_month: number | null
  months_since_latest: number | null
  annual_heat_kwh: number | null
  penalty_exposure_eur: number | null
  status: string // ready | partial | at_risk
}

export type UviComplianceResponse = {
  deadline: string
  buildings_total: number
  buildings_ready: number
  buildings_at_risk: number
  total_penalty_exposure_eur: number
  heat_tariff_eur_kwh: number
  note: string
  rows: UviComplianceRow[]
}

export async function fetchUviCompliance(
  accessToken: string
): Promise<FetchResult<UviComplianceResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }
  try {
    const res = await fetch(`${backendUrl}/residential/uvi-compliance`, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchUviCompliance] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as UviComplianceResponse }
  } catch (err) {
    console.error("[fetchUviCompliance] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

export async function fetchResidentialPortfolio(
  accessToken: string
): Promise<FetchResult<ResidentialPortfolioResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }
  try {
    const res = await fetch(`${backendUrl}/residential/portfolio`, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchResidentialPortfolio] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as ResidentialPortfolioResponse }
  } catch (err) {
    console.error("[fetchResidentialPortfolio] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}
