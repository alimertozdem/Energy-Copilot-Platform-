/**
 * /residential — portfolio-level residential overview (manager command centre).
 *
 * Server component, auth-guarded. Lists every RESIDENTIAL building the manager
 * (or partner) may see, each with a rollup (units, avg EUI, EPC mix, UVI status)
 * and a drill-down to /buildings/[id]/residential. Custom React, NO Power BI embed.
 * Reads /residential/portfolio (visibility = buildings repo, partner-aware).
 */
import Link from "next/link"
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { LandlordPortfolioBand } from "@/components/residential/LandlordPortfolioBand"
import { UviComplianceBand } from "@/components/residential/UviComplianceBand"
import { fetchActions } from "@/lib/api/actions"
import {
  fetchResidentialPortfolio,
  fetchUviCompliance,
} from "@/lib/api/residentialManager"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

const ACCENT = "#1D9E75"
const MONTHS = [
  "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
const EPC_COLORS: Record<string, string> = {
  A: "#10b981", B: "#34d399", C: "#a3e635", D: "#fbbf24", E: "#f87171",
}

function fmt(n: number | null): string {
  if (n === null || Number.isNaN(n)) return "—"
  return n.toLocaleString("en-US", { maximumFractionDigits: 0 })
}

export default async function ResidentialPortfolioPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const [result, uviResult, actionsResult] = await Promise.all([
    fetchResidentialPortfolio(session.accessToken),
    fetchUviCompliance(session.accessToken),
    fetchActions(session.accessToken, { limit: 500 }),
  ])
  const buildings = result.ok ? result.data.buildings : []
  const residentialIds = buildings.map((b) => b.fabric_building_id)

  return (
    <AppChrome
      breadcrumb={[{ label: "Residential" }]}
      pageTitle="Residential Portfolio"
      subtitle={
        result.ok
          ? `${buildings.length} residential ${buildings.length === 1 ? "building" : "buildings"}`
          : "Could not load residential portfolio"
      }
      accentColor={ACCENT}
    >
      <div className="relative z-10 mx-auto max-w-7xl px-6 py-8 space-y-6">
        {uviResult.ok && <UviComplianceBand data={uviResult.data} />}

        {actionsResult.ok && residentialIds.length > 0 && (
          <LandlordPortfolioBand
            actions={actionsResult.data.actions}
            residentialIds={residentialIds}
          />
        )}

        {!result.ok ? (
          <FetchErrorNotice error={result.error} label="residential portfolio" />
        ) : buildings.length === 0 ? (
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-6">
            <p className="text-sm font-semibold text-text-primary">
              No residential buildings yet.
            </p>
            <p className="mt-1 text-sm text-text-muted">
              Buildings with a residential type appear here with per-unit heating KPIs
              and monthly consumption (UVI) status. Add one from{" "}
              <Link href="/buildings" className="text-brand-emerald hover:underline">
                Buildings
              </Link>
              .
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {buildings.map((b) => {
              const uvi = b.rollup.uvi
              const uviText =
                uvi.latest_year && uvi.latest_month
                  ? `${MONTHS[uvi.latest_month] ?? uvi.latest_month} ${uvi.latest_year} · ${uvi.units_covered}`
                  : "No UVI data"
              const bands = ["A", "B", "C", "D", "E"].filter(
                (band) => b.rollup.epc_distribution[band]
              )
              return (
                <Link
                  key={b.fabric_building_id}
                  href={`/buildings/${encodeURIComponent(b.fabric_building_id)}/residential`}
                  className="group flex flex-col rounded-xl border border-border-subtle bg-bg-elevated/40 p-5 transition-colors hover:border-brand-emerald/50"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-text-primary">{b.name}</p>
                      <p className="mt-0.5 text-xs text-text-muted">
                        {[b.country_code, b.city, b.fabric_building_id].filter(Boolean).join(" · ")}
                      </p>
                    </div>
                    <span className="shrink-0 text-xs text-brand-emerald opacity-0 transition-opacity group-hover:opacity-100">
                      View units →
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-text-faint">Units</p>
                      <p className="text-lg font-semibold text-text-primary">
                        {b.rollup.units_with_data}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-wider text-text-faint">Avg EUI</p>
                      <p className="text-lg font-semibold text-text-primary">
                        {fmt(b.rollup.building_avg_eui_kwh_m2_yr)}
                        <span className="ml-1 text-[10px] font-normal text-text-muted">kWh/m²·yr</span>
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1">
                      {bands.length === 0 ? (
                        <span className="text-xs text-text-faint">No EPC</span>
                      ) : (
                        bands.map((band) => (
                          <span
                            key={band}
                            className="inline-flex h-5 items-center gap-0.5 rounded px-1 text-[10px] font-bold text-bg-base"
                            style={{ background: EPC_COLORS[band] ?? "#94a3b8" }}
                          >
                            {band}
                            <span className="font-normal">{b.rollup.epc_distribution[band]}</span>
                          </span>
                        ))
                      )}
                    </div>
                    <span className="text-[11px] text-text-muted">UVI: {uviText}</span>
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </AppChrome>
  )
}
