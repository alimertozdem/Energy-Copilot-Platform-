/**
 * /actions API helpers — server-side fetch + browser-side mutate.
 *
 * Read path:
 *   `fetchActions(accessToken, params?)` runs inside a server component or
 *   route handler. It needs the user's JWT, obtained from
 *   getServerSession().accessToken.
 *
 * Write path:
 *   `updateActionStatus(action_id, body)` runs in the browser (client
 *   components). It calls our own Next.js proxy `/api/actions/{id}` which
 *   forwards the user's session cookie to FastAPI as a Bearer token.
 *   This keeps BACKEND_URL out of the client bundle.
 */

// ----------------------------------------------------------------------------
// Types — stay in lockstep with backend app/schemas/actions.py
// ----------------------------------------------------------------------------

export type ActionStatus =
  | "open"
  | "in_progress"
  | "completed"
  | "dismissed"
  | "not_applicable"

export type ActionItem = {
  action_id: string // synthetic "{building_id}|{rank}"
  fabric_building_id: string
  building_name: string
  rank: number | null

  action_type: string | null
  title: string | null
  description: string | null

  priority_label: string | null
  priority_score: number | null
  compliance_driver: string | null

  annual_saving_eur: number | null
  co2_saving_kg: number | null
  capex_eur: number | null
  net_capex_eur: number | null
  grant_eur: number | null
  payback_years: number | null
  npv_eur: number | null

  status: ActionStatus
  status_updated_at: string | null // ISO datetime
  completed_at: string | null
  notes: string | null

  can_manage: boolean
}

export type ActionStatusCounts = {
  open: number
  in_progress: number
  completed: number
  dismissed: number
  not_applicable: number
  total: number
}

export type ActionsResponse = {
  actions: ActionItem[]
  status_counts: ActionStatusCounts
}

export type ActionStatusUpdateRequest = {
  status: ActionStatus
  notes?: string | null
}

export type ActionStatusUpdateResponse = {
  action_id: string
  status: ActionStatus
  status_updated_at: string
  completed_at: string | null
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

// ----------------------------------------------------------------------------
// Server-side: GET /actions
// ----------------------------------------------------------------------------

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

export type FetchActionsParams = {
  status?: ActionStatus | "all"
  building_id?: string
  category?: string
  limit?: number
}

export async function fetchActions(
  accessToken: string,
  params: FetchActionsParams = {}
): Promise<FetchResult<ActionsResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchActions] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  const search = new URLSearchParams()
  if (params.status) search.set("status", params.status)
  if (params.building_id) search.set("building_id", params.building_id)
  if (params.category) search.set("category", params.category)
  if (params.limit != null) search.set("limit", String(params.limit))

  const qs = search.toString()
  const url = `${backendUrl}/actions${qs ? `?${qs}` : ""}`

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
        console.warn(`[fetchActions] Fabric data temporarily unavailable`)
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchActions] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    const data = (await res.json()) as ActionsResponse
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchActions] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

// ----------------------------------------------------------------------------
// Browser-side: PATCH /actions/{id} via Next.js proxy
// ----------------------------------------------------------------------------

/**
 * Update an action's status from the client side.
 *
 * Goes through /api/actions/{action_id} on Next.js, which forwards the
 * session cookie to FastAPI as Bearer. Use from a client component
 * (e.g. the inline status dropdown in the actions table).
 */
export async function updateActionStatus(
  action_id: string,
  body: ActionStatusUpdateRequest
): Promise<FetchResult<ActionStatusUpdateResponse>> {
  try {
    // action_id contains '|' which must be URL-encoded.
    const res = await fetch(
      `/api/actions/${encodeURIComponent(action_id)}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    )
    if (!res.ok) {
      const text = await res.text().catch(() => "")
      return { ok: false, error: `Update failed (${res.status}): ${text}` }
    }
    const data = (await res.json()) as ActionStatusUpdateResponse
    return { ok: true, data }
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : String(err),
    }
  }
}
