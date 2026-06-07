"use client"

/**
 * Route error boundary for the app. Catches render/runtime errors in page
 * segments and shows a branded "something went wrong" card with a retry,
 * instead of a blank crash. (Root-layout errors would need global-error.tsx;
 * this covers page-level errors, which is what we want.)
 */
import { useEffect } from "react"

export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log only the message -- never the whole error object (avoids leaking
    // cross-origin refs into the dev logger; mirrors the embed-logging caveat).
    console.error("[route error]", error?.message ?? "unknown")
  }, [error])

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-bg-base bg-radial-emerald-glow p-8">
      <div className="absolute inset-0 bg-dot-grid pointer-events-none" aria-hidden />
      <div className="relative w-full max-w-md rounded-2xl border border-border-subtle bg-bg-elevated/70 p-8 text-center backdrop-blur-sm">
        <h1 className="text-lg font-semibold text-text-primary">
          Something went wrong
        </h1>
        <p className="mt-2 text-sm text-text-muted">
          An unexpected error occurred while loading this page. You can try
          again, or head back and retry.
        </p>
        <button
          type="button"
          onClick={() => reset()}
          className="mt-6 inline-flex items-center rounded-md border border-border-subtle px-4 py-2 text-sm text-text-primary transition-colors hover:border-brand-emerald hover:text-brand-emerald"
        >
          Try again
        </button>
      </div>
    </div>
  )
}
