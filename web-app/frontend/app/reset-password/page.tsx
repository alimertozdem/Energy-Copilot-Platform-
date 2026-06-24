"use client"
import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { LogoCard } from "@/app/components/LogoCard"

const inputCls =
  "w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 pr-10 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent transition-all"

function ResetPasswordForm() {
  const router = useRouter()
  const token = useSearchParams().get("token") || ""

  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (password !== confirm) {
      setError("The two passwords do not match.")
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        let message = "Could not reset your password. Please try again."
        if (res.status === 400) {
          message =
            typeof body.detail === "string"
              ? body.detail
              : "This reset link is invalid or has expired. Request a new one."
        } else if (res.status === 422) {
          const detail = body.detail
          if (Array.isArray(detail) && detail[0]?.msg) {
            message = detail[0].msg.replace(/^Value error,\s*/, "")
          }
        } else if (typeof body.detail === "string") {
          message = body.detail
        }
        setError(message)
        setLoading(false)
        return
      }
      router.push("/login?reset=1")
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
          {!token ? (
            <div className="text-center">
              <h1 className="text-2xl font-bold text-text-primary mb-3 tracking-tight">
                Invalid reset link
              </h1>
              <p className="text-text-muted text-sm mb-6 leading-relaxed">
                This link is missing its reset token. Request a fresh one and try again.
              </p>
              <Link
                href="/forgot-password"
                className="inline-block bg-brand-emerald hover:bg-brand-deep text-white font-medium px-5 py-2 rounded-md text-sm transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
              >
                Request a new link
              </Link>
            </div>
          ) : (
            <>
              <h1 className="text-2xl font-bold text-text-primary mb-1 tracking-tight">
                Choose a new password
              </h1>
              <p className="text-text-muted text-sm mb-6">
                Pick a strong password you have not used here before.
              </p>

              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div>
                  <label htmlFor="password" className="block text-sm text-text-muted mb-1.5">
                    New password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      required
                      minLength={8}
                      maxLength={128}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="At least 8 characters, 1 number"
                      className={inputCls}
                      disabled={loading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-text-faint hover:text-text-muted p-1 transition-colors"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirm" className="block text-sm text-text-muted mb-1.5">
                    Confirm new password
                  </label>
                  <input
                    id="confirm"
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={8}
                    maxLength={128}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="Re-enter your new password"
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
                  {loading ? "Saving..." : "Reset password"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </main>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  )
}
