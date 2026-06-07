/**
 * /settings API helpers -- server-side read + browser-side mutations.
 *
 * Read path:  fetchOrgSettings(accessToken) runs in the /settings Server
 *   Component with the user's JWT (from getServerSession().accessToken).
 * Write paths: the mutation helpers run in the browser and go through our
 *   Next.js proxies under /api/settings/*, which forward the session cookie
 *   to FastAPI as Bearer (keeps BACKEND_URL out of the client bundle).
 *
 * Types stay in lockstep with backend app/schemas/settings.py.
 */

export type OrgRole = "admin" | "manager" | "viewer"
export type InviteRole = "manager" | "viewer"

export type OrganizationProfile = {
  id: string
  name: string
  slug: string
  billing_email: string | null
  country_code: string | null
  subscription_tier: string
  subscription_status: string
  is_sample: boolean
}

export type OrgMemberItem = {
  user_id: string
  email: string
  display_name: string | null
  role: OrgRole
  is_pending: boolean
  joined_at: string | null // ISO datetime
  is_self: boolean
}

export type PendingInviteItem = {
  id: string
  email: string
  role: InviteRole
  status: string
  token: string
  invited_by_email: string | null
  expires_at: string // ISO datetime
  created_at: string // ISO datetime
}

export type OrgSettingsResponse = {
  organization: OrganizationProfile
  members: OrgMemberItem[]
  pending_invites: PendingInviteItem[]
  current_user_role: OrgRole
  can_manage: boolean
}

export type OrgUpdateRequest = {
  name?: string | null
  billing_email?: string | null
  country_code?: string | null
}

export type MemberInviteRequest = {
  email: string
  role: InviteRole
}

export type MemberInviteResponse = {
  invite: PendingInviteItem
  invite_path: string
}

export type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

// ---------------------------------------------------------------------------
// Server-side read
// ---------------------------------------------------------------------------

export async function fetchOrgSettings(
  accessToken: string
): Promise<FetchResult<OrgSettingsResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchOrgSettings] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  try {
    const res = await fetch(`${backendUrl}/settings/organization`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      console.error(
        `[fetchOrgSettings] Backend ${res.status}: ${body.slice(0, 200)}`
      )
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as OrgSettingsResponse }
  } catch (err) {
    console.error("[fetchOrgSettings] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

// ---------------------------------------------------------------------------
// Browser-side mutations (via Next.js proxies)
// ---------------------------------------------------------------------------

async function mutate<T>(
  url: string,
  method: "PATCH" | "POST" | "DELETE",
  body?: unknown
): Promise<FetchResult<T>> {
  try {
    const res = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail =
        data && typeof data === "object" && "detail" in data
          ? String((data as { detail: unknown }).detail)
          : `Request failed (${res.status})`
      return { ok: false, error: detail }
    }
    return { ok: true, data: data as T }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

export function updateOrganization(
  body: OrgUpdateRequest
): Promise<FetchResult<OrganizationProfile>> {
  return mutate("/api/settings/organization", "PATCH", body)
}

export function inviteMember(
  body: MemberInviteRequest
): Promise<FetchResult<MemberInviteResponse>> {
  return mutate("/api/settings/organization/members/invite", "POST", body)
}

export function changeMemberRole(
  userId: string,
  role: OrgRole
): Promise<FetchResult<OrgMemberItem>> {
  return mutate(
    `/api/settings/organization/members/${encodeURIComponent(userId)}`,
    "PATCH",
    { role }
  )
}

export function removeMember(
  userId: string
): Promise<FetchResult<{ ok: boolean }>> {
  return mutate(
    `/api/settings/organization/members/${encodeURIComponent(userId)}`,
    "DELETE"
  )
}

export function revokeInvite(
  inviteId: string
): Promise<FetchResult<{ ok: boolean }>> {
  return mutate(
    `/api/settings/organization/invites/${encodeURIComponent(inviteId)}`,
    "DELETE"
  )
}

// ---------------------------------------------------------------------------
// Invitation accept flow (/invite/[token])
// ---------------------------------------------------------------------------

export type InvitationPreview = {
  organization_name: string
  role: InviteRole
  email: string
  status: string
  is_valid: boolean
  expires_at: string // ISO datetime
}

export type InvitationAcceptResponse = {
  ok: boolean
  organization_id: string
  organization_slug: string
  role: OrgRole
}

/**
 * Public preview of an invitation -- runs server-side in the /invite landing
 * page. No auth: the visitor may not be signed in yet.
 */
export async function fetchInvitePreview(
  token: string
): Promise<FetchResult<InvitationPreview>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchInvitePreview] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  try {
    const res = await fetch(
      `${backendUrl}/settings/invitations/${encodeURIComponent(token)}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) {
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as InvitationPreview }
  } catch (err) {
    console.error("[fetchInvitePreview] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

/**
 * Accept an invitation. Browser-side; requires the user to be signed in.
 * Goes through the Next.js proxy which forwards the session token as Bearer.
 */
export function acceptInvite(
  token: string
): Promise<FetchResult<InvitationAcceptResponse>> {
  return mutate(
    `/api/settings/invitations/${encodeURIComponent(token)}/accept`,
    "POST"
  )
}

// ---------------------------------------------------------------------------
// Activity feed (org audit log) -- server-side read, admin-only on the backend
// ---------------------------------------------------------------------------

export type SettingsActivityRow = {
  id: string
  actor_email: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  details: Record<string, unknown> | null
  created_at: string // ISO datetime
}

export type SettingsActivityResponse = {
  events: SettingsActivityRow[]
  total: number
}

export async function fetchSettingsActivity(
  accessToken: string
): Promise<FetchResult<SettingsActivityResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchSettingsActivity] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  try {
    const res = await fetch(`${backendUrl}/settings/activity`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })
    if (!res.ok) {
      // 403 for non-admins is expected -- the caller just hides the section.
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as SettingsActivityResponse }
  } catch (err) {
    console.error("[fetchSettingsActivity] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}
