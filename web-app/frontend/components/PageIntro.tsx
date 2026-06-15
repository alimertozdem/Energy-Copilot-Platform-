"use client"

/**
 * PageIntro — a subtle, dismissible "what this page does" callout.
 *
 * Gives a newcomer (or a demo audience) a one-line read of a page's purpose and
 * how to use it. Dismissible per-page via localStorage so returning power users
 * aren't nagged. Starts visible (no flash-in for first-time/demo viewers); hides
 * on mount only if previously dismissed.
 */
import { Info, X } from "lucide-react"
import { useEffect, useState } from "react"

export function PageIntro({
  id,
  children,
}: {
  id: string
  children: React.ReactNode
}) {
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    try {
      if (localStorage.getItem(`el_intro_${id}`) === "1") setDismissed(true)
    } catch {
      /* localStorage unavailable — keep showing */
    }
  }, [id])

  if (dismissed) return null

  return (
    <div className="relative flex items-start gap-2.5 overflow-hidden rounded-lg border border-border-subtle border-l-2 border-l-brand-emerald/60 bg-gradient-to-r from-brand-emerald/[0.07] via-bg-elevated/40 to-transparent px-4 py-2.5 text-sm text-text-muted">
      <Info size={15} className="mt-0.5 shrink-0 text-brand-emerald" aria-hidden />
      <div className="flex-1 leading-relaxed">{children}</div>
      <button
        type="button"
        onClick={() => {
          try {
            localStorage.setItem(`el_intro_${id}`, "1")
          } catch {
            /* ignore */
          }
          setDismissed(true)
        }}
        aria-label="Dismiss this tip"
        className="shrink-0 rounded p-0.5 text-text-faint transition-colors hover:text-text-primary"
      >
        <X size={14} aria-hidden />
      </button>
    </div>
  )
}
