/**
 * CrremStranding — CRREM-style transition-risk section for /compliance.
 *
 * Pure server component. Computes each building's stranding year from existing
 * portfolio data (CO₂ + floor area) against an illustrative 1.5°C pathway.
 * The pathway values are indicative, not the licensed CRREM dataset (see
 * lib/crrem) — clearly labelled below.
 */
import Link from "next/link"

import { InfoTip } from "@/components/ui/info-tip"

import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import {
  PATHWAY_END_YEAR,
  PATHWAY_START_YEAR,
  summarizeStranding,
  type StrandingResult,
} from "@/lib/crrem"

function fmtInt(n: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}

type Meta = { label: string; badge: string; bar: string; frac: number }

function statusMeta(r: StrandingResult): Meta {
  switch (r.status) {
    case "stranded_now":
      return {
        label: "Stranded now",
        badge: "bg-red-500/15 text-red-200 border-red-500/40",
        bar: "bg-red-400",
        frac: 0.04,
      }
    case "stranding": {
      const y = r.strandingYear ?? PATHWAY_END_YEAR
      const frac = (y - PATHWAY_START_YEAR) / (PATHWAY_END_YEAR - PATHWAY_START_YEAR)
      const soon = y <= 2030
      return {
        label: `Strands ${y}`,
        badge: soon
          ? "bg-amber-500/15 text-amber-200 border-amber-500/40"
          : "bg-amber-400/10 text-amber-200/90 border-amber-400/30",
        bar: soon ? "bg-amber-400" : "bg-amber-300",
        frac,
      }
    }
    case "on_track":
      return {
        label: "Aligned to 2050",
        badge: "bg-emerald-500/15 text-emerald-200 border-emerald-500/30",
        bar: "bg-emerald-400",
        frac: 1,
      }
    default:
      return {
        label: "No data",
        badge: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
        bar: "bg-zinc-500",
        frac: 0,
      }
  }
}

function rank(r: StrandingResult): number {
  if (r.status === "stranded_now") return 0
  if (r.status === "stranding") return 1
  if (r.status === "on_track") return 2
  return 3
}

export function CrremStranding({ buildings }: { buildings: PortfolioBuildingRow[] }) {
  const s = summarizeStranding(buildings)
  const ordered = [...s.results].sort((a, b) => {
    const dr = rank(a) - rank(b)
    if (dr !== 0) return dr
    return (a.strandingYear ?? 9999) - (b.strandingYear ?? 9999)
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="inline-flex items-center gap-1.5 text-base font-semibold text-text-primary">
          CRREM-aligned stranding risk
          <InfoTip term="stranding" />
        </h2>
        <p className="text-xs text-text-muted mt-0.5">
          The year each building&apos;s carbon intensity exceeds the 1.5°C
          decarbonisation pathway, holding today&apos;s performance flat.
        </p>
      </div>

      <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 px-4 py-3 text-sm text-sky-200/90">
        <span className="font-medium">Illustrative pathways.</span> These 1.5°C
        curves are indicative, not the official licensed CRREM dataset (available
        via a CRREM License Partner agreement). The method is CRREM-standard; only
        the curve values are placeholders, swappable from one module.
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Assessed" value={`${s.assessed} / ${buildings.length}`} sub="have CO₂ + area data" />
        <Stat label="Stranded now" value={`${s.strandedNow}`} sub="above 2025 pathway" tone="red" />
        <Stat label="Strand by 2030" value={`${s.strandedBy2030}`} sub="within this decade" tone="amber" />
        <Stat
          label="Avg stranding year"
          value={s.avgStrandingYear != null ? `${s.avgStrandingYear}` : "—"}
          sub="of at-risk buildings"
        />
      </div>

      <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-[0.12em] text-text-faint">
                <th className="px-5 py-2 font-medium">Building</th>
                <th className="px-5 py-2 font-medium">Type</th>
                <th className="px-5 py-2 font-medium">Intensity</th>
                <th className="px-5 py-2 font-medium">Status</th>
                <th className="px-5 py-2 font-medium w-[180px]">
                  {PATHWAY_START_YEAR} → {PATHWAY_END_YEAR}
                </th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((r) => {
                const m = statusMeta(r)
                const b = r.building
                return (
                  <tr
                    key={b.fabric_building_id}
                    className="border-b border-border-subtle/50 last:border-b-0 hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-5 py-3">
                      <Link
                        href={`/buildings/${encodeURIComponent(b.fabric_building_id)}`}
                        className="text-text-primary hover:text-brand-emerald transition-colors font-medium"
                      >
                        {b.name}
                      </Link>
                      <div className="text-[11px] text-text-faint">
                        {b.city}, {b.country}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-text-muted text-xs uppercase tracking-wider">
                      {b.building_type.replace(/_/g, " ")}
                    </td>
                    <td className="px-5 py-3 tabular-nums text-text-muted">
                      {r.intensity != null ? `${fmtInt(r.intensity)} kgCO₂/m²·yr` : "—"}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border ${m.badge}`}
                      >
                        {m.label}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {r.status === "unknown" ? (
                        <span className="text-text-faint text-xs">—</span>
                      ) : (
                        <div className="relative h-1.5 w-full rounded-full bg-white/10">
                          <div
                            className={`absolute left-0 top-0 h-full rounded-full ${m.bar}`}
                            style={{ width: `${Math.max(3, Math.min(100, m.frac * 100))}%` }}
                          />
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function Stat({
  label,
  value,
  sub,
  tone,
}: {
  label: string
  value: string
  sub: string
  tone?: "red" | "amber"
}) {
  const valCls =
    tone === "red"
      ? "text-red-300"
      : tone === "amber"
        ? "text-amber-300"
        : "text-text-primary"
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 px-5 py-4">
      <div className="text-[11px] uppercase tracking-[0.12em] text-text-muted">
        {label}
      </div>
      <div className={`text-2xl font-semibold mt-1 tabular-nums ${valCls}`}>
        {value}
      </div>
      <div className="text-xs text-text-faint mt-0.5">{sub}</div>
    </div>
  )
}
