/**
 * PortfolioScreeningPanel — the Tier-A engine across the WHOLE portfolio.
 *
 * Every building gets a screening EUI / cost band + confidence, even with zero
 * uploads, so a manager sees their full portfolio "lit up". Estimates fill the
 * gaps and sharpen to "Actual" as bills arrive. Pure presentational.
 */
import type { PortfolioEstimateRow, PortfolioEstimates } from "@/lib/api/estimation"

const CONF: Record<string, string> = {
  high: "text-emerald-300",
  medium: "text-amber-300",
  low: "text-amber-300",
  very_low: "text-orange-300",
}

function eur(n: number | null): string {
  if (n == null) return "—"
  return "€" + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}

function band(r: PortfolioEstimateRow): string {
  if (r.eui_point == null) return "—"
  return `${Math.round(r.eui_low ?? 0)}–${Math.round(r.eui_point)}–${Math.round(r.eui_high ?? 0)}`
}

export function PortfolioScreeningPanel({ data }: { data: PortfolioEstimates }) {
  if (!data || data.total === 0) return null
  const rows = [...data.rows].sort((a, b) => (b.eui_point ?? -1) - (a.eui_point ?? -1))

  return (
    <section className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-text-primary">Portfolio screening</h2>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="rounded border border-white/15 bg-white/5 px-1.5 py-0.5 text-text-muted">
            {data.scored}/{data.total} scored
          </span>
          <span className="rounded border border-amber-400/30 bg-amber-400/10 px-1.5 py-0.5 text-amber-300">
            {data.estimated_count} estimated
          </span>
          <span className="rounded border border-emerald-400/30 bg-emerald-400/10 px-1.5 py-0.5 text-emerald-300">
            {data.actual_count} from real data
          </span>
        </div>
      </div>
      <p className="mb-3 text-xs text-text-muted">
        Every building scored from whatever data it has — estimates fill the gaps and sharpen to
        “Actual” as bills are uploaded.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-[11px] uppercase tracking-wide text-text-faint">
            <tr>
              <th className="py-1.5 pr-3">Building</th>
              <th className="py-1.5 pr-3">Type</th>
              <th className="py-1.5 pr-3 text-right">EUI (kWh/m²·yr)</th>
              <th className="py-1.5 pr-3 text-right">Cost / yr</th>
              <th className="py-1.5 pr-3">Confidence</th>
              <th className="py-1.5">Basis</th>
            </tr>
          </thead>
          <tbody className="text-text-secondary">
            {rows.map((r) => (
              <tr key={r.building_id} className="border-t border-white/5">
                <td className="py-1.5 pr-3 text-text-primary">{r.name ?? "—"}</td>
                <td className="py-1.5 pr-3">{r.building_type ?? "—"}</td>
                <td className="py-1.5 pr-3 text-right tabular-nums">
                  {r.available ? band(r) : <span className="text-text-faint">not modeled</span>}
                </td>
                <td className="py-1.5 pr-3 text-right tabular-nums">{eur(r.annual_cost_eur_point)}</td>
                <td className={`py-1.5 pr-3 ${CONF[r.confidence] ?? "text-text-muted"}`}>
                  {r.available ? r.confidence : "—"}
                </td>
                <td className="py-1.5">
                  {r.available ? (
                    <span
                      className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${
                        r.basis === "actual"
                          ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-300"
                          : "border-amber-400/40 bg-amber-400/10 text-amber-300"
                      }`}
                    >
                      {r.basis}
                    </span>
                  ) : (
                    <span className="text-text-faint">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
