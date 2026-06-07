/**
 * One headline KPI tile for /portfolio.
 *
 * Color semantics depend on the metric, via `lowerIsBetter`:
 *   - lowerIsBetter=true  (energy/EUI/cost/CO2): down -> emerald, up -> amber
 *   - lowerIsBetter=false (solar generation/renewable rate): up -> emerald, down -> amber
 * The arrow always reflects the physical change; only the color encodes good/bad.
 */
import { cn } from "@/lib/utils"
import { InfoTip } from "@/components/ui/info-tip"
import type { TermKey } from "@/lib/glossary"

type Direction = "up" | "down" | "neutral"

export type KPITileProps = {
  label: string
  value: number
  unit: string
  delta_pct: number | null
  direction: Direction
  accent: string
  /** When true (default) a decrease is "good". Set false for solar metrics. */
  lowerIsBetter?: boolean
  /** Optional glossary term key — renders an InfoTip beside the label. */
  term?: TermKey
}

function formatValue(value: number, unit: string): string {
  if (Math.abs(value) >= 10_000) {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(value)
  }
  const oneDecimal = unit === "EUR" || unit === "%" || unit.includes("kWh/m")
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: oneDecimal ? 1 : 0,
  }).format(value)
}

function formatDelta(pct: number | null, direction: Direction): string | null {
  if (pct === null) return null
  const arrow = direction === "up" ? "▲" : direction === "down" ? "▼" : "→"
  return `${arrow} ${Math.abs(pct).toFixed(1)}%`
}

const DELTA_STYLES: Record<"good" | "bad" | "neutral", string> = {
  good: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  bad: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  neutral: "bg-zinc-500/10 text-zinc-400 border-zinc-500/30",
}

export function KPITile({
  label,
  value,
  unit,
  delta_pct,
  direction,
  accent,
  lowerIsBetter = true,
  term,
}: KPITileProps) {
  const deltaText = formatDelta(delta_pct, direction)
  const goodDir: Direction = lowerIsBetter ? "down" : "up"
  const styleKey: "good" | "bad" | "neutral" =
    direction === "neutral" ? "neutral" : direction === goodDir ? "good" : "bad"

  return (
    <div
      className="relative rounded-xl border border-white/10 bg-white/[0.03] backdrop-blur-sm px-6 py-5"
      style={{ borderTopColor: accent, borderTopWidth: 2 }}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="size-1.5 rounded-full" style={{ backgroundColor: accent }} />
        <span className="text-[11px] uppercase tracking-[0.12em] text-white/60">
          {label}
        </span>
        {term && <InfoTip term={term} />}
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className="text-3xl font-semibold tabular-nums text-white">
          {formatValue(value, unit)}
        </span>
        <span className="text-sm font-normal text-white/50">{unit}</span>
      </div>

      {deltaText && (
        <div className="mt-3">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium border tabular-nums",
              DELTA_STYLES[styleKey]
            )}
          >
            {deltaText}
            <span className="text-white/40 font-normal">vs prior 30d</span>
          </span>
        </div>
      )}
    </div>
  )
}
