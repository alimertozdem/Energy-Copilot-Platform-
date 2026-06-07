/**
 * Server-only fetch helper for the resident view (/residence).
 *
 * The resident is NOT a NextAuth B2B user, so this sends NO bearer token. The
 * resident's identity is passed as the `X-Resident-Id` header; the backend only
 * honors it when RESIDENT_DEV_MODE=1 (P4-1 dev override), and returns 401
 * otherwise. P4-3 (magic-link session) will replace the header source with a real
 * resident session — this fetcher's shape stays the same.
 *
 * Types must stay in lockstep with backend app/schemas/residence.py.
 */

export type ResidenceKpi = {
  eui_kwh_m2_yr: number | null
  eui_climate_adjusted_kwh_m2_yr: number | null
  climate_adjustment_factor: number | null
  epc_band: string | null
  heating_dhw_kwh_annual: number | null
  building_avg_eui_kwh_m2_yr: number | null
  vs_building_pct: number | null
  coverage_start: string | null
  coverage_end: string | null
  cov_days: number | null
}

export type ResidenceCommonArea = {
  unit_metered_kwh: number | null
  unit_allocated_kwh: number | null
  allocation_share: number | null
  cons_weight: number | null
  area_weight: number | null
  cons_share: number | null
  area_share: number | null
  building_total_kwh: number | null
  coverage_start: string | null
  coverage_end: string | null
}

export type ResidenceMonthlyPoint = {
  year: number
  month: number
  energy_type: string
  kwh: number | null
  cost_eur: number | null
  building_avg_kwh: number | null
  vs_building_pct: number | null
}

export type ResidenceUnit = {
  unit_id: string
  area_m2: number | null
  is_heated: boolean | null
  kpi: ResidenceKpi | null
  common_area: ResidenceCommonArea | null
  monthly: ResidenceMonthlyPoint[]
}

export type ResidenceSummary = {
  as_of: string
  units: ResidenceUnit[]
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

function getBackendUrl(): string {
  // Defaults to the local uvicorn instance; production overrides via env.
  return process.env.BACKEND_URL || "http://127.0.0.1:8000"
}

/**
 * Server-side fetch of the resident's own-unit summary.
 *
 * `residentId` is the resident_identity UUID (dev: from the ?resident= query
 * param; later: from the resident session). No auth bearer — see module docstring.
 */
export type ResidentIdentity = { token?: string | null; devResidentId?: string | null }

export async function fetchResidenceSummary(
  identity: ResidentIdentity
): Promise<FetchResult<ResidenceSummary>> {
  const url = `${getBackendUrl()}/residence/summary`
  const headers: Record<string, string> = { Accept: "application/json" }
  if (identity.token) {
    headers["Authorization"] = `Bearer ${identity.token}`
  } else if (identity.devResidentId) {
    headers["X-Resident-Id"] = identity.devResidentId
  }
  try {
    const res = await fetch(url, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        return { ok: false, error: "fabric_unavailable" }
      }
      if (res.status === 401) {
        // Dev override off, or no/invalid resident id.
        return { ok: false, error: "resident_unauthorized" }
      }
      console.error(`[fetchResidenceSummary] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as ResidenceSummary
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchResidenceSummary] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}
