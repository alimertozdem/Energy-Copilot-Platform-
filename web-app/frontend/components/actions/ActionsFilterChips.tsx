"use client"

/**
 * ActionsFilterChips — Linear/Asana-style status chips with live counts.
 *
 * Selecting "All" returns null to the parent (no filter). Otherwise the
 * filter value is one of ActionStatus.
 *
 * Counts come from backend ActionStatusCounts. They include open
 * recommendations that have no recommendation_status row yet (implicit
 * 'open'), so the sum matches the catalog size.
 */
import { cn } from "@/lib/utils"

import type { ActionStatus, ActionStatusCounts } from "@/lib/api/actions"

import { STATUS_ORDER, STATUS_VISUALS } from "./ActionStatusBadge"

type FilterValue = ActionStatus | "all"

type ActionsFilterChipsProps = {
  active: FilterValue
  counts: ActionStatusCounts
  onChange: (next: FilterValue) => void
}

export function ActionsFilterChips({
  active,
  counts,
  onChange,
}: ActionsFilterChipsProps) {
  const items: {
    value: FilterValue
    label: string
    count: number
    dotClass: string
    activeClass: string
  }[] = [
    {
      value: "all",
      label: "All",
      count: counts.total,
      dotClass: "bg-white/50",
      activeClass:
        "bg-white/15 text-white border-white/30",
    },
    ...STATUS_ORDER.map((s) => ({
      value: s as FilterValue,
      label: STATUS_VISUALS[s].label,
      count: countOf(counts, s),
      dotClass: STATUS_VISUALS[s].dotClass,
      activeClass: STATUS_VISUALS[s].badgeClass,
    })),
  ]

  return (
    <div className="flex flex-wrap items-center gap-2">
      {items.map((it) => {
        const isActive = active === it.value
        return (
          <button
            key={it.value}
            type="button"
            onClick={() => onChange(it.value)}
            aria-pressed={isActive}
            className={cn(
              "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[12px] font-medium",
              "border transition-all",
              isActive
                ? it.activeClass
                : "bg-white/[0.03] border-white/10 text-white/60 hover:text-white/90 hover:border-white/25"
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
              className={cn(
                "tabular-nums text-[11px]",
                isActive ? "" : "text-white/40"
              )}
            >
              {it.count}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function countOf(counts: ActionStatusCounts, status: ActionStatus): number {
  switch (status) {
    case "open":
      return counts.open
    case "in_progress":
      return counts.in_progress
    case "completed":
      return counts.completed
    case "dismissed":
      return counts.dismissed
    case "not_applicable":
      return counts.not_applicable
  }
}
