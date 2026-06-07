"use client"

/**
 * Exchanges the magic-link token for the resident session cookie, then redirects
 * to /residence. Shows a minimal status while working and a friendly error if the
 * link is invalid/expired. No NextAuth involvement.
 */
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

import { LogoCard } from "@/app/components/LogoCard"

export function ResidenceEnterClient({ token }: { token: string | null }) {
  const router = useRouter()
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setErrorMsg("This sign-in link is missing its token.")
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch("/api/residence/session", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        })
        if (cancelled) return
        if (res.ok) {
          router.replace("/residence")
        } else {
          const data = await res.json().catch(() => ({}))
          setErrorMsg(data.detail || "This sign-in link is invalid or has expired.")
        }
      } catch {
        if (!cancelled) setErrorMsg("Something went wrong. Please try again.")
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token, router])

  return (
    <div className="relative min-h-screen bg-bg-base bg-radial-emerald-glow">
      <div className="absolute inset-0 bg-dot-grid pointer-events-none" aria-hidden />
      <main className="relative z-10 mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6">
        <div className="mb-6">
          <LogoCard iconSize={44} />
        </div>
        <div className="w-full rounded-xl border border-border-subtle bg-bg-elevated/40 p-6 text-center">
          {errorMsg === null ? (
            <>
              <p className="text-sm font-semibold text-text-primary">Signing you in…</p>
              <p className="mt-1 text-xs text-text-muted">One moment while we open your home energy view.</p>
            </>
          ) : (
            <>
              <p className="text-sm font-semibold text-text-primary">We couldn&rsquo;t sign you in</p>
              <p className="mt-1 text-xs text-text-muted">{errorMsg}</p>
              <p className="mt-3 text-[11px] text-text-faint">
                Ask your building manager for a fresh link.
              </p>
              <Link
                href="/residence"
                className="mt-4 inline-block text-xs font-medium text-brand-emerald hover:text-brand-emerald/80"
              >
                Go to my home energy
              </Link>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
