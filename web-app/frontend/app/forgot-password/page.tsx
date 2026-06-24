"use client"
import { useState } from "react"
import Link from "next/link"
import { Loader2 } from "lucide-react"
import { LogoCard } from "@/app/components/LogoCard"

/**
 * /forgot-password — request a password-reset link.
 *
 * Posts the email to /api/auth/forgot-password (which proxies the backend with
 * INTERNAL_API_KEY). The backend always responds 200 and only emails a link if
 * an email/password account exists, so this page shows the same "check your
 * inbox" state either way — no account enumeration.
 */
export default function ForgotPassword() {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })
      if (!res.ok) {
        setError("Something went wrong. Please try again.")
        setLoading(false)
        return
      }
      setSent(true)
    } catch {
      setError("Network error. Please try again.")
      setLoading(false)
    }
  }

  return (
    <main id="main-content" className="min-h-screen bg-radial-emerald-glow flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-dot-grid opacity-30 pointer-events-none" />

      <Link
        href="/login"
        className="fixed top-6 left-6 z-20 text-text-faint hover:text-text-muted text-sm transition-colors"
      >
        ← Back to sign in
      </Link>

      <div className="relative z-10 w-full max-w-md">
        <div className="flex justify-center mb-8">
          <LogoCard iconSize={56} />
        </div>

        <div className="bg-bg-elevated border border-border-subtle rounded-lg p-8 shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          {sent ? (
            <div className="text-center">
              <h1 className="text-2xl font-bold text-text-primary mb-3 tracking-tight">
                Check your inbox
              </h1>
              <p className="text-text-muted text-sm mb-4 leading-relaxed">
                If an account exists for{" "}
                <span className="text-text-primary break-all">{email}</span>, we have
                sent a link to reset your password. It expires in 1 hour.
              </p>
              <p className="text-text-faint text-xs mb-6 leading-relaxed">
                Did not arrive? Check your spam folder, or email{" "}
                <a
                  href="mailto:alimert@energylens.eu"
                  className="text-brand-mint hover:text-brand-glow transition-colors"
                >
                  alimert@energylens.eu
                </a>
                .
              </p>
              <Link
                href="/login"
                className="inline-block bg-brand-emerald hover:bg-brand-deep text-white font-medium px-5 py-2 rounded-md text-sm transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
              >
                Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-text-primary mb-1 tracking-tight">
                Forgot your password?
              </h1>
              <p className="text-text-muted text-sm mb-6">
                Enter your account email and we will send you a link to reset it.
              </p>

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div>
                  <label htmlFor="email" className="block text-sm text-text-muted mb-1.5">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent transition-all"
                    disabled={loading}
                  />
                </div>

                {error && (
                  <div className="text-sm text-accent-red bg-accent-red/10 border border-accent-red/30 rounded-md px-3 py-2">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-brand-emerald hover:bg-brand-deep disabled:bg-brand-deep disabled:opacity-60 text-white font-medium px-6 py-2.5 rounded-md flex items-center justify-center gap-2 transition-colors mt-2 shadow-[0_0_24px_rgba(29,158,117,0.2)]"
                >
                  {loading && <Loader2 size={16} className="animate-spin" />}
                  {loading ? "Sending..." : "Send reset link"}
                </button>
              </form>

              <p className="text-center text-sm text-text-muted mt-6">
                Remembered it?{" "}
                <Link href="/login" className="text-brand-mint hover:text-brand-glow font-medium transition-colors">
                  Sign in
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </main>
  )
}
