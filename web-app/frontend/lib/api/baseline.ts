/**
 * Baseline KPIs (Tier-1, Postgres-side) — client fetch helper.
 *
 * For a building still pending a Fabric bridge (fabric_building_id NULL), the
 * backend computes indicative KPIs from the uploaded monthly consumption so the
 * dashboard + advisor light up before live data is connected. Addressed by the
 * Postgres UUID via the /api/buildings/{id}/kpis proxy (forwards the session
 * token). Type stays in lockstep with backend schemas/consumption.py::BaselineKPIs.
 */
export type BaselineKpis = {
  source: string
  has_data: boolean
  months_available: number
  window_months: number
  period_start: string | null
  period_end: string | null
  window: string
  is_annualized: boolean
  annual_energy_kwh: number | null
  eui_kwh_m2_yr: number | null
  annual_co2_kg: number | null
  annual_cost_eur: number | null
  kwh_30d: number | null
  co2_30d_kg: number | null
  cost_30d_eur: number | null
  cost_basis: string
  cost_rate_eur_kwh: number | null
  co2_factor_kg_kwh: number | null
  co2_factor_year: number | null
  co2_factor_confidence: string | null
  co2_factor_source: string | null
  floor_area_m2: number | null
}

export type BaselineResult =
  | { ok: true; data: BaselineKpis }
  | { ok: false; error: string }

export async function fetchBuildingBaselineKpis(
  buildingId: string
): Promise<BaselineResult> {
  try {
    const res = await fetch(
      `/api/buildings/${encodeURIComponent(buildingId)}/kpis`,
      { headers: { Accept: "application/json" } }
    )
    if (!res.ok) {
      const text = await res.text().catch(() => "")
      return {
        ok: false,
        error: `KPIs failed (${res.status}): ${text.slice(0, 160)}`,
      }
    }
    return { ok: true, data: (await res.json()) as BaselineKpis }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

/**
 * Server-side fetch of a building's baseline KPIs (direct to the backend with
 * the session token). Returns null on any failure (e.g. the building is not
 * manage-gated for this user) so the detail page degrades gracefully.
 */
export async function fetchBuildingBaselineKpisServer(
  accessToken: string,
  buildingId: string
): Promise<BaselineKpis | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/kpis`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    return (await res.json()) as BaselineKpis
  } catch {
    return null
  }
}
