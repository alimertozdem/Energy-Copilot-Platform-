/**
 * SubsidyPanel — concrete BAFA/KfW programme mapping + iSFP roadmap for the
 * retrofit measures. SUPPORT, NOT ADVICE: reuses lib/finance/subsidy (the single
 * source for German programme rates). We surface the PROGRAMME + RATE + process
 * (iSFP +5%, apply-before-signing), not a EUR grant — the per-unit caps make a
 * EUR figure unreliable for commercial stock, and the package already shows the
 * net-of-subsidy CapEx.
 */
import { Landmark } from "lucide-react"

import { estimateSubsidy } from "@/lib/finance/subsidy"
import type { HeatingMeasure } from "@/lib/api/heating"

/** Map a measure key to a clean type for the subsidy classifier (label text can
 *  mis-match, e.g. "hydraulic balancing + heating curve" should be controls, not
 *  renewable-heating). */
function typeForKey(key: string): string {
  if (key.startsWith("fabric_")) return "envelope insulation"
  if (key === "heat_pump") return "heat pump"
  if (key === "operational") return "controls"
  return "other"
}

type Group = {
  program: string
  scheme: string
  ratePct: number
  maxRatePct: number
  note: string
  measures: string[]
}

export function SubsidyPanel({ measures }: { measures: HeatingMeasure[] }) {
  const eligible = measures
    .filter((m) => m.capex_gross > 0)
    .map((m) => ({ m, sub: estimateSubsidy(typeForKey(m.key), m.capex_gross) }))
    .filter((r) => r.sub.eligible)
  if (eligible.length === 0) return null

  const byProgram = new Map<string, Group>()
  for (const { m, sub } of eligible) {
    const g =
      byProgram.get(sub.program) ??
      { program: sub.program, scheme: sub.scheme, ratePct: sub.ratePct, maxRatePct: sub.maxRatePct, note: sub.note, measures: [] }
    g.measures.push(m.label)
    byProgram.set(sub.program, g)
  }
  const groups = [...byProgram.values()]

  return (
    <section>
      <div className="mb-2 flex items-center gap-2">
        <Landmark className="h-4 w-4 text-brand-emerald" aria-hidden />
        <h2 className="text-sm font-semibold text-text-primary">Subsidy &amp; funding</h2>
      </div>
      <div className="space-y-2">
        {groups.map((g) => (
          <div key={g.program} className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
            <div className="flex flex-wrap items-baseline justify-between gap-x-2">
              <span className="text-sm font-medium text-text-primary">
                {g.program} — {g.scheme}
              </span>
              <span className="text-xs font-semibold tabular-nums text-brand-emerald">
                {g.ratePct}
                {g.maxRatePct > g.ratePct ? `–${g.maxRatePct}` : ""}%
              </span>
            </div>
            <div className="mt-0.5 text-[11px] text-text-faint">{g.measures.join(" · ")}</div>
            <div className="mt-0.5 text-[11px] text-text-faint">{g.note}</div>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-text-faint">
        An <span className="text-text-muted">individueller Sanierungsfahrplan (iSFP)</span> — an
        Energieberater-certified version of the staged roadmap above — adds{" "}
        <span className="text-brand-emerald">+5%</span> to BAFA envelope measures and raises the
        eligible-cost cap. Critical:{" "}
        <span className="text-amber-300">always apply before signing a contract</span> — signing
        first forfeits the grant. Support, not advice — verify against the live programme.
      </p>
    </section>
  )
}
