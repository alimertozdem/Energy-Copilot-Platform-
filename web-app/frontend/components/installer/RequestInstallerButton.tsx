"use client"

/**
 * RequestInstallerButton — Execution Marketplace Phase 0 (founder-brokered).
 *
 * A self-contained "Request an installer" affordance: button → confirm modal
 * (trust framing + the honest "early access, brokered manually" note) → POST
 * /api/installer-requests → "request sent" state. Drop it on a recommendation
 * row (source="actions") or the residential investment case (source="residential").
 *
 * Phase 1+ (vendor matching, quotes, tracking) is roadmap — surfaced in the modal
 * so it reads as "thought-through", not half-built.
 */
import { useEffect, useState } from "react"
import { createPortal } from "react-dom"

export function RequestInstallerButton({
  fabricBuildingId,
  actionType = null,
  measureLabel = null,
  source,
  compact = false,
}: {
  fabricBuildingId: string
  actionType?: string | null
  measureLabel?: string | null
  source: string
  compact?: boolean
}) {
  const [mounted, setMounted] = useState(false)
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => setMounted(true), [])

  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [open])

  async function send() {
    setBusy(true)
    setError(null)
    try {
      const res = await fetch("/api/installer-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fabric_building_id: fabricBuildingId,
          action_type: actionType,
          measure_label: measureLabel,
          source,
        }),
      })
      if (res.ok) {
        setDone(true)
      } else {
        const data = await res.json().catch(() => ({}))
        setError(data.detail || "Could not send the request. Please try again.")
      }
    } catch {
      setError("Something went wrong. Please try again.")
    } finally {
      setBusy(false)
    }
  }

  if (done && !open) {
    return (
      <span
        className={
          compact
            ? "inline-flex items-center gap-1 text-[11px] font-medium text-brand-emerald"
            : "inline-flex items-center gap-1.5 text-sm font-medium text-brand-emerald"
        }
      >
        ✓ Installer requested
      </span>
    )
  }

  const btnCls = compact
    ? "inline-flex items-center gap-1 rounded-md border border-brand-emerald/40 px-2 py-1 text-[11px] font-medium text-brand-emerald transition-colors hover:bg-brand-emerald/10"
    : "inline-flex items-center gap-1.5 rounded-md bg-brand-emerald px-4 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-brand-emerald/90"

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className={btnCls}>
        Request an installer
      </button>

      {open &&
        mounted &&
        createPortal(
          <div
            className="fixed inset-0 z-[70] flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-label="Request an installer"
          >
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => !busy && setOpen(false)}
              aria-hidden
            />
            <div className="relative w-full max-w-md rounded-xl border border-border-subtle bg-bg-elevated p-5 shadow-2xl">
              {done ? (
                <div className="space-y-3">
                  <h2 className="text-sm font-semibold text-brand-emerald">
                    ✓ Request received
                  </h2>
                  <p className="text-sm text-text-muted leading-relaxed">
                    We&rsquo;ll connect you with a vetted installer for{" "}
                    <span className="text-text-primary font-medium">
                      {measureLabel || "this measure"}
                    </span>
                    . Expect to hear from us shortly.
                  </p>
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => setOpen(false)}
                      className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-text-primary hover:bg-white/5"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <h2 className="text-sm font-semibold text-text-primary">
                    Request an installer
                  </h2>
                  <p className="text-sm text-text-muted leading-relaxed">
                    We&rsquo;ll introduce you to a vetted installer for{" "}
                    <span className="text-text-primary font-medium">
                      {measureLabel || "this measure"}
                    </span>
                    .
                  </p>
                  <p className="rounded-md border border-amber-400/20 bg-amber-400/5 px-3 py-2 text-[11px] leading-relaxed text-amber-200/90">
                    <span className="font-medium">Early access.</span> EnergyLens
                    introduces you to an installer — it does not warrant, price or
                    contract the work. We broker the introduction manually for now;
                    in-app matching, quotes and project tracking are on the roadmap.
                  </p>
                  {error && <p className="text-xs text-red-300">{error}</p>}
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setOpen(false)}
                      disabled={busy}
                      className="rounded-md border border-border-subtle px-3 py-1.5 text-sm text-text-primary hover:bg-white/5 disabled:opacity-60"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={send}
                      disabled={busy}
                      className="rounded-md bg-brand-emerald px-4 py-1.5 text-sm font-semibold text-bg-base hover:bg-brand-emerald/90 disabled:opacity-60"
                    >
                      {busy ? "Sending…" : "Send request"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>,
          document.body
        )}
    </>
  )
}
