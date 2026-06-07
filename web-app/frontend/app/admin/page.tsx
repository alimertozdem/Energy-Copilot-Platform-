/**
 * /admin -- platform admin (founder-only). Server component, read-only.
 *
 * Gate:
 *   1. getServerSession -> require token, else redirect "/".
 *   2. fetchAdminStats: a 403 means the caller isn't is_platform_admin ->
 *      notFound() so the whole area is invisible (looks like it doesn't exist).
 *   3. Fetch orgs/users/buildings/audit in parallel; render AdminShell.
 *      Per-section failures degrade to an inline error banner in AdminShell.
 *
 * No browser proxy routes for reads -- this area fetches the backend directly
 * server-side with the session token. (Mutations use /api/admin/* proxies.)
 */
import { notFound, redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AdminShell } from "@/components/admin/AdminShell"
import {
  fetchAdminAudit,
  fetchAdminBuildings,
  fetchAdminOrganizations,
  fetchAdminStats,
  fetchAdminUsers,
} from "@/lib/api/admin"
import { fetchAdminBridgeRequestsServer } from "@/lib/api/bridge"
import { fetchAdminPilotRequestsServer } from "@/lib/api/pilot"
import { authOptions } from "@/lib/auth/options"

export default async function AdminPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const token = session.accessToken
  const statsResult = await fetchAdminStats(token)

  // Non-admins get 403 from the gate -> hide the area behind a 404.
  if (!statsResult.ok && statsResult.status === 403) {
    notFound()
  }

  const [orgsResult, usersResult, buildingsResult, auditResult, bridgeResult, pilotResult] =
    await Promise.all([
      fetchAdminOrganizations(token),
      fetchAdminUsers(token),
      fetchAdminBuildings(token),
      fetchAdminAudit(token),
      fetchAdminBridgeRequestsServer(token),
      fetchAdminPilotRequestsServer(token),
    ])

  return (
    <AdminShell
      stats={statsResult.ok ? statsResult.data : null}
      organizations={orgsResult.ok ? orgsResult.data.organizations : null}
      users={usersResult.ok ? usersResult.data.users : null}
      buildings={buildingsResult.ok ? buildingsResult.data.buildings : null}
      events={auditResult.ok ? auditResult.data.events : null}
      bridgeRequests={bridgeResult.ok ? bridgeResult.data.requests : null}
      pilotRequests={pilotResult.ok ? pilotResult.data.requests : null}
    />
  )
}
