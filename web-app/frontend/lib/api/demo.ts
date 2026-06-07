/**
 * Server-only fetch helpers for the public /demo endpoints.
 *
 * Demo endpoints take NO authentication — anyone (incognito browser, bot,
 * web archive crawler) can hit them. We still go through the Next.js server
 * for the initial /demo page render so BACKEND_URL stays a server-only env
 * variable.
 *
 * For the embed token (which happens at runtime in the browser),
 * PowerBIReport calls the backend directly via the public CORS origin —
 * proxying that round-trip through Next.js adds latency with no security
 * benefit (token already short-lived + RLS-restricted).
 */

// ----------------------------------------------------------------------------
// Types -- stay in lockstep with backend app/schemas/demo.py
// ----------------------------------------------------------------------------

export type DemoBuilding = {
  fabric_building_id: string
  name: string
  city: string
  country: string
  building_type: string
  floor_area_m2: number
  epc_class: string | null
  kwh_30d: number
}

export type DemoBuildingsResponse = {
  buildings: DemoBuilding[]
}

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

// ----------------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------------

function getBackendUrl(): string {
  // Defaults to the local uvicorn instance; production overrides via env.
  return process.env.BACKEND_URL || "http://127.0.0.1:8000"
}

/**
 * Server-side fetch of the public demo portfolio.
 *
 * Called from app/demo/page.tsx during initial render. No auth header.
 * cache: "no-store" so the demo always shows fresh numbers — Fabric data
 * is slowly-changing but a stale cache during a pitch demo would look bad.
 */
export async function fetchDemoBuildings(): Promise<FetchResult<DemoBuildingsResponse>> {
  const url = `${getBackendUrl()}/demo/buildings`
  try {
    const res = await fetch(url, {
      method: "GET",
      cache: "no-store",
    })
    if (!res.ok) {
      const text = await res.text().catch(() => "")
      return {
        ok: false,
        error: `Backend ${res.status}: ${text || res.statusText}`,
      }
    }
    const data = (await res.json()) as DemoBuildingsResponse
    return { ok: true, data }
  } catch (e) {
    return {
      ok: false,
      error: e instanceof Error ? e.message : String(e),
    }
  }
}
