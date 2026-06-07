"use client"

/**
 * BridgeRequestsTable -- the founder's self-serve bridge queue (Access Layer 3).
 *
 * Customers file requests to bridge a pending building into Fabric; the founder
 * reviews the readiness snapshot here, links the fabric_building_id in the
 * Buildings table, then marks the request fulfilled. Each action hits the
 * /api/admin/bridge-requests proxy then router.refresh() re-reads the table.
 */
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"

import { fmtDate } from "@/components/admin/adminFormat"
import {
  type AdminBridgeRequestRow,
  type AutomatedBridgeResult,
  automateBridgeRequest,
  resolveBridgeRequest,
} from "@/lib/api/bridge"
import { cn } from "@/lib/utils"

const STATUS_STYLE: Record<string, string> = {
  pending: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  approved: "border-accent-blue/30 bg-accent-blue/10 text-accent-blue",
  fulfilled: "border-brand-emerald/30 bg-brand-emerald/10 text-brand-emerald",
  rejected: "border-border-subtle bg-white/5 text-text-faint",
  cancelled: "border-border-subtle bg-white/5 text-text-faint",
}

export function BridgeRequestsTable({
  requests,
}: {
  requests: AdminBridgeRequestRow[]
}) {
  const pendingCount = requests.filter((r) => r.status === "pending").length
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60">
      <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
        <h2 className="text-sm font-semibold text-text-primary">Bridge requests</h2>
        <span className="text-xs text-text-muted">
          {pendingCount} pending · {requests.length} total
        </span>
      </header>
      {requests.length === 0 ? (
        <div className="px-5 py-6 text-sm text-text-muted">
          No bridge requests yet. Customers request these from a pending building&rsquo;s page.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted">
                <th className="px-5 py-2 font-medium">Building</th>
                <th className="px-3 py-2 font-medium">Organization</th>
                <th className="px-3 py-2 font-medium">Requested by</th>
                <th className="px-3 py-2 font-medium">Readiness</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-5 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {requests.map((r) => (
                <RequestRow key={r.id} req={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function RequestRow({ req }: { req: AdminBridgeRequestRow }) {
  const router = useRouter()
  const [refreshing, startTransition] = useTransition()
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fabric, setFabric] = useState(req.fabric_building_id ?? "")
  const [autoResult, setAutoResult] = useState<AutomatedBridgeResult | null>(null)

  const isPending = req.status === "pending"
  const anyBusy = refreshing || busy !== null

  async function auto(dryRun: boolean) {
    setError(null)
    setAutoResult(null)
    setBusy(dryRun ? "dryrun" : "auto")
    const res = await automateBridgeRequest(req.id, {
      dryRun,
      fabricBuildingId: fabric.trim() || undefined,
    })
    setBusy(null)
    if (!res.ok) {
      setError(res.error)
      return
    }
    setAutoResult(res.data)
    // A successful LIVE bridge flips the building to live -> re-read the table.
    if (res.data.ok && !res.data.dry_run) {
      startTransition(() => router.refresh())
    }
  }

  async function act(
    status: "approved" | "rejected" | "fulfilled",
    fabricId?: string
  ) {
    setError(null)
    let note: string | undefined
    if (status === "rejected") {
      note = window.prompt("Reason (optional, shown to the customer):") ?? undefined
    }
    setBusy(status)
    const res = await resolveBridgeRequest(req.id, status, note, fabricId)
    setBusy(null)
    if (!res.ok) {
      setError(res.error)
      return
    }
    startTransition(() => router.refresh())
  }

  const tier = req.readiness?.overall_tier ?? "—"
  const ready = req.readiness?.ready_pages
  const total = req.readiness?.total_pages

  return (
    <>
      <tr className="hover:bg-white/5 align-top">
        <td className="px-5 py-2.5">
          <div className="text-text-primary">{req.building_name}</div>
          <div className="text-xs text-text-faint">
            {req.fabric_building_id ? req.fabric_building_id : "pending — link a Fabric ID"}
          </div>
        </td>
        <td className="px-3 py-2.5 text-text-muted">{req.organization_name}</td>
        <td className="px-3 py-2.5 text-text-muted">
          <div>{req.requested_by_email ?? "—"}</div>
          <div className="text-xs text-text-faint">{fmtDate(req.created_at)}</div>
        </td>
        <td className="px-3 py-2.5 text-text-muted">
          <div className="capitalize">{tier}</div>
          {ready != null && total != null && (
            <div className="text-xs text-text-faint">{ready}/{total} pages ready</div>
          )}
          {req.note && (
            <div className="mt-0.5 max-w-[16rem] truncate text-xs text-text-faint" title={req.note}>
              “{req.note}”
            </div>
          )}
        </td>
        <td className="px-3 py-2.5">
          <span
            className={cn(
              "inline-flex rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize",
              STATUS_STYLE[req.status] ?? "border-border-subtle bg-white/5 text-text-faint"
            )}
          >
            {req.status}
          </span>
        </td>
        <td className="px-5 py-2.5 text-right">
          {isPending ? (
            <div className="inline-flex items-center gap-1">
              <input
                value={fabric}
                onChange={(e) => setFabric(e.target.value)}
                placeholder="B0xx"
                aria-label={`Fabric ID for ${req.building_name}`}
                disabled={anyBusy}
                className="h-7 w-16 rounded-md border border-input bg-bg-elevated px-2 text-xs text-text-primary outline-none focus-visible:border-ring disabled:opacity-50"
              />
              <button
                type="button"
                disabled={anyBusy}
                onClick={() => act("fulfilled", fabric.trim() || undefined)}
                title="Link the Fabric ID (if set) and mark the request fulfilled"
                className="inline-flex items-center gap-1 rounded-md border border-brand-emerald/30 px-2 py-1 text-[11px] text-brand-emerald transition-colors hover:bg-brand-emerald/10 disabled:opacity-50"
              >
                {busy === "fulfilled" && <Loader2 className="h-3 w-3 animate-spin" />}
                Fulfil
              </button>
              <button
                type="button"
                disabled={anyBusy}
                onClick={() => act("approved")}
                className="rounded-md border border-border-subtle px-2 py-1 text-[11px] text-text-muted transition-colors hover:text-text-primary disabled:opacity-50"
              >
                {busy === "approved" ? "…" : "Approve"}
              </button>
              <button
                type="button"
                disabled={anyBusy}
                onClick={() => act("rejected")}
                className="rounded-md border border-border-subtle px-2 py-1 text-[11px] text-text-faint transition-colors hover:text-accent-red disabled:opacity-50"
              >
                {busy === "rejected" ? "…" : "Reject"}
              </button>
              <span className="mx-0.5 h-4 w-px bg-border-subtle" aria-hidden />
              <button
                type="button"
                disabled={anyBusy}
                onClick={() => auto(true)}
                title="Phase 3.2 — simulate the automated bridge (no Fabric calls, no capacity needed)"
                className="rounded-md border border-border-subtle px-2 py-1 text-[11px] text-text-muted transition-colors hover:text-text-primary disabled:opacity-50"
              >
                {busy === "dryrun" ? "…" : "Dry-run"}
              </button>
              <button
                type="button"
                disabled={anyBusy}
                onClick={() => auto(false)}
                title="Phase 3.2 — run the automated Fabric bridge (needs an active capacity)"
                className="inline-flex items-center gap-1 rounded-md border border-accent-blue/30 px-2 py-1 text-[11px] text-accent-blue transition-colors hover:bg-accent-blue/10 disabled:opacity-50"
              >
                {busy === "auto" && <Loader2 className="h-3 w-3 animate-spin" />}
                Auto-bridge
              </button>
            </div>
          ) : (
            <span className="text-xs text-text-faint">
              {req.resolved_at ? fmtDate(req.resolved_at) : "—"}
            </span>
          )}
        </td>
      </tr>
      {error && (
        <tr>
          <td colSpan={6} className="px-5 pb-2 text-xs text-accent-red">
            {error}
          </td>
        </tr>
      )}
      {autoResult && (
        <tr>
          <td colSpan={6} className="px-5 pb-3">
            <div className="rounded-md border border-border-subtle bg-bg-base/60 p-2.5 text-xs">
              <div className="mb-1.5 flex items-center gap-2">
                <span
                  className={cn(
                    "font-medium",
                    autoResult.ok ? "text-brand-emerald" : "text-accent-red"
                  )}
                >
                  {autoResult.dry_run ? "Dry-run" : "Auto-bridge"}{" "}
                  {autoResult.ok ? "ok" : "failed"}
                </span>
                {autoResult.fabric_building_id && (
                  <span className="text-text-muted">→ {autoResult.fabric_building_id}</span>
                )}
                {!autoResult.automation_enabled && (
                  <span className="text-amber-300">
                    automation off — use Fulfil for manual go-live
                  </span>
                )}
              </div>
              <ol className="space-y-0.5">
                {autoResult.steps.map((s, i) => (
                  <li key={i} className="flex gap-2 text-text-faint">
                    <span
                      className={cn(
                        "w-20 shrink-0",
                        s.status.startsWith("ok")
                          ? "text-brand-emerald"
                          : s.status === "failed"
                            ? "text-accent-red"
                            : "text-text-muted"
                      )}
                    >
                      {s.status}
                    </span>
                    <span className="text-text-muted">{s.step}</span>
                    {s.message && <span className="text-text-faint">— {s.message}</span>}
                  </li>
                ))}
              </ol>
              {autoResult.error && (
                <div className="mt-1 text-accent-red">{autoResult.error}</div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
