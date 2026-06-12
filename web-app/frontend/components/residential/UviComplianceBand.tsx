/**
 * UviComplianceBand — the residential "why now" wedge (R1).
 *
 * Server component. Surfaces HKVO/EED monthly-consumption-info (UVI) readiness
 * across the residential portfolio: a Jan-2027 deadline countdown, how many
 * buildings are ready vs at-risk, the indicative §12 3% penalty exposure, and a
 * per-building work queue (at-risk first). Reads the server-authoritative
 * /residential/uvi-compliance. Honest footnote — decision-support, not legal advice.
 */
import { InfoTip } from "@/components/ui/info-tip"
import type { UviComplianceResponse } from "@/lib/api/residentialManager"

const MONTHS = [
  "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

const STATUS_META: Record<string, { label: string; cls: string }> = {
  ready: { label: "Ready", cls: "border-brand-emerald/30 bg-brand-emerald/10 text-brand-emerald" },
  partial: { label: "Partial", cls: "border-amber-400/30 bg-amber-400/10 text-amber-300" },
  at_risk: { label: "At risk", cls: "border-red-500/30 bg-red-500/10 text-red-300" },
}

function eur(n: number | null): string {
  if (n === null || n === undefined) return "—"
  return "€" + Math.round(n).toLocaleString("en-US")
}

export function UviComplianceBand({ data }: { data: UviComplianceResponse }) {
  if (data.rows.length === 0) return null

  const deadline = new Date(data.deadline)
  const days = Math.max(
    0,
    Math.ceil((deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  )

  const stats = [
    { label: "Buildings ready", value: `${data.buildings_ready}/${data.buildings_total}`, tone: "text-brand-emerald" },
    { label: "At risk", value: String(data.buildings_at_risk), tone: data.buildings_at_risk > 0 ? "text-red-300" : "text-text-primary" },
    { label: "Penalty exposure", value: eur(data.total_penalty_exposure_eur), tone: "text-text-primary" },
    { label: "Days to mandate", value: String(days), tone: "text-text-primary" },
  ]

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="inline-flex items-center gap-1.5 text-sm font-semibold text-text-primary">
            UVI compliance readiness
            <InfoTip term="uvi" />
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Monthly consumption information (HKVO §6a) is mandatory from{" "}
            {data.deadline}. Breaching the duty lets residents cut 3% of their heating cost (§12).
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-1 text-[11px] font-medium text-amber-300">
          {days} days to mandate
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2.5">
            <div className="text-[10px] uppercase tracking-wider text-text-faint">{s.label}</div>
            <div className={`mt-0.5 text-lg font-semibold ${s.tone}`}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-text-muted">
              <th className="px-3 py-2 font-medium">Building</th>
              <th className="px-3 py-2 font-medium text-right">Coverage</th>
              <th className="px-3 py-2 font-medium text-right">Latest UVI</th>
              <th className="px-3 py-2 font-medium text-right">Penalty exposure</th>
              <th className="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {data.rows.map((r) => {
              const meta = STATUS_META[r.status] ?? STATUS_META.partial
              const latest =
                r.latest_year && r.latest_month
                  ? `${MONTHS[r.latest_month] ?? r.latest_month} ${r.latest_year}`
                  : "—"
              const cov =
                r.coverage_pct === null
                  ? "—"
                  : `${Math.round(r.coverage_pct * 100)}% (${r.units_covered}/${r.total_units})`
              return (
                <tr key={r.fabric_building_id} className="hover:bg-white/5">
                  <td className="px-3 py-2 text-text-primary">{r.name}</td>
                  <td className="px-3 py-2 text-right text-text-muted">{cov}</td>
                  <td className="px-3 py-2 text-right text-text-muted">{latest}</td>
                  <td className="px-3 py-2 text-right text-text-muted">{eur(r.penalty_exposure_eur)}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-medium ${meta.cls}`}>
                      {meta.label}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-text-faint">{data.note}</p>
    </section>
  )
}
