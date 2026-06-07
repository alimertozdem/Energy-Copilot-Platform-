/**
 * Fetch helpers for the platform-admin endpoints (/admin/*).
 *
 * Server-only: call getServerSession() in a server component and pass
 * session.accessToken in. The /admin area is read-only and fully server
 * rendered, so there are no browser proxy routes -- the page fetches directly.
 *
 * The backend gates every endpoint on is_platform_admin and returns 403 for
 * non-admins. The error variant carries `status` so the page can map 403 -> a
 * 404 (the admin area stays invisible to normal users).
 *
 * Types mirror backend app/schemas/admin.py.
 */

export type FetchResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number }

export type PlatformStats = {
  organizations_total: number
  organizations_sample: number
  users_total: number
  users_demo: number
  buildings_total: number
  buildings_connected: number
  iot_enabled: number
  battery_enabled: number
}

export type AdminOrgRow = {
  id: string
  name: string
  slug: string
  subscription_tier: string
  subscription_status: string
  country_code: string | null
  is_sample: boolean
  member_count: number
  building_count: number
  created_at: string
}

export type AdminUserRow = {
  id: string
  email: string
  display_name: string | null
  is_active: boolean
  is_demo: boolean
  is_platform_admin: boolean
  providers: string[]
  org_count: number
  last_login_at: string | null
  created_at: string
}

export type AdminBuildingModule = { module_key: string; enabled: boolean }

export type AdminBuildingRow = {
  id: string
  fabric_building_id: string | null
  name: string
  city: string | null
  country_code: string | null
  building_type: string | null
  organization_id: string
  organization_name: string
  is_connected: boolean
  modules: AdminBuildingModule[]
  created_at: string
}

export type AdminOrganizationsResponse = {
  organizations: AdminOrgRow[]
  total: number
}
export type AdminUsersResponse = { users: AdminUserRow[]; total: number }
export type AdminBuildingsResponse = {
  buildings: AdminBuildingRow[]
  total: number
}

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

async function adminGet<T>(
  accessToken: string,
  path: string,
  scope: string
): Promise<FetchResult<T>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error(`[${scope}] BACKEND_URL not configured`)
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }
  try {
    const res = await fetch(`${backendUrl}${path}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      console.error(`[${scope}] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}`, status: res.status }
    }
    return { ok: true, data: (await res.json()) as T }
  } catch (err) {
    console.error(`[${scope}] Network/unknown error:`, err)
    return { ok: false, error: "Network error" }
  }
}

export function fetchAdminStats(
  accessToken: string
): Promise<FetchResult<PlatformStats>> {
  return adminGet<PlatformStats>(accessToken, "/admin/stats", "fetchAdminStats")
}

export function fetchAdminOrganizations(
  accessToken: string
): Promise<FetchResult<AdminOrganizationsResponse>> {
  return adminGet<AdminOrganizationsResponse>(
    accessToken,
    "/admin/organizations",
    "fetchAdminOrganizations"
  )
}

export function fetchAdminUsers(
  accessToken: string
): Promise<FetchResult<AdminUsersResponse>> {
  return adminGet<AdminUsersResponse>(
    accessToken,
    "/admin/users",
    "fetchAdminUsers"
  )
}

export function fetchAdminBuildings(
  accessToken: string
): Promise<FetchResult<AdminBuildingsResponse>> {
  return adminGet<AdminBuildingsResponse>(
    accessToken,
    "/admin/buildings",
    "fetchAdminBuildings"
  )
}

// --- Audit / activity (admin read) ---

export type AdminAuditRow = {
  id: string
  actor_email: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  details: Record<string, unknown> | null
  created_at: string
}

export type AdminAuditResponse = {
  events: AdminAuditRow[]
  total: number
}

export function fetchAdminAudit(
  accessToken: string
): Promise<FetchResult<AdminAuditResponse>> {
  return adminGet<AdminAuditResponse>(
    accessToken,
    "/admin/audit",
    "fetchAdminAudit"
  )
}
