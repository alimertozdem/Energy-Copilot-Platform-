/**
 * Server-only fetch for the ESRS-E1-aligned compliance report.
 * Types mirror backend app/schemas/esrs.py.
 */

export type EsrsScopeBreakdown = {
  scope1_tco2e: number
  scope2_location_tco2e: number
  scope2_market_tco2e: number
  scope3_tco2e: number
  total_location_tco2e: number
  total_market_tco2e: number
}

export type EsrsBuildingRow = {
  fabric_building_id: string
  name: string
  building_type: string
  floor_area_m2: number
  scope1_tco2e: number
  scope2_location_tco2e: number
  scope2_market_tco2e: number
  scope3_tco2e: number
  total_location_tco2e: number
  ghg_intensity_tco2e_m2: number | null
  data_quality_flag: string | null
}

export type EsrsDataQuality = {
  complete: number
  estimated: number
  missing_gas: number
  other: number
}

export type EsrsReport = {
  reporting_year: number | null
  has_data: boolean
  buildings_total: number
  buildings_reported: number
  floor_area_m2: number
  energy_total_mwh: number
  energy_renewable_pct: number | null
  ghg: EsrsScopeBreakdown
  ghg_intensity_tco2e_m2: number | null
  data_quality: EsrsDataQuality
  rows: EsrsBuildingRow[]
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

export async function fetchEsrsReport(
  accessToken: string,
  buildingId?: string | null
): Promise<FetchResult<EsrsReport>> {
  const backendUrl = process.env.BACKEND_URL || null
  if (!backendUrl) {
    console.error("[fetchEsrsReport] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }

  const url = buildingId
    ? `${backendUrl}/compliance/esrs?building_id=${encodeURIComponent(buildingId)}`
    : `${backendUrl}/compliance/esrs`

  try {
    const res = await fetch(url, {
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
        console.warn("[fetchEsrsReport] Fabric data temporarily unavailable")
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchEsrsReport] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as EsrsReport
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchEsrsReport] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}
