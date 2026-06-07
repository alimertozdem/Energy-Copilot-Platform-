/**
 * BuildingAdvisorPanel — the AI Energy Advisor side rail (server component).
 *
 * Layer 1 (this file): deterministic, data-grounded insights for ONE building,
 * computed by lib/insights/buildingAdvisor (no LLM, always available, demo-safe).
 * Each insight shows the issue, why it matters, an indicative range, its
 * confidence + assumption, and a deep-link that acts on it.
 *
 * Layer 2: the "Ask the advisor" button opens the building-focused copilot
 * (/copilot?building_id=…) — the conversational layer, live once an LLM provider
 * is configured. If it isn't, the link still lands on the copilot gracefully.
 */
import Link from "next/link"
import { ArrowRight, MessageCircle, Sparkles } from "lucide-react"

import type { Insight, InsightSeverity } from "@/lib/insights/buildingAdvisor"

const SEV: Record<InsightSeverity, { dot: string; chip: string; label: string }> = {
  action: { dot: "bg-red-400", chip: "border-red-400/30 text-red-300", label: "Act" },
  watch: { dot: "bg-amber-400", chip: "border-amber-400/30 text-amber-300", label: "Watch" },
  info: { dot: "bg-sky-400", chip: "border-sky-400/30 text-sky-300", label: "Note" },
  good: { dot: "bg-brand-emerald", chip: "border-brand-emerald/30 text-brand-emerald", label: "Good" },
}

function InsightCard({ insight }: { insight: Insight }) {
  const sev = SEV[insight.severity]
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4 transition-colors hover:border-brand-emerald/40">
      <div className="flex items-start gap-2.5">
        <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${sev.dot}`} aria-hidden />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-semibold leading-snug text-text-primary">{insight.title}</h3>
            {insight.metric && (
              <span className="shrink-0 rounded-md border border-border-subtle px-1.5 py-0.5 text-[10px] tabular-nums text-text-muted">
                {insight.metric}
              </span>
            )}
          </div>

          <p className="mt-1.5 text-xs leading-relaxed text-text-muted">{insight.detail}</p>

          {insight.range && (
            <p className="mt-2 text-sm font-semibold text-brand-emerald">{insight.range}</p>
          )}

          {insight.recommendation && (
            <p className="mt-2 flex gap-1.5 text-xs leading-relaxed text-text-primary/90">
              <span className="shrink-0 font-semibold text-brand-emerald">→</span>
              <span>{insight.recommendation}</span>
            </p>
          )}

          <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${sev.chip}`}>
              {sev.label}
            </span>
            <span className="text-[10px] text-text-faint">{insight.confidence} confidence</span>
          </div>

          {insight.assumption && (
            <p className="mt-2 text-[10px] leading-relaxed text-text-faint">{insight.assumption}</p>
          )}

          {insight.href && insight.cta && (
            <Link
              href={insight.href}
              className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-brand-emerald transition-colors hover:text-brand-mint"
            >
              {insight.cta}
              <ArrowRight className="h-3 w-3" aria-hidden />
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export function BuildingAdvisorPanel({
  insights,
  buildingId,
  buildingName,
}: {
  insights: Insight[]
  buildingId: string
  buildingName: string
}) {
  return (
    <aside className="lg:sticky lg:top-28 space-y-3" aria-label="AI Energy Advisor">
      {/* Header */}
      <div className="rounded-xl border border-brand-emerald/30 bg-gradient-to-br from-brand-emerald/[0.08] to-transparent p-4">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-emerald/15 ring-1 ring-brand-emerald/30">
            <Sparkles className="h-4 w-4 text-brand-emerald" aria-hidden />
          </span>
          <div className="min-w-0">
            <h2 className="font-display text-sm font-semibold text-text-primary">AI Energy Advisor</h2>
            <p className="truncate text-[11px] text-text-muted">Reading {buildingName}&rsquo;s live data</p>
          </div>
        </div>
      </div>

      {/* Insights */}
      {insights.length === 0 ? (
        <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
          <p className="text-sm font-semibold text-text-primary">No advice yet</p>
          <p className="mt-1 text-xs text-text-muted">
            Once this building is connected to live data, the advisor surfaces prioritised, costed
            actions here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {insights.map((ins) => (
            <InsightCard key={ins.id} insight={ins} />
          ))}
        </div>
      )}

      {/* Layer 2 — Ask the advisor (building-focused copilot) */}
      <Link
        href={`/copilot?building_id=${encodeURIComponent(buildingId)}`}
        className="group flex items-center gap-3 rounded-xl border border-brand-emerald/40 bg-brand-emerald/[0.06] p-3.5 transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
      >
        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-emerald/15">
          <MessageCircle className="h-4 w-4 text-brand-emerald" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-text-primary">Ask the advisor</p>
          <p className="text-[11px] text-text-muted">Chat about this building&rsquo;s energy</p>
        </div>
        <ArrowRight className="h-4 w-4 shrink-0 text-brand-emerald transition-transform group-hover:translate-x-0.5" aria-hidden />
      </Link>

      <p className="px-1 text-[10px] leading-relaxed text-text-faint">
        Indicative guidance from this building&rsquo;s data — verify against site conditions before
        investment decisions.
      </p>
    </aside>
  )
}
