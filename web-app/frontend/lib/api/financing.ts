/**
 * /financing API — portfolio financing summary (server fetch).
 * Mirrors backend schemas/financing.py + finance_model.py. SUPPORT, NOT ADVICE;
 * every forward figure is a screening-grade scenario range.
 */

export type FinancingMeasure = {
  building_name: string
  fabric_building_id: string
  title: string
  action_type: string | null
  program: string
  scheme: string
  eligible: boolean
  rate_low_pct: number
  rate_high_pct: number
  eligible_cost_eur: number | null
  grant_low_eur: number | null
  grant_high_eur: number | null
  units_basis: number | null
  subsidy_note: string
  capex_gross_eur: number
  net_capex_eur: number
  assumed_lifetime_years: number
  simple_payback_years: number | null
  npv_base_eur: number | null
}

export type FinancingScenario = {
  scenario: "conservative" | "base" | "high" | string
  total_npv_eur: number
  carbon_2030_eur_t: number
  energy_inflation_pct: number
}

export type FinancingValueUplift = {
  priority_buildings: number
  assumed_band_jump: number
  uplift_low_pct: number
  uplift_high_pct: number
  note: string
}

export type FinancingPortfolio = {
  total_capex_gross_eur: number
  total_grant_low_eur: number
  total_grant_high_eur: number
  total_net_after_grant_eur: number
  eligible_measure_count: number
  scenarios: FinancingScenario[]
  value_uplift: FinancingValueUplift | null
}

export type FinancingSummary = {
  measures: FinancingMeasure[]
  portfolio: FinancingPortfolio
  assumptions: Record<string, unknown>
  note: string
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

export async function fetchFinancingSummary(
  accessToken: string,
  params: { building_id?: string; has_isfp?: boolean } = {}
): Promise<FetchResult<FinancingSummary>> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  const search = new URLSearchParams()
  if (params.building_id) search.set("building_id", params.building_id)
  if (params.has_isfp) search.set("has_isfp", "true")
  const qs = search.toString()
  const url = `${backendUrl}/financing/summary${qs ? `?${qs}` : ""}`

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) {
      const body = await res.text().catch(() => "")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        return { ok: false, error: "fabric_unavailable" }
      }
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as FinancingSummary }
  } catch {
    return { ok: false, error: "Network error" }
  }
}
