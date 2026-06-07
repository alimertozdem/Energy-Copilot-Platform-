/**
 * FetchErrorNotice — shared error block for server-fetched pages.
 *
 * Distinguishes two cases so the demo never shows a scary crash:
 *   - "fabric_unavailable" → a calm amber notice (the Fabric warehouse is
 *     syncing / briefly offline; a gold table dropped or hasn't synced). This
 *     is operational, not a user error — see the backend pyodbc.Error → 503
 *     handler in main.py.
 *   - anything else → the generic red "Failed to load {label}" block.
 *
 * Used by /portfolio, /actions, /solar, /alerts error branches.
 */
import { CloudOff } from "lucide-react"

export function FetchErrorNotice({
  error,
  label,
}: {
  error: string
  label: string
}) {
  if (error === "fabric_unavailable") {
    return (
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-6 text-center">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-amber-500/15">
          <CloudOff className="h-5 w-5 text-amber-300" aria-hidden />
        </div>
        <h3 className="text-sm font-semibold text-text-primary">
          Live data is temporarily unavailable
        </h3>
        <p className="mx-auto mt-1 max-w-md text-xs text-text-muted">
          The analytics warehouse is syncing or briefly offline. This usually
          clears on its own — refresh in a moment.
        </p>
      </div>
    )
  }
  return (
    <div className="rounded-lg border border-accent-red/30 bg-accent-red/5 p-4 text-text-primary">
      <div className="text-sm font-medium mb-1">Failed to load {label}</div>
      <div className="text-xs text-text-muted">{error}</div>
    </div>
  )
}
