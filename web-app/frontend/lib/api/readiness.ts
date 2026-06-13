/**
 * Server-only fetch for a building's Data Score + report readiness.
 * Reads GET /buildings/{building_id}/readiness (UUID-addressed; works pre-bridge).
 * Types mirror backend app/schemas/readiness.py.
 */

export type ReadinessSignal = {
  key: string
  label: string
  points: number
  present: boolean
  applicable: boolean
  help: string
}

export type ReadinessReport = {
  key: string
  label: string
  status: "ready" | "partial" | "locked" | "not_applicable"
  missing: string[]
  note: string
}

export type ReadinessAction = {
  key: string
  label: string
  points: number
  help: string
  unlocks: string[]
}

export type BuildingReadiness = {
  data_score: number
  points_earned: number
  points_possible: number
  signals: ReadinessSignal[]
  reports: ReadinessReport[]
  next_actions: ReadinessAction[]
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

export async function fetchBuildingReadiness(
  accessToken: string,
  buildingId: string
): Promise<FetchResult<BuildingReadiness>> {
  const backendUrl = process.env.BACKEND_URL || null
  if (!backendUrl) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }
  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(buildingId)}/readiness`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) {
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as BuildingReadiness }
  } catch (err) {
    console.error("[fetchBuildingReadiness] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}
