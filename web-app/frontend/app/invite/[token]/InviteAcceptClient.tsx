"use client"

/**
 * InviteAcceptClient — interactive half of the /invite landing page.
 *
 * Signed in  -> "Accept invitation" button -> acceptInvite -> /portfolio.
 * Signed out -> Sign in / Create account links carrying callbackUrl back to
 *               this same invite URL, so the user returns here to accept.
 */
import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Check, Loader2 } from "lucide-react"

import { type InvitationPreview, acceptInvite } from "@/lib/api/settings"

export function InviteAcceptClient({
  token,
  preview,
  loggedIn,
}: {
  token: string
  preview: InvitationPreview
  loggedIn: boolean
}) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const callbackTarget = encodeURIComponent(`/invite/${token}`)

  async function accept() {
    setBusy(true)
    setError(null)
    const result = await acceptInvite(token)
    if (!result.ok) {
      setError(result.error)
      setBusy(false)
      return
    }
    setDone(true)
    // Brief confirmation, then land in the portfolio of the joined org.
    setTimeout(() => router.push("/portfolio"), 1200)
  }

  if (done) {
    return (
      <div className="mt-3">
        <div className="flex items-center gap-2 text-brand-mint">
          <Check className="w-4 h-4" />
          <span className="text-sm font-medium">
            You&apos;ve joined {preview.organization_name}.
          </span>
        </div>
        <p className="text-text-muted text-sm mt-2">Taking you in…</p>
      </div>
    )
  }

  return (
    <div className="mt-2">
      <p className="text-text-muted text-sm">
        Join{" "}
        <span className="text-text-primary font-medium">
          {preview.organization_name}
        </span>{" "}
        as <span className="capitalize">{preview.role}</span>.
      </p>

      {loggedIn ? (
        <>
          <button
            type="button"
            onClick={accept}
            disabled={busy}
            className="mt-6 w-full bg-brand-emerald hover:bg-brand-deep disabled:bg-brand-deep disabled:opacity-60 text-white font-medium px-6 py-2.5 rounded-md flex items-center justify-center gap-2 transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
          >
            {busy && <Loader2 size={16} className="animate-spin" />}
            {busy ? "Joining…" : "Accept invitation"}
          </button>
          {error && (
            <div className="mt-3 text-sm text-accent-red bg-accent-red/10 border border-accent-red/30 rounded-md px-3 py-2">
              {error}
            </div>
          )}
        </>
      ) : (
        <div className="mt-6 space-y-3">
          <p className="text-sm text-text-muted">
            Sign in or create an account to accept this invitation.
          </p>
          <div className="flex gap-3">
            <Link
              href={`/login?callbackUrl=${callbackTarget}`}
              className="flex-1 text-center bg-brand-emerald hover:bg-brand-deep text-white font-medium px-4 py-2.5 rounded-md transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
            >
              Sign in
            </Link>
            <Link
              href={`/signup?callbackUrl=${callbackTarget}`}
              className="flex-1 text-center border border-border-subtle hover:border-brand-emerald text-text-primary hover:text-brand-emerald font-medium px-4 py-2.5 rounded-md transition-colors"
            >
              Create account
            </Link>
          </div>
          <p className="text-xs text-text-faint">
            Invitation for {preview.email}
          </p>
        </div>
      )}
    </div>
  )
}
