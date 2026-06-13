"use client"

/**
 * ActionsTable — sortable recommendations table backed by TanStack v8.
 *
 * Columns:
 *   - Building   → links to /buildings/[fabric_building_id]
 *   - Action     → action_type badge
 *   - Title      → title_en, wraps to two lines
 *   - Priority   → priority_label + score
 *   - Savings    → annual_saving_eur (compact € notation)
 *   - Payback    → payback_years (e.g. "3.2 yr")
 *   - Status     → inline editable dropdown
 *
 * Selection state lives in ActionsShell; this component is purely
 * presentational. Status changes call the onStatusChange callback.
 */
import {
  ColumnDef,
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
import { RequestInstallerButton } from "@/components/installer/RequestInstallerButton"

import type { ActionItem, ActionStatus } from "@/lib/api/actions"

import { ActionStatusDropdown } from "./ActionStatusDropdown"
import { ActionStatusBadge } from "./ActionStatusBadge"

import { TermLabel } from "@/components/ui/info-tip"

// --------------------------------------------------------------------------
// Cell-level helpers
// --------------------------------------------------------------------------

function fmtCompactEur(value: number | null): string {
  if (value === null || value === 0) return "—"
  if (Math.abs(value) >= 10_000) {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(value)
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value)
}

function fmtPaybackYears(years: number | null): string {
  if (years === null) return "—"
  if (years < 1) return `${(years * 12).toFixed(0)} mo`
  return `${years.toFixed(1)} yr`
}

// A measure with no quantified financial payback: either it saves nothing
// (annual_saving_eur null/0) or its payback is the backend "no real payback"
// sentinel (~99 yr). These are operational / no-capex tweaks — show them as an
// "Operational" measure instead of a misleading "99.0 yr".
const OPERATIONAL_PAYBACK_YEARS = 50

function isOperationalMeasure(a: ActionItem): boolean {
  const noSaving = a.annual_saving_eur === null || a.annual_saving_eur === 0
  const noPayback =
    a.payback_years === null || a.payback_years >= OPERATIONAL_PAYBACK_YEARS
  return noSaving || noPayback
}

function priorityStyle(label: string | null): string {
  switch ((label ?? "").toLowerCase()) {
    case "high":
    case "critical":
      return "text-red-300"
    case "medium":
      return "text-amber-300"
    case "low":
      return "text-emerald-300"
    default:
      return "text-white/60"
  }
}

const ACTION_TYPE_BADGE: Record<string, string> = {
  HVAC: "bg-sky-500/10 text-sky-300 border-sky-500/30",
  Lighting: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  Envelope: "bg-purple-500/10 text-purple-300 border-purple-500/30",
  Controls: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  Renewables: "bg-lime-500/10 text-lime-300 border-lime-500/30",
}

function actionTypeBadgeClass(t: string | null): string {
  if (!t) return "bg-zinc-500/10 text-zinc-400 border-zinc-500/30"
  return (
    ACTION_TYPE_BADGE[t] ?? "bg-white/5 text-white/70 border-white/15"
  )
}

// --------------------------------------------------------------------------
// Column definitions
// --------------------------------------------------------------------------

type ActionsTableProps = {
  actions: ActionItem[]
  pendingActionId: string | null
  onStatusChange: (action_id: string, next: ActionStatus) => void
}

function buildColumns(
  pendingActionId: string | null,
  onStatusChange: (id: string, s: ActionStatus) => void
): ColumnDef<ActionItem>[] {
  return [
    {
      accessorKey: "building_name",
      header: "Building",
      cell: ({ row }) => (
        <Link
          href={`/buildings/${row.original.fabric_building_id}`}
          className="text-white hover:text-emerald-300 transition-colors text-sm font-medium"
        >
          {row.original.building_name}
          <span className="ml-1 text-white/40 text-[11px]">
            {row.original.fabric_building_id}
          </span>
        </Link>
      ),
    },
    {
      accessorKey: "action_type",
      header: "Type",
      cell: ({ row }) => (
        <span
          className={cn(
            "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border tracking-wider uppercase",
            actionTypeBadgeClass(row.original.action_type)
          )}
        >
          {row.original.action_type ?? "—"}
        </span>
      ),
    },
    {
      accessorKey: "title",
      header: "Recommendation",
      cell: ({ row }) => (
        <div className="max-w-[420px]">
          <p className="text-sm text-white leading-snug line-clamp-2">
            {row.original.title ?? "—"}
          </p>
          {row.original.compliance_driver && (
            <p className="text-[10px] text-white/50 uppercase tracking-wider mt-0.5">
              {row.original.compliance_driver}
            </p>
          )}
        </div>
      ),
      enableSorting: false,
    },
    {
      accessorKey: "priority_score",
      header: "Priority",
      cell: ({ row }) => (
        <div className="flex flex-col">
          <span
            className={cn(
              "text-xs font-semibold",
              priorityStyle(row.original.priority_label)
            )}
          >
            {row.original.priority_label ?? "—"}
          </span>
          {row.original.priority_score !== null && (
            <span className="text-[10px] text-white/40 tabular-nums">
              {row.original.priority_score.toFixed(1)}
            </span>
          )}
        </div>
      ),
    },
    {
      accessorKey: "annual_saving_eur",
      header: "Savings / yr",
      cell: ({ row }) => (
        <span className="tabular-nums text-emerald-300 font-medium">
          €{fmtCompactEur(row.original.annual_saving_eur)}
        </span>
      ),
    },
    {
      accessorKey: "payback_years",
      header: () => <TermLabel term="payback">Payback</TermLabel>,
      cell: ({ row }) =>
        isOperationalMeasure(row.original) ? (
          <span className="inline-flex flex-col leading-tight">
            <span className="tabular-nums text-white/50">—</span>
            <span className="text-[10px] uppercase tracking-wider text-white/40">
              Operational
            </span>
          </span>
        ) : (
          <span className="tabular-nums text-white/80">
            {fmtPaybackYears(row.original.payback_years)}
          </span>
        ),
    },
    {
      id: "status",
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) =>
        row.original.can_manage ? (
          <ActionStatusDropdown
            status={row.original.status}
            pending={pendingActionId === row.original.action_id}
            onChange={(next) => onStatusChange(row.original.action_id, next)}
          />
        ) : (
          <span
            className="inline-flex items-center gap-1.5"
            title="Read-only — you can view this building but not change its status"
          >
            <ActionStatusBadge status={row.original.status} />
            <Lock className="h-3 w-3 text-white/40" aria-label="Read-only" />
          </span>
        ),
    },
    {
      id: "request_installer",
      header: "Installer",
      enableSorting: false,
      cell: ({ row }) => (
        <RequestInstallerButton
          compact
          fabricBuildingId={row.original.fabric_building_id}
          actionType={row.original.action_type}
          measureLabel={row.original.title}
          source="actions"
        />
      ),
    },
  ]
}

// --------------------------------------------------------------------------
// Component
// --------------------------------------------------------------------------

export function ActionsTable({
  actions,
  pendingActionId,
  onStatusChange,
}: ActionsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "annual_saving_eur", desc: true },
  ])

  const columns = buildColumns(pendingActionId, onStatusChange)

  const table = useReactTable({
    data: actions,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (actions.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-12 text-center text-white/50">
        No recommendations match the current filter.
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr
                key={headerGroup.id}
                className="border-b border-white/10"
              >
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
                className="border-b border-white/5 last:border-b-0 hover:bg-white/[0.02] transition-colors"
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
