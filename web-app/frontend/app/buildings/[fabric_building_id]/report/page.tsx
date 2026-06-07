/**
 * /buildings/[fabric_building_id]/report — single-building PDF report.
 *
 * Server component, force-dynamic, auth-guarded. Reuses the portfolio buildings
 * fetch (to find this building's summary row) plus building-scoped actions and
 * alerts — no new backend, no Fabric change. Wraps BuildingReportDocument in
 * the shared ReportFrame. A client deliverable: "here is your building's energy
 * report".
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { BuildingReportDocument } from "@/components/report/BuildingReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { authOptions } from "@/lib/auth/options"
import { fetchActions } from "@/lib/api/actions"
import { fetchAlerts } from "@/lib/api/alerts"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { fetchBuildingResidential } from "@/lib/api/residentialManager"
import { buildAdvisorInsights } from "@/lib/insights/buildingAdvisor"

export const dynamic = "force-dynamic"

type PageProps = {
  params: Promise<{ fabric_building_id: string }>
}

export default async function BuildingReportPage({ params }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { fabric_building_id } = await params
  const id = decodeURIComponent(fabric_building_id)

  const [buildingsResult, actionsResult, alertsResult] = await Promise.all([
    fetchPortfolioBuildings(session.accessToken),
    fetchActions(session.accessToken, { building_id: id, limit: 500 }),
    fetchAlerts(session.accessToken, {
      building_id: id,
      resolution: "unresolved",
      limit: 500,
    }),
  ])

  const building = buildingsResult.ok
    ? buildingsResult.data.buildings.find((b) => b.fabric_building_id === id) ?? null
    : null
  const buildingError = buildingsResult.ok ? null : buildingsResult.error

  // Advisor highlights — reuse the deterministic insight engine. Residential
  // buildings get their per-unit rollup so the heating / UVI / EPC-mix insights
  // apply; commercial buildings need only the portfolio row + scoped actions.
  const isResidential = (building?.building_type || "").toLowerCase().includes("residential")
  const residentialResult =
    isResidential && building ? await fetchBuildingResidential(session.accessToken, id) : null
  const insights = buildAdvisorInsights({
    kpis: building,
    topActions: actionsResult.ok ? actionsResult.data.actions : [],
    isResidential,
    residential: residentialResult && residentialResult.ok ? residentialResult.data : null,
  })

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const metaLine = building ? `${building.name} · ${building.city}, ${building.country}` : id

  return (
    <ReportFrame
      backHref={`/buildings/${encodeURIComponent(id)}`}
      backLabel="Back to building"
      title="Building Energy Report"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="Last 30 days"
    >
      <BuildingReportDocument
        building={building}
        buildingError={buildingError}
        insights={insights}
        actions={actionsResult.ok ? actionsResult.data.actions : []}
        actionsCounts={actionsResult.ok ? actionsResult.data.status_counts : null}
        actionsError={actionsResult.ok ? null : actionsResult.error}
        alerts={alertsResult.ok ? alertsResult.data.alerts : []}
        alertsCounts={alertsResult.ok ? alertsResult.data.severity_counts : null}
        alertsError={alertsResult.ok ? null : alertsResult.error}
      />
    </ReportFrame>
  )
}
