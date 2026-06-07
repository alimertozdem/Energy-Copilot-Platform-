/**
 * Abatement (MACC) — server-side fetch helper.
 *
 * Reads the portfolio Marginal Abatement Cost Curve from FastAPI
 * GET /abatement/macc (server-authoritative MAC compute). Used by the
 * /decarbonisation server component. Types mirror backend schemas/abatement.py.
 */

export type MaccMeasure = {
  action_id: string
  fabric_building_id: string
  building_name: string
  title: string | null
  action_type: string | null
  compliance_driver: string | null
  annual_co2_t: number
  annual_saving_eur: number
  net_capex_eur: number
  assumed_lifetime_years: number
  mac_eur_per_t: number
  is_profitable: boolean
  cumulative_co2_t: number
}

export type MaccTotals = {
  measure_count: number
  total_annual_co2_t: number
  profitable_annual_co2_t: number
  total_net_capex_eur: number
  profitable_net_capex_eur: number
  weighted_avg_mac_eur_per_t: number | null
}

export type MaccResponse = {
  measures: MaccMeasure[]
  totals: MaccTotals
  lifetime_assumptions: Record<string, number>
  note: string
}

type ServerResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number }

/** Fetch the portfolio MACC server-side. Optional building scope. */
export async function fetchMacc(
  accessToken: string,
  opts?: { building_id?: string; limit?: number }
): Promise<ServerResult<MaccResponse>> {
  const base = process.env.BACKEND_URL
  if (!base) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  const params = new URLSearchParams()
  if (opts?.building_id) params.set("building_id", opts.building_id)
  if (opts?.limit) params.set("limit", String(opts.limit))
  const qs = params.toString()

  try {
    const res = await fetch(`${base}/abatement/macc${qs ? `?${qs}` : ""}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) return { ok: false, error: `Backend ${res.status}`, status: res.status }
    return { ok: true, data: (await res.json()) as MaccResponse }
  } catch {
    return { ok: false, error: "Network error" }
  }
}
