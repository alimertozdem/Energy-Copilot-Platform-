/**
 * WizardScorePreview — the live Data Score strip shown during onboarding.
 *
 * Pure presentational. Receives a BuildingReadiness computed client-side by
 * previewReadiness(data) and renders a compact ring + "reports ready / need
 * data" counts + the single biggest next unlock. It makes the score visibly
 * climb as the user fills the form — the gamified loop — without claiming the
 * building is "sustainable" (this is data completeness only).
 */
import type { BuildingReadiness } from "@/lib/api/readiness"

function scoreColor(score: number): string {
  if (score >= 70) return "#1D9E75"
  if (score >= 40) return "#b45309"
  return "#b91c1c"
}

function MiniRing({ score }: { score: number }) {
  const color = scoreColor(score)
  return (
    <svg viewBox="0 0 36 36" className="h-12 w-12 shrink-0" role="img" aria-label={`Data score ${score} of 100`}>
      <path
        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
        fill="none"
        stroke="rgba(255,255,255,0.12)"
        strokeWidth="3.6"
      />
      <path
        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
        fill="none"
        stroke={color}
        strokeWidth="3.6"
        strokeDasharray={`${Math.max(0, Math.min(100, score))}, 100`}
        strokeLinecap="round"
        style={{ transition: "stroke-dasharray 0.5s ease, stroke 0.5s ease" }}
      />
      <text x="18" y="21" textAnchor="middle" fontSize="11" fontWeight="700" fill={color}>
        {score}
      </text>
    </svg>
  )
}

export function WizardScorePreview({ preview }: { preview: BuildingReadiness }) {
  const ready = preview.reports.filter((r) => r.status === "ready").length
  const needData = preview.reports.filter((r) => r.status === "locked").length
  const top = preview.next_actions[0]

  return (
    <div className="mb-6 flex items-center gap-3 rounded-xl border border-border-subtle bg-white/[0.02] px-3.5 py-2.5">
      <MiniRing score={preview.data_score} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
          <span className="text-sm font-semibold text-text-primary">{preview.data_score}/100</span>
          <span className="text-xs text-text-faint">data score · {ready} report{ready === 1 ? "" : "s"} ready, {needData} need data</span>
        </div>
        {top ? (
          <p className="mt-0.5 truncate text-xs text-text-muted" title={top.help}>
            <span className="font-medium text-brand-emerald">+{top.points}</span>{" "}
            add {top.label}
            {top.unlocks.length > 0 && (
              <span className="text-text-faint"> → unlocks {top.unlocks.slice(0, 2).join(", ")}{top.unlocks.length > 2 ? "…" : ""}</span>
            )}
          </p>
        ) : (
          <p className="mt-0.5 text-xs text-brand-emerald">All available data captured — nice.</p>
        )}
      </div>
    </div>
  )
}
