/**
 * Edge-agent tokens (Tier-2) — browser client helpers.
 *
 * Building-scoped credentials an edge gateway uses to pull its node-map from the
 * backend /agent/config. Issued/listed/revoked through the manage-gated
 * /api/buildings/{uuid}/agent-tokens proxies. The plaintext token is returned
 * exactly ONCE (on issue) and never stored — surface it to the user immediately.
 * Types stay in lockstep with backend app/schemas/agent.py.
 */
export type AgentToken = {
  id: string
  building_id: string
  name: string
  token_prefix: string
  last_used_at: string | null
  revoked_at: string | null
  created_at: string
  is_active: boolean
}

export type IssuedToken = AgentToken & { token: string }

export type Result<T> = { ok: true; data: T } | { ok: false; error: string }

async function jreq<T>(url: string, method: "GET" | "POST" | "DELETE", body?: unknown): Promise<Result<T>> {
  try {
    const res = await fetch(url, {
      method,
      headers: { Accept: "application/json", ...(body !== undefined ? { "Content-Type": "application/json" } : {}) },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
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

const base = (b: string) => `/api/buildings/${encodeURIComponent(b)}/agent-tokens`

export function fetchAgentTokens(buildingId: string): Promise<Result<{ tokens: AgentToken[] }>> {
  return jreq<{ tokens: AgentToken[] }>(base(buildingId), "GET")
}

export function issueAgentToken(buildingId: string, name = "edge agent"): Promise<Result<IssuedToken>> {
  return jreq<IssuedToken>(base(buildingId), "POST", { name })
}

export function revokeAgentToken(buildingId: string, tokenId: string): Promise<Result<AgentToken>> {
  return jreq<AgentToken>(`${base(buildingId)}/${encodeURIComponent(tokenId)}`, "DELETE")
}
