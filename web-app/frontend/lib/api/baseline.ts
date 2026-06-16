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

/**
 * Provisional baseline ESTIMATE (no uploaded consumption yet). Ranges from an
 * archetype intensity × floor area; cost/CO₂ use the real tariff + grid factors.
 * Mirrors backend schemas/consumption.py::BaselineEstimate.
 */
export type BaselineEstimate = {
  basis: string
  building_type: string | null
  type_modeled: boolean
  country_code: string | null
  year: number
  eui_low: number
  eui_high: number
  annual_kwh_low: number
  annual_kwh_high: number
  annual_cost_eur_low: number
  annual_cost_eur_high: number
  annual_co2_kg_low: number
  annual_co2_kg_high: number
  tariff_eur_kwh: number
  grid_factor_kg_kwh: number
}

/** Server-side fetch; returns null when no estimate is available (real data
 *  exists, no floor area, or an unmodeled building type). */
export async function fetchBaselineEstimateServer(
  accessToken: string,
  buildingId: string
): Promise<BaselineEstimate | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/baseline-estimate`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    const data = (await res.json()) as { available: boolean; estimate: BaselineEstimate | null }
    return data?.available && data.estimate ? data.estimate : null
  } catch {
    return null
  }
}

/**
 * Measured heat-pump COP from telemetry (heat meter ÷ electricity). Mirrors
 * backend schemas/consumption.py::BuildingCopResponse. status:
 *   measured | device_reported | needs_heat_meter
 */
export type BuildingCop = {
  status: "measured" | "device_reported" | "needs_heat_meter"
  cop: number | null
  heat_kwh: number | null
  elec_kwh: number | null
  window_days: number
  basis: string | null
  simulated: boolean
}

export async function fetchBuildingCopServer(
  accessToken: string,
  buildingId: string
): Promise<BuildingCop | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/cop`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    return (await res.json()) as BuildingCop
  } catch {
    return null
  }
}

/**
 * Live telemetry monitoring (latest per sensor_type) from bronze_iot_readings.
 * Mirrors backend schemas/monitoring.py. App-native (no Fabric).
 */
export type MonitoringSensor = {
  sensor_type: string
  value: number | null
  unit: string | null
  zone: string | null
  received_at: string
  simulated: boolean
}

export type BuildingMonitoring = {
  sensors: MonitoringSensor[]
  reading_count: number
  window_hours: number
  last_reading_at: string | null
  basis: "live" | "simulated" | "none"
}

export async function fetchBuildingMonitoringServer(
  accessToken: string,
  buildingId: string
): Promise<BuildingMonitoring | null> {
  const backendUrl = process.env.BACKEND_URL
  if (!backendUrl || !accessToken) return null
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/monitoring`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    return (await res.json()) as BuildingMonitoring
  } catch {
    return null
  }
}
