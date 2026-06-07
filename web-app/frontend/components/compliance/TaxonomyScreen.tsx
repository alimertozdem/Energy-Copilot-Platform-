/**
 * TaxonomyScreen — EU Taxonomy alignment-indication section for /compliance.
 *
 * Pure server component. Screens each building against EU Taxonomy activity 7.7
 * (acquisition and ownership of buildings), climate-change-mitigation
 * substantial contribution, from existing /portfolio data. Indicative only and
 * never a "Taxonomy-aligned" claim — DNSH + minimum safeguards are out of scope
 * (see lib/taxonomy for the full energy-logic and assumptions).
 */
import Link from "next/link"

import { InfoTip } from "@/components/ui/info-tip"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import {
  TAXONOMY_ROUTES,
  summarizeTaxonomy,
  type BuildingTaxonomy,
  type TaxonomyRoute,
} from "@/lib/taxonomy"

const ROUTE_ORDER: TaxonomyRoute[] = [
  "epc_a",
  "top15_potential",
  "not_met",
  "epc_needed",
]

function pct(n: number): string {
  return `${Math.round(n * 100)}%`
}

export function TaxonomyScreen({
  buildings,
}: {
  buildings: PortfolioBuildingRow[]
}) {
  const s = summarizeTaxonomy(buildings)
  const ordered = [...s.results].sort(
    (a, b) =>
      TAXONOMY_ROUTES[b.route].weight - TAXONOMY_ROUTES[a.route].weight ||
      (b.building.floor_area_m2 || 0) - (a.building.floor_area_m2 || 0)
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="inline-flex items-center gap-1.5 text-base font-semibold text-text-primary">
          EU Taxonomy alignment
          <InfoTip term="eu_taxonomy" />
        </h2>
        <p className="text-xs text-text-muted mt-0.5">
          Indicative screen for activity 7.7 (acquisition and ownership of
          buildings), climate-change-mitigation substantial contribution.
        </p>
      </div>

      {/* Anti-greenwashing caveat — always visible */}
      <div className="rounded-lg border border-teal-500/30 bg-teal-500/5 px-4 py-3 text-sm text-teal-100/90">
        <span className="font-medium">Indication, not a verdict.</span> Based on
        EPC class only. The top-15% primary-energy route needs national
        verification, and full Taxonomy alignment also requires
        do-no-significant-harm (DNSH) and minimum-safeguards checks that are out
        of scope here. This screen shows a route, not a statement of Taxonomy
        alignment or compliance.
      </div>

      {/* Indicative share cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat
          label="On the EPC-A route"
          value={`${s.onRouteCount} / ${s.total}`}
          sub={`${pct(s.onRouteShare)} of buildings`}
          tone="emerald"
        />
        <Stat
          label="Floor area on route"
          value={pct(s.onRouteAreaShare)}
          sub="area-weighted proxy"
          tone="emerald"
        />
        <Stat
          label="Potential (top-15%)"
          value={`${s.counts.top15_potential}`}
          sub="EPC B–C, needs check"
          tone="teal"
        />
        <Stat
          label="EPC needed"
          value={`${s.counts.epc_needed}`}
          sub="no certificate on file"
          tone="sky"
        />
      </div>

      {/* Route legend */}
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        {ROUTE_ORDER.map((r) => {
          const m = TAXONOMY_ROUTES[r]
          return (
            <div
              key={r}
              className="inline-flex items-center gap-2 text-xs text-text-muted"
            >
              <span className={`size-2 rounded-full ${m.dotClass}`} />
              {m.label}
              <span className="text-text-faint">· {s.counts[r]}</span>
            </div>
          )
        })}
      </div>

      {/* Per-building table */}
      <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-[0.12em] text-text-faint">
                <th className="px-5 py-2 font-medium">Building</th>
                <th className="px-5 py-2 font-medium">Type</th>
                <th className="px-5 py-2 font-medium">EPC</th>
                <th className="px-5 py-2 font-medium">Indication</th>
                <th className="px-5 py-2 font-medium">Notes</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((r) => (
                <TaxRow key={r.building.fabric_building_id} r={r} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function TaxRow({ r }: { r: BuildingTaxonomy }) {
  const m = TAXONOMY_ROUTES[r.route]
  const b = r.building
  const bacsNote = r.bacsRelevant
    ? r.bacsMet
      ? " Large non-residential: energy-performance monitoring in place (IoT)."
      : " Large non-residential: BACS/monitoring evidence required (>290 kW)."
    : ""
  return (
    <tr className="border-b border-border-subtle/50 last:border-b-0 hover:bg-white/[0.02] transition-colors">
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
          className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border ${m.badgeClass}`}
        >
          {b.epc_class ?? "—"}
        </span>
      </td>
      <td className="px-5 py-3">
        <span className={`text-xs font-medium ${m.textClass}`}>{m.label}</span>
      </td>
      <td className="px-5 py-3 text-xs text-text-muted max-w-[320px]">
        {r.reason}
        {bacsNote ? <span className="text-text-faint">{bacsNote}</span> : null}
      </td>
    </tr>
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
  tone?: "emerald" | "teal" | "sky"
}) {
  const valCls =
    tone === "emerald"
      ? "text-emerald-300"
      : tone === "teal"
        ? "text-teal-300"
        : tone === "sky"
          ? "text-sky-300"
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
