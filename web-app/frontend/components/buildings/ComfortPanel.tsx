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
  heatCostEur,
}: {
  comfort: ComfortAssessment
  buildingId: string
  heatCostEur?: number | null
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

      {comfort.actions && comfort.actions.length > 0 && (
        <div className="mt-3 space-y-2">
          <div className="text-[11px] font-medium uppercase tracking-wide text-text-faint">
            Operational actions — low / no CapEx
          </div>
          {comfort.actions.map((a) => {
            const tone =
              a.kind === "savings"
                ? "border-brand-emerald/25 bg-brand-emerald/5"
                : a.kind === "comfort"
                  ? "border-amber-400/25 bg-amber-400/5"
                  : "border-sky-400/25 bg-sky-400/5"
            const hasEur =
              a.kind === "savings" && a.saving_pct_low != null && a.saving_pct_high != null && heatCostEur != null && heatCostEur > 0
            const eurLow = hasEur ? Math.round((heatCostEur as number) * (a.saving_pct_low as number) / 100) : null
            const eurHigh = hasEur ? Math.round((heatCostEur as number) * (a.saving_pct_high as number) / 100) : null
            return (
              <div key={a.key} className={`flex items-start gap-2 rounded-md border px-3 py-2 ${tone}`}>
                <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-text-muted" aria-hidden />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                    <span className="text-xs font-medium text-text-primary">{a.title}</span>
                    {hasEur ? (
                      <span className="text-xs font-semibold tabular-nums text-brand-emerald">
                        €{new Intl.NumberFormat("en-US").format(eurLow as number)}–€
                        {new Intl.NumberFormat("en-US").format(eurHigh as number)}/yr
                        <span className="ml-1 text-[10px] font-normal text-text-faint">
                          ({a.saving_pct_low}–{a.saving_pct_high}%)
                        </span>
                      </span>
                    ) : a.kind === "savings" && a.saving_pct_low != null ? (
                      <span className="text-[10px] text-text-faint">{a.saving_pct_low}–{a.saving_pct_high}% heating</span>
                    ) : (
                      <span className="text-[10px] uppercase tracking-wide text-text-faint">
                        {a.kind === "iaq" ? "air quality" : "comfort"}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 text-[11px] leading-relaxed text-text-faint">{a.detail}</div>
                </div>
              </div>
            )
          })}
          <p className="text-[10px] text-text-faint">
            Operational tuning — overlaps the package&rsquo;s hydraulic-balancing (T0) step; don&rsquo;t add it on top of the retrofit total.
          </p>
        </div>
      )}

      <p className="mt-2 text-[10px] text-text-faint">
        Comfort references: DIN EN 16798-1 (20–24°C Cat. II), CO₂ 800/1200 ppm. Indicative.
      </p>
    </div>
  )
}
