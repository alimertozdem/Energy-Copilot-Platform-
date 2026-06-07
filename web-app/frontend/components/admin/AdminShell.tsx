/**
 * AdminShell -- top-level layout for the platform-admin page.
 *
 * Server component. Wraps AppChrome (client) and lays out the stat cards +
 * three cross-org tables + the recent-activity log. Each data slice is
 * nullable: when a backend section fails it renders an inline error banner
 * instead of taking down the page.
 *
 * The tables embed their own interactive controls, but the shell itself is a
 * server component.
 */
import { AppChrome } from "@/components/AppChrome"
import { ActivityTable } from "@/components/admin/ActivityTable"
import { BridgeRequestsTable } from "@/components/admin/BridgeRequestsTable"
import { PilotRequestsTable } from "@/components/admin/PilotRequestsTable"
import { BuildingsTable } from "@/components/admin/BuildingsTable"
import { OrganizationsTable } from "@/components/admin/OrganizationsTable"
import { StatsCards } from "@/components/admin/StatsCards"
import { UsersTable } from "@/components/admin/UsersTable"
import type {
  AdminAuditRow,
  AdminBuildingRow,
  AdminOrgRow,
  AdminUserRow,
  PlatformStats,
} from "@/lib/api/admin"
import type { AdminBridgeRequestRow } from "@/lib/api/bridge"
import type { AdminPilotRequestRow } from "@/lib/api/pilot"

// Violet -- the same "special" hue Copilot uses, marking the admin surface as
// distinct from the emerald customer-facing pages.
const ADMIN_ACCENT = "#7B5BD6"

type AdminShellProps = {
  stats: PlatformStats | null
  organizations: AdminOrgRow[] | null
  users: AdminUserRow[] | null
  buildings: AdminBuildingRow[] | null
  events: AdminAuditRow[] | null
  bridgeRequests: AdminBridgeRequestRow[] | null
  pilotRequests: AdminPilotRequestRow[] | null
}

function SectionError({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-accent-red/30 bg-accent-red/5 p-4 text-text-primary">
      <div className="text-sm font-medium">Failed to load {label}</div>
      <div className="text-xs text-text-muted">
        The backend returned an error for this section.
      </div>
    </div>
  )
}

export function AdminShell({
  stats,
  organizations,
  users,
  buildings,
  events,
  bridgeRequests,
  pilotRequests,
}: AdminShellProps) {
  return (
    <AppChrome
      breadcrumb={[{ label: "Admin" }]}
      pageTitle="Platform Admin"
      subtitle="Founder-only · cross-organization view"
      accentColor={ADMIN_ACCENT}
    >
      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto space-y-8">
        {stats ? <StatsCards stats={stats} /> : <SectionError label="stats" />}

        {bridgeRequests ? (
          <BridgeRequestsTable requests={bridgeRequests} />
        ) : (
          <SectionError label="bridge requests" />
        )}

        <PilotRequestsTable requests={pilotRequests} />

        {organizations ? (
          <OrganizationsTable organizations={organizations} />
        ) : (
          <SectionError label="organizations" />
        )}

        {users ? <UsersTable users={users} /> : <SectionError label="users" />}

        {buildings ? (
          <BuildingsTable buildings={buildings} />
        ) : (
          <SectionError label="buildings" />
        )}

        {events ? (
          <ActivityTable events={events} />
        ) : (
          <SectionError label="activity" />
        )}
      </div>
    </AppChrome>
  )
}
