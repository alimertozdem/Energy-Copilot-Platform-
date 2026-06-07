"use client"

/**
 * ActionsShell — client root for /actions.
 *
 * Owns:
 *   - actions[] in state (so we can optimistically mutate row status)
 *   - status_counts in state (live updated on optimistic changes)
 *   - active filter chip
 *   - pendingActionId — which row is currently mid-update (locks dropdown)
 *
 * Optimistic update flow:
 *   1. User picks a new status in the dropdown.
 *   2. setActions immediately reflects the change in the UI.
 *   3. counts are decremented from old status and incremented to new.
 *   4. updateActionStatus fires to /api/actions/{id}.
 *   5. On success → keep state, optionally show toast.
 *   6. On failure → revert to original row, log error.
 *
 * Errors are surfaced as a small inline banner above the table (toast
 * library is V1.5 backlog).
 */
import { useMemo, useState } from "react"

import {
  type ActionItem,
  type ActionsResponse,
  type ActionStatus,
  type ActionStatusCounts,
  updateActionStatus,
} from "@/lib/api/actions"

import { ActionsFilterChips } from "@/components/actions/ActionsFilterChips"
import { ActionsTable } from "@/components/actions/ActionsTable"

type FilterValue = ActionStatus | "all"

type ActionsShellProps = {
  initial: ActionsResponse
}

export function ActionsShell({ initial }: ActionsShellProps) {
  const [actions, setActions] = useState<ActionItem[]>(initial.actions)
  const [counts, setCounts] = useState<ActionStatusCounts>(initial.status_counts)
  const [filter, setFilter] = useState<FilterValue>("all")
  const [pendingActionId, setPendingActionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const visibleActions = useMemo(() => {
    if (filter === "all") return actions
    return actions.filter((a) => a.status === filter)
  }, [actions, filter])

  function bumpCounts(prev: ActionStatusCounts, from: ActionStatus, to: ActionStatus) {
    if (from === to) return prev
    return {
      ...prev,
      [from]: Math.max(0, (prev[from] ?? 0) - 1),
      [to]: (prev[to] ?? 0) + 1,
    }
  }

  async function handleStatusChange(action_id: string, next: ActionStatus) {
    setError(null)
    const original = actions.find((a) => a.action_id === action_id)
    if (!original) return
    if (original.status === next) return

    const prevStatus = original.status

    // 1. Optimistic apply
    setPendingActionId(action_id)
    setActions((rows) =>
      rows.map((r) =>
        r.action_id === action_id ? { ...r, status: next } : r
      )
    )
    setCounts((c) => bumpCounts(c, prevStatus, next))

    // 2. Fire backend update
    const result = await updateActionStatus(action_id, { status: next })

    if (!result.ok) {
      // 3a. Rollback on failure
      setActions((rows) =>
        rows.map((r) =>
          r.action_id === action_id ? { ...r, status: prevStatus } : r
        )
      )
      setCounts((c) => bumpCounts(c, next, prevStatus))
      setError(`Couldn't save: ${result.error}`)
    } else {
      // 3b. Merge server timestamps without disturbing other fields
      setActions((rows) =>
        rows.map((r) =>
          r.action_id === action_id
            ? {
                ...r,
                status: result.data.status,
                status_updated_at: result.data.status_updated_at,
                completed_at: result.data.completed_at,
              }
            : r
        )
      )
    }
    setPendingActionId(null)
  }

  return (
    <div className="space-y-6">
      <ActionsFilterChips
        active={filter}
        counts={counts}
        onChange={setFilter}
      />

      {error && (
        <div className="rounded-lg border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      <ActionsTable
        actions={visibleActions}
        pendingActionId={pendingActionId}
        onStatusChange={handleStatusChange}
      />
    </div>
  )
}
