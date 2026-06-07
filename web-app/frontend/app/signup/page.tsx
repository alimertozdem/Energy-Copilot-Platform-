"use client"
import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { signIn } from "next-auth/react"
import Link from "next/link"
import { Eye, EyeOff, Loader2 } from "lucide-react"
import { LogoCard } from "@/app/components/LogoCard"

function SignUpForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  // Where to land after signup. Defaults to /dashboard (unchanged behavior);
  // /invite passes its own URL so a freshly-created account returns to accept.
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard"

  const [displayName, setDisplayName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const loginHref =
    callbackUrl !== "/dashboard"
      ? `/login?callbackUrl=${encodeURIComponent(callbackUrl)}`
      : "/login"

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, display_name: displayName }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        let message = "Could not create account. Please try again."
        if (res.status === 409) {
          message = "Email already registered. Try signing in instead."
        } else if (res.status === 422) {
          const detail = body.detail
          if (Array.isArray(detail) && detail[0]?.msg) {
            message = detail[0].msg.replace(/^Value error,\s*/, "")
          }
        } else if (body.detail && typeof body.detail === "string") {
          message = body.detail
        }
        setError(message)
        setLoading(false)
        return
      }

      const signInResult = await signIn("credentials", {
        email,
        password,
        redirect: false,
      })

      if (signInResult?.error) {
        router.push(
          callbackUrl !== "/dashboard"
            ? `/login?registered=1&callbackUrl=${encodeURIComponent(callbackUrl)}`
            : "/login?registered=1"
        )
        return
      }

      router.push(callbackUrl)
    } catch {
      setError("Network error. Please try again.")
      setLoading(false)
    }
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
            Create account
          </h1>
          <p className="text-text-muted text-sm mb-6">
            Start your free workspace.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label htmlFor="displayName" className="block text-sm text-text-muted mb-1.5">
                Full Name
              </label>
              <input
                id="displayName"
                type="text"
                required
                maxLength={255}
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Ali Mert Özdemir"
                className="w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent transition-all"
                disabled={loading}
              />
            </div>

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

            <div>
              <label htmlFor="password" className="block text-sm text-text-muted mb-1.5">
                Password
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
              {loading ? "Creating..." : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-text-muted mt-6">
            Already have an account?{" "}
            <Link href={loginHref} className="text-brand-mint hover:text-brand-glow font-medium transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}

export default function SignUpPage() {
  return (
    <Suspense>
      <SignUpForm />
    </Suspense>
  )
}
