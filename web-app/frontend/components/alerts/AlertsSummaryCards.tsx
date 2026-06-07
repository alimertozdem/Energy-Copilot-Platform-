"use client"

/**
 * AlertsSummaryCards — four headline tiles over the alerts table.
 *
 * Leads with the triage queue (unhandled = unresolved AND not acknowledged/
 * dismissed) by severity, then the total unhandled backlog, then how many a
 * human has acknowledged. This is the "3 critical alerts need attention" line.
 *
 * Numbers come from backend AlertSeverityCounts (GROUP BY + overlay merge --
 * accurate regardless of the table row cap). They update optimistically as the
 * user acknowledges rows.
 */
import { cn } from "@/lib/utils"

import type { AlertSeverityCounts } from "@/lib/api/alerts"

export function AlertsSummaryCards({ counts }: { counts: AlertSeverityCounts }) {
  const cards: {
    label: string
    value: number
    valueClass: string
    hint: string
  }[] = [
    {
      label: "Unhandled Critical",
      value: counts.unhandled_critical,
      valueClass: "text-red-300",
      hint: "Needs attention now",
    },
    {
      label: "Unhandled High",
      value: counts.unhandled_high,
      valueClass: "text-orange-300",
      hint: "Investigate soon",
    },
    {
      label: "Open & Unhandled",
      value: counts.unhandled_total,
      valueClass: "text-white",
      hint: "Active triage queue",
    },
    {
      label: "Acknowledged",
      value: counts.acknowledged,
      valueClass: "text-sky-300",
      hint: "Owned by a human",
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm px-4 py-3"
        >
          <div className="text-[11px] uppercase tracking-[0.12em] text-white/50 font-medium">
            {c.label}
          </div>
          <div className={cn("mt-1 text-2xl font-semibold tabular-nums", c.valueClass)}>
            {c.value}
          </div>
          <div className="mt-0.5 text-[11px] text-white/40">{c.hint}</div>
        </div>
      ))}
    </div>
  )
}
