/**
 * Fetch + mutate helpers for backend /buildings endpoints.
 *
 * Read helpers (fetchBuildings/fetchBuilding) are server-only: call
 * getServerSession() in a server component, pass session.accessToken in.
 * createBuilding is browser-side and goes through the /api/buildings proxy
 * (which forwards the session token as Bearer) -- used by the onboarding wizard.
 *
 * Result shape: discriminated union { ok: true, data } | { ok: false, error }.
 * Types must stay in lockstep with backend app/schemas/buildings.py.
 */

// ----------------------------------------------------------------------------
// Types
// ----------------------------------------------------------------------------

export type ModuleKey = "meters" | "iot" | "battery" | "solar"

export type BuildingModule = {
  module_key: ModuleKey
  enabled: boolean
}

export type Building = {
  id: string // UUID
  fabric_building_id: string | null // e.g. "B001"; NULL until Fabric data is connected
  name: string
  city: string | null
  country_code: string | null
  building_type: string | null
  floor_area_m2: number | null
  pv_capacity_kwp: number | null
  construction_year: number | null
  epc_class: string | null
  heating_system: string | null
  cooling_system: string | null
  occupancy_pattern: string | null
  floors_above_ground: number | null
  typical_occupants: number | null
  timezone: string
  is_active: boolean
  organization_id: string // UUID
  is_sample_org: boolean
  modules: BuildingModule[]
}

export type BuildingListResponse = {
  buildings: Building[]
  total: number
}

export type BuildingModuleInput = {
  module_key: ModuleKey
  enabled: boolean
  notes?: string | null
}

export type BuildingCreateRequest = {
  name: string
  building_type?: string | null
  city?: string | null
  country_code?: string | null
  address?: string | null
  floor_area_m2?: number | null
  construction_year?: number | null
  epc_class?: string | null
  heating_system?: string | null
  cooling_system?: string | null
  occupancy_pattern?: string | null
  floors_above_ground?: number | null
  typical_occupants?: number | null
  timezone?: string
  pv_capacity_kwp?: number | null
  wall_u_value?: number | null
  roof_u_value?: number | null
  window_u_value?: number | null
  insulation_year?: number | null
  has_gas_heating?: boolean | null
  modules?: BuildingModuleInput[]
}

export type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

function logError(scope: string, status: number, body: string) {
  console.error(`[${scope}] Backend ${status}: ${body.slice(0, 200)}`)
}

/**
 * Number of the user's OWN (non-sample) buildings. Drives onboarding gating:
 * 0 own buildings -> user must complete /onboarding. Sample buildings
 * (visible to everyone) don't count as "onboarded".
 */
export function countOwnBuildings(buildings: Building[]): number {
  return buildings.filter((b) => !b.is_sample_org).length
}

// ----------------------------------------------------------------------------
// Read (server-only)
// ----------------------------------------------------------------------------

export async function fetchBuildings(
  accessToken: string
): Promise<FetchResult<BuildingListResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchBuildings] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }

  try {
    const res = await fetch(`${backendUrl}/buildings`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      logError("fetchBuildings", res.status, body)
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as BuildingListResponse
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchBuildings] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}

export async function fetchBuilding(
  accessToken: string,
  fabricBuildingId: string
): Promise<FetchResult<Building>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchBuilding] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }

  try {
    const res = await fetch(
      `${backendUrl}/buildings/${encodeURIComponent(fabricBuildingId)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: "application/json",
        },
        cache: "no-store",
      }
    )

    if (res.status === 404) {
      return { ok: false, error: "Not found" }
    }

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      logError("fetchBuilding", res.status, body)
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as Building
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchBuilding] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}

// ----------------------------------------------------------------------------
// Create (browser-side, via /api/buildings proxy) -- onboarding wizard
// ----------------------------------------------------------------------------

export async function createBuilding(
  body: BuildingCreateRequest
): Promise<FetchResult<Building>> {
  try {
    const res = await fetch("/api/buildings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail =
        data && typeof data === "object" && "detail" in data
          ? String((data as { detail: unknown }).detail)
          : `Request failed (${res.status})`
      return { ok: false, error: detail }
    }
    return { ok: true, data: data as Building }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

/**
 * True when the user has own (non-sample) buildings and ALL of them are still
 * data-pending (no fabric_building_id). Drives the DataPendingBanner so a
 * freshly-onboarded customer understands why reports/KPIs are empty.
 */
export function ownBuildingsAllPending(buildings: Building[]): boolean {
  const own = buildings.filter((b) => !b.is_sample_org)
  return own.length > 0 && own.every((b) => b.fabric_building_id === null)
}

/**
 * Fetch one building by its Postgres UUID (server-only) — for buildings still
 * pending a Fabric bridge, which have no fabric_building_id to look up by.
 */
export async function fetchBuildingByUuid(
  accessToken: string,
  buildingId: string
): Promise<FetchResult<Building>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchBuildingByUuid] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }
  try {
    const res = await fetch(
      `${backendUrl}/buildings/by-id/${encodeURIComponent(buildingId)}`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    if (res.status === 404) return { ok: false, error: "Not found" }
    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      logError("fetchBuildingByUuid", res.status, body)
      return { ok: false, error: `Backend ${res.status}` }
    }
    return { ok: true, data: (await res.json()) as Building }
  } catch (err) {
    console.error("[fetchBuildingByUuid] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}
