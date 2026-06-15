/**
 * HomeCockpit — the persona-aware home for /dashboard (design audit P0-2 + polish, 2026-06-15).
 *
 * Server (presentational) component. Three KPI-area states:
 *   - has data    → KPI strip (energy · EUI · cost · CO₂)
 *   - load failed → calm "data temporarily unavailable" note (honest, no misleading zeros)
 *   - empty       → "light up your portfolio" get-started CTA (no hardware)
 * Plus four intent cards mirroring the nav clusters (equal height) and two triage mini-lists.
 */

import Link from "next/link"

import { CountUp } from "@/components/CountUp"
import {
  Activity,
  ArrowRight,
  ListChecks,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Users,
} from "lucide-react"

import type { ActionItem } from "@/lib/api/actions"
import type { AlertItem } from "@/lib/api/alerts"
import type { KPITile, PortfolioKPIs } from "@/lib/api/portfolio"

type Props = {
  kpis: PortfolioKPIs | null
  coreLoadFailed: boolean
  buildingCount: number
  unhandledAlerts: number
  openActions: number
  topAlerts: AlertItem[]
  topActions: ActionItem[]
  hasPartnerClients: boolean
}

function fmt(n: number): string {
  return Math.abs(n) >= 1000
    ? n.toLocaleString("en-US", { maximumFractionDigits: 0 })
    : n.toLocaleString("en-US", { maximumFractionDigits: 1 })
}

function deltaClass(direction: KPITile["direction"]): string {
  if (direction === "down") return "text-brand-emerald"
  if (direction === "up") return "text-red-300"
  return "text-text-muted"
}

function deltaArrow(direction: KPITile["direction"]): string {
  if (direction === "down") return "▼"
  if (direction === "up") return "▲"
  return "•"
}

function Kpi({ label, tile }: { label: string; tile: KPITile }) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <span className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-brand-emerald via-brand-mint to-accent-cyan" aria-hidden />
      <div className="text-[11px] uppercase tracking-wider text-text-faint">{label}</div>
      <div className="mt-1 text-2xl font-semibold font-display tabular-nums text-text-primary">
        <CountUp value={tile.value} />{" "}
        <span className="text-xs font-normal text-text-muted">{tile.unit}</span>
      </div>
      {tile.delta_pct != null && (
        <div className={`mt-1 text-xs ${deltaClass(tile.direction)}`}>
          {deltaArrow(tile.direction)} {Math.abs(tile.delta_pct).toFixed(1)}% vs prev. period
        </div>
      )}
    </div>
  )
}

type Card = {
  href: string
  title: string
  blurb: string
  icon: typeof Activity
  color: string
  stat?: string
  statTone?: "amber" | "red"
}

