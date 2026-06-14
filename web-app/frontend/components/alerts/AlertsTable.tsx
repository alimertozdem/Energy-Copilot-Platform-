"use client"

/**
 * AlertsTable — sortable anomaly table backed by TanStack v8.
 *
 * Columns:
 *   - Building   → links to /buildings/[fabric_building_id]
 *   - Severity   → SeverityBadge (sortable by severity rank)
 *   - Anomaly    → type badge + description + recommended action
 *   - Detected   → detected_at (default sort, newest first)
 *   - Reading    → metric vs threshold + deviation %
 *   - State      → open / resolved pill (Fabric is_resolved, read-only)
 *   - Triage     → acknowledge / dismiss dropdown (Postgres overlay, editable)
 *
 * Filtering + optimistic ack state live in AlertsShell; this component is
 * presentational and calls onAckChange. Rows with no anomaly_id can't be
 * acked (no stable key to PATCH) so their dropdown is disabled.
 */
import {
  ColumnDef,
  SortingFn,
  SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import Link from "next/link"
import { useState } from "react"
import { Lock } from "lucide-react"

import { cn } from "@/lib/utils"

import type { AckStatus, AlertItem } from "@/lib/api/alerts"

import { AlertAckBadge, AlertAckDropdown } from "./AlertAckDropdown"
import { SEVERITY_RANK, SeverityBadge, normalizeSeverity } from "./SeverityBadge"

import { TermLabel } from "@/components/ui/info-tip"

// --------------------------------------------------------------------------
// Cell-level helpers
// --------------------------------------------------------------------------

function fmtNum(v: number | null): string {
  if (v === null) return "—"
  const abs = Math.abs(v)
  if (abs >= 10_000) {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(v)
  }
  if (abs >= 100) {
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(v)
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(v)
}

function fmtDeviation(pct: number | null): { text: string; cls: string } {
  if (pct === null) return { text: "", cls: "" }
  const sign = pct > 0 ? "+" : ""
  const cls = pct > 0 ? "text-red-300" : "text-emerald-300"
  return { text: `${sign}${pct.toFixed(0)}%`, cls }
}

/** Deterministic ISO → "YYYY-MM-DD HH:mm" (no locale → no hydration drift). */
function fmtDetected(iso: string | null): string {
  if (!iso) return "—"
  const [datePart, timePart] = iso.split("T")
  if (!timePart) return datePart
  return `${datePart} ${timePart.slice(0, 5)}`
}

function rankOf(s: string | null): number {
  const n = normalizeSeverity(s)
  return n ? SEVERITY_RANK[n] : 99
}

const severitySort: SortingFn<AlertItem> = (a, b) =>
  rankOf(a.original.severity) - rankOf(b.original.severity)

function StateResolvedPill({ resolved }: { resolved: boolean }) {
  if (resolved) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold border bg-emerald-500/10 text-emerald-300 border-emerald-500/30">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        Resolved
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-semibold border bg-amber-500/10 text-amber-200 border-amber-500/30">
      <span className="relative inline-flex w-1.5 h-1.5" aria-hidden>
        <span className="absolute inset-0 rounded-full bg-amber-400 opacity-60 animate-ping" />
        <span className="relative w-1.5 h-1.5 rounded-full bg-amber-400" />
      </span>
      Open
    </span>
  )
}

// --------------------------------------------------------------------------
// Column definitions
// --------------------------------------------------------------------------

type AlertsTableProps = {
  alerts: AlertItem[]
  pendingAnomalyId: string | null
  onAckChange: (anomaly_id: string, next: AckStatus) => void
  onSelect?: (alert: AlertItem) => void
}

function buildColumns(
  pendingAnomalyId: string | null,
  onAckChange: (anomaly_id: string, next: AckStatus) => void
): ColumnDef<AlertItem>[] {
  return [
    {
      accessorKey: "building_name",
      header: "Building",
      cell: ({ row }) => (
        <Link
          href={`/buildings/${row.original.fabric_building_id}`}
          className="text-white hover:text-emerald-300 transition-colors text-sm font-medium"
          onClick={(e) => e.stopPropagation()}
        >
          {row.original.building_name}
          <span className="ml-1 text-white/40 text-[11px]">
            {row.original.fabric_building_id}
          </span>
        </Link>
      ),
    },
    {
      accessorKey: "severity",
      header: () => <TermLabel term="severity">Severity</TermLabel>,
      cell: ({ row }) => <SeverityBadge severity={row.original.severity} />,
      sortingFn: severitySort,
    },
    {
      accessorKey: "anomaly_type",
      header: () => <TermLabel term="anomaly">Anomaly</TermLabel>,
      enableSorting: false,
      cell: ({ row }) => (
        <div className="max-w-[400px]">
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border tracking-wider uppercase bg-white/5 text-white/70 border-white/15">
            {row.original.anomaly_type ?? "—"}
          </span>
          {row.original.occurrence_count > 1 && (
            <span
              className="ml-1.5 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold border bg-amber-500/10 text-amber-200 border-amber-500/25 align-middle"
              title={
                `One ongoing issue — ${row.original.occurrence_count} daily occurrences` +
                (row.original.first_detected_at
                  ? ` since ${row.original.first_detected_at.slice(0, 10)}`
                  : "")
              }
            >
              ↻ {row.original.occurrence_count}× recurring
            </span>
          )}
          {row.original.description && (
            <p className="text-sm text-white/90 leading-snug line-clamp-2 mt-1">
              {row.original.description}
            </p>
          )}
          {row.original.recommended_action && (
            <p className="text-[11px] text-white/45 leading-snug line-clamp-1 mt-0.5">
              → {row.original.recommended_action}
            </p>
          )}
        </div>
      ),
    },
    {
      accessorKey: "detected_at",
      header: "Detected",
      cell: ({ row }) => (
        <span className="tabular-nums text-xs text-white/70 whitespace-nowrap">
          {fmtDetected(row.original.detected_at)}
        </span>
      ),
    },
    {
      accessorKey: "deviation_pct",
      header: "Reading",
      enableSorting: false,
      cell: ({ row }) => {
        const m = row.original.metric_value
        const t = row.original.threshold_value
        const dev = fmtDeviation(row.original.deviation_pct)
        if (m === null && t === null) {
          return <span className="text-white/40">—</span>
        }
        return (
          <div className="text-xs tabular-nums whitespace-nowrap">
            <span className="text-white/90">{fmtNum(m)}</span>
            <span className="text-white/40"> vs {fmtNum(t)}</span>
            {dev.text && (
              <span className={cn("ml-1.5 font-medium", dev.cls)}>{dev.text}</span>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: "is_resolved",
      header: "State",
      cell: ({ row }) => <StateResolvedPill resolved={row.original.is_resolved} />,
    },
    {
      id: "triage",
      accessorKey: "ack_status",
      header: "Triage",
      enableSorting: false,
      cell: ({ row }) => {
        const aid = row.original.anomaly_id
        if (!aid) {
          return <span className="text-white/30 text-[11px]">—</span>
        }
        if (!row.original.can_manage) {
          return (
            <span
              className="inline-flex items-center gap-1.5"
              title="Read-only — you can view this building but not change its status"
            >
              <AlertAckBadge ackStatus={row.original.ack_status} />
              <Lock className="h-3 w-3 text-white/40" aria-label="Read-only" />
            </span>
          )
        }
        return (
          <div onClick={(e) => e.stopPropagation()}>
            <AlertAckDropdown
              ackStatus={row.original.ack_status}
              pending={pendingAnomalyId === aid}
              onChange={(next) => onAckChange(aid, next)}
            />
          </div>
        )
      },
    },
  ]
}

// --------------------------------------------------------------------------
// Component
// --------------------------------------------------------------------------

export function AlertsTable({
  alerts,
  pendingAnomalyId,
  onAckChange,
  onSelect,
}: AlertsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "detected_at", desc: true },
  ])

  const columns = buildColumns(pendingAnomalyId, onAckChange)

  const table = useReactTable({
    data: alerts,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getRowId: (row, index) => row.anomaly_id ?? `row-${index}`,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (alerts.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-12 text-center text-white/50">
        No alerts match the current filter.
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-white/10">
                {headerGroup.headers.map((header) => {
                  const canSort = header.column.getCanSort()
                  const sortDir = header.column.getIsSorted()
                  return (
                    <th
                      key={header.id}
                      className={cn(
                        "text-left px-4 py-3 text-[11px] uppercase tracking-[0.12em] text-white/50 font-medium",
                        canSort &&
                          "cursor-pointer select-none hover:text-white/80 transition-colors"
                      )}
                      onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                    >
                      <span className="inline-flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {sortDir === "asc" && <span className="text-white/40">▲</span>}
                        {sortDir === "desc" && <span className="text-white/40">▼</span>}
                      </span>
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                onClick={() => onSelect?.(row.original)}
                className="border-b border-white/5 last:border-b-0 hover:bg-white/[0.02] transition-colors cursor-pointer"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3 align-top">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
