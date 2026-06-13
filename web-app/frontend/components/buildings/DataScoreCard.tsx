/**
 * DataScoreCard — the gamified Data Score + report-readiness map for a building.
 *
 * Shows a 0–100 Data Score ring (DATA COMPLETENESS, not a sustainability rating),
 * a per-report readiness map (🟢 ready · 🟡 partial/estimated · 🔴 needs data · n/a),
 * and the prioritised "add X → +N points → unlocks Y" next actions. Pure presentational
 * server component; consumes GET /buildings/{id}/readiness.
 */
import type { BuildingReadiness, ReadinessReport } from "@/lib/api/readiness"
import { cn } from "@/lib/utils"

function scoreColor(score: number): string {
  if (score >= 70) return "#1D9E75"
  if (score >= 40) return "#b45309"
  return "#b91c1c"
}

const STATUS: Record<ReadinessReport["status"], { dot: string; label: string }> = {
  ready: { dot: "bg-brand-emerald", label: "Ready" },
  partial: { dot: "bg-amber-400", label: "Partial" },
  locked: { dot: "bg-red-400", label: "Needs data" },
  not_applicable: { dot: "bg-white/25", label: "N/A" },
}

function Ring({ score }: { score: number }) {
  const color = scoreColor(score)
  return (
    <svg viewBox="0 0 36 36" className="h-24 w-24 shrink-0" role="img" aria-label={`Data score ${score} of 100`}>
      <path
        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
        fill="none"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth="3.4"
      />
      <path
        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
        fill="none"
        stroke={color}
        strokeWidth="3.4"
        strokeDasharray={`${Math.max(0, Math.min(100, score))}, 100`}
        strokeLinecap="round"
      />
      <text x="18" y="18.5" textAnchor="middle" fontSize="9" fontWeight="700" fill={color}>
        {score}
      </text>
      <text x="18" y="24.5" textAnchor="middle" fontSize="3.4" fill="#94a3b8">
        / 100
      </text>
    </svg>
  )
}

export function DataScoreCard({ readiness }: { readiness: BuildingReadiness }) {
  const reports = readiness.reports
  const counts = {
    ready: reports.filter((r) => r.status === "ready").length,
    partial: reports.filter((r) => r.status === "partial").length,
    locked: reports.filter((r) => r.status === "locked").length,
  }
  const actions = readiness.next_actions.slice(0, 3)

  return (
    <section aria-labelledby="data-score-heading" className="mt-8">
      <div className="flex items-baseline justify-between gap-3">
        <h2 id="data-score-heading" className="text-base font-semibold text-text-primary">
          Data score
        </h2>
        <p className="text-xs text-text-faint">More data → more reports &amp; savings insight</p>
      </div>

      <div className="mt-3 rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
        <div className="flex flex-wrap items-center gap-5">
          <Ring score={readiness.data_score} />
          <div className="min-w-0 flex-1">
            <p className="text-sm text-text-primary">
              <span className="font-semibold">{readiness.data_score}/100</span> data completeness
            </p>
            <p className="mt-0.5 text-xs text-text-muted">
              This measures how much data is on file (not how sustainable the building is). The
              more you add, the more reports unlock.
            </p>
            <div className="mt-2 flex flex-wrap gap-3 text-xs">
              <span className="inline-flex items-center gap-1.5 text-text-muted">
                <span className="h-2 w-2 rounded-full bg-brand-emerald" /> {counts.ready} ready
              </span>
              <span className="inline-flex items-center gap-1.5 text-text-muted">
                <span className="h-2 w-2 rounded-full bg-amber-400" /> {counts.partial} partial
              </span>
              <span className="inline-flex items-center gap-1.5 text-text-muted">
                <span className="h-2 w-2 rounded-full bg-red-400" /> {counts.locked} need data
              </span>
            </div>
          </div>
        </div>

        {/* readiness map */}
        <div className="mt-4 grid grid-cols-1 gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
          {reports.map((r) => {
            const s = STATUS[r.status]
            return (
              <div
                key={r.key}
                className="flex items-center gap-2 rounded-md border border-white/5 bg-white/[0.02] px-2.5 py-1.5"
                title={
                  r.status === "locked" && r.missing.length
                    ? `Needs: ${r.missing.join(", ")}`
                    : r.note || s.label
                }
              >
                <span className={cn("h-2 w-2 shrink-0 rounded-full", s.dot)} />
                <span className="flex-1 truncate text-xs text-text-primary">{r.label}</span>
                {r.status === "locked" && r.missing.length > 0 && (
                  <span className="shrink-0 text-[10px] text-red-300/80">+ {r.missing[0]}</span>
                )}
                {r.status === "partial" && (
                  <span className="shrink-0 text-[10px] text-amber-300/80">est.</span>
                )}
              </div>
            )
          })}
        </div>

        {/* next actions */}
        {actions.length > 0 && (
          <div className="mt-4 border-t border-border-subtle pt-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">
              Unlock more
            </p>
            <ul className="mt-1.5 space-y-1.5">
              {actions.map((a) => (
                <li key={a.key} className="flex items-start gap-2 text-xs" title={a.help}>
                  <span className="mt-0.5 shrink-0 rounded bg-brand-emerald/10 px-1.5 py-0.5 text-[10px] font-semibold text-brand-emerald">
                    +{a.points}
                  </span>
                  <span className="text-text-muted">
                    <span className="font-medium text-text-primary">Add {a.label}</span>
                    {a.unlocks.length > 0 && (
                      <span className="text-text-faint"> → unlocks {a.unlocks.join(", ")}</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  )
}
