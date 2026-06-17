/**
 * /buildings/by-id/[uuid] — detail view for a building still PENDING a Fabric
 * bridge (no fabric_building_id, so it can't use the Fabric-backed detail page).
 *
 * Server component. Addresses the building by its Postgres UUID, shows the
 * baseline KPIs computed from uploaded consumption (Tier-1), and the full AI
 * advisor panel — the same engine the card teaser uses, but the complete set.
 * If the building turns out to be bridged, we redirect to the live detail page.
 */
import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingAdvisorPanel } from "@/components/buildings/BuildingAdvisorPanel"
import { BridgeUnlockPanel } from "@/components/buildings/BridgeUnlockPanel"
import { UploadDataButton } from "@/components/buildings/UploadDataButton"
import { DataProvenanceBadge } from "@/components/ui/DataProvenanceBadge"
import { EngineEstimateCard } from "@/components/buildings/EngineEstimateCard"
import { SharpenEstimateForm } from "@/components/buildings/SharpenEstimateForm"
import { CopCard } from "@/components/buildings/CopCard"
import { LiveMonitoringPanel } from "@/components/buildings/LiveMonitoringPanel"
import { DataPendingBanner } from "@/components/DataPendingBanner"
import { type BaselineKpis, fetchBuildingBaselineKpisServer, fetchBaselineEstimateServer, fetchBuildingCopServer, fetchBuildingMonitoringServer } from "@/lib/api/baseline"
import { fetchBuildingEstimateServer } from "@/lib/api/estimation"
import { fetchBridgeReadinessServer } from "@/lib/api/bridge"
import { type Building, fetchBuildingByUuid } from "@/lib/api/buildings"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import { buildAdvisorInsights } from "@/lib/insights/buildingAdvisor"
import { authOptions } from "@/lib/auth/options"

function toRow(b: Building, k: BaselineKpis | null): PortfolioBuildingRow {
  return {
    fabric_building_id: "",
    name: b.name,
    city: b.city ?? "",
    country: b.country_code ?? "",
    building_type: b.building_type ?? "",
    floor_area_m2: b.floor_area_m2 ?? 0,
    epc_class: b.epc_class,
    kwh_30d: k?.kwh_30d ?? 0,
    cost_30d_eur: k?.cost_30d_eur ?? 0,
    co2_30d_kg: k?.co2_30d_kg ?? 0,
    eui_kwh_m2_yr: k?.eui_kwh_m2_yr ?? null,
    open_anomalies: 0,
    open_recommendations: 0,
    has_pv: (b.pv_capacity_kwp ?? 0) > 0,
    has_battery: b.modules.some((m) => m.module_key === "battery" && m.enabled),
    has_iot: b.modules.some((m) => m.module_key === "iot" && m.enabled),
    subscription_tier: "Monitor",
  }
}

function fmtEnergy(kwh: number): string {
  if (kwh >= 1_000_000) return `${(kwh / 1_000_000).toFixed(1)} GWh`
  if (kwh >= 1_000) return `${(kwh / 1_000).toFixed(0)} MWh`
  return `${Math.round(kwh)} kWh`
}
function fmtCo2(kg: number): string {
  return kg >= 1_000 ? `${(kg / 1_000).toFixed(1)} t` : `${Math.round(kg)} kg`
}
function eur(n: number): string {
  return "€" + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}

function provenance(k: BaselineKpis): string {
  const basis = k.is_annualized ? `${k.months_available} mo, annualized` : "trailing 12 mo"
  const cost = k.cost_basis === "actual" ? "actual cost" : "est. cost"
  return `From your uploaded data · ${basis} · ${cost}`
}

function Tile({ label, value, unit }: { label: string; value: string; unit?: string }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <div className="text-[11px] uppercase tracking-wide text-text-faint">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-text-primary tabular-nums">
        {value}
        {unit && <span className="ml-1 text-sm font-normal text-text-muted">{unit}</span>}
      </div>
    </div>
  )
}

