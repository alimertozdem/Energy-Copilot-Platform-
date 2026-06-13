"use client"

/**
 * SampleDataToggle — per-user switch to load / remove the sample (demo) buildings.
 *
 * The sample buildings (B001–B010) carry full Fabric data, so they are useful for
 * previewing and testing the reports. A real customer can turn them OFF to see only
 * their own buildings. On change it PUTs via the proxy and refreshes the server
 * component so the building list / portfolio updates.
 */
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"

import { setSampleData } from "@/lib/api/sampleData"

export function SampleDataToggle({ initialEnabled }: { initialEnabled: boolean }) {
  const router = useRouter()
  const [enabled, setEnabled] = useState(initialEnabled)
  const [busy, setBusy] = useState(false)
  const [, startTransition] = useTransition()
  const [error, setError] = useState<string | null>(null)

  async function toggle() {
    if (busy) return
    setBusy(true)
    setError(null)
    const next = !enabled
    const res = await setSampleData(next)
    if (res.ok) {
      setEnabled(res.data.enabled)
      startTransition(() => router.refresh())
    } else {
      setError(res.error)
    }
    setBusy(false)
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        onClick={toggle}
        disabled={busy}
        title="Show the sample / demo buildings (with full data) in your portfolio"
        className="inline-flex items-center gap-2 rounded-full border border-border-subtle bg-bg-elevated/50 px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text-primary disabled:opacity-60"
      >
        <span
          className={`inline-block h-4 w-7 rounded-full p-0.5 transition-colors ${
            enabled ? "bg-brand-emerald/70" : "bg-white/15"
          }`}
        >
          <span
            className={`block h-3 w-3 rounded-full bg-white transition-transform ${
              enabled ? "translate-x-3" : "translate-x-0"
            }`}
          />
        </span>
        <span>Sample data {enabled ? "on" : "off"}</span>
      </button>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
}
