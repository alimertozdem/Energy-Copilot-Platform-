"use client"

/**
 * Sortable portfolio buildings table — backed by @tanstack/react-table v8.
 *
 * Columns:
 *   - Building name      → links to /buildings/[fabric_building_id]
 *   - Location           → "City, Country"
 *   - Type               → building_type badge
 *   - Area               → m²
 *   - EUI                → annualized kWh/m²·yr, color-tiered
 *   - Energy 30d         → kWh (compact notation)
 *   - Cost 30d           → € (compact notation)
 *   - CO₂ 30d            → kg (compact notation)
 *   - Anomalies          → count, color by severity volume
 *   - EPC                → A-G badge, color by class
 *
 * Default sort: kWh 30d desc (matches the backend ordering, but the user
 * can click any header to override).
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

import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import { cn } from "@/lib/utils"
import { TermLabel } from "@/components/ui/info-tip"

// ---------------------------------------------------------------------------
// Cell-level helpers
// ---------------------------------------------------------------------------

const fmtInt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 })

function fmtCompact(value: number, digits = 1): string {
  if (Math.abs(value) >= 10_000) {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: digits,
    }).format(value)
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value)
}

function euiTier(eui: number | null): "good" | "fair" | "poor" | "unknown" {
  if (eui === null || eui === 0) return "unknown"
  // Daily ASHRAE bands × 365 (ref: DAX EUI Benchmark Status)
  //   ≤ 100  → good       (≤ 0.27 kWh/m²/day)
  //   ≤ 200  → fair       (≤ 0.55)
  //   > 200  → poor
  if (eui <= 100) return "good"
  if (eui <= 200) return "fair"
  return "poor"
}

const EUI_STYLE: Record<ReturnType<typeof euiTier>, string> = {
  good: "text-emerald-300",
  fair: "text-amber-300",
  poor: "text-red-300",
  unknown: "text-white/40",
}

function anomalyStyle(n: number): string {
  if (n === 0) return "text-white/40"
  if (n <= 3) return "text-amber-300"
  return "text-red-300"
}

const EPC_BADGE: Record<string, string> = {
  A: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  B: "bg-emerald-400/15 text-emerald-200 border-emerald-400/30",
  C: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  D: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  E: "bg-red-500/15 text-red-300 border-red-500/30",
  F: "bg-red-600/15 text-red-200 border-red-600/30",
  G: "bg-red-700/15 text-red-100 border-red-700/30",
}

function epcBadgeClass(epc: string | null): string {
  if (!epc || !EPC_BADGE[epc]) {
    return "bg-zinc-500/10 text-zinc-400 border-zinc-500/30"
  }
  return EPC_BADGE[epc]
}

// ---------------------------------------------------------------------------
// Column definitions
// ---------------------------------------------------------------------------

const columns: ColumnDef<PortfolioBuildingRow>[] = [
  {
    accessorKey: "name",
    header: "Building",
    cell: ({ row }) => (
      <Link
        href={`/buildings/${row.original.fabric_building_id}`}
        className="font-medium text-white hover:text-emerald-300 transition-colors"
      >
        {row.original.name}
      </Link>
    ),
  },
  {
    id: "location",
    header: "Location",
    cell: ({ row }) => (
      <span className="text-white/70">
        {row.original.city}
        <span className="text-white/40">, {row.original.country}</span>
      </span>
    ),
    enableSorting: false,
  },
  {
    accessorKey: "building_type",
    header: "Type",
    cell: ({ row }) => (
      <span className="text-xs uppercase tracking-wider text-white/60">
        {row.original.building_type.replace(/_/g, " ")}
      </span>
    ),
  },
  {
    accessorKey: "floor_area_m2",
    header: "Area",
    cell: ({ row }) => (
      <span className="tabular-nums text-white/70">
        {fmtInt.format(row.original.floor_area_m2)} m²
      </span>
    ),
  },
  {
    accessorKey: "eui_kwh_m2_yr",
    header: () => <TermLabel term="eui">EUI</TermLabel>,
    cell: ({ row }) => {
      const eui = row.original.eui_kwh_m2_yr
      const tier = euiTier(eui)
      if (eui === null) {
        return <span className="text-white/40">—</span>
      }
      return (
        <span className={cn("tabular-nums font-medium", EUI_STYLE[tier])}>
          {fmtCompact(eui, 0)}
          <span className="text-white/40 text-xs ml-1">kWh/m²·yr</span>
        </span>
      )
    },
  },
  {
    accessorKey: "kwh_30d",
    header: "Energy 30d",
    cell: ({ row }) => (
      <span className="tabular-nums text-white/80">
        {fmtCompact(row.original.kwh_30d)}
        <span className="text-white/40 text-xs ml-1">kWh</span>
      </span>
    ),
  },
  {
    accessorKey: "cost_30d_eur",
    header: "Cost 30d",
    cell: ({ row }) => (
      <span className="tabular-nums text-white/80">
        €{fmtCompact(row.original.cost_30d_eur)}
      </span>
    ),
  },
  {
    accessorKey: "co2_30d_kg",
    header: "CO₂ 30d",
    cell: ({ row }) => (
      <span className="tabular-nums text-white/80">
        {fmtCompact(row.original.co2_30d_kg)}
        <span className="text-white/40 text-xs ml-1">kg</span>
      </span>
    ),
  },
  {
    accessorKey: "open_anomalies",
    header: () => <TermLabel term="anomaly">Anomalies</TermLabel>,
    cell: ({ row }) => {
      const n = row.original.open_anomalies
      if (n === 0) {
        return <span className="tabular-nums text-white/40">0</span>
      }
      return (
        <Link
          href={`/alerts?building_id=${encodeURIComponent(row.original.fabric_building_id)}`}
          className={cn("tabular-nums font-medium hover:underline", anomalyStyle(n))}
          title="View alerts for this building"
        >
          {n}
        </Link>
      )
    },
  },
  {
    accessorKey: "epc_class",
    header: () => <TermLabel term="epc">EPC</TermLabel>,
    cell: ({ row }) => {
      const epc = row.original.epc_class
      return (
        <span
          className={cn(
            "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border",
            epcBadgeClass(epc)
          )}
        >
          {epc ?? "—"}
        </span>
      )
    },
  },
]

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function BuildingsTable({
  buildings,
}: {
  buildings: PortfolioBuildingRow[]
}) {
  const [sorting, setSorting] = useState<SortingState>([
    // Default sort matches backend ORDER BY kwh_30d DESC
    { id: "kwh_30d", desc: true },
  ])

  const table = useReactTable({
    data: buildings,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (buildings.length === 0) {
    return (
      <div className="rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-12 text-center text-white/50">
        No buildings to display.
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
                        canSort && "cursor-pointer select-none hover:text-white/80 transition-colors"
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
                  <td key={cell.id} className="px-4 py-3">
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
