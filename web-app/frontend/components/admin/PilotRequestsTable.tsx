"use client"

/**
 * PilotRequestsTable — the founder's public pilot-lead queue.
 *
 * Public visitors submit via /pilot (or the landing CTA). The founder works the
 * pipeline here: new → contacted → qualified → closed. Each change hits the
 * /api/admin/pilot-requests proxy then router.refresh() re-reads the table.
 */
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"

import { fmtDate } from "@/components/admin/adminFormat"
import { type AdminPilotRequestRow, resolvePilotRequest } from "@/lib/api/pilot"
import { cn } from "@/lib/utils"

const STATUSES = ["new", "contacted", "qualified", "closed"] as const

const STATUS_STYLE: Record<string, string> = {
  new: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  contacted: "border-accent-blue/30 bg-accent-blue/10 text-accent-blue",
  qualified: "border-brand-emerald/30 bg-brand-emerald/10 text-brand-emerald",
  closed: "border-border-subtle bg-white/5 text-text-faint",
}

export function PilotRequestsTable({ requests }: { requests: AdminPilotRequestRow[] | null }) {
  const newCount = (requests ?? []).filter((r) => r.status === "new").length

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60">
      <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
        <h2 className="text-sm font-semibold text-text-primary">Pilot requests</h2>
        <span className="text-xs text-text-muted">
          {newCount} new · {(requests ?? []).length} total
        </span>
      </header>
      {requests === null ? (
        <div className="px-5 py-6 text-sm text-accent-red">Couldn&rsquo;t load pilot requests.</div>
      ) : requests.length === 0 ? (
        <div className="px-5 py-6 text-sm text-text-muted">
          No pilot requests yet. Leads from the landing page, demo and tour appear here.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted">
                <th className="px-5 py-2 font-medium">Contact</th>
                <th className="px-3 py-2 font-medium">Organization</th>
                <th className="px-3 py-2 font-medium">Portfolio</th>
                <th className="px-3 py-2 font-medium">Source</th>
                <th className="px-3 py-2 font-medium">Received</th>
                <th className="px-5 py-2 font-medium text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {requests.map((r) => (
                <PilotRow key={r.id} req={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function PilotRow({ req }: { req: AdminPilotRequestRow }) {
  const router = useRouter()
  const [refreshing, startTransition] = useTransition()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function change(status: (typeof STATUSES)[number]) {
    setError(null)
    setBusy(true)
    const res = await resolvePilotRequest(req.id, status)
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
          <div className="text-text-primary">{req.name}</div>
          <a href={`mailto:${req.email}`} className="text-xs text-accent-blue hover:underline">
            {req.email}
          </a>
        </td>
        <td className="px-3 py-2.5 text-text-muted">
          {req.organization ?? "—"}
          {req.message && (
            <div className="mt-0.5 max-w-[18rem] truncate text-xs text-text-faint" title={req.message}>
              “{req.message}”
            </div>
          )}
        </td>
        <td className="px-3 py-2.5 text-text-muted">
          {[req.building_count != null ? `${req.building_count} bldg` : null, req.country_code]
            .filter(Boolean)
            .join(" · ") || "—"}
        </td>
        <td className="px-3 py-2.5 text-text-faint">{req.source ?? "—"}</td>
        <td className="px-3 py-2.5 text-text-faint">{fmtDate(req.created_at)}</td>
        <td className="px-5 py-2.5 text-right">
          <select
            value={req.status}
            disabled={busy || refreshing}
            onChange={(e) => change(e.target.value as (typeof STATUSES)[number])}
            aria-label={`Status for ${req.name}`}
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
          <td colSpan={6} className="px-5 pb-2 text-xs text-accent-red">{error}</td>
        </tr>
      )}
    </>
  )
}
