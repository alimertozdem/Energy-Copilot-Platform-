/**
 * Installer-request API helpers (Execution Marketplace Phase 0).
 *
 * Customer create goes through /api/installer-requests (the button posts it
 * directly). Admin reads are server-side (founder queue); the status PATCH goes
 * through the /api/installer-requests/admin proxy. Types mirror backend
 * app/schemas/installer.py.
 */

export type AdminInstallerRequestRow = {
  id: string
  organization_id: string
  fabric_building_id: string
  building_name: string | null
  action_type: string | null
  measure_label: string | null
  note: string | null
  source: string | null
  status: string
  created_at: string
}

export type AdminInstallerRequestsResponse = {
  requests: AdminInstallerRequestRow[]
}

type Result<T> = { ok: true; data: T } | { ok: false; error: string }
type ServerResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number }

export async function fetchAdminInstallerRequestsServer(
  token: string
): Promise<ServerResult<AdminInstallerRequestsResponse>> {
  const base = process.env.BACKEND_URL
  if (!base) return { ok: false, error: "Server misconfigured" }
  try {
    const res = await fetch(`${base}/installer-requests/admin`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) {
      return { ok: false, error: `Backend ${res.status}`, status: res.status }
    }
    return { ok: true, data: (await res.json()) as AdminInstallerRequestsResponse }
  } catch (err) {
    console.error("[fetchAdminInstallerRequestsServer] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

export async function updateInstallerRequestStatus(
  requestId: string,
  status: "requested" | "contacted" | "quoted" | "closed"
): Promise<Result<unknown>> {
  try {
    const res = await fetch(
      `/api/installer-requests/admin/${encodeURIComponent(requestId)}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      }
    )
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      return {
        ok: false,
        error: (body && (body.detail as string)) || `Failed (${res.status})`,
      }
    }
    return { ok: true, data: await res.json().catch(() => ({})) }
  } catch {
    return { ok: false, error: "Network error" }
  }
}
