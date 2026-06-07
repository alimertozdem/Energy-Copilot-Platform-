"use client"

/**
 * SeverityBadge — visual presentation for an anomaly's severity.
 *
 * Shared colour source for the table cell, the filter chips, and the summary
 * cards so the whole /alerts surface reads consistently. Mirrors the role
 * ActionStatusBadge plays for /actions.
 *
 * Severity values arrive UPPERCASE from Fabric (CRITICAL/HIGH/MEDIUM/LOW).
 */
import { cn } from "@/lib/utils"

import type { AlertSeverity } from "@/lib/api/alerts"

export type SeverityVisual = {
  label: string
  badgeClass: string
  dotClass: string
  /** Solid text colour for summary-card numerals. */
  textClass: string
}

export const SEVERITY_VISUALS: Record<AlertSeverity, SeverityVisual> = {
  CRITICAL: {
    label: "Critical",
    badgeClass: "bg-red-500/15 text-red-200 border-red-500/40",
    dotClass: "bg-red-400",
    textClass: "text-red-300",
  },
  HIGH: {
    label: "High",
    badgeClass: "bg-orange-500/15 text-orange-200 border-orange-500/40",
    dotClass: "bg-orange-400",
    textClass: "text-orange-300",
  },
  MEDIUM: {
    label: "Medium",
    badgeClass: "bg-amber-500/15 text-amber-200 border-amber-500/30",
    dotClass: "bg-amber-400",
    textClass: "text-amber-300",
  },
  LOW: {
    label: "Low",
    badgeClass: "bg-sky-500/15 text-sky-200 border-sky-500/30",
    dotClass: "bg-sky-400",
    textClass: "text-sky-300",
  },
}

export const SEVERITY_ORDER: AlertSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

/** Sort rank — lower = more severe (CRITICAL first). */
export const SEVERITY_RANK: Record<AlertSeverity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
}

export function normalizeSeverity(s: string | null | undefined): AlertSeverity | null {
  if (!s) return null
  const u = s.toUpperCase()
  if (u === "CRITICAL" || u === "HIGH" || u === "MEDIUM" || u === "LOW") {
    return u as AlertSeverity
  }
  return null
}

export function SeverityBadge({ severity }: { severity: string | null }) {
  const norm = normalizeSeverity(severity)
  if (!norm) {
    return <span className="text-white/40 text-xs">—</span>
  }
  const v = SEVERITY_VISUALS[norm]
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
