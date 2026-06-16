/**
 * Server-only fetch helpers for backend /portfolio endpoints.
 * Types must stay in lockstep with backend app/schemas/portfolio.py.
 */

export type Direction = "up" | "down" | "neutral"

export type KPITile = {
  value: number
  unit: string
  delta_pct: number | null
  direction: Direction
}

export type PortfolioPeriod = {
  start_date: string
  end_date: string
  days: number
}

export type SolarKPIs = {
  generated: KPITile
  renewable_rate: KPITile
  exported: KPITile
  co2_avoided: KPITile
}

export type PortfolioKPIs = {
  period: PortfolioPeriod
  total_energy: KPITile
  avg_eui: KPITile
  total_cost: KPITile
  total_co2: KPITile
  solar: SolarKPIs | null
}

export type PortfolioBuildingRow = {
  fabric_building_id: string
  name: string
  city: string
  country: string
  building_type: string
  floor_area_m2: number
  epc_class: string | null
  epc_year?: number | null
  kwh_30d: number
  cost_30d_eur: number
  co2_30d_kg: number
  eui_kwh_m2_yr: number | null
  open_anomalies: number
  open_recommendations: number
  has_pv: boolean
  has_battery: boolean
  has_iot: boolean
  subscription_tier: string
}

export type PortfolioBuildingsResponse = {
  buildings: PortfolioBuildingRow[]
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

function logError(scope: string, status: number, body: string) {
  console.error(`[${scope}] Backend ${status}: ${body.slice(0, 200)}`)
}

async function getJson<T>(
  scope: string,
  path: string,
  accessToken: string
): Promise<FetchResult<T>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error(`[${scope}] BACKEND_URL not configured`)
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }

  try {
    const res = await fetch(`${backendUrl}${path}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        console.warn(`[${scope}] Fabric data temporarily unavailable`)
        return { ok: false, error: "fabric_unavailable" }
      }
      logError(scope, res.status, body)
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as T
    return { ok: true, data }
  } catch (err) {
    console.error(`[${scope}] Network/unknown error:`, err)
    return { ok: false, error: "Network error" }
  }
}

export async function fetchPortfolioKPIs(
  accessToken: string,
  clientOrgId?: string | null
): Promise<FetchResult<PortfolioKPIs>> {
  const q = clientOrgId ? `?client=${encodeURIComponent(clientOrgId)}` : ""
  return getJson<PortfolioKPIs>("fetchPortfolioKPIs", `/portfolio/kpis${q}`, accessToken)
}

export async function fetchPortfolioBuildings(
  accessToken: string,
  clientOrgId?: string | null
): Promise<FetchResult<PortfolioBuildingsResponse>> {
  const q = clientOrgId ? `?client=${encodeURIComponent(clientOrgId)}` : ""
  return getJson<PortfolioBuildingsResponse>(
    "fetchPortfolioBuildings",
    `/portfolio/buildings${q}`,
    accessToken
  )
}
