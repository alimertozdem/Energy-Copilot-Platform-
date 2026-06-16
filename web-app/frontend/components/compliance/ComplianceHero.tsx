/**
 * ComplianceHero — the at-a-glance scorecard atop /compliance (design 2026-06-16).
 *
 * Summarises all five compliance dimensions in one glass panel so the page leads
 * with a verdict, not a table: MEPS renovation priority, CRREM stranding, EU
 * Taxonomy route, flexibility readiness and ESRS-E1 status. Each cell links to
 * its section. Scoped by the building slicer (the page passes already-filtered
 * counts), and paired with the bespoke ComplianceMotif. Server component.
 *
 * KPI framing (energy-kpi-designer): every cell carries a label, a value, and a
 * one-line interpretation; values are counts/shares from existing portfolio +
 * GHG data — no fake precision, indicative throughout.
 */
import { ComplianceMotif } from "@/components/motifs/ComplianceMotif"
import { GlassCard } from "@/components/ui/glass-card"

export type ScoreTone = "emerald" | "amber" | "red" | "teal" | "sky" | "neutral"

export type ScoreItem = {
  /** Anchor id of the section this cell summarises (e.g. "meps"). */
  href: string
  label: string
  value: string
  sub: string
  tone?: ScoreTone
}

const TONE_TEXT: Record<ScoreTone, string> = {
  emerald: "text-emerald-300",
  amber: "text-amber-300",
  red: "text-red-300",
  teal: "text-teal-300",
  sky: "text-sky-300",
  neutral: "text-text-primary",
}

const TONE_DOT: Record<ScoreTone, string> = {
  emerald: "bg-emerald-400",
  amber: "bg-amber-400",
  red: "bg-red-400",
  teal: "bg-teal-400",
  sky: "bg-sky-400",
  neutral: "bg-text-muted",
}

export function ComplianceHero({
  title,
  context,
  items,
  accent = "#0D9488",
}: {
  title: string
  context: string
  items: ScoreItem[]
  accent?: string
}) {
  return (
    <GlassCard accent={accent} className="p-6 md:p-7">
      <div className="flex items-start justify-between gap-6">
        <div className="min-w-0">
          <h2 className="font-display text-lg font-semibold text-text-primary">
            {title}
          </h2>
          <p className="mt-1 max-w-xl text-sm text-text-muted">{context}</p>
        </div>
        {/* bespoke motif — hidden on small screens to keep the scorecard legible */}
        <ComplianceMotif
          accent={accent}
          className="hidden h-24 w-44 shrink-0 lg:block"
        />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-px overflow-hidden rounded-xl bg-white/[0.06] sm:grid-cols-3 lg:grid-cols-5">
        {items.map((it) => {
          const tone = it.tone ?? "neutral"
          return (
            <a
              key={it.href}
              href={it.href}
              className="group flex flex-col gap-1 bg-bg-base/40 px-4 py-3.5 transition-colors hover:bg-white/[0.04]"
            >
              <span className="inline-flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.12em] text-text-muted">
                <span className={`size-1.5 rounded-full ${TONE_DOT[tone]}`} />
                {it.label}
              </span>
              <span
                className={`text-2xl font-semibold tabular-nums ${TONE_TEXT[tone]}`}
              >
                {it.value}
              </span>
              <span className="text-[11px] leading-snug text-text-muted">
                {it.sub}
              </span>
            </a>
          )
        })}
      </div>
    </GlassCard>
  )
}
