/**
 * RouteLoading -- branded full-page loading skeleton for route-level loading.tsx
 * files. The app has no shared authenticated layout (each page renders its own
 * AppChrome), so this stands alone on the brand background with a faux top bar +
 * content shimmer. It approximates the page structure (KPI tiles + table rows)
 * so the swap to the real page feels continuous rather than a blank flash.
 */
type RouteLoadingProps = {
  accent?: string
  label?: string
}

export function RouteLoading({
  accent = "#1D9E75",
  label = "Loading…",
}: RouteLoadingProps) {
  return (
    <div className="relative min-h-screen bg-bg-base bg-radial-emerald-glow">
      <div className="absolute inset-0 bg-dot-grid pointer-events-none" aria-hidden />

      {/* Faux top bar -- mirrors AppChrome's height/position so the handoff to
          the real chrome is smooth. */}
      <div className="relative border-b border-border-subtle bg-bg-elevated/60 backdrop-blur-sm">
        <div className="flex items-center gap-4 px-6 py-3">
          <div className="h-10 w-10 animate-pulse rounded-lg bg-white/5" />
          <div className="h-4 w-40 animate-pulse rounded bg-white/5" />
          <div className="ml-auto h-7 w-24 animate-pulse rounded-md bg-white/5" />
        </div>
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-6 py-8">
        <div className="mb-6 flex items-center gap-2">
          <span className="relative inline-flex h-2 w-2" aria-hidden>
            <span
              className="absolute inset-0 animate-ping rounded-full opacity-60"
              style={{ backgroundColor: accent }}
            />
            <span
              className="relative h-2 w-2 rounded-full"
              style={{ backgroundColor: accent }}
            />
          </span>
          <span className="text-sm text-text-muted">{label}</span>
        </div>

        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-xl border border-border-subtle bg-bg-elevated/60"
            />
          ))}
        </div>

        <div className="space-y-3">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-12 animate-pulse rounded-lg border border-border-subtle bg-bg-elevated/40"
            />
          ))}
        </div>
      </div>
    </div>
  )
}
