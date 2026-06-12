/**
 * MepsRadar — portfolio renovation / MEPS-readiness overview for /compliance.
 *
 * Pure server component: takes a ComplianceSummary (computed from existing
 * /portfolio building data) and renders the band distribution, EPBD milestone
 * context, and a priority-buildings table. Indicative only (see lib/compliance).
 */
import Link from "next/link"

import { InfoTip } from "@/components/ui/info-tip"

import { RISK_BANDS, type ComplianceSummary, type RiskBand } from "@/lib/compliance"

const BAND_ORDER: RiskBand[] = ["high", "watch", "epc_needed", "lower"]

function pct(n: number, total: number): string {
  if (total === 0) return "0%"
  return `${Math.round((n / total) * 100)}%`
}

export function MepsRadar({ summary }: { summary: ComplianceSummary }) {
  const { total, counts, priority } = summary

  return (
    <div className="space-y-8">
      <div>
        <h2 className="inline-flex items-center gap-1.5 text-base font-semibold text-text-primary">
          Renovation and MEPS risk
          <InfoTip term="meps" />
        </h2>
      </div>
      {/* Indicative disclaimer */}
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-200/90">
        <span className="font-medium">Indicative view.</span> National minimum
        energy performance standards (MEPS) under the revised EPBD are not yet
        finalised (transposition due May 2026; non-residential MEPS by 2027).
        These bands are based on EPC class and measured energy use — a planning
        signal, not a compliance verdict.
      </div>

      {/* Band distribution */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {BAND_ORDER.map((band) => {
          const meta = RISK_BANDS[band]
          const n = counts[band]
          return (
            <div
              key={band}
              className="rounded-xl border border-border-subtle bg-bg-elevated/40 px-5 py-4"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className={`size-2 rounded-full ${meta.dotClass}`} />
                <span className="text-[11px] uppercase tracking-[0.12em] text-text-muted">
                  {meta.label}
                </span>
              </div>
              <div className={`text-3xl font-semibold tabular-nums ${meta.textClass}`}>
                {n}
              </div>
              <div className="text-xs text-text-faint mt-0.5">
                {pct(n, total)} of portfolio
              </div>
              <div className="text-[11px] text-text-faint mt-2 leading-snug">
                {meta.blurb}
              </div>
            </div>
          )
        })}
      </div>

      {/* EPBD milestone context */}
      <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
        <h3 className="inline-flex items-center gap-1.5 text-sm font-medium text-text-primary mb-1">
          EPBD renovation milestones
          <InfoTip term="epbd" />
        </h3>
        <p className="text-xs text-text-muted leading-relaxed">
          The revised EPBD asks member states to renovate the worst-performing{" "}
          <span className="text-text-primary font-medium">16%</span> of the
          non-residential stock by{" "}
          <span className="text-text-primary font-medium">2030</span> and{" "}
          <span className="text-text-primary font-medium">26%</span> by{" "}
          <span className="text-text-primary font-medium">2033</span>, with
          national MEPS set by 2027. Buildings in the{" "}
          <span className="text-red-300 font-medium">Renovation priority</span>{" "}
          band are the most likely to fall in scope.
        </p>
      </div>

      {/* Priority buildings */}
      <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 overflow-hidden">
        <div className="px-5 py-3 border-b border-border-subtle">
          <h3 className="text-sm font-medium text-text-primary">
            Priority buildings
          </h3>
          <p className="text-xs text-text-muted mt-0.5">
            Worst EPC bands and buildings without an EPC, highest risk first.
          </p>
        </div>
        {priority.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-text-muted">
            No renovation-priority buildings — your rated buildings sit in EPC
            A–E and have an EPC on file.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-[0.12em] text-text-faint">
                  <th className="px-5 py-2 font-medium">Building</th>
                  <th className="px-5 py-2 font-medium">Type</th>
                  <th className="px-5 py-2 font-medium">EPC</th>
                  <th className="px-5 py-2 font-medium">EUI</th>
                  <th className="px-5 py-2 font-medium">Why</th>
                </tr>
              </thead>
              <tbody>
                {priority.map(({ building: b, band, reason }) => {
                  const meta = RISK_BANDS[band]
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
                          className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border ${meta.badgeClass}`}
                        >
                          {b.epc_class ?? "—"}
                        </span>
                      </td>
                      <td className="px-5 py-3 tabular-nums text-text-muted">
                        {b.eui_kwh_m2_yr != null
                          ? `${Math.round(b.eui_kwh_m2_yr)} kWh/m²·yr`
                          : "—"}
                      </td>
                      <td className="px-5 py-3 text-xs text-text-muted max-w-[280px]">
                        {reason}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
