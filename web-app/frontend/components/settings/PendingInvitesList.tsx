"use client"

/**
 * PendingInvitesList — admin view of outstanding invitations.
 *
 * Each row offers "Copy link" (builds {origin}/invite/{token} and writes it
 * to the clipboard) and "Revoke". Renders nothing when there are no pending
 * invites so the page stays clean for a fresh org.
 */
import { useState } from "react"
import { Check, Clock, Copy, Loader2, X } from "lucide-react"

import { cn } from "@/lib/utils"
import { type PendingInviteItem, revokeInvite } from "@/lib/api/settings"

export function PendingInvitesList({
  invites,
  onRevoked,
}: {
  invites: PendingInviteItem[]
  onRevoked: (id: string) => void
}) {
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (invites.length === 0) return null

  function inviteUrl(token: string) {
    const origin = typeof window !== "undefined" ? window.location.origin : ""
    return `${origin}/invite/${token}`
  }

  async function copy(inv: PendingInviteItem) {
    setError(null)
    try {
      await navigator.clipboard.writeText(inviteUrl(inv.token))
      setCopiedId(inv.id)
      setTimeout(
        () => setCopiedId((c) => (c === inv.id ? null : c)),
        2000
      )
    } catch {
      setError("Couldn't copy to clipboard — copy the link manually.")
    }
  }

  async function revoke(id: string) {
    setBusyId(id)
    setError(null)
    const result = await revokeInvite(id)
    setBusyId(null)
    if (!result.ok) {
      setError(result.error)
      return
    }
    onRevoked(id)
  }

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-5">
      <header className="flex items-center gap-2 mb-2">
        <Clock className="w-4 h-4 text-brand-emerald" />
        <h2 className="text-sm font-semibold text-text-primary">
          Pending invitations
        </h2>
      </header>

      {error && <p className="mb-2 text-xs text-accent-red">{error}</p>}

      <div className="divide-y divide-border-subtle">
        {invites.map((inv) => {
          const busy = busyId === inv.id
          const copied = copiedId === inv.id
          return (
            <div
              key={inv.id}
              className="flex flex-wrap items-center gap-3 py-3"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-text-primary truncate">
                    {inv.email}
                  </span>
                  <span className="rounded-full border border-border-subtle bg-white/5 px-1.5 py-0.5 text-[10px] font-medium capitalize text-text-muted">
                    {inv.role}
                  </span>
                </div>
                <div className="text-xs text-text-muted">
                  Expires {new Date(inv.expires_at).toLocaleDateString()}
                  {inv.invited_by_email ? ` · invited by ${inv.invited_by_email}` : ""}
                </div>
              </div>

              <button
                type="button"
                onClick={() => copy(inv)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs transition-colors",
                  copied
                    ? "border-brand-emerald/40 text-brand-emerald"
                    : "border-border-subtle text-text-muted hover:border-brand-emerald hover:text-brand-emerald"
                )}
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
                {copied ? "Copied" : "Copy link"}
              </button>

              <button
                type="button"
                onClick={() => revoke(inv.id)}
                disabled={busy}
                aria-label={`Revoke invitation for ${inv.email}`}
                className="inline-flex h-7 w-7 items-center justify-center rounded-md text-text-muted transition-colors hover:bg-accent-red/10 hover:text-accent-red disabled:opacity-50"
              >
                {busy ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <X className="w-4 h-4" />
                )}
              </button>
            </div>
          )
        })}
      </div>
    </section>
  )
}
