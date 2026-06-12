/**
 * FinancingView — portfolio subsidy-capture view (server component).
 *
 * Maps each recommended measure to its likely public programme (KfW 458 / BAFA
 * BEG EM / KfW 261) and an INDICATIVE grant, from the recommendation catalog
 * (/actions). Support, not advice — see the banner + lib/finance/subsidy.ts.
 */
import Link from "next/link"

import type { ActionItem } from "@/lib/api/actions"
import { InfoTip } from "@/components/ui/info-tip"
import type { TermKey } from "@/lib/glossary"
import { estimateSubsidy } from "@/lib/finance/subsidy"

function eur(n: number | null): string {
  if (n === null || Number.isNaN(n)) return "—"
  if (Math.abs(n) >= 10000) {
    return "€" + new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n)
  }
  return "€" + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}

function Card({
  label,
  value,
  hint,
  tone,
  term,
}: {
  label: string
  value: string
  hint?: string
  tone?: "good"
  term?: TermKey
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-elevated/40 p-4">
      <p className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
        {label}
        {term && <InfoTip term={term} />}
      </p>
      <p className={`mt-1.5 text-2xl font-semibold ${tone === "good" ? "text-brand-emerald" : "text-text-primary"}`}>
        {value}
      </p>
      {hint && <p className="mt-1 text-[11px] text-text-faint">{hint}</p>}
    </div>
  )
}

export function FinancingView({ actions }: { actions: ActionItem[] }) {
  const rows = actions
    .map((a) => {
      const capex = a.net_capex_eur ?? a.capex_eur ?? null
      return { a, capex, sub: estimateSubsidy(a.action_type, capex) }
    })
    .filter((r) => r.sub.eligible && r.sub.grantEur != null)
    .sort((x, y) => (y.sub.grantEur ?? 0) - (x.sub.grantEur ?? 0))

  const totalGrant = rows.reduce((s, r) => s + (r.sub.grantEur ?? 0), 0)
  const totalCapex = rows.reduce((s, r) => s + (r.capex ?? 0), 0)
  const byProgram = new Map<string, number>()
  for (const r of rows) {
    byProgram.set(r.sub.program, (byProgram.get(r.sub.program) ?? 0) + (r.sub.grantEur ?? 0))
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-xs leading-relaxed text-amber-200/90">
        Indicative subsidy-application <span className="font-semibold">support</span> — not financial advice.
        Programmes (KfW 458 · BAFA BEG EM · KfW 261) and bonus eligibility change; verify against the live
        programme. Crucially, <span className="font-semibold">apply before signing any contract</span> —
        signing first forfeits the subsidy.
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card label="Indicative subsidy" value={eur(totalGrant)} hint="across eligible measures" tone="good" term="subsidy" />
        <Card label="Eligible measures" value={String(rows.length)} />
        <Card label="Capex (eligible)" value={eur(totalCapex)} />
        <Card label="Net after subsidy" value={eur(totalCapex - totalGrant)} />
      </div>

      {byProgram.size > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] uppercase tracking-wider text-text-faint">By programme</span>
          {[...byProgram.entries()].map(([p, g]) => (
            <span key={p} className="rounded-md border border-border-subtle bg-bg-elevated/40 px-3 py-1 text-xs text-text-muted">
              {p}: <span className="font-medium text-brand-emerald">{eur(g)}</span>
            </span>
          ))}
          <Link
            href="/financing/report"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-auto inline-flex items-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
          >
            Export application pack (PDF)
          </Link>
        </div>
      )}

      {rows.length === 0 ? (
        <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-6">
          <p className="text-sm font-semibold text-text-primary">No grant-eligible measures yet.</p>
          <p className="mt-1 text-sm text-text-muted">
            Heating, envelope and controls recommendations with a capex estimate map to KfW/BAFA
            programmes here. Solar PV is funded separately (EEG).
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border-subtle bg-bg-elevated/40">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-wider text-text-muted">
                <th className="px-4 py-3 font-semibold">Measure</th>
                <th className="px-4 py-3 font-semibold">Building</th>
                <th className="px-4 py-3 font-semibold">Programme</th>
                <th className="px-4 py-3 text-right font-semibold">Rate</th>
                <th className="px-4 py-3 text-right font-semibold">Capex</th>
                <th className="px-4 py-3 text-right font-semibold">Indicative grant</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-border-subtle/60 text-text-primary/90">
                  <td className="px-4 py-2.5">
                    <div className="font-medium">{r.a.title ?? r.a.action_type ?? "Measure"}</div>
                    <div className="text-[11px] text-text-faint">{r.sub.scheme}</div>
                  </td>
                  <td className="px-4 py-2.5 text-text-muted">{r.a.building_name}</td>
                  <td className="px-4 py-2.5">
                    <span className="rounded-md border border-brand-emerald/30 bg-brand-emerald/5 px-2 py-0.5 text-xs text-brand-emerald">
                      {r.sub.program}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-text-muted">
                    {r.sub.ratePct}%
                    {r.sub.maxRatePct > r.sub.ratePct ? <span className="text-text-faint">–{r.sub.maxRatePct}%</span> : null}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{eur(r.capex)}</td>
                  <td className="px-4 py-2.5 text-right font-semibold tabular-nums text-brand-emerald">{eur(r.sub.grantEur)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-[11px] leading-relaxed text-text-faint">
        Indicative grants use each programme&rsquo;s base rate on capex capped per unit (KfW 458 ~€30k,
        BAFA BEG EM €30k). Actual amounts depend on bonuses (speed, income, iSFP), unit counts and the
        live programme. Treat as a planning estimate; a financing partner referral is not a lending offer.
      </p>
    </div>
  )
}
