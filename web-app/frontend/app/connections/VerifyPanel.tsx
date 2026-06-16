"use client"

/**
 * VerifyPanel — "prove the pipeline works" section of /connections.
 *
 * Sends a few SIMULATED readings through the real ingest path (POST
 * /buildings/{id}/test-telemetry → bronze_iot_readings) and shows the latest
 * landed readings. This lets a manager confirm ingestion end-to-end with no
 * hardware and no CLI — replacing the old manual SQL token + simulator dance.
 *
 * Honest by design: simulated rows are tagged, and a test reading does NOT
 * change any device's status (status only reflects a real on-site agent).
 */
import { useCallback, useEffect, useState } from "react"
import { Activity, CheckCircle2, FlaskConical, RefreshCw } from "lucide-react"

import {
  type RecentReading,
  fetchRecentReadings,
  sendTestTelemetry,
} from "@/lib/api/connections"

function relTime(iso: string): string {
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return ""
  const mins = Math.floor((Date.now() - t) / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return new Date(iso).toLocaleString()
}

export function VerifyPanel({ buildingId }: { buildingId: string }) {
  const [readings, setReadings] = useState<RecentReading[]>([])
  const [sending, setSending] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    if (!buildingId) return
    const r = await fetchRecentReadings(buildingId, 8)
    if (r.ok) setReadings(r.data.readings)
  }, [buildingId])

  useEffect(() => {
    setNotice(null)
    setError(null)
    void reload()
  }, [reload])

  async function sendTest() {
    setSending(true)
    setError(null)
    setNotice(null)
    const r = await sendTestTelemetry(buildingId)
    setSending(false)
    if (!r.ok) {
      setError(r.error)
      return
    }
    const n = r.data.accepted
    setNotice(`${n} simulated reading${n === 1 ? "" : "s"} landed through the live ingest path.`)
    void reload()
  }

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/30 p-4">
      <div className="mb-3 flex items-center gap-2.5">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-emerald/15 ring-1 ring-brand-emerald/30">
          <FlaskConical className="h-4 w-4 text-brand-emerald" aria-hidden />
        </span>
        <div>
          <h2 className="font-display text-sm font-semibold text-text-primary">Verify the pipeline</h2>
          <p className="text-[11px] text-text-muted">
            Send a few simulated readings through the real ingest path — confirms it works end-to-end, no hardware.
          </p>
        </div>
      </div>

      {notice && (
        <div className="mb-3 flex items-center gap-1.5 rounded-md border border-brand-emerald/30 bg-brand-emerald/5 px-2.5 py-1.5 text-[11px] text-brand-emerald">
          <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> {notice}
        </div>
      )}
      {error && <div className="mb-3 text-xs text-red-300">{error}</div>}

      <div className="mb-3 flex items-center gap-2">
        <button
          type="button"
          onClick={() => void sendTest()}
          disabled={sending}
          className="inline-flex items-center gap-1.5 rounded-md border border-brand-emerald/40 px-3 py-1.5 text-sm text-brand-emerald transition-colors hover:bg-brand-emerald/10 disabled:opacity-50"
        >
          <FlaskConical className="h-3.5 w-3.5" />
          {sending ? "Sending…" : "Send test reading"}
        </button>
        <button
          type="button"
          onClick={() => void reload()}
          aria-label="Refresh readings"
          className="inline-flex items-center gap-1.5 rounded-md border border-border-subtle px-2.5 py-1.5 text-xs text-text-muted transition-colors hover:border-brand-emerald/60 hover:text-brand-emerald"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="mb-1.5 flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-text-faint">
        <Activity className="h-3 w-3" aria-hidden /> Recent landed readings
      </div>
      {readings.length === 0 ? (
        <p className="text-[11px] text-text-faint">
          No readings yet. Send a test reading, or point a live agent at this building.
        </p>
      ) : (
        <div className="space-y-1">
          {readings.map((r, i) => (
            <div
              key={i}
              className="flex flex-wrap items-center gap-2 rounded-md border border-border-subtle/60 bg-white/[0.02] px-2.5 py-1.5 text-[11px]"
            >
              <span className="text-text-primary">{r.sensor_type}</span>
              <span className="text-text-muted">
                {r.reading_value ?? "—"}
                {r.reading_unit ? ` ${r.reading_unit}` : ""}
              </span>
              {r.sensor_location && <span className="text-text-faint">@ {r.sensor_location}</span>}
              {r.simulated && (
                <span className="rounded border border-amber-400/30 bg-amber-400/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-300">
                  Simulated
                </span>
              )}
              <span className="ml-auto text-text-faint">{relTime(r.received_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
