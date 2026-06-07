"use client"

/**
 * AlertsFilterChips — severity chips + two visibility toggles.
 *
 * Filter dimensions:
 *   1. Severity: All / Critical / High / Medium / Low  (server-side re-fetch).
 *   2. Resolution toggle: open (unresolved) vs resolved (server-side re-fetch).
 *   3. Handled toggle: reveal acknowledged / dismissed rows (client-side).
 *
 * The severity + resolution controls drive a backend re-fetch in AlertsShell,
 * so the chip counts come from the backend severity_counts (a GROUP BY over the
 * full set) and stay accurate under the row cap. While a re-fetch is in flight
 * the controls are disabled (`loading`).
 *
 * Chip counts are supplied by the parent for the current resolution scope, so
 * each chip shows how many of that severity exist in the scope being viewed.
 */
import { Check, CheckCheck, Eye, EyeOff } from "lucide-react"

import { cn } from "@/lib/utils"

import type { AlertSeverity } from "@/lib/api/alerts"

import { SEVERITY_ORDER, SEVERITY_VISUALS } from "./SeverityBadge"

export type SeverityFilter = AlertSeverity | "all"

export type ChipCounts = {
  all: number
  CRITICAL: number
  HIGH: number
  MEDIUM: number
  LOW: number
}

type AlertsFilterChipsProps = {
  activeSeverity: SeverityFilter
  chipCounts: ChipCounts
  showResolved: boolean
  showHandled: boolean
  loading?: boolean
  onSeverityChange: (next: SeverityFilter) => void
  onToggleResolved: (next: boolean) => void
  onToggleHandled: (next: boolean) => void
}

export function AlertsFilterChips({
  activeSeverity,
  chipCounts,
  showResolved,
  showHandled,
  loading = false,
  onSeverityChange,
  onToggleResolved,
  onToggleHandled,
}: AlertsFilterChipsProps) {
  const items: {
    value: SeverityFilter
    label: string
    count: number
    dotClass: string
    activeClass: string
  }[] = [
    {
      value: "all",
      label: "All",
      count: chipCounts.all,
      dotClass: "bg-white/50",
      activeClass: "bg-white/15 text-white border-white/30",
    },
    ...SEVERITY_ORDER.map((s) => ({
      value: s as SeverityFilter,
      label: SEVERITY_VISUALS[s].label,
      count: chipCounts[s],
      dotClass: SEVERITY_VISUALS[s].dotClass,
      activeClass: SEVERITY_VISUALS[s].badgeClass,
    })),
  ]

  return (
    <div className={cn("flex flex-wrap items-center gap-2", loading && "opacity-70")}>
      {items.map((it) => {
        const isActive = activeSeverity === it.value
        return (
          <button
            key={it.value}
            type="button"
            onClick={() => onSeverityChange(it.value)}
            disabled={loading}
            aria-pressed={isActive}
            className={cn(
              "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[12px] font-medium",
              "border transition-all",
              isActive
                ? it.activeClass
                : "bg-white/[0.03] border-white/10 text-white/60 hover:text-white/90 hover:border-white/25",
              loading && "cursor-not-allowed"
            )}
          >
            <span
              className={cn(
                "w-1.5 h-1.5 rounded-full transition-opacity",
                it.dotClass,
                !isActive && "opacity-50"
              )}
              aria-hidden
            />
            <span>{it.label}</span>
            <span
              className={cn("tabular-nums text-[11px]", isActive ? "" : "text-white/40")}
            >
              {it.count}
            </span>
          </button>
        )
      })}

      <div className="h-5 w-px bg-white/10 mx-1" aria-hidden />

      <button
        type="button"
        onClick={() => onToggleResolved(!showResolved)}
        disabled={loading}
        aria-pressed={showResolved}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium border transition-all",
          showResolved
            ? "bg-emerald-500/15 text-emerald-200 border-emerald-500/30"
            : "bg-white/[0.03] border-white/10 text-white/60 hover:text-white/90 hover:border-white/25",
          loading && "cursor-not-allowed"
        )}
      >
        {showResolved ? (
          <Eye className="w-3.5 h-3.5" aria-hidden />
        ) : (
          <EyeOff className="w-3.5 h-3.5" aria-hidden />
        )}
        <span>{showResolved ? "Showing resolved" : "Unresolved only"}</span>
      </button>

      <button
        type="button"
        onClick={() => onToggleHandled(!showHandled)}
        disabled={loading}
        aria-pressed={showHandled}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[12px] font-medium border transition-all",
          showHandled
            ? "bg-sky-500/15 text-sky-200 border-sky-500/30"
            : "bg-white/[0.03] border-white/10 text-white/60 hover:text-white/90 hover:border-white/25",
          loading && "cursor-not-allowed"
        )}
      >
        {showHandled ? (
          <CheckCheck className="w-3.5 h-3.5" aria-hidden />
        ) : (
          <Check className="w-3.5 h-3.5" aria-hidden />
        )}
        <span>{showHandled ? "Showing handled" : "Hide handled"}</span>
      </button>
    </div>
  )
}