export function HomeCockpit({
  kpis,
  coreLoadFailed,
  buildingCount,
  unhandledAlerts,
  openActions,
  topAlerts,
  topActions,
  hasPartnerClients,
}: Props) {
  const cards: Card[] = [
    {
      href: "/portfolio",
      title: "Monitor",
      blurb: `${buildingCount} ${buildingCount === 1 ? "building" : "buildings"} · energy, cost & carbon`,
      icon: Activity,
      color: "#1D9E75",
      stat: unhandledAlerts > 0 ? `${unhandledAlerts} alert${unhandledAlerts === 1 ? "" : "s"} need attention` : undefined,
      statTone: "red",
    },
    {
      href: "/actions",
      title: "Act",
      blurb: "Prioritised retrofit & efficiency measures",
      icon: ListChecks,
      color: "#EAB308",
      stat: openActions > 0 ? `${openActions} open recommendation${openActions === 1 ? "" : "s"}` : undefined,
      statTone: "amber",
    },
    {
      href: "/compliance",
      title: "Comply",
      blurb: "EPBD/MEPS, CRREM stranding, ESRS & Taxonomy",
      icon: ShieldCheck,
      color: "#A855F7",
    },
    hasPartnerClients
      ? {
          href: "/partners",
          title: "Clients",
          blurb: "Switch between the portfolios you manage",
          icon: Users,
          color: "#06B6D4",
        }
      : {
          href: "/copilot",
          title: "Ask Copilot",
          blurb: "Natural-language answers across your portfolio",
          icon: Sparkles,
          color: "#7B5BD6",
        },
  ]

  return (
    <div className="space-y-8">
      {/* KPI area — three states */}
      {kpis ? (
        <div className="el-stagger grid grid-cols-2 gap-4 md:grid-cols-4">
          <Kpi label="Energy" tile={kpis.total_energy} />
          <Kpi label="Avg EUI" tile={kpis.avg_eui} />
          <Kpi label="Cost" tile={kpis.total_cost} />
          <Kpi label="CO₂" tile={kpis.total_co2} />
        </div>
      ) : coreLoadFailed ? (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.06] p-4 text-sm text-amber-100/90">
          Your live data isn’t reachable right now. The dashboard fills in automatically once the
          connection is back — nothing is lost.
        </div>
      ) : (
        <div className="rounded-xl border border-brand-emerald/30 bg-brand-emerald/[0.06] p-5">
          <h3 className="text-sm font-semibold text-text-primary">Light up your portfolio</h3>
          <p className="mt-1 max-w-2xl text-xs leading-relaxed text-text-muted">
            Add your first building and upload a meter reading or utility bill — no hardware needed —
            and your KPIs, alerts and recommendations appear right here.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/onboarding"
              className="inline-flex items-center gap-1.5 rounded-md bg-brand-emerald px-3.5 py-2 text-xs font-semibold text-bg-base transition-colors hover:bg-brand-emerald/90"
            >
              Add a building <ArrowRight size={13} aria-hidden />
            </Link>
            <Link
              href="/connections"
              className="inline-flex items-center gap-1.5 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3.5 py-2 text-xs font-semibold text-brand-emerald transition-colors hover:bg-brand-emerald/10"
            >
              Connect data
            </Link>
          </div>
        </div>
      )}

      {/* Intent cards (equal height) */}
      <div className="el-fade-stagger grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <Link
            key={c.title}
            href={c.href}
            className="group flex flex-col rounded-xl border border-border-subtle bg-bg-elevated/40 p-5 transition-all hover:-translate-y-0.5 hover:border-brand-emerald/50 hover:shadow-[0_12px_34px_-14px_rgba(29,158,117,0.45)]"
          >
            <div className="flex items-center justify-between">
              <span
                className="inline-flex h-10 w-10 items-center justify-center rounded-lg transition-transform duration-300 group-hover:scale-110"
                style={{ background: `${c.color}1A`, border: `1px solid ${c.color}40` }}
              >
                <c.icon size={20} style={{ color: c.color }} aria-hidden />
              </span>
              {c.stat && (
                <span
                  className={
                    "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold border " +
                    (c.statTone === "red"
                      ? "bg-red-500/15 text-red-200 border-red-500/40"
                      : "bg-amber-500/15 text-amber-200 border-amber-500/40")
                  }
                >
                  <TriangleAlert size={10} aria-hidden /> {c.stat}
                </span>
              )}
            </div>
            <h3 className="mt-3 text-sm font-semibold text-text-primary">{c.title}</h3>
            <p className="mt-1 text-xs leading-relaxed text-text-muted">{c.blurb}</p>
            <span className="mt-auto pt-3 inline-flex items-center gap-1 text-xs text-brand-emerald">
              Open <ArrowRight size={13} className="transition-transform group-hover:translate-x-0.5" aria-hidden />
            </span>
          </Link>
        ))}
      </div>

      {/* Triage mini-lists */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text-primary">Needs attention</h3>
            <Link href="/alerts" className="text-xs text-brand-emerald hover:text-brand-mint">
              All alerts →
            </Link>
          </div>
          <div className="mt-3 space-y-2">
            {topAlerts.length === 0 ? (
              <p className="text-xs text-text-muted">No open alerts right now.</p>
            ) : (
              topAlerts.map((a, i) => (
                <Link
                  key={a.anomaly_id ?? `${a.fabric_building_id}-${i}`}
                  href="/alerts"
                  className="flex items-center justify-between gap-3 rounded-lg border border-border-faint bg-white/[0.02] px-3 py-2 transition-colors hover:border-brand-emerald/40"
                >
                  <div className="min-w-0">
                    <div className="truncate text-xs font-medium text-text-primary">{a.building_name}</div>
                    <div className="truncate text-[11px] text-text-muted">
                      {a.anomaly_type ?? a.description ?? "Anomaly"}
                      {a.occurrence_count > 1 ? ` · ×${a.occurrence_count}` : ""}
                    </div>
                  </div>
                  {a.severity && (
                    <span className="shrink-0 rounded-full border border-red-500/40 bg-red-500/15 px-2 py-0.5 text-[10px] font-semibold text-red-200">
                      {a.severity}
                    </span>
                  )}
                </Link>
              ))
            )}
          </div>
        </section>

        <section className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-text-primary">Recommended next</h3>
            <Link href="/actions" className="text-xs text-brand-emerald hover:text-brand-mint">
              All actions →
            </Link>
          </div>
          <div className="mt-3 space-y-2">
            {topActions.length === 0 ? (
              <p className="text-xs text-text-muted">No open recommendations right now.</p>
            ) : (
              topActions.map((a, i) => (
                <Link
                  key={a.action_id ?? `${a.fabric_building_id}-${i}`}
                  href="/actions"
                  className="flex items-center justify-between gap-3 rounded-lg border border-border-faint bg-white/[0.02] px-3 py-2 transition-colors hover:border-brand-emerald/40"
                >
                  <div className="min-w-0">
                    <div className="truncate text-xs font-medium text-text-primary">
                      {a.title ?? a.action_type ?? "Measure"}
                    </div>
                    <div className="truncate text-[11px] text-text-muted">{a.building_name}</div>
                  </div>
                  {a.annual_saving_eur != null && a.annual_saving_eur > 0 && (
                    <span className="shrink-0 rounded-full border border-brand-emerald/40 bg-brand-emerald/10 px-2 py-0.5 text-[10px] font-semibold text-brand-mint">
                      ~€{fmt(a.annual_saving_eur)}/yr
                    </span>
                  )}
                </Link>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
