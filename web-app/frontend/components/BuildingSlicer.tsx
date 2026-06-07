"use client"

/**
 * BuildingSlicer — a reusable "filter by building" dropdown.
 *
 * Navigates the current page with `?building_id=<id>` (or clears it for "All
 * buildings"). Pages that read `searchParams.building_id` then scope their data
 * server-side. Keeps other query params intact.
 */
import { usePathname, useRouter } from "next/navigation"
import { useTransition } from "react"

export type SlicerBuilding = { id: string; name: string }

export function BuildingSlicer({
  buildings,
  value,
  param = "building_id",
  label = "Building",
}: {
  buildings: SlicerBuilding[]
  value: string | null
  param?: string
  label?: string
}) {
  const router = useRouter()
  const pathname = usePathname() ?? ""
  const [pending, startTransition] = useTransition()

  if (buildings.length === 0) return null

  function onChange(next: string) {
    const url =
      next === "all" ? pathname : `${pathname}?${param}=${encodeURIComponent(next)}`
    startTransition(() => router.push(url))
  }

  return (
    <label className="inline-flex items-center gap-2 text-xs text-text-muted">
      <span className="hidden sm:inline">{label}:</span>
      <select
        value={value ?? "all"}
        disabled={pending}
        onChange={(e) => onChange(e.target.value)}
        aria-label="Filter by building"
        className="rounded-md border border-border-subtle bg-bg-elevated px-2.5 py-1.5 text-sm text-text-primary outline-none focus-visible:border-ring disabled:opacity-50"
      >
        <option value="all">All buildings</option>
        {buildings.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name}
          </option>
        ))}
      </select>
    </label>
  )
}
