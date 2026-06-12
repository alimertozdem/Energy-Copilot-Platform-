"use client"

/**
 * InstallerRequestsTable — the founder's installer-brokering queue (Marketplace
 * Phase 0). Customers raise requests from /actions + the residential investment
 * case; the founder works the pipeline here: requested → contacted → quoted →
 * closed. Each change hits the /api/installer-requests/admin proxy, then
 * router.refresh() re-reads. Mirrors PilotRequestsTable.
 */
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"

import { fmtDate } from "@/components/admin/adminFormat"
import {
  type AdminInstallerRequestRow,
  updateInstallerRequestStatus,
} from "@/lib/api/installer"
import { cn } from "@/lib/utils"

const STATUSES = ["requested", "contacted", "quoted", "closed"] as const

const STATUS_STYLE: Record<string, string> = {
  requested: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  contacted: "border-accent-blue/30 bg-accent-blue/10 text-accent-blue",
  quoted: "border-brand-emerald/30 bg-brand-emerald/10 text-brand-emerald",
  closed: "border-border-subtle bg-white/5 text-text-faint",
}

export function InstallerRequestsTable({
  requests,
}: {
  requests: AdminInstallerRequestRow[] | null
}) {
  const openCount = (requests ?? []).filter((r) => r.status === "requested").length

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60">
      <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
        <h2 className="text-sm font-semibold text-text-primary">Installer requests</h2>
        <span className="text-xs text-text-muted">
          {openCount} new · {(requests ?? []).length} total
        </span>
      </header>
      {requests === null ? (
        <div className="px-5 py-6 text-sm text-accent-red">
          Couldn&rsquo;t load installer requests.
        </div>
      ) : requests.length === 0 ? (
        <div className="px-5 py-6 text-sm text-text-muted">
          No installer requests yet. Customer requests from Actions and the
          residential investment case appear here for you to broker.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted">
                <th className="px-5 py-2 font-medium">Building</th>
                <th className="px-3 py-2 font-medium">Measure</th>
                <th className="px-3 py-2 font-medium">Source</th>
                <th className="px-3 py-2 font-medium">Received</th>
                <th className="px-5 py-2 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {requests.map((r) => (
                <InstallerRow key={r.id} req={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function InstallerRow({ req }: { req: AdminInstallerRequestRow }) {
  const router = useRouter()
  const [refreshing, startTransition] = useTransition()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function change(status: (typeof STATUSES)[number]) {
    setError(null)
    setBusy(true)
    const res = await updateInstallerRequestStatus(req.id, status)
    setBusy(false)
    if (!res.ok) {
      setError(res.error)
      return
    }
    startTransition(() => router.refresh())
  }

  return (
    <>
      <tr className="align-top hover:bg-white/5">
        <td className="px-5 py-2.5">
          <div className="text-text-primary">{req.building_name ?? req.fabric_building_id}</div>
          <div className="text-xs text-text-faint">{req.fabric_building_id}</div>
        </td>
        <td className="px-3 py-2.5 text-text-muted">
          {req.measure_label ?? req.action_type ?? "—"}
          {req.note && (
            <div
              className="mt-0.5 max-w-[18rem] truncate text-xs text-text-faint"
              title={req.note}
            >
              “{req.note}”
            </div>
          )}
        </td>
        <td className="px-3 py-2.5 text-text-faint">{req.source ?? "—"}</td>
        <td className="px-3 py-2.5 text-text-faint">{fmtDate(req.created_at)}</td>
        <td className="px-5 py-2.5 text-right">
          <select
            value={req.status}
            disabled={busy || refreshing}
            onChange={(e) => change(e.target.value as (typeof STATUSES)[number])}
            aria-label={`Status for ${req.building_name ?? req.fabric_building_id}`}
            className={cn(
              "rounded-md border px-2 py-1 text-[11px] font-medium capitalize outline-none disabled:opacity-50",
              STATUS_STYLE[req.status] ?? "border-border-subtle bg-white/5 text-text-faint"
            )}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s} className="bg-bg-elevated text-text-primary">
                {s}
              </option>
            ))}
          </select>
        </td>
      </tr>
      {error && (
        <tr>
          <td colSpan={5} className="px-5 pb-2 text-xs text-accent-red">
            {error}
          </td>
        </tr>
      )}
    </>
  )
}
