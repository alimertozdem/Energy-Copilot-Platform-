/**
 * Self-serve Fabric bridging (Access Layer 3) — client + server fetch helpers.
 *
 * Customer surface: read a building's bridge-readiness (which report pages its
 * data earns) and file/cancel a bridge request. Founder surface: list + resolve
 * the cross-org request queue. Types mirror backend app/schemas/bridge.py.
 *
 * Server fetches go straight to FastAPI with the session token (used by server
 * components); client actions go through the /api/* proxies that attach the token.
 */

export type BridgeStatus = "ready" | "partial" | "locked"

export type BridgeReadinessPage = {
  key: string
  label: string
  status: BridgeStatus
  reason: string
}

export type BridgeRequestState = {
  id: string
  status: string // pending | approved | rejected | fulfilled | cancelled
  target_tier: string
  note: string | null
  created_at: string
  resolved_at: string | null
  resolution_note: string | null
}

export type BridgeReadiness = {
  overall_tier: string // empty | baseline | monitoring | full
  can_request: boolean
  ready_pages: number
  partial_pages: number
  total_pages: number
  consumption_months: number
  pages: BridgeReadinessPage[]
  summary: string
  blocking: string[]
  request: BridgeRequestState | null
  is_bridged: boolean
}

export type AdminBridgeRequestRow = {
  id: string
  building_id: string
  building_name: string
  fabric_building_id: string | null
  organization_id: string
  organization_name: string
  requested_by_email: string | null
  status: string
  target_tier: string
  note: string | null
  readiness: BridgeReadiness | null
  created_at: string
  resolved_at: string | null
  resolution_note: string | null
}

export type AdminBridgeRequestsResponse = {
  requests: AdminBridgeRequestRow[]
  total: number
}

type Result<T> = { ok: true; data: T } | { ok: false; error: string }
type ServerResult<T> = { ok: true; data: T } | { ok: false; error: string; status?: number }

// --- Server-side (server components) ---

/** Read a building's bridge-readiness server-side. null on any failure (graceful). */
export async function fetchBridgeReadinessServer(
  accessToken: string,
  buildingId: string
): Promise<BridgeReadiness | null> {
  const base = process.env.BACKEND_URL
  if (!base || !accessToken) return null
  try {
    const res = await fetch(
      `${base}/buildings/${encodeURIComponent(buildingId)}/bridge-readiness`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) return null
    return (await res.json()) as BridgeReadiness
  } catch {
    return null
  }
}

/** Founder: the cross-org bridge-request queue, server-side. */
export async function fetchAdminBridgeRequestsServer(
  accessToken: string
): Promise<ServerResult<AdminBridgeRequestsResponse>> {
  const base = process.env.BACKEND_URL
  if (!base) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }
  try {
    const res = await fetch(`${base}/admin/bridge-requests`, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) return { ok: false, error: `Backend ${res.status}`, status: res.status }
    return { ok: true, data: (await res.json()) as AdminBridgeRequestsResponse }
  } catch {
    return { ok: false, error: "Network error" }
  }
}

// --- Client-side (through /api proxies) ---

/** Re-read readiness client-side after a request/cancel. */
export async function fetchBridgeReadiness(buildingId: string): Promise<Result<BridgeReadiness>> {
  return clientJson<BridgeReadiness>(
    `/api/buildings/${encodeURIComponent(buildingId)}/bridge-readiness`,
    { method: "GET" }
  )
}

/** File a bridge request for a building. */
export async function requestBridge(
  buildingId: string,
  note?: string
): Promise<Result<BridgeRequestState>> {
  return clientJson<BridgeRequestState>(
    `/api/buildings/${encodeURIComponent(buildingId)}/bridge-request`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: note || null, target_tier: "full" }),
    }
  )
}

/** Cancel a building's pending bridge request. */
export async function cancelBridge(buildingId: string): Promise<Result<BridgeRequestState>> {
  return clientJson<BridgeRequestState>(
    `/api/buildings/${encodeURIComponent(buildingId)}/bridge-request`,
    { method: "DELETE" }
  )
}

/** Founder: approve / reject / fulfil a request (through the admin proxy). */
export async function resolveBridgeRequest(
  requestId: string,
  status: "approved" | "rejected" | "fulfilled",
  resolutionNote?: string,
  fabricBuildingId?: string
): Promise<Result<{ ok: boolean }>> {
  return clientJson<{ ok: boolean }>(
    `/api/admin/bridge-requests/${encodeURIComponent(requestId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status,
        resolution_note: resolutionNote || null,
        fabric_building_id: fabricBuildingId || null,
      }),
    }
  )
}

// --- Phase 3.2: automated bridge ("armed one-click") ---

export type AutomatedBridgeStep = {
  step: string
  status: string
  message: string | null
}

export type AutomatedBridgeResult = {
  ok: boolean
  dry_run: boolean
  fabric_building_id: string | null
  failed_step: string | null
  error: string | null
  steps: AutomatedBridgeStep[]
  automation_enabled: boolean
}

/**
 * Founder: run (or dry-run) the automated Fabric bridge for a request.
 * dryRun=true plans the steps without calling Fabric (€0, no capacity needed).
 */
export async function automateBridgeRequest(
  requestId: string,
  opts?: { dryRun?: boolean; fabricBuildingId?: string }
): Promise<Result<AutomatedBridgeResult>> {
  return clientJson<AutomatedBridgeResult>(
    `/api/admin/bridge-requests/${encodeURIComponent(requestId)}/automate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dry_run: opts?.dryRun ?? false,
        fabric_building_id: opts?.fabricBuildingId || null,
      }),
    }
  )
}

async function clientJson<T>(url: string, init: RequestInit): Promise<Result<T>> {
  try {
    const res = await fetch(url, { ...init, headers: { Accept: "application/json", ...(init.headers || {}) } })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail = (body && (body.detail as string)) || `Request failed (${res.status})`
      return { ok: false, error: detail }
    }
    return { ok: true, data: (await res.json()) as T }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}
