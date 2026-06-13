/**
 * Server-only fetch for the per-building GEG conformity report.
 *
 * Reads GET /compliance/geg/{id} (B2B JWT). GEG (Gebäudeenergiegesetz) screening —
 * §71 renewable heating + §48/Anlage 7 envelope U-values — for one visible building.
 * Types mirror backend app/schemas/geg_conformity.py.
 */

export type GegComponent = {
  component: string
  current_u: number | null
  limit_u: number
  compliant: boolean | null
  note: string | null
}

export type GegConformity = {
  fabric_building_id: string
  building_name: string
  building_type: string
  country_code: string | null
  applies: boolean
  has_data: boolean
  geg_score: number | null
  geg_status: string | null
  heating_compliant: boolean | null
  heating_note: string
  components: GegComponent[]
  components_compliant: number
  components_total: number
  note: string
  data_source: string
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

export async function fetchGegConformity(
  accessToken: string,
  fabricBuildingId: string
): Promise<FetchResult<GegConformity>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) return { ok: false, error: "Server misconfigured" }
  if (!accessToken) return { ok: false, error: "Missing access token" }

  try {
    const res = await fetch(
      `${backendUrl}/compliance/geg/${encodeURIComponent(fabricBuildingId)}`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      if (res.status === 503 && body.includes("fabric_unavailable")) {
        return { ok: false, error: "fabric_unavailable" }
      }
      console.error(`[fetchGegConformity] Backend ${res.status}: ${body.slice(0, 200)}`)
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as GegConformity }
  } catch (err) {
    console.error("[fetchGegConformity] Network error:", err)
    return { ok: false, error: "Network error" }
  }
}
