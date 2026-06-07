/**
 * Browser-side partner-layer mutations. Each posts to a /api/partners/* proxy route,
 * which attaches the session token and forwards to the FastAPI endpoint. On success the
 * caller should call router.refresh() to re-read the server-rendered table (no optimistic
 * local state, matching adminMutations).
 */
export type MutationResult = { ok: true } | { ok: false; error: string }

async function postJson(url: string, body?: unknown): Promise<MutationResult> {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      const detail =
        data && typeof data === "object" && "detail" in data
          ? String((data as { detail: unknown }).detail)
          : `Request failed (${res.status})`
      return { ok: false, error: detail }
    }
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

export function createPartnerLink(body: {
  client_org_id: string
  scope: string
  commission_model?: Record<string, unknown> | null
}): Promise<MutationResult> {
  return postJson("/api/partners/links", body)
}

export function acceptPartnerLink(linkId: string): Promise<MutationResult> {
  return postJson(`/api/partners/links/${encodeURIComponent(linkId)}/accept`)
}

export function revokePartnerLink(linkId: string): Promise<MutationResult> {
  return postJson(`/api/partners/links/${encodeURIComponent(linkId)}/revoke`)
}