export default async function PendingBuildingPage({
  params,
}: {
  params: Promise<{ building_id: string }>
}) {
  const { building_id } = await params
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const res = await fetchBuildingByUuid(session.accessToken, building_id)
  if (!res.ok) {
    notFound()
  }
  const building = res.data
  // Already bridged? Use the live Fabric-backed detail page instead.
  if (building.fabric_building_id) {
    redirect(`/buildings/${encodeURIComponent(building.fabric_building_id)}`)
  }

  const [kpis, bridgeReadiness, estimate, cop, monitoring, engineEstimate] = await Promise.all([
    fetchBuildingBaselineKpisServer(session.accessToken, building_id),
    fetchBridgeReadinessServer(session.accessToken, building_id),
    fetchBaselineEstimateServer(session.accessToken, building_id),
    fetchBuildingCopServer(session.accessToken, building_id),
    fetchBuildingMonitoringServer(session.accessToken, building_id),
    fetchBuildingEstimateServer(session.accessToken, building_id),
  ])
  const hasIot = building.modules.some((m) => m.module_key === "iot" && m.enabled)
  const insights = buildAdvisorInsights({
    kpis: toRow(building, kpis),
    topActions: [],
    isResidential: false,
    profile: { epc_class: building.epc_class, heating_system: building.heating_system },
    estimate: engineEstimate,
  })

  const hasKpis = Boolean(kpis?.has_data)
  // Upload only makes sense for buildings the user owns (not read-only samples).
  const canUpload = !building.is_sample_org

  return (
    <AppChrome
      breadcrumb={[{ label: "Buildings", href: "/buildings" }, { label: building.name }]}
      pageTitle={building.name}
      subtitle={[building.city, building.building_type].filter(Boolean).join(" · ")}
      backHref="/buildings"
      backLabel="Buildings"
    >
      <div className="relative z-10 px-6 py-8 max-w-6xl mx-auto">
        <div className="mb-6">
          <DataPendingBanner />
        </div>

        <div className="mb-5 flex flex-wrap gap-2">
          <Link
            href={`/hvac?building_id=${encodeURIComponent(building.id)}`}
            className="inline-flex items-center gap-1.5 rounded-md border border-amber-400/30 bg-amber-400/5 px-3 py-1.5 text-xs text-amber-200 transition-colors hover:border-amber-400/60"
          >
            Heating &amp; HVAC — retrofit ROI, COP &amp; comfort →
          </Link>
          <Link
            href="/compliance"
            className="inline-flex items-center gap-1.5 rounded-md border border-brand-emerald/30 bg-brand-emerald/5 px-3 py-1.5 text-xs text-brand-emerald transition-colors hover:border-brand-emerald/60"
          >
            Compliance &amp; CRREM stranding →
          </Link>
          <Link
            href="/financing"
            className="inline-flex items-center gap-1.5 rounded-md border border-brand-emerald/30 bg-brand-emerald/5 px-3 py-1.5 text-xs text-brand-emerald transition-colors hover:border-brand-emerald/60"
          >
            Financing &amp; subsidies →
          </Link>
        </div>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-5">
            {!hasKpis && engineEstimate && (
              <div>
                <EngineEstimateCard estimate={engineEstimate} />
                <SharpenEstimateForm
                  buildingId={building.id}
                  canManage={canUpload}
                  current={{
                    construction_year: building.construction_year ?? null,
                    epc_class: building.epc_class ?? null,
                    heating_system: building.heating_system ?? null,
                    floor_area_m2: building.floor_area_m2 ?? null,
                  }}
                />
              </div>
            )}
            <div>
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-text-primary">
                    {hasKpis ? "Your measured baseline" : "Baseline KPIs"}
                  </h2>
                  {hasKpis && <DataProvenanceBadge basis="measured" />}
                </div>
                {canUpload && hasKpis && <UploadDataButton buildings={[building]} />}
              </div>
              {hasKpis && kpis ? (
                <>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <Tile
                      label="EUI"
                      value={kpis.eui_kwh_m2_yr != null ? String(Math.round(kpis.eui_kwh_m2_yr)) : "—"}
                      unit={kpis.eui_kwh_m2_yr != null ? "kWh/m²·yr" : undefined}
                    />
                    <Tile
                      label="Energy / yr"
                      value={kpis.annual_energy_kwh != null ? fmtEnergy(kpis.annual_energy_kwh) : "—"}
                    />
                    <Tile
                      label="CO₂ / yr"
                      value={kpis.annual_co2_kg != null ? fmtCo2(kpis.annual_co2_kg) : "—"}
                    />
                    <Tile
                      label="Cost / yr"
                      value={kpis.annual_cost_eur != null ? eur(kpis.annual_cost_eur) : "—"}
                    />
                  </div>
                  <p className="mt-2 text-[11px] text-text-faint">{provenance(kpis)}</p>
                </>
              ) : estimate ? (
                <div className="space-y-3">
                  {canUpload && (
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-dashed border-border-subtle bg-bg-elevated/20 px-4 py-3">
                      <span className="text-xs text-text-muted">
                        Upload a bill or CSV to replace the estimate with your real KPIs.
                      </span>
                      <UploadDataButton buildings={[building]} variant="solid" />
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-border-subtle bg-bg-elevated/20 p-6 text-center">
                  <div className="text-sm text-text-primary mb-1">No uploaded consumption yet</div>
                  <div className="text-xs text-text-muted">
                    Upload a CSV or a PDF utility bill to light up this building&rsquo;s baseline
                    KPIs (EUI, energy, carbon, cost) and the advisor.
                  </div>
                  {canUpload && (
                    <div className="mt-4 flex justify-center">
                      <UploadDataButton buildings={[building]} variant="solid" />
                    </div>
                  )}
                </div>
              )}
            </div>

            {cop && (building.heating_system === "heat_pump" || cop.status !== "needs_heat_meter") && (
              <CopCard cop={cop} buildingId={building.id} />
            )}

            {monitoring && (monitoring.basis !== "none" || hasIot) && (
              <LiveMonitoringPanel monitoring={monitoring} buildingId={building.id} />
            )}

            <div className="rounded-xl border border-border-subtle bg-bg-elevated/30 p-4">
              <h2 className="mb-2 text-sm font-semibold text-text-primary">About this building</h2>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-3">
                {building.floor_area_m2 != null && (
                  <Meta label="Floor area" value={`${building.floor_area_m2.toLocaleString("en-US")} m²`} />
                )}
                {building.epc_class && <Meta label="EPC" value={building.epc_class} />}
                {building.heating_system && <Meta label="Heating" value={building.heating_system} />}
                {building.country_code && <Meta label="Country" value={building.country_code} />}
                {building.construction_year != null && (
                  <Meta label="Built" value={String(building.construction_year)} />
                )}
                <Meta label="Data status" value="Pending Fabric bridge" />
              </dl>
            </div>

            {canUpload && bridgeReadiness && (
              <BridgeUnlockPanel buildingId={building.id} initial={bridgeReadiness} />
            )}
          </div>

          <BuildingAdvisorPanel insights={insights} buildingId={building.id} buildingName={building.name} />
        </div>
      </div>
    </AppChrome>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-text-faint">{label}</dt>
      <dd className="text-text-primary">{value}</dd>
    </div>
  )
}
