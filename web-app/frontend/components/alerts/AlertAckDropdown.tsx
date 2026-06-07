"use client"

/**
 * AlertAckDropdown — inline triage selector for an anomaly (Day 31 overlay).
 *
 * Native <select> (keyboard + touch a11y for free, no popover lib) styled with
 * the ack palette so the cell reads "tagged" rather than form-y. Mirrors
 * ActionStatusDropdown. Writes the Postgres operational state only — it never
 * touches Fabric is_resolved.
 *
 * AlertAckBadge is the read-only twin (used wherever a non-editable display is
 * wanted), sharing ACK_VISUALS so badge ↔ dropdown stay cohesive.
 */
import { ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"

import type { AckStatus } from "@/lib/api/alerts"

export type AckVisual = {
  label: string
  badgeClass: string
  dotClass: string
}

export const ACK_VISUALS: Record<AckStatus, AckVisual> = {
  new: {
    label: "New",
    badgeClass: "bg-white/10 text-white/80 border-white/20",
    dotClass: "bg-white/60",
  },
  acknowledged: {
    label: "Acknowledged",
    badgeClass: "bg-sky-500/15 text-sky-200 border-sky-500/30",
    dotClass: "bg-sky-400",
  },
  dismissed: {
    label: "Dismissed",
    badgeClass: "bg-zinc-500/15 text-zinc-300 border-zinc-500/30",
    dotClass: "bg-zinc-400",
  },
}

export const ACK_ORDER: AckStatus[] = ["new", "acknowledged", "dismissed"]

export function AlertAckBadge({ ackStatus }: { ackStatus: AckStatus }) {
  const v = ACK_VISUALS[ackStatus]
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

type AlertAckDropdownProps = {
  ackStatus: AckStatus
  pending?: boolean
  disabled?: boolean
  onChange: (next: AckStatus) => void
}

export function AlertAckDropdown({
  ackStatus,
  pending = false,
  disabled = false,
  onChange,
}: AlertAckDropdownProps) {
  const v = ACK_VISUALS[ackStatus]
  return (
    <div className="relative inline-flex">
      <select
        value={ackStatus}
        onChange={(e) => onChange(e.target.value as AckStatus)}
        disabled={disabled || pending}
        aria-label="Change alert triage status"
        className={cn(
          "appearance-none cursor-pointer",
          "pl-2.5 pr-7 py-1 rounded-md text-[11px] font-semibold border",
          "transition-all focus:outline-none focus:ring-2 focus:ring-brand-emerald/60",
          v.badgeClass,
          (disabled || pending) && "opacity-60 cursor-wait"
        )}
      >
        {ACK_ORDER.map((s) => (
          <option key={s} value={s} className="text-bg-base">
            {ACK_VISUALS[s].label}
          </option>
        ))}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 opacity-70"
        aria-hidden
      />
    </div>
  )
}
