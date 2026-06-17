/**
 * ComplianceScreeningSection — extends compliance COVERAGE to the buildings the
 * measured-data radar can't assess yet.
 *
 * Uses the Tier-A estimate to show a likely energy class + an indicative EPBD/MEPS
 * watch from type / age / climate. Clearly labelled "estimate": it COMPLEMENTS,
 * never replaces, the measured / connected-data sections above. No gold compliance
 * number is touched. Pure presentational.
 */
import type { PortfolioEstimates } from "@/lib/api/estimation"

// German GEG Energieausweis final-energy classes (kWh/m²·yr) — public standard
// (GEG Anlage 10). Residential basis; non-residential mapping is approximate.
const GEG: { cls: string; max: number }[] = [
  { cls: "A+", max: 30 },
  { cls: "A", max: 50 },
  { cls: "B", max: 75 },
  { cls: "C", max: 100 },
  { cls: "D", max: 130 },
  { cls: "E", max: 160 },
  { cls: "F", max: 200 },
  { cls: "G", max: 250 },
  { cls: "H", max: Number.POSITIVE_INFINITY },
]
function euiClass(eui: number): string {
  return GEG.find((c) => eui <= c.max)?.cls ?? "H"
}
// Worst bands ~ EPBD MEPS renovation scope (indicative; exact thresholds depend
// on national transposition + a real EPC).
const MEPS = new Set(["F", "G", "H"])

export function ComplianceScreeningSection({ data }: { data: PortfolioEstimates }) {
  const rows = data.rows.filter(
    (r) => r.available && r.basis === "estimated" && r.eui_point != null
  )
  if (rows.length === 0) return null

  const enriched = rows
    .map((r) => ({ r, cls: euiClass(r.eui_point as number) }))
    .sort((a, b) => (b.r.eui_point ?? 0) - (a.r.eui_point ?? 0))
  const mepsCount = enriched.filter((e) => MEPS.has(e.cls)).length

  return (
    <div className="rounded-2xl border border-amber-400/20 bg-amber-400/[0.03] p-5">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-text-primary">Screening coverage (estimates)</h3>
        <span className="rounded border border-amber-400/40 bg-amber-400/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-300">
          {rows.length} estimated · {mepsCount} MEPS watch
        </span>
      </div>
      <p className="mb-3 text-xs text-text-muted">
        The sections above score buildings from measured / connected data. These are screening
        estimates for the rest — a likely energy class from type, age and climate. Confirm with a real
        EPC or audit before acting; indicative, not a legal verdict.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-[11px] uppercase tracking-wide text-text-faint">
            <tr>
              <th className="py-1.5 pr-3">Building</th>
              <th className="py-1.5 pr-3">Type</th>
              <th className="py-1.5 pr-3 text-right">Est. EUI</th>
              <th className="py-1.5 pr-3">Est. class</th>
              <th className="py-1.5">EPBD / MEPS</th>
            </tr>
          </thead>
          <tbody className="text-text-secondary">
            {enriched.map(({ r, cls }) => {
              const watch = MEPS.has(cls)
              return (
                <tr key={r.building_id} className="border-t border-white/5">
                  <td className="py-1.5 pr-3 text-text-primary">{r.name ?? "—"}</td>
                  <td className="py-1.5 pr-3">{r.building_type ?? "—"}</td>
                  <td className="py-1.5 pr-3 text-right tabular-nums">
                    {Math.round(r.eui_point as number)}
                    <span className="ml-1 text-text-faint">kWh/m²·yr</span>
                  </td>
                  <td className="py-1.5 pr-3">
                    <span
                      className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${
                        watch
                          ? "border-orange-400/40 bg-orange-400/10 text-orange-300"
                          : "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                      }`}
                    >
                      ~{cls}
                    </span>
                  </td>
                  <td className="py-1.5 text-[11px]">
                    {watch ? (
                      <span className="text-orange-300">Likely renovation priority</span>
                    ) : (
                      <span className="text-text-faint">Not flagged</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[11px] text-text-faint">
        Estimated class uses the German Energieausweis kWh/m²·yr scale (residential basis);
        non-residential mapping is approximate. EPBD/MEPS scope is indicative — exact thresholds depend
        on national transposition and a real EPC.
      </p>
    </div>
  )
}
