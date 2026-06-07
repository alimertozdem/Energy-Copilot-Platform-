"use client"

/**
 * BuildingsTable -- every active building with interactive admin controls:
 *   * module toggles (meters / iot / battery) -- enabling iot/battery unlocks
 *     the matching /reports page for that building
 *   * fabric_building_id link -- connect an onboarded building to Fabric data
 *
 * Each mutation hits a /api/admin/* proxy then router.refresh() re-reads the
 * server tables (no optimistic local state). Founder-only -- the backend gate
 * still applies even though the controls render here.
 */
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"

import { fmtDate } from "@/components/admin/adminFormat"
import type { AdminBuildingRow } from "@/lib/api/admin"
import {
  updateBuildingFabricId,
  updateBuildingModule,
} from "@/lib/api/adminMutations"
import { cn } from "@/lib/utils"

const MODULE_KEYS = ["meters", "iot", "battery"] as const

type BuildingsTableProps = {
  buildings: AdminBuildingRow[]
}

export function BuildingsTable({ buildings }: BuildingsTableProps) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60">
      <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
        <h2 className="text-sm font-semibold text-text-primary">Buildings</h2>
        <span className="text-xs text-text-muted">{buildings.length} active</span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-text-muted">
              <th className="px-5 py-2 font-medium">Building</th>
              <th className="px-3 py-2 font-medium">Organization</th>
              <th className="px-3 py-2 font-medium">Type</th>
              <th className="px-3 py-2 font-medium">Modules</th>
              <th className="px-3 py-2 font-medium">Fabric ID</th>
              <th className="px-5 py-2 font-medium text-right">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {buildings.map((b) => (
              <BuildingRow key={b.id} building={b} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function BuildingRow({ building }: { building: AdminBuildingRow }) {
  const router = useRouter()
  const [refreshing, startTransition] = useTransition()
  const [busyModule, setBusyModule] = useState<string | null>(null)
  const [savingFabric, setSavingFabric] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fabricInput, setFabricInput] = useState(
    building.fabric_building_id ?? ""
  )

  const moduleEnabled = (key: string) =>
    building.modules.some((m) => m.module_key === key && m.enabled)

  const fabricDirty =
    fabricInput.trim() !== (building.fabric_building_id ?? "")
  const anyBusy = refreshing || busyModule !== null || savingFabric

  async function toggleModule(key: string) {
    setError(null)
    setBusyModule(key)
    const res = await updateBuildingModule(building.id, {
      module_key: key,
      enabled: !moduleEnabled(key),
    })
    setBusyModule(null)
    if (!res.ok) {
      setError(res.error)
      return
    }
    startTransition(() => router.refresh())
  }

  async function saveFabric() {
    setError(null)
    setSavingFabric(true)
    const trimmed = fabricInput.trim()
    const res = await updateBuildingFabricId(building.id, {
      fabric_building_id: trimmed === "" ? null : trimmed,
    })
    setSavingFabric(false)
    if (!res.ok) {
      setError(res.error)
      return
    }
    startTransition(() => router.refresh())
  }

  return (
    <>
      <tr className="hover:bg-white/5">
        <td className="px-5 py-2.5">
          <div className="text-text-primary">{building.name}</div>
          <div className="text-xs text-text-faint">
            {building.is_connected ? "connected" : "pending"}
          </div>
        </td>
        <td className="px-3 py-2.5 text-text-muted">
          {building.organization_name}
        </td>
        <td className="px-3 py-2.5 text-text-muted">
          {building.building_type ?? "—"}
        </td>
        <td className="px-3 py-2.5">
          <div className="flex flex-wrap gap-1">
            {MODULE_KEYS.map((key) => {
              const on = moduleEnabled(key)
              const busy = busyModule === key
              return (
                <button
                  key={key}
                  type="button"
                  disabled={anyBusy}
                  onClick={() => toggleModule(key)}
                  aria-pressed={on}
                  className={cn(
                    "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize transition-colors disabled:opacity-50",
                    on
                      ? "border-brand-emerald/30 bg-brand-emerald/10 text-brand-emerald"
                      : "border-border-subtle bg-white/5 text-text-faint hover:text-text-muted"
                  )}
                >
                  {busy && <Loader2 className="h-3 w-3 animate-spin" />}
                  {key}
                </button>
              )
            })}
          </div>
        </td>
        <td className="px-3 py-2.5">
          <div className="flex items-center gap-1.5">
            <input
              value={fabricInput}
              onChange={(e) => setFabricInput(e.target.value)}
              placeholder="e.g. B011"
              aria-label={`Fabric ID for ${building.name}`}
              disabled={anyBusy}
              className="h-7 w-24 rounded-md border border-input bg-bg-elevated px-2 text-xs text-text-primary outline-none focus-visible:border-ring disabled:opacity-50"
            />
            <button
              type="button"
              onClick={saveFabric}
              disabled={!fabricDirty || anyBusy}
              className="inline-flex h-7 items-center rounded-md border border-border-subtle px-2 text-xs text-text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald disabled:opacity-40"
            >
              {savingFabric ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                "Save"
              )}
            </button>
          </div>
        </td>
        <td className="px-5 py-2.5 text-right text-text-muted">
          {fmtDate(building.created_at)}
        </td>
      </tr>
      {error && (
        <tr>
          <td colSpan={6} className="px-5 pb-2 text-xs text-accent-red">
            {error}
          </td>
        </tr>
      )}
    </>
  )
}
