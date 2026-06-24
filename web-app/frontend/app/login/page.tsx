"use client"
import { useState, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { signIn } from "next-auth/react"
import Link from "next/link"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { LogoCard } from "@/app/components/LogoCard"

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const justRegistered = searchParams.get("registered") === "1"
  const justReset = searchParams.get("reset") === "1"
  // Where to land after a successful sign-in. Defaults to /dashboard so
  // existing behavior is unchanged; /invite passes its own URL here.
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard"

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    })

    if (result?.error) {
      setError("Invalid email or password.")
      setLoading(false)
      return
    }

    router.push(callbackUrl)
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
            Welcome back
          </h1>
          <p className="text-text-muted text-sm mb-6">
            Sign in with email and password.
          </p>

          {justRegistered && (
            <div className="text-sm text-brand-mint bg-brand-emerald/10 border border-brand-emerald/30 rounded-md px-3 py-2 mb-4">
              Account created. Please sign in to continue.
            </div>
          )}

          {justReset && (
            <div className="text-sm text-brand-mint bg-brand-emerald/10 border border-brand-emerald/30 rounded-md px-3 py-2 mb-4">
              Password updated. Sign in with your new password.
            </div>
          )}

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
                autoFocus
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="block text-sm text-text-muted">
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-text-faint hover:text-text-muted transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 pr-10 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent transition-all"
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
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm text-text-muted mt-6">
            New here?{" "}
            <Link
              href="/signup"
              className="text-brand-mint hover:text-brand-glow font-medium transition-colors"
            >
              Create account
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
