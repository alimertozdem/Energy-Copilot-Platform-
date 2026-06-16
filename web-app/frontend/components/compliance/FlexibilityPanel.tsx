/**
 * FlexibilityPanel — indicative demand-side flexibility readiness for /compliance.
 *
 * Pure server component. Surfaces, per building, whether the asset inventory
 * (battery / solar / IoT) makes it ready to shift load to low-price / low-carbon
 * hours under dynamic tariffs + the EU Demand Response Network Code. Indicative,
 * asset-inventory based — not a metered load-shift or savings figure
 * (see lib/flexibility).
 */
import Link from "next/link"

import { InfoTip } from "@/components/ui/info-tip"

import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import { FLEX_META, summarizeFlex } from "@/lib/flexibility"

function rank(r: "ready" | "partial" | "limited"): number {
  return r === "ready" ? 0 : r === "partial" ? 1 : 2
}

export function FlexibilityPanel({
  buildings,
}: {
  buildings: PortfolioBuildingRow[]
}) {
  const s = summarizeFlex(buildings)
  const ordered = [...s.results].sort(
    (a, b) => rank(a.readiness) - rank(b.readiness)
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="inline-flex items-center gap-1.5 text-base font-semibold text-text-primary">
          Demand-side flexibility readiness
          <InfoTip term="flexibility" />
        </h2>
        <p className="text-xs text-text-muted mt-0.5">
          Which buildings can shift load to low-price / low-carbon hours under
          dynamic tariffs and the EU Demand Response Network Code (rules expected
          from ~2027).
        </p>
      </div>

      <div className="rounded-lg border border-violet-500/30 bg-violet-500/5 px-4 py-3 text-sm text-violet-200/90">
        <span className="font-medium">Indicative.</span> Flexibility is the
        ability to shift load in time, so &quot;ready&quot; needs both
        orchestration (IoT controls) and dispatchable storage (battery). On-site
        solar is generation, not a demand-shift mechanism, so it never makes a
        building ready on its own. Inferred from the asset inventory plus a typical
        shiftable-load share by type — not a metered load-shift or guaranteed-savings
        figure. Price/carbon-aware optimisation for battery sites is modelled in
        Battery Strategy.
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card label="Flexibility-ready" value={`${s.ready}`} tone="emerald" sub="battery + IoT controls" />
        <Card label="Partial" value={`${s.partial}`} tone="amber" sub="some enablers" />
        <Card label="Limited" value={`${s.limited}`} sub="meters / solar only" />
        <Card
          label="Avg shiftable load"
          value={s.avg_shiftable_pct != null ? `${s.avg_shiftable_pct} %` : "—"}
          sub="indicative, by type"
        />
      </div>

      <div className="rounded-2xl border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.015))] backdrop-blur-xl ring-1 ring-inset ring-white/[0.04] shadow-[0_10px_30px_-14px_rgba(0,0,0,0.6)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-[0.12em] text-text-faint">
                <th className="px-5 py-2 font-medium">Building</th>
                <th className="px-5 py-2 font-medium">Type</th>
                <th className="px-5 py-2 font-medium">Readiness</th>
                <th className="px-5 py-2 font-medium">Enablers</th>
                <th className="px-5 py-2 font-medium">Shiftable load</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((r) => {
                const m = FLEX_META[r.readiness]
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
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-semibold border ${m.badge}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${m.dot}`} />
                        {m.label}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-xs text-text-muted">
                      {r.enablers.length > 0 ? r.enablers.join(" · ") : "—"}
                    </td>
                    <td className="px-5 py-3 tabular-nums text-text-muted">
                      ~{r.shiftable_share_pct} %
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

function Card({
  label,
  value,
  sub,
  tone,
}: {
  label: string
  value: string
  sub: string
  tone?: "emerald" | "amber"
}) {
  const valCls =
    tone === "emerald"
      ? "text-emerald-300"
      : tone === "amber"
        ? "text-amber-300"
        : "text-text-primary"
  return (
    <div className="rounded-2xl border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.015))] backdrop-blur-xl ring-1 ring-inset ring-white/[0.04] shadow-[0_10px_30px_-14px_rgba(0,0,0,0.6)] px-5 py-4">
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
