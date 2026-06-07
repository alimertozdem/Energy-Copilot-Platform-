"use client"

/**
 * ActionStatusBadge — visual presentation for an action's status.
 *
 * Used as the read-only display in the actions table. The interactive
 * dropdown (ActionStatusDropdown) reuses these colours so badge ↔ dropdown
 * transitions feel cohesive.
 */
import { cn } from "@/lib/utils"

import type { ActionStatus } from "@/lib/api/actions"

export type StatusVisual = {
  label: string
  badgeClass: string
  dotClass: string
}

export const STATUS_VISUALS: Record<ActionStatus, StatusVisual> = {
  open: {
    label: "Open",
    badgeClass: "bg-amber-500/15 text-amber-200 border-amber-500/30",
    dotClass: "bg-amber-400",
  },
  in_progress: {
    label: "In Progress",
    badgeClass: "bg-sky-500/15 text-sky-200 border-sky-500/30",
    dotClass: "bg-sky-400",
  },
  completed: {
    label: "Completed",
    badgeClass: "bg-emerald-500/15 text-emerald-200 border-emerald-500/30",
    dotClass: "bg-emerald-400",
  },
  dismissed: {
    label: "Dismissed",
    badgeClass: "bg-zinc-500/15 text-zinc-300 border-zinc-500/30",
    dotClass: "bg-zinc-400",
  },
  not_applicable: {
    label: "Not Applicable",
    badgeClass: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
    dotClass: "bg-zinc-500",
  },
}

export const STATUS_ORDER: ActionStatus[] = [
  "open",
  "in_progress",
  "completed",
  "dismissed",
  "not_applicable",
]

export function ActionStatusBadge({ status }: { status: ActionStatus }) {
  const v = STATUS_VISUALS[status]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold border",
        v.badgeClass
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", v.dotClass)} />
      {v.label}
    </span>
  )
}
