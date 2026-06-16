/**
 * ComfortPanel — comfort & operation analytics (Layer 3 of Heating & HVAC).
 *
 * Setpoint compliance, over-/under-heating, supply/return delta-T, CO₂ air
 * quality, humidity — from bronze telemetry. Surfaces the operational savings
 * lever when over-heating is significant. Honest: standard comfort bands, basis
 * badge, empty state when no climate sensors are connected.
 */
import Link from "next/link"
import { Lightbulb, Thermometer, Wind } from "lucide-react"

import type { ComfortAssessment } from "@/lib/api/heating"

function Bar({ segments }: { segments: { pct: number; cls: string }[] }) {
  return (
    <div className="mt-1 flex h-2 w-full overflow-hidden rounded-full bg-white/5">
      {segments.map((s, i) => (
        <div key={i} className={s.cls} style={{ width: `${s.pct}%` }} />
      ))}
    </div>
  )
}

export function ComfortPanel({
  comfort,
  buildingId,
}: {
  comfort: ComfortAssessment
  buildingId: string
}) {
  const connectHref = `/connections?building_id=${encodeURIComponent(buildingId)}`

  if (!comfort.has_data) {
    return (
      <div className="rounded-xl border border-dashed border-border-subtle bg-bg-elevated/20 p-5 text-center">
        <Thermometer className="mx-auto mb-2 h-6 w-6 text-text-faint" aria-hidden />
        <div className="mb-1 text-sm text-text-primary">No comfort data yet</div>
        <div className="text-xs text-text-muted">
          Connect zone temperature / CO₂ sensors (or{" "}
          <Link href={connectHref} className="text-brand-emerald hover:underline">add points & send a test reading</Link>
          ) to see setpoint compliance, ΔT and air quality.
        </div>
      </div>
    )
  }

  const t = comfort.temperature
  const c = comfort.co2
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/30 p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Thermometer className="h-4 w-4 text-sky-300" aria-hidden />
        <h2 className="text-sm font-semibold text-text-primary">Comfort &amp; operation</h2>
        {comfort.simulated && (
          <span className="rounded border border-amber-400/30 bg-amber-400/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-300">
            Simulated
          </span>
        )}
        <span className="ml-auto text-[11px] text-text-faint">last {Math.round(comfort.window_hours / 24)}d</span>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {t && (
          <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-[11px] uppercase tracking-wide text-text-faint">Zone temperature</span>
              <span className="text-sm font-semibold tabular-nums text-text-primary">{t.avg}°C avg</span>
            </div>
            <Bar
              segments={[
                { pct: t.under_pct, cls: "bg-amber-400/70" },
                { pct: t.in_band_pct, cls: "bg-brand-emerald/70" },
                { pct: t.over_pct, cls: "bg-red-400/70" },
              ]}
            />
            <div className="mt-1 text-[11px] text-text-faint">
              {t.in_band_pct}% in band ({t.band_low}–{t.band_high}°C) · {t.under_pct}% under · {t.over_pct}% over
            </div>
          </div>
        )}

        {c && (
          <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
            <div className="flex items-baseline justify-between">
              <span className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-text-faint">
                <Wind className="h-3 w-3" aria-hidden /> CO₂ air quality
              </span>
              <span className="text-sm font-semibold tabular-nums text-text-primary">{c.avg} ppm avg</span>
            </div>
            <Bar
              segments={[
                { pct: c.good_pct, cls: "bg-brand-emerald/70" },
                { pct: c.fair_pct, cls: "bg-amber-400/70" },
                { pct: c.poor_pct, cls: "bg-red-400/70" },
              ]}
            />
            <div className="mt-1 text-[11px] text-text-faint">
              {c.good_pct}% good (&lt;800) · {c.fair_pct}% fair · {c.poor_pct}% poor (&gt;1200)
            </div>
          </div>
        )}

        {comfort.delta_t != null && (
          <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
            <span className="text-[11px] uppercase tracking-wide text-text-faint">Supply − return ΔT</span>
            <div className="mt-1 text-sm font-semibold tabular-nums text-text-primary">{comfort.delta_t} °C</div>
            <div className="text-[11px] text-text-faint">context-dependent — heat pumps favour a low ΔT (~5°C); radiator systems run higher</div>
          </div>
        )}

        {comfort.humidity && (
          <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
            <span className="text-[11px] uppercase tracking-wide text-text-faint">Humidity</span>
            <div className="mt-1 text-sm font-semibold tabular-nums text-text-primary">{comfort.humidity.avg}%</div>
            <div className="text-[11px] text-text-faint">{comfort.humidity.in_band_pct}% in 30–60% comfort band</div>
          </div>
        )}
      </div>

      {comfort.operational_hint && (
        <div className="mt-3 flex items-start gap-2 rounded-md border border-amber-400/30 bg-amber-400/5 px-3 py-2 text-[11px] text-amber-200">
          <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          <span>{comfort.operational_hint}</span>
        </div>
      )}

      <p className="mt-2 text-[10px] text-text-faint">
        Comfort references: DIN EN 16798-1 (20–24°C Cat. II), CO₂ 800/1200 ppm. Indicative.
      </p>
    </div>
  )
}
