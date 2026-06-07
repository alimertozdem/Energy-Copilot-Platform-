/**
 * /buildings/[fabric_building_id] — the building HOME (overview).
 *
 * Server component, auth-guarded. Landing screen for a building: meta + headline
 * KPIs + section tiles. The full Power BI report lives one click deeper at
 * /buildings/[id]/reports (persistent embed). Custom React, NO embed here.
 *
 * Data (all reused, no new backend): fetchBuilding (meta + modules + sample flag),
 * the building's row from /portfolio (commercial KPIs), and — for residential
 * buildings — the /residential rollup.
 */
import { notFound, redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingAdvisorPanel } from "@/components/buildings/BuildingAdvisorPanel"
import { BuildingOverview } from "@/components/buildings/BuildingOverview"
import { fetchActions } from "@/lib/api/actions"
import { fetchAlerts } from "@/lib/api/alerts"
import { fetchBuilding } from "@/lib/api/buildings"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { fetchBuildingResidential } from "@/lib/api/residentialManager"
import { authOptions } from "@/lib/auth/options"
import { buildAdvisorInsights } from "@/lib/insights/buildingAdvisor"

export const dynamic = "force-dynamic"

const ACCENT = "#1D9E75"

type PageProps = {
  params: Promise<{ fabric_building_id: string }>
}

export default async function BuildingDetailPage({ params }: PageProps) {
  const { fabric_building_id } = await params

  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const buildingResult = await fetchBuilding(session.accessToken, fabric_building_id)
  if (!buildingResult.ok) {
    notFound()
  }
  const building = buildingResult.data

  const isResidential = (building.building_type || "").toLowerCase().includes("residential")
  const [portfolioResult, residentialResult, actionsResult, alertsResult] =
    await Promise.all([
      fetchPortfolioBuildings(session.accessToken),
      isResidential
        ? fetchBuildingResidential(session.accessToken, fabric_building_id)
        : Promise.resolve(null),
      fetchActions(session.accessToken, { building_id: fabric_building_id, limit: 6 }),
      fetchAlerts(session.accessToken, {
        building_id: fabric_building_id,
        limit: 8,
        resolution: "unresolved",
      }),
    ])

  const kpis = portfolioResult.ok
    ? portfolioResult.data.buildings.find(
        (b) => b.fabric_building_id === fabric_building_id
      ) ?? null
    : null
  const residential =
    residentialResult && residentialResult.ok ? residentialResult.data : null
  const topActions = actionsResult.ok ? actionsResult.data.actions : []
  const topAlerts = alertsResult.ok ? alertsResult.data.alerts : []
  const insights = buildAdvisorInsights({
    kpis,
    topActions,
    topAlerts,
    isResidential,
    residential,
    profile: { epc_class: building.epc_class, heating_system: building.heating_system },
  })

  return (
    <AppChrome
      breadcrumb={[
        { label: "Buildings", href: "/buildings" },
        { label: `${building.fabric_building_id ?? "—"} — ${building.name}` },
      ]}
      pageTitle={building.name}
      subtitle={[building.country_code, building.city].filter(Boolean).join(" · ")}
      backHref="/buildings"
      backLabel="All buildings"
      accentColor={ACCENT}
    >
      <div className="relative z-10 mx-auto max-w-7xl px-6 py-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-w-0">
            <BuildingOverview building={building} kpis={kpis} residential={residential} />
          </div>
          <BuildingAdvisorPanel
            insights={insights}
            buildingId={building.fabric_building_id ?? fabric_building_id}
            buildingName={building.name}
          />
        </div>
      </div>
    </AppChrome>
  )
}
