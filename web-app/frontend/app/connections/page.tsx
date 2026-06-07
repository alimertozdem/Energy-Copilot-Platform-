/**
 * /connections — Devices & Connections (Tier-2/3 wiring).
 *
 * Server component. Auth-guarded. Loads the user's buildings and hands them to
 * the client, which owns a building selector + device/point CRUD. Top-level
 * (not building-scoped) + UUID-addressed, so it's reachable for buildings still
 * pending a Fabric bridge — exactly the ones being wired up for live data.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { fetchBuildings } from "@/lib/api/buildings"
import { authOptions } from "@/lib/auth/options"

import { ConnectionsClient } from "./ConnectionsClient"

export const metadata = { title: "Devices & Connections" }

export default async function ConnectionsPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }
  const result = await fetchBuildings(session.accessToken)
  const buildings = result.ok ? result.data.buildings : []

  return (
    <AppChrome
      breadcrumb={[{ label: "Connections" }]}
      pageTitle="Devices & Connections"
      subtitle="Wire up live data sources"
    >
      <div className="relative z-10 px-6 py-8 max-w-5xl mx-auto">
        <ConnectionsClient buildings={buildings} />
      </div>
    </AppChrome>
  )
}
