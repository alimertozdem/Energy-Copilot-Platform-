/**
 * 404 Not Found — branded page for any unmatched route.
 *
 * Server component. Renders on the brand background (matches RouteLoading /
 * error.tsx) with paths back into the app. Previously the app fell through to
 * Next's default 404; this keeps a bad URL on-brand for the demo.
 */
import Link from "next/link"

export default function NotFound() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-bg-base bg-radial-emerald-glow p-8">
      <div className="absolute inset-0 bg-dot-grid pointer-events-none" aria-hidden />

      <div className="relative w-full max-w-md rounded-2xl border border-border-subtle bg-bg-elevated/70 p-8 text-center backdrop-blur-sm">
        <div className="text-5xl font-semibold tracking-tight text-brand-emerald tabular-nums">
          404
        </div>
        <h1 className="mt-2 text-lg font-semibold text-text-primary">
          Page not found
        </h1>
        <p className="mt-2 text-sm text-text-muted">
          The page you&apos;re looking for doesn&apos;t exist or may have moved.
        </p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <Link
            href="/portfolio"
            className="inline-flex items-center rounded-md border border-border-subtle px-4 py-2 text-sm text-text-primary transition-colors hover:border-brand-emerald hover:text-brand-emerald"
          >
            Back to portfolio
          </Link>
          <Link
            href="/demo"
            className="inline-flex items-center rounded-md px-4 py-2 text-sm text-text-muted transition-colors hover:text-text-primary"
          >
            View demo
          </Link>
        </div>
      </div>
    </div>
  )
}
