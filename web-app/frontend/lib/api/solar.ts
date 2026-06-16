/**
 * Server-only fetch helper for the /solar detail page.
 * Types in lockstep with backend app/schemas/solar.py.
 */

export type SolarSeriesPoint = {
  date: string
  generated_kwh: number
  self_consumed_kwh: number
  exported_kwh: number
  performance_ratio: number | null
}

export type SolarSummary = {
  total_generated_kwh: number
  total_self_consumed_kwh: number
  total_exported_kwh: number
  avg_performance_ratio: number | null
  self_consumption_rate: number
  specific_yield_kwh_kwp: number | null
  specific_yield_annualized: boolean | null
  pv_capacity_kwp: number
  days: number
  data_basis: string
  real_building_count: number
  simulated_building_count: number
  self_consumption_available: boolean
  self_consumption_coverage_pct: number | null
}

export type SolarDetailResponse = {
  has_data: boolean
  series: SolarSeriesPoint[]
  summary: SolarSummary | null
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

export async function fetchSolarDetail(
  accessToken: string
): Promise<FetchResult<SolarDetailResponse>> {
  const backendUrl = process.env.BACKEND_URL || null
  if (!backendUrl) {
    console.error("[fetchSolarDetail] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  try {
    const res = await fetch(`${backendUrl}/solar/detail`, {
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
        console.warn(`[fetchSolarDetail] Fabric data temporarily unavailable`)
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchSolarDetail] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as SolarDetailResponse }
  } catch (err) {
    console.error("[fetchSolarDetail] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}
