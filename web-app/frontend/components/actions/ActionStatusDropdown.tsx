"use client"

/**
 * ActionStatusDropdown — inline editable status selector.
 *
 * Used inside ActionsTable cells. The dropdown calls back to the parent
 * (ActionsShell) which:
 *   1. Optimistically updates local state
 *   2. Fires updateActionStatus to the Next.js proxy
 *   3. Rolls back on failure (with a toast — for now console.error)
 *
 * Native <select> chosen on purpose:
 *   - Keyboard a11y for free
 *   - Touch device behaviour is correct out of the box
 *   - No floating-UI / popover library needed in the demo phase
 * Visual styling matches the badge palette so the cell looks "tagged" rather
 * than form-y.
 */
import { ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"

import type { ActionStatus } from "@/lib/api/actions"

import { STATUS_ORDER, STATUS_VISUALS } from "./ActionStatusBadge"

type ActionStatusDropdownProps = {
  status: ActionStatus
  pending?: boolean
  disabled?: boolean
  onChange: (next: ActionStatus) => void
}

export function ActionStatusDropdown({
  status,
  pending = false,
  disabled = false,
  onChange,
}: ActionStatusDropdownProps) {
  const v = STATUS_VISUALS[status]
  return (
    <div className="relative inline-flex">
      <select
        value={status}
        onChange={(e) => onChange(e.target.value as ActionStatus)}
        disabled={disabled || pending}
        aria-label="Change action status"
        className={cn(
          "appearance-none cursor-pointer",
          "pl-2.5 pr-7 py-1 rounded-md text-[11px] font-semibold border",
          "transition-all focus:outline-none focus:ring-2 focus:ring-brand-emerald/60",
          v.badgeClass,
          (disabled || pending) && "opacity-60 cursor-wait"
        )}
      >
        {STATUS_ORDER.map((s) => (
          <option key={s} value={s} className="text-bg-base">
            {STATUS_VISUALS[s].label}
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
