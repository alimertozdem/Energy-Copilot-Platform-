/**
 * Browser-side admin mutation helpers. Called from the interactive admin tables
 * (client components). Each posts to a /api/admin/* proxy route, which attaches
 * the session token and forwards to the FastAPI PATCH endpoint.
 *
 * On success the caller should call router.refresh() to re-read the server
 * tables (no optimistic local state in V1).
 */
export type MutationResult = { ok: true } | { ok: false; error: string }

async function patchJson(url: string, body: unknown): Promise<MutationResult> {
  try {
    const res = await fetch(url, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
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

export function updateOrgSubscription(
  orgId: string,
  body: { subscription_tier?: string; subscription_status?: string }
): Promise<MutationResult> {
  return patchJson(`/api/admin/organizations/${encodeURIComponent(orgId)}`, body)
}

export function updateBuildingModule(
  buildingId: string,
  body: { module_key: string; enabled: boolean }
): Promise<MutationResult> {
  return patchJson(
    `/api/admin/buildings/${encodeURIComponent(buildingId)}/modules`,
    body
  )
}

export function updateBuildingFabricId(
  buildingId: string,
  body: { fabric_building_id: string | null }
): Promise<MutationResult> {
  return patchJson(`/api/admin/buildings/${encodeURIComponent(buildingId)}`, body)
}
