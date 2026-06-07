/**
 * Server-side fetch helpers for the partner (consultant) endpoints (/partners/*).
 *
 * Mirrors lib/api/admin.ts: call getServerSession() in a server component and pass
 * session.accessToken in. Mutations live in lib/api/partnerMutations.ts (browser-side,
 * via the /api/partners/* proxy routes). Types mirror backend app/schemas/partner.py.
 */
export type FetchResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status?: number }

export type PartnerLinkRow = {
  id: string
  partner_org_id: string
  client_org_id: string
  // The OTHER side's org name (client name in a partner view; partner name in a client view).
  counterparty_org_name: string
  relationship_status: string // pending | active | suspended | revoked
  scope: string // read_only | full_manage
  client_consent_at: string | null
  granted_at: string | null
  revoked_at: string | null
  created_at: string
}

export type PartnerLinksResponse = { links: PartnerLinkRow[]; total: number }

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

export async function fetchPartnerLinks(
  accessToken: string
): Promise<FetchResult<PartnerLinksResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchPartnerLinks] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }
  try {
    const res = await fetch(`${backendUrl}/partners/links`, {
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
        `[fetchPartnerLinks] Backend ${res.status}: ${body.slice(0, 200)}`
      )
      return { ok: false, error: `Backend ${res.status}`, status: res.status }
    }
    return { ok: true, data: (await res.json()) as PartnerLinksResponse }
  } catch (err) {
    console.error("[fetchPartnerLinks] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}

export type PartnerClientRow = {
  organization_id: string
  name: string
  slug: string
  scope: string
}

export type PartnerClientsResponse = { clients: PartnerClientRow[]; total: number }

export async function fetchPartnerClients(
  accessToken: string
): Promise<FetchResult<PartnerClientsResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchPartnerClients] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }
  try {
    const res = await fetch(`${backendUrl}/partners/clients`, {
      method: "GET",
      headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      console.error(`[fetchPartnerClients] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}`, status: res.status }
    }
    return { ok: true, data: (await res.json()) as PartnerClientsResponse }
  } catch (err) {
    console.error("[fetchPartnerClients] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}
