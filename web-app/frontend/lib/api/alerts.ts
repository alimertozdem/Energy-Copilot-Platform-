/**
 * /alerts API helpers — server-side read + browser-side acknowledge mutate.
 *
 * Read path:
 *   `fetchAlerts(accessToken, params?)` runs in a server component / route
 *   handler. Needs the user's JWT from getServerSession().accessToken.
 *
 * Write path (Day 31 overlay):
 *   `updateAlertAck(anomaly_id, body)` runs in the browser. It calls our own
 *   Next.js proxy /api/alerts/{anomaly_id} which forwards the session cookie to
 *   FastAPI as Bearer. This only writes the Postgres operational state
 *   (acknowledged / dismissed / new) — Fabric is_resolved stays pipeline-owned.
 *
 * Types stay in lockstep with backend app/schemas/alerts.py.
 */

// ----------------------------------------------------------------------------
// Types
// ----------------------------------------------------------------------------

export type AlertSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
export type AckStatus = "new" | "acknowledged" | "dismissed"
export type AlertResolution = "unresolved" | "resolved" | "all"

export type AlertItem = {
  anomaly_id: string | null
  fabric_building_id: string
  building_name: string

  anomaly_type: string | null
  severity: string | null // CRITICAL / HIGH / MEDIUM / LOW (uppercase)
  detected_at: string | null // ISO datetime
  is_resolved: boolean

  // Unit-neutral — an anomaly may be kWh, CO2 ppm, °C, or a ratio.
  metric_value: number | null
  threshold_value: number | null
  deviation_pct: number | null

  description: string | null
  recommended_action: string | null

  // Day 31 acknowledge overlay (Postgres).
  ack_status: AckStatus
  acknowledged_at: string | null
  ack_notes: string | null

  can_manage: boolean
}

export type AlertSeverityCounts = {
  critical: number
  high: number
  medium: number
  low: number
  total: number
  unresolved_total: number
  unresolved_critical: number
  unresolved_high: number
  unresolved_medium: number
  unresolved_low: number
  // Unhandled = unresolved AND not acknowledged/dismissed (triage queue + badge).
  unhandled_total: number
  unhandled_critical: number
  unhandled_high: number
  // Operational overlay tallies.
  acknowledged: number
  dismissed: number
}

export type AlertsResponse = {
  alerts: AlertItem[]
  severity_counts: AlertSeverityCounts
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

// ----------------------------------------------------------------------------
// Server-side: GET /alerts
// ----------------------------------------------------------------------------

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

export type FetchAlertsParams = {
  severity?: AlertSeverity | "all"
  building_id?: string
  unresolved_only?: boolean
  resolution?: AlertResolution
  limit?: number
}

export async function fetchAlerts(
  accessToken: string,
  params: FetchAlertsParams = {}
): Promise<FetchResult<AlertsResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchAlerts] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  const qs = alertsQuery(params)
  const url = `${backendUrl}/alerts${qs ? `?${qs}` : ""}`

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
        console.warn(`[fetchAlerts] Fabric data temporarily unavailable`)
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchAlerts] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    const data = (await res.json()) as AlertsResponse
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchAlerts] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

// ----------------------------------------------------------------------------
// Browser-side: PATCH /alerts/{anomaly_id} via Next.js proxy
// ----------------------------------------------------------------------------

export type AlertAckUpdateRequest = {
  ack_status: AckStatus
  building_id: string
  notes?: string | null
}

export type AlertAckUpdateResponse = {
  anomaly_id: string
  ack_status: AckStatus
  acknowledged_at: string | null
}

export async function updateAlertAck(
  anomaly_id: string,
  body: AlertAckUpdateRequest
): Promise<FetchResult<AlertAckUpdateResponse>> {
  try {
    const res = await fetch(`/api/alerts/${encodeURIComponent(anomaly_id)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => "")
      return { ok: false, error: `Update failed (${res.status}): ${text}` }
    }
    const data = (await res.json()) as AlertAckUpdateResponse
    return { ok: true, data }
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : String(err),
    }
  }
}

// ----------------------------------------------------------------------------
// Shared query builder + browser-side read (client-driven filter re-fetch)
// ----------------------------------------------------------------------------

/** Build the /alerts query string shared by the server + browser reads. */
function alertsQuery(params: FetchAlertsParams): string {
  const search = new URLSearchParams()
  if (params.severity) search.set("severity", params.severity)
  if (params.building_id) search.set("building_id", params.building_id)
  if (params.unresolved_only) search.set("unresolved_only", "true")
  if (params.resolution) search.set("resolution", params.resolution)
  if (params.limit != null) search.set("limit", String(params.limit))
  return search.toString()
}

/**
 * Browser-side GET /alerts through our Next.js proxy (/api/alerts). Used by
 * AlertsShell to re-fetch when the user changes the severity or resolution
 * filter, so the table + counts come from the server (accurate under the row
 * cap) instead of slicing a stale client-loaded set. The proxy injects the
 * session JWT, so no token is needed here.
 */
export async function fetchAlertsViaProxy(
  params: FetchAlertsParams = {}
): Promise<FetchResult<AlertsResponse>> {
  const qs = alertsQuery(params)
  try {
    const res = await fetch(`/api/alerts${qs ? `?${qs}` : ""}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        console.warn("[fetchAlertsViaProxy] Fabric data temporarily unavailable")
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchAlertsViaProxy] ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Request failed (${res.status})` }
    }
    const data = (await res.json()) as AlertsResponse
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchAlertsViaProxy] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}
