/**
 * Pilot lead capture — public submit + founder admin queue.
 *
 * Public submit goes through /api/pilot-requests (no auth). Admin reads go
 * server-side with the session token; admin resolve goes through the admin proxy.
 * Types mirror backend app/schemas/pilot.py.
 */

export type PilotFormInput = {
  name: string
  email: string
  organization?: string | null
  country_code?: string | null
  building_count?: number | null
  message?: string | null
  source?: string | null
}

export type AdminPilotRequestRow = {
  id: string
  name: string
  email: string
  organization: string | null
  country_code: string | null
  building_count: number | null
  message: string | null
  source: string | null
  status: string
  created_at: string
}

export type AdminPilotRequestsResponse = {
  requests: AdminPilotRequestRow[]
  total: number
}

type Result<T> = { ok: true; data: T } | { ok: false; error: string }
type ServerResult<T> = { ok: true; data: T } | { ok: false; error: string; status?: number }

/** Public: submit a pilot request (no auth). */
export async function submitPilotRequest(
  input: PilotFormInput
): Promise<Result<{ ok: boolean; id: string }>> {
  try {
    const res = await fetch("/api/pilot-requests", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(input),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail = (body && (body.detail as string)) || `Request failed (${res.status})`
      return { ok: false, error: detail }
    }
    return { ok: true, data: (await res.json()) as { ok: boolean; id: string } }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

/** Founder: list pilot leads server-side. */
export async function fetchAdminPilotRequestsServer(
  accessToken: string
): Promise<ServerResult<AdminPilotRequestsResponse>> {
  const base = process.env.BACKEND_URL
  if (!base) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }
  try {
    const res = await fetch(`${base}/admin/pilot-requests`, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) return { ok: false, error: `Backend ${res.status}`, status: res.status }
    return { ok: true, data: (await res.json()) as AdminPilotRequestsResponse }
  } catch {
    return { ok: false, error: "Network error" }
  }
}

/** Founder: move a pilot lead along the pipeline (through the admin proxy). */
export async function resolvePilotRequest(
  requestId: string,
  status: "new" | "contacted" | "qualified" | "closed"
): Promise<Result<{ ok: boolean }>> {
  try {
    const res = await fetch(
      `/api/admin/pilot-requests/${encodeURIComponent(requestId)}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ status }),
      }
    )
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      return { ok: false, error: (body && (body.detail as string)) || `Failed (${res.status})` }
    }
    return { ok: true, data: (await res.json()) as { ok: boolean } }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}
