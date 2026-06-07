"use client"

/**
 * AlertsShell — client root for /alerts.
 *
 * Server-side filtering (Day 37): the severity chips and the resolution toggle
 * drive a re-fetch of /api/alerts instead of slicing a one-shot client-loaded
 * set. This fixes two row-cap bugs:
 *   - severity chip counts come from the backend GROUP BY (severity_counts), so
 *     MEDIUM/LOW are no longer undercounted when the 500-row cap truncates the
 *     table;
 *   - "Showing resolved" fetches the resolved set with its own query (ordered
 *     newest-first), so it is never starved by the unresolved-first cap.
 *
 * Resolution is a two-way scope: OFF = open (unresolved), ON = resolved. The
 * "Hide handled" toggle (acknowledged / dismissed) stays client-side over the
 * loaded rows -- it is an operational overlay refinement, not a Fabric query
 * dimension.
 *
 * The first render uses the server-provided `initial` (which already matches
 * the default view: all severities, unresolved); only later filter changes
 * trigger a network round-trip. A stale-response guard keeps fast toggles from
 * applying out of order.
 */
import { useEffect, useMemo, useRef, useState } from "react"

import {
  type AckStatus,
  type AlertItem,
  type AlertResolution,
  type AlertSeverityCounts,
  type AlertsResponse,
  fetchAlertsViaProxy,
  updateAlertAck,
} from "@/lib/api/alerts"

import {
  AlertsFilterChips,
  type ChipCounts,
  type SeverityFilter,
} from "@/components/alerts/AlertsFilterChips"
import { AlertsSummaryCards } from "@/components/alerts/AlertsSummaryCards"
import { AlertDetailPanel } from "@/components/alerts/AlertDetailPanel"
import { AlertsTable } from "@/components/alerts/AlertsTable"
import { normalizeSeverity } from "@/components/alerts/SeverityBadge"

const ROW_LIMIT = 500

function resolutionFor(showResolved: boolean): AlertResolution {
  return showResolved ? "resolved" : "unresolved"
}

/**
 * Per-severity chip counts straight from the backend severity_counts (a GROUP
 * BY over the full visible set, accurate regardless of the row cap). The
 * resolution scope picks which breakdown to show; resolved = total - unresolved.
 */
function deriveChipCounts(
  counts: AlertSeverityCounts,
  resolution: AlertResolution
): ChipCounts {
  if (resolution === "resolved") {
    return {
      all: Math.max(0, counts.total - counts.unresolved_total),
      CRITICAL: Math.max(0, counts.critical - counts.unresolved_critical),
      HIGH: Math.max(0, counts.high - counts.unresolved_high),
      MEDIUM: Math.max(0, counts.medium - counts.unresolved_medium),
      LOW: Math.max(0, counts.low - counts.unresolved_low),
    }
  }
  if (resolution === "all") {
    return {
      all: counts.total,
      CRITICAL: counts.critical,
      HIGH: counts.high,
      MEDIUM: counts.medium,
      LOW: counts.low,
    }
  }
  // unresolved (default triage scope)
  return {
    all: counts.unresolved_total,
    CRITICAL: counts.unresolved_critical,
    HIGH: counts.unresolved_high,
    MEDIUM: counts.unresolved_medium,
    LOW: counts.unresolved_low,
  }
}

function recountOnAck(
  counts: AlertSeverityCounts,
  severity: string | null,
  isResolved: boolean,
  oldAck: AckStatus,
  newAck: AckStatus
): AlertSeverityCounts {
  const c = { ...counts }
  if (oldAck === "acknowledged") c.acknowledged = Math.max(0, c.acknowledged - 1)
  if (oldAck === "dismissed") c.dismissed = Math.max(0, c.dismissed - 1)
  if (newAck === "acknowledged") c.acknowledged += 1
  if (newAck === "dismissed") c.dismissed += 1

  // Unhandled only counts unresolved rows.
  if (!isResolved) {
    const sev = normalizeSeverity(severity)
    const wasUnhandled = oldAck === "new"
    const nowUnhandled = newAck === "new"
    if (wasUnhandled && !nowUnhandled) {
      c.unhandled_total = Math.max(0, c.unhandled_total - 1)
      if (sev === "CRITICAL") c.unhandled_critical = Math.max(0, c.unhandled_critical - 1)
      else if (sev === "HIGH") c.unhandled_high = Math.max(0, c.unhandled_high - 1)
    } else if (!wasUnhandled && nowUnhandled) {
      c.unhandled_total += 1
      if (sev === "CRITICAL") c.unhandled_critical += 1
      else if (sev === "HIGH") c.unhandled_high += 1
    }
  }
  return c
}

