/**
 * PortfolioAdvisor — portfolio-level triage (server component).
 *
 * Runs the per-building insight engine across the whole portfolio and surfaces
 * the buildings that need attention first, each with its single most-severe
 * headline and a link to that building's full advisor. Reuses the data the
 * portfolio page already fetches (PortfolioBuildingRow[]) — no extra backend.
 */
import Link from "next/link"
import { ArrowRight, Sparkles } from "lucide-react"

import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import { rankBuildingsByUrgency, type InsightSeverity } from "@/lib/insights/buildingAdvisor"

const DOT: Record<InsightSeverity, string> = {
  action: "bg-red-400",
  watch: "bg-amber-400",
  info: "bg-sky-400",
  good: "bg-brand-emerald",
}

export function PortfolioAdvisor({ buildings }: { buildings: PortfolioBuildingRow[] }) {
  if (buildings.length === 0) return null

  const ranked = rankBuildingsByUrgency(buildings)
  const attention = ranked.filter((r) => r.needsAttention)
  const shown = attention.slice(0, 5)
  const openAlerts = buildings.reduce((s, b) => s + (b.open_anomalies || 0), 0)
  const openRecs = buildings.reduce((s, b) => s + (b.open_recommendations || 0), 0)

  return (
    <section className="rounded-2xl border border-brand-emerald/30 bg-gradient-to-br from-brand-emerald/[0.07] to-transparent p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-brand-emerald/15 ring-1 ring-brand-emerald/30">
            <Sparkles className="h-4 w-4 text-brand-emerald" aria-hidden />
          </span>
          <div>
            <h2 className="font-display text-base font-semibold text-text-primary">Portfolio Advisor</h2>
            <p className="text-xs text-text-muted">
              {attention.length > 0
                ? `${attention.length} of ${buildings.length} buildings need attention`
                : `All ${buildings.length} buildings are in good shape`}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 text-[11px]">
          <span className="rounded-md border border-border-subtle bg-bg-elevated/40 px-2.5 py-1 text-text-muted">
            {openAlerts} open alert{openAlerts === 1 ? "" : "s"}
          </span>
          <span className="rounded-md border border-border-subtle bg-bg-elevated/40 px-2.5 py-1 text-text-muted">
            {openRecs} opportunit{openRecs === 1 ? "y" : "ies"}
          </span>
        </div>
      </div>

      {attention.length === 0 ? (
        <p className="mt-4 text-sm text-text-muted">
          No critical issues across the portfolio right now. Open any building for its full advisor.
        </p>
      ) : (
        <div className="mt-4 space-y-2">
          {shown.map((r) => (
            <Link
              key={r.building.fabric_building_id}
              href={`/buildings/${encodeURIComponent(r.building.fabric_building_id)}`}
              className="group flex items-center gap-3 rounded-xl border border-border-subtle bg-bg-elevated/40 p-3 transition-colors hover:border-brand-emerald/50"
            >
              <span
                className={`h-2 w-2 shrink-0 rounded-full ${r.top ? DOT[r.top.severity] : "bg-text-faint"}`}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium text-text-primary">{r.building.name}</span>
                  <span className="shrink-0 text-[11px] text-text-faint">
                    {r.building.city}, {r.building.country}
                  </span>
                </div>
                {r.top && <p className="truncate text-xs text-text-muted">{r.top.title}</p>}
              </div>
              {r.top?.metric && (
                <span className="hidden shrink-0 rounded-md border border-border-subtle px-1.5 py-0.5 text-[10px] tabular-nums text-text-muted sm:inline">
                  {r.top.metric}
                </span>
              )}
              <ArrowRight
                className="h-4 w-4 shrink-0 text-text-faint transition-transform group-hover:translate-x-0.5"
                aria-hidden
              />
            </Link>
          ))}
          {attention.length > shown.length && (
            <p className="px-1 pt-1 text-xs text-text-faint">
              and {attention.length - shown.length} more building
              {attention.length - shown.length === 1 ? "" : "s"} need attention — see the table below.
            </p>
          )}
        </div>
      )}
    </section>
  )
}
