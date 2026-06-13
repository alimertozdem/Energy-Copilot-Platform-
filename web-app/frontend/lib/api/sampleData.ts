/**
 * Sample/demo building visibility — fetch (server) + set (client via local proxy).
 *
 * GET is server-side (BACKEND_URL + session token). The toggle PUTs to the local
 * /api/sample-data proxy, which attaches the session token. Mirrors backend
 * GET/PUT /buildings/sample-data (per-user flag).
 */

export type SampleDataState = { enabled: boolean }

type ServerResult<T> = { ok: true; data: T } | { ok: false; error: string }
type Result<T> = { ok: true; data: T } | { ok: false; error: string }

export async function fetchSampleDataState(
  token: string
): Promise<ServerResult<SampleDataState>> {
  const base = process.env.BACKEND_URL
  if (!base) return { ok: false, error: "Server misconfigured" }
  try {
    const res = await fetch(`${base}/buildings/sample-data`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      cache: "no-store",
    })
    if (!res.ok) return { ok: false, error: `Backend ${res.status}` }
    return { ok: true, data: (await res.json()) as SampleDataState }
  } catch (err) {
    console.error("[fetchSampleDataState] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}

export async function setSampleData(enabled: boolean): Promise<Result<SampleDataState>> {
  try {
    const res = await fetch("/api/sample-data", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      return { ok: false, error: (body && (body.detail as string)) || `Failed (${res.status})` }
    }
    return { ok: true, data: (await res.json()) as SampleDataState }
  } catch {
    return { ok: false, error: "Network error" }
  }
}
