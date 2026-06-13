/**
 * ESRS E-1 narrative — fetch (server) + save (client via local proxy).
 *
 * GET is server-side (reads BACKEND_URL with the session token, like the other
 * fetchers). Save is a client mutation that PUTs to the local /api/esrs-narrative
 * proxy, which attaches the session token (the app's mutation pattern; no token in
 * client JS). Types mirror backend app/schemas/esrs_narrative.py.
 */

export type EsrsNarrativeItem = {
  datapoint_key: string
  content: string
  reporting_year: number | null
  updated_at: string | null
}

export type EsrsNarrativeResponse = { items: EsrsNarrativeItem[] }

type ServerResult<T> = { ok: true; data: T } | { ok: false; error: string }
type Result<T> = { ok: true; data: T } | { ok: false; error: string }

export async function fetchEsrsNarrativeServer(
  token: string
): Promise<ServerResult<EsrsNarrativeResponse>> {
  const base = process.env.BACKEND_URL
  if (!base) return { ok: false, error: "Server misconfigured" }
  try {
    const res = await fetch(`${base}/compliance/esrs/narrative`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) return { ok: false, error: `Backend ${res.status}` }
    return { ok: true, data: (await res.json()) as EsrsNarrativeResponse }
  } catch (err) {
    console.error("[fetchEsrsNarrativeServer] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

/** Client-side: save one disclosure via the local proxy (token added server-side). */
export async function saveEsrsNarrative(
  key: string,
  content: string,
  reportingYear?: number | null
): Promise<Result<EsrsNarrativeItem>> {
  try {
    const res = await fetch(`/api/esrs-narrative/${encodeURIComponent(key)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, reporting_year: reportingYear ?? null }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      return { ok: false, error: (body && (body.detail as string)) || `Failed (${res.status})` }
    }
    return { ok: true, data: (await res.json()) as EsrsNarrativeItem }
  } catch {
    return { ok: false, error: "Network error" }
  }
}

/** Turn the items list into a { datapoint_key: content } map (non-empty only). */
export function narrativeMap(items: EsrsNarrativeItem[]): Record<string, string> {
  const m: Record<string, string> = {}
  for (const it of items) {
    if (it.content && it.content.trim()) m[it.datapoint_key] = it.content
  }
  return m
}