export function AlertsShell({
  initial,
  buildingId,
}: {
  initial: AlertsResponse
  buildingId?: string
}) {
  const [alerts, setAlerts] = useState<AlertItem[]>(initial.alerts)
  const [counts, setCounts] = useState<AlertSeverityCounts>(initial.severity_counts)
  const [severity, setSeverity] = useState<SeverityFilter>("all")
  const [showResolved, setShowResolved] = useState(false)
  const [showHandled, setShowHandled] = useState(false)
  const [pendingAnomalyId, setPendingAnomalyId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<AlertItem | null>(null)

  // Stale-response guard: only the latest in-flight fetch may apply its result.
  const reqIdRef = useRef(0)
  // Skip the re-fetch on first mount -- `initial` already covers the default
  // view (all severities, unresolved scope).
  const didMountRef = useRef(false)

  const resolution = resolutionFor(showResolved)

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true
      return
    }
    const reqId = ++reqIdRef.current
    setLoading(true)
    setError(null)
    const params = {
      limit: ROW_LIMIT,
      resolution: resolutionFor(showResolved),
      ...(severity !== "all" ? { severity } : {}),
      ...(buildingId ? { building_id: buildingId } : {}),
    }
    fetchAlertsViaProxy(params).then((result) => {
      if (reqId !== reqIdRef.current) return // a newer request superseded us
      if (result.ok) {
        setAlerts(result.data.alerts)
        setCounts(result.data.severity_counts)
      } else {
        setError(result.error)
      }
      setLoading(false)
    })
  }, [severity, showResolved, buildingId])

  // Server already filtered by severity + resolution; only the handled overlay
  // toggle is applied client-side here.
  const visible = useMemo(() => {
    if (showHandled) return alerts
    return alerts.filter((a) => a.ack_status === "new")
  }, [alerts, showHandled])

  const chipCounts: ChipCounts = useMemo(
    () => deriveChipCounts(counts, resolution),
    [counts, resolution]
  )

  const liveSelected = useMemo<AlertItem | null>(() => {
    if (!selected) return null
    if (selected.anomaly_id == null) return selected
    return alerts.find((a) => a.anomaly_id === selected.anomaly_id) ?? selected
  }, [selected, alerts])

  async function handleAckChange(anomaly_id: string, next: AckStatus) {
    setError(null)
    const original = alerts.find((a) => a.anomaly_id === anomaly_id)
    if (!original || original.ack_status === next) return
    const prevAck = original.ack_status

    // 1. Optimistic apply
    setPendingAnomalyId(anomaly_id)
    setAlerts((rows) =>
      rows.map((r) => (r.anomaly_id === anomaly_id ? { ...r, ack_status: next } : r))
    )
    setCounts((c) => recountOnAck(c, original.severity, original.is_resolved, prevAck, next))

    // 2. Fire backend update
    const result = await updateAlertAck(anomaly_id, {
      ack_status: next,
      building_id: original.fabric_building_id,
    })

    if (!result.ok) {
      // 3a. Rollback
      setAlerts((rows) =>
        rows.map((r) => (r.anomaly_id === anomaly_id ? { ...r, ack_status: prevAck } : r))
      )
      setCounts((c) => recountOnAck(c, original.severity, original.is_resolved, next, prevAck))
      setError(`Couldn't save change: ${result.error}`)
    } else {
      // 3b. Merge server fields
      setAlerts((rows) =>
        rows.map((r) =>
          r.anomaly_id === anomaly_id
            ? {
                ...r,
                ack_status: result.data.ack_status,
                acknowledged_at: result.data.acknowledged_at,
              }
            : r
        )
      )
    }
    setPendingAnomalyId(null)
  }

  return (
    <div className="space-y-6">
      <AlertsSummaryCards counts={counts} />

      <AlertsFilterChips
        activeSeverity={severity}
        chipCounts={chipCounts}
        showResolved={showResolved}
        showHandled={showHandled}
        loading={loading}
        onSeverityChange={setSeverity}
        onToggleResolved={setShowResolved}
        onToggleHandled={setShowHandled}
      />

      {error && (
        <div
          className={
            error === "fabric_unavailable"
              ? "rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs text-amber-200"
              : "rounded-lg border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200"
          }
        >
          {error === "fabric_unavailable"
            ? "Live data is temporarily unavailable — syncing. Showing the last loaded set."
            : error}
        </div>
      )}

      <div className={loading ? "opacity-60 pointer-events-none transition-opacity" : "transition-opacity"}>
        <AlertsTable
          alerts={visible}
          pendingAnomalyId={pendingAnomalyId}
          onAckChange={handleAckChange}
          onSelect={setSelected}
        />
      </div>

      <AlertDetailPanel
        alert={liveSelected}
        pending={pendingAnomalyId != null && pendingAnomalyId === liveSelected?.anomaly_id}
        onClose={() => setSelected(null)}
        onAckChange={handleAckChange}
      />
    </div>
  )
}
