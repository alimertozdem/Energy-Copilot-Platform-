/**
 * /dashboard — persona-aware home cockpit (design audit P0-2 + P1-4, 2026-06-15).
 *
 * Post-login landing: a "what needs you today + where to act" home that reuses the
 * portfolio/alerts/actions fetchers and adapts to real signals (data-pending,
 * partner clients). A visible data-basis strip surfaces the honesty layer (P1-4).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { CitySkylineMotif } from "@/components/CitySkylineMotif"
import { DataBasisNote } from "@/components/DataBasisNote"
import { DataPendingBanner } from "@/components/DataPendingBanner"
import { PageIntro } from "@/components/PageIntro"
import { SustainabilityMotif } from "@/components/SustainabilityMotif"
import { HomeCockpit } from "@/components/dashboard/HomeCockpit"
import { fetchActions } from "@/lib/api/actions"
import { fetchAlerts } from "@/lib/api/alerts"
import {
  countOwnBuildings,
  fetchBuildings,
  ownBuildingsAllPending,
} from "@/lib/api/buildings"
import { fetchPartnerClients } from "@/lib/api/partners"
import { fetchPortfolioKPIs } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"

const ACCENT = "#1D9E75"

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }
  const token = session.accessToken

  const [kpisResult, ownResult, alertsResult, actionsResult, clientsResult] =
    await Promise.all([
      fetchPortfolioKPIs(token),
      fetchBuildings(token),
      fetchAlerts(token, { unresolved_only: true, limit: 5 }),
      fetchActions(token, { status: "open", limit: 5 }),
      fetchPartnerClients(token),
    ])

  if (ownResult.ok && countOwnBuildings(ownResult.data.buildings) === 0) {
    redirect("/onboarding")
  }

  const buildingCount = ownResult.ok
    ? countOwnBuildings(ownResult.data.buildings)
    : 0
  const showPending =
    ownResult.ok && ownBuildingsAllPending(ownResult.data.buildings)

  const kpis = kpisResult.ok ? kpisResult.data : null
  const unhandledAlerts = alertsResult.ok
    ? alertsResult.data.severity_counts.unhandled_total
    : 0
  const topAlerts = alertsResult.ok ? alertsResult.data.alerts.slice(0, 4) : []
  const openActions = actionsResult.ok
    ? actionsResult.data.status_counts.open
    : 0
  const topActions = actionsResult.ok
    ? actionsResult.data.actions.slice(0, 4)
    : []
  const hasPartnerClients =
    clientsResult.ok && clientsResult.data.clients.length > 0

  const firstName = session.user?.email?.split("@")[0] ?? null

  return (
    <AppChrome
      breadcrumb={[{ label: "Home" }]}
      pageTitle="Home"
      subtitle="Your portfolio at a glance"
      accentColor={ACCENT}
    >
      <SustainabilityMotif />
      <CitySkylineMotif />

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto space-y-8">
        <p className="text-sm text-text-muted">
          Welcome back{firstName ? `, ${firstName}` : ""}. Here&apos;s what needs you
          today — and where to act.
        </p>

        <PageIntro id="dashboard">
          Your home base. The KPI strip is your whole portfolio today vs the previous period; the
          four cards jump straight to <span className="text-text-primary">Monitor</span>,{" "}
          <span className="text-text-primary">Act</span>,{" "}
          <span className="text-text-primary">Comply</span> and{" "}
          <span className="text-text-primary">Copilot</span>. Click any building or alert below to act on it.
        </PageIntro>

        {showPending && <DataPendingBanner />}

        <HomeCockpit
          kpis={kpis}
          coreLoadFailed={!ownResult.ok}
          buildingCount={buildingCount}
          unhandledAlerts={unhandledAlerts}
          openActions={openActions}
          topAlerts={topAlerts}
          topActions={topActions}
          hasPartnerClients={hasPartnerClients}
        />

        <DataBasisNote />
      </div>
    </AppChrome>
  )
}
