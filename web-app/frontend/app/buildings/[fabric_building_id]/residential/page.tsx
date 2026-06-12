/**
 * /buildings/[fabric_building_id]/residential — manager residential dashboard.
 *
 * Server component, auth-guarded. Per-unit residential KPIs + a rollup for one
 * building (segment-aware: linked from the building view only for Residential
 * buildings). Custom React, NO Power BI embed (like /portfolio). Visibility is
 * enforced server-side: fetchBuilding 404s for buildings the user can't see.
 */
import { notFound, redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { LandlordInvestmentCase } from "@/components/residential/LandlordInvestmentCase"
import { ResidentialDashboard } from "@/components/residential/ResidentialDashboard"
import { ResidentInvitePanel } from "@/components/residential/ResidentInvitePanel"
import { fetchActions } from "@/lib/api/actions"
import { fetchBuilding } from "@/lib/api/buildings"
import { fetchBuildingResidential } from "@/lib/api/residentialManager"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

const ACCENT = "#1D9E75"

type PageProps = {
  params: Promise<{ fabric_building_id: string }>
}

export default async function BuildingResidentialPage({ params }: PageProps) {
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

  const [dataResult, actionsResult] = await Promise.all([
    fetchBuildingResidential(session.accessToken, fabric_building_id),
    fetchActions(session.accessToken, { building_id: fabric_building_id, limit: 500 }),
  ])

  const subtitle = [building.country_code, building.building_type, `${building.name}`]
    .filter(Boolean)
    .join(" · ")

  return (
    <AppChrome
      breadcrumb={[
        { label: "Buildings", href: "/buildings" },
        {
          label: `${building.fabric_building_id ?? "—"} — ${building.name}`,
          href: `/buildings/${encodeURIComponent(fabric_building_id)}`,
        },
        { label: "Residential" },
      ]}
      pageTitle="Residential — Units"
      subtitle={subtitle}
      backHref={`/buildings/${encodeURIComponent(fabric_building_id)}`}
      backLabel="Back to building"
      accentColor={ACCENT}
    >
      <div className="relative z-10 mx-auto max-w-7xl px-6 py-8 space-y-6">
        <ResidentInvitePanel
          fabricBuildingId={fabric_building_id}
          units={dataResult.ok ? dataResult.data.units.map((u) => u.unit_id) : []}
        />
        <ResidentialDashboard
          data={dataResult.ok ? dataResult.data : null}
          error={dataResult.ok ? null : dataResult.error}
        />
        <LandlordInvestmentCase
          actions={actionsResult.ok ? actionsResult.data.actions : []}
          epcClass={building.epc_class ?? null}
          fabricBuildingId={fabric_building_id}
        />
      </div>
    </AppChrome>
  )
}
