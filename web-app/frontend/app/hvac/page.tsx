/**
 * /hvac — building-level Heating & HVAC deep-dive (web-app native, no Fabric).
 *
 * Three layers for one building: demand + envelope + retrofit ROI (approved
 * method), supply efficiency (measured COP), and comfort/operation (live IoT).
 * Building-scoped via ?building_id (defaults to the first own building), like
 * /solar. Complements the portfolio-level /decarbonisation + the Power BI page.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingSlicer } from "@/components/BuildingSlicer"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { HeatingAssessmentView } from "@/components/buildings/HeatingAssessmentView"
import { CopCard } from "@/components/buildings/CopCard"
import { ComfortPanel } from "@/components/buildings/ComfortPanel"
import { authOptions } from "@/lib/auth/options"
import { fetchBuildings } from "@/lib/api/buildings"
import { fetchBuildingHeatingServer, fetchBuildingComfortServer } from "@/lib/api/heating"
import { fetchBuildingCopServer } from "@/lib/api/baseline"

const ACCENT = "#F59E0B"

type PageProps = { searchParams: Promise<{ building_id?: string }> }

export default async function HvacPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) redirect("/")

  const { building_id } = await searchParams
  const result = await fetchBuildings(session.accessToken)
  const visible = result.ok ? result.data.buildings : []  // own + sample, so the demo account showcases HVAC too
  const slicer = visible.map((b) => ({ id: b.id, name: b.name }))
  const selected =
    building_id && visible.some((b) => b.id === building_id) ? building_id : visible[0]?.id ?? null

  if (!selected) {
    return (
      <AppChrome breadcrumb={[{ label: "Heating & HVAC" }]} pageTitle="Heating & HVAC" subtitle="Heat demand, envelope & comfort" accentColor={ACCENT}>
        <div className="relative z-10 px-6 py-8 max-w-3xl mx-auto">
          <div className="rounded-lg border border-border-subtle bg-bg-elevated/30 p-8 text-center">
            <div className="text-sm text-text-primary mb-1">No buildings yet</div>
            <div className="text-xs text-text-muted">Add a building to see its heating assessment.</div>
          </div>
        </div>
      </AppChrome>
    )
  }

  const [heating, cop, comfort] = await Promise.all([
    fetchBuildingHeatingServer(session.accessToken, selected),
    fetchBuildingCopServer(session.accessToken, selected),
    fetchBuildingComfortServer(session.accessToken, selected),
  ])
  const buildingName = visible.find((b) => b.id === selected)?.name ?? "Building"

  return (
    <AppChrome
      breadcrumb={[{ label: "Heating & HVAC" }]}
      pageTitle="Heating & HVAC"
      subtitle={`${buildingName} · heat demand, envelope & comfort`}
      accentColor={ACCENT}
    >
      <div className="relative z-10 px-6 py-8 max-w-5xl mx-auto space-y-6">
        {slicer.length > 1 && (
          <div className="flex justify-end">
            <BuildingSlicer buildings={slicer} value={selected} />
          </div>
        )}

        {heating ? (
          <HeatingAssessmentView data={heating} buildingId={selected} />
        ) : (
          <FetchErrorNotice error="Could not load the heating assessment." label="heating data" />
        )}

        {/* Supply: measured COP */}
        {cop && <CopCard cop={cop} buildingId={selected} />}

        {/* Comfort / operation analytics: live IoT */}
        {comfort && (
          <ComfortPanel comfort={comfort} buildingId={selected} heatCostEur={heating?.supply.heat_cost_eur ?? null} />
        )}
      </div>
    </AppChrome>
  )
}
