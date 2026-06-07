"use client"

/**
 * BridgeUnlockPanel — the self-serve "Unlock full analytics" wizard (Access Layer 3).
 *
 * Shows a building's data-tier-aware readiness (which report pages its data earns,
 * with honest reasons), then lets the owner file a bridge request the founder
 * fulfils. The assessment is computed server-side (deterministic, no LLM) and
 * passed in as `initial`; actions re-fetch to refresh the state.
 *
 * Honest by design: bridging never promises "all pages" — only the pages the
 * data supports. Locked pages show exactly what's missing.
 */
import { useState } from "react"
import { ArrowRight, Check, Loader2, Lock, Minus, Sparkles } from "lucide-react"

import {
  type BridgeReadiness,
  cancelBridge,
  fetchBridgeReadiness,
  requestBridge,
} from "@/lib/api/bridge"

const TIER_LABEL: Record<string, string> = {
  empty: "No data yet",
  baseline: "Baseline",
  monitoring: "Live monitoring",
  full: "Full",
}

function StatusDot({ status }: { status: string }) {
  if (status === "ready") {
    return (
      <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-brand-emerald/20 text-brand-emerald">
        <Check className="h-3 w-3" aria-hidden />
      </span>
    )
  }
  if (status === "partial") {
    return (
      <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-amber-400/20 text-amber-300">
        <Minus className="h-3 w-3" aria-hidden />
      </span>
    )
  }
  return (
    <span className="mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-white/5 text-text-faint">
      <Lock className="h-2.5 w-2.5" aria-hidden />
    </span>
  )
}

export function BridgeUnlockPanel({
  buildingId,
  initial,
}: {
  buildingId: string
  initial: BridgeReadiness
}) {
  const [r, setR] = useState<BridgeReadiness>(initial)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [note, setNote] = useState("")
  const [showNote, setShowNote] = useState(false)

  async function refresh() {
    const res = await fetchBridgeReadiness(buildingId)
    if (res.ok) setR(res.data)
  }

  async function onRequest() {
    setBusy(true)
    setError(null)
    const res = await requestBridge(buildingId, note.trim() || undefined)
    setBusy(false)
    if (!res.ok) {
      setError(res.error)
      return
    }
    setShowNote(false)
    setNote("")
    await refresh()
  }

  async function onCancel() {
    setBusy(true)
    setError(null)
    const res = await cancelBridge(buildingId)
    setBusy(false)
    if (!res.ok) {
      setError(res.error)
      return
    }
    await refresh()
  }

  const req = r.request
  const pending = req?.status === "pending"
  const fulfilled = req?.status === "fulfilled" || r.is_bridged
  const rejected = req?.status === "rejected"

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/30 p-5">
      <div className="flex items-center gap-2.5">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-emerald/15 ring-1 ring-brand-emerald/30">
          <Sparkles className="h-4 w-4 text-brand-emerald" aria-hidden />
        </span>
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-text-primary">Unlock full analytics</h2>
          <div className="text-[11px] text-text-faint">
            Readiness check · {TIER_LABEL[r.overall_tier] ?? r.overall_tier} tier ·{" "}
            {r.ready_pages}/{r.total_pages} pages ready
          </div>
        </div>
      </div>

      <p className="mt-3 text-xs leading-relaxed text-text-muted">{r.summary}</p>

      {/* Per-page readiness */}
      <ul className="mt-4 space-y-2">
        {r.pages.map((p) => (
          <li key={p.key} className="flex items-start gap-2.5">
            <StatusDot status={p.status} />
            <div className="min-w-0">
              <div
                className={`text-xs font-medium ${
                  p.status === "locked" ? "text-text-faint" : "text-text-primary"
                }`}
              >
                {p.label}
              </div>
              <div className="text-[11px] text-text-muted">{p.reason}</div>
            </div>
          </li>
        ))}
      </ul>

      {/* Next steps to unlock more */}
      {r.blocking.length > 0 && !fulfilled && (
        <div className="mt-4 rounded-lg border border-border-subtle bg-white/[0.02] p-3">
          <div className="text-[11px] font-medium uppercase tracking-wide text-text-faint">
            To unlock more
          </div>
          <ul className="mt-1.5 space-y-1">
            {r.blocking.map((b, i) => (
              <li key={i} className="text-[11px] text-text-muted">
                · {b}
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && (
        <div className="mt-3 rounded-lg border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      {/* Action zone */}
      <div className="mt-4 border-t border-border-subtle/60 pt-4">
        {fulfilled ? (
          <div className="flex items-center gap-2 text-xs text-brand-emerald">
            <Check className="h-4 w-4" aria-hidden />
            <span>Bridged to Fabric — full analytics are live.</span>
          </div>
        ) : pending ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-amber-200">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              <span>
                Requested — pending review
                {req?.created_at ? ` · ${new Date(req.created_at).toLocaleDateString()}` : ""}
              </span>
            </div>
            <button
              type="button"
              onClick={onCancel}
              disabled={busy}
              className="text-[11px] text-text-faint underline-offset-2 hover:text-text-muted hover:underline disabled:opacity-50"
            >
              Cancel request
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {rejected && req?.resolution_note && (
              <div className="rounded-lg border border-amber-400/30 bg-amber-400/5 px-3 py-2 text-[11px] text-amber-200">
                Previous request declined: {req.resolution_note}
              </div>
            )}
            {showNote && (
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={2}
                maxLength={1000}
                placeholder="Anything we should know? (optional)"
                className="w-full rounded-md border border-border-faint bg-bg-input px-3 py-2 text-xs text-text-primary focus:outline-none focus:ring-2 focus:ring-brand-emerald"
              />
            )}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onRequest}
                disabled={busy || !r.can_request}
                className="inline-flex items-center gap-1.5 rounded-md bg-brand-emerald px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep disabled:opacity-50"
              >
                {busy ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                ) : (
                  <ArrowRight className="h-4 w-4" aria-hidden />
                )}
                <span>Request full analytics</span>
              </button>
              {r.can_request && !showNote && (
                <button
                  type="button"
                  onClick={() => setShowNote(true)}
                  className="text-[11px] text-text-faint hover:text-text-muted"
                >
                  Add a note
                </button>
              )}
            </div>
            {!r.can_request && (
              <p className="text-[11px] text-text-faint">
                Upload consumption or connect a device first, then you can request the bridge.
              </p>
            )}
            <p className="text-[11px] text-text-faint">
              A request notifies us to connect this building to Microsoft Fabric. You keep the
              baseline analytics meanwhile.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
