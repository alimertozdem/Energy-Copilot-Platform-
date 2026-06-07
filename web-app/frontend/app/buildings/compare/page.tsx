/**
 * /buildings/compare?ids=B001,B003,B005 -- multi-building comparison page.
 *
 * Server component. Flow:
 *   1. Parse `ids` query param (comma-separated fabric_building_ids).
 *   2. Guard against missing auth or empty / malformed ids.
 *   3. fetchBuildings() then filter to the requested ids (preserves order).
 *   4. Hand off to CompareReportShell for rendering.
 *
 * Authorization is enforced by /buildings (RLS + sample org rule). If a user
 * smuggles an id they shouldn't see into the URL, the filter drops it
 * silently — they never get data they're not entitled to.
 */
import { notFound, redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { fetchBuildings } from "@/lib/api/buildings"
import { authOptions } from "@/lib/auth/options"

import { CompareReportShell } from "./CompareReportShell"

type PageProps = {
  searchParams: Promise<{ ids?: string }>
}

const MAX_COMPARE = 5

export default async function ComparePage({ searchParams }: PageProps) {
  const { ids: rawIds } = await searchParams

  // Parse + sanitize: trim, drop empties, dedupe, cap at MAX_COMPARE.
  const requestedIds = Array.from(
    new Set(
      (rawIds ?? "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
    )
  ).slice(0, MAX_COMPARE)

  // Need at least 2 to make a comparison meaningful.
  if (requestedIds.length < 2) {
    redirect("/buildings")
  }

  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchBuildings(session.accessToken)
  if (!result.ok) {
    notFound()
  }

  // Filter to requested ids, preserving the order in the URL (so the user's
  // selection order is reflected in the report's filter / subtitle).
  const byId = new Map(
    result.data.buildings.map((b) => [b.fabric_building_id ?? "", b])
  )
  const buildings = requestedIds
    .map((id) => byId.get(id))
    .filter((b): b is NonNullable<typeof b> => Boolean(b))

  if (buildings.length < 2) {
    // The user couldn't see at least 2 of the requested ids -> bounce.
    redirect("/buildings")
  }

  return <CompareReportShell buildings={buildings} />
}
