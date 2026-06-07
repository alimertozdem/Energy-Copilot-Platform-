/**
 * /invite/[token] — invitation landing page.
 *
 * Server component, intentionally NOT inside AppChrome: the visitor may be
 * signed out and isn't a member of the org yet, so the authenticated nav is
 * inappropriate. Uses the same standalone branded shell as /login.
 *
 * Branches:
 *   - invalid token / expired / revoked / accepted -> static reason card
 *   - valid + signed in   -> Accept button (InviteAcceptClient)
 *   - valid + signed out  -> Sign in / Create account links (with callbackUrl)
 */
import Link from "next/link"
import { getServerSession } from "next-auth"

import { LogoCard } from "@/app/components/LogoCard"
import { authOptions } from "@/lib/auth/options"
import { fetchInvitePreview } from "@/lib/api/settings"

import { InviteAcceptClient } from "./InviteAcceptClient"

export default async function InvitePage({
  params,
}: {
  params: Promise<{ token: string }>
}) {
  const { token } = await params
  const session = await getServerSession(authOptions)
  const loggedIn = Boolean(session?.accessToken)
  const preview = await fetchInvitePreview(token)

  const valid = preview.ok && preview.data.is_valid

  let reason: string | null = null
  if (!preview.ok) {
    reason = "This invitation link is invalid or could not be found."
  } else if (!preview.data.is_valid) {
    reason =
      preview.data.status === "expired"
        ? "This invitation has expired. Ask an admin to send a new one."
        : preview.data.status === "revoked"
          ? "This invitation has been revoked."
          : preview.data.status === "accepted"
            ? "This invitation has already been accepted."
            : "This invitation is no longer valid."
  }

  return (
    <main id="main-content" className="min-h-screen bg-radial-emerald-glow flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-dot-grid opacity-30 pointer-events-none" />

      <Link
        href="/"
        className="fixed top-6 left-6 z-20 text-text-faint hover:text-text-muted text-sm transition-colors"
      >
        ← Back to home
      </Link>

      <div className="relative z-10 w-full max-w-md">
        <div className="flex justify-center mb-8">
          <LogoCard iconSize={56} />
        </div>

        <div className="bg-bg-elevated border border-border-subtle rounded-lg p-8 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          <h1 className="text-2xl font-bold text-text-primary mb-1 tracking-tight">
            You&apos;re invited
          </h1>

          {valid && preview.ok ? (
            <InviteAcceptClient
              token={token}
              preview={preview.data}
              loggedIn={loggedIn}
            />
          ) : (
            <>
              <p className="text-text-muted text-sm mt-2">{reason}</p>
              <Link
                href="/"
                className="mt-6 inline-block text-sm text-brand-mint hover:text-brand-glow font-medium transition-colors"
              >
                Go to EnergyLens →
              </Link>
            </>
          )}
        </div>
      </div>
    </main>
  )
}
