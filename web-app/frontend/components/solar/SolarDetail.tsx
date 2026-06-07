/**
 * Solar detail content (Solar initiative C). Pure presentational, server-safe.
 * Custom SVG charts (no chart lib): a generation-trend area + a
 * self-consumed-vs-total area. Summary stats above.
 */
import type { SolarDetailResponse, SolarSeriesPoint } from "@/lib/api/solar"
import { InfoTip } from "@/components/ui/info-tip"
import type { TermKey } from "@/lib/glossary"

const AMBER = "#F59E0B"
const EMERALD = "#1D9E75"

function fmt(n: number, digits = 0): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(n)
}

export function SolarDetail({ data }: { data: SolarDetailResponse }) {
  if (!data.has_data || !data.summary) {
    return (
      <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-8 text-center">
        <div className="text-sm text-text-primary mb-1">No solar generation yet</div>
        <div className="text-xs text-text-muted">
          None of your buildings has on-site solar data in this window. Add a
          building with solar PV, or explore the sample portfolio to preview
          how this page looks.
        </div>
      </div>
    )
  }

  const s = data.summary

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Generated" value={`${fmt(s.total_generated_kwh)} kWh`} sub={`last ${s.days} days`} />
        <Stat label="Self-consumption" term="self_consumption" value={`${fmt(s.self_consumption_rate, 1)} %`} sub="of generation used on-site" />
        <Stat
          label="Specific yield"
          term="specific_yield"
          value={s.specific_yield_kwh_kwp != null ? `${fmt(s.specific_yield_kwh_kwp)} kWh/kWp` : "—"}
          sub="annualized"
        />
        <Stat
          label="Avg performance"
          term="performance_ratio"
          value={s.avg_performance_ratio != null ? `${fmt(s.avg_performance_ratio * 100, 1)} %` : "—"}
          sub={s.avg_performance_ratio != null && s.avg_performance_ratio < 0.65 ? "below 65% — check panels" : "performance ratio"}
        />
      </div>

      <ChartCard title="Daily generation" subtitle={`${fmt(s.pv_capacity_kwp)} kWp installed`}>
        <AreaChart
          series={data.series}
          pick={(p) => p.generated_kwh}
          stroke={AMBER}
          fill={AMBER}
        />
      </ChartCard>

      <ChartCard
        title="Self-consumed vs total generation"
        subtitle={`${fmt(s.total_self_consumed_kwh)} kWh used · ${fmt(s.total_exported_kwh)} kWh exported`}
      >
        <LayeredAreaChart series={data.series} />
        <div className="flex items-center gap-4 mt-2 text-xs text-text-muted">
          <Legend color={EMERALD} label="Self-consumed" />
          <Legend color={AMBER} label="Total generated (rest = exported)" />
        </div>
      </ChartCard>
    </div>
  )
}

function Stat({
  label,
  value,
  sub,
  term,
}: {
  label: string
  value: string
  sub: string
  term?: TermKey
}) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 px-5 py-4">
      <div className="flex items-center gap-1 text-[11px] uppercase tracking-[0.12em] text-text-muted">
        {label}
        {term && <InfoTip term={term} />}
      </div>
      <div className="text-2xl font-semibold text-text-primary mt-1 tabular-nums">{value}</div>
      <div className="text-xs text-text-faint mt-0.5">{sub}</div>
    </div>
  )
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
      <div className="mb-3">
        <h3 className="text-sm font-medium text-text-primary">{title}</h3>
        {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </section>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="size-2.5 rounded-sm" style={{ backgroundColor: color }} />
      {label}
    </span>
  )
}

const W = 760
const H = 180

function AreaChart({
  series,
  pick,
  stroke,
  fill,
}: {
  series: SolarSeriesPoint[]
  pick: (p: SolarSeriesPoint) => number
  stroke: string
  fill: string
}) {
  const vals = series.map(pick)
  const n = vals.length
  const max = Math.max(...vals, 1)
  const x = (i: number) => (n <= 1 ? 0 : (i / (n - 1)) * W)
  const y = (v: number) => H - (v / max) * (H - 8)
  const line = vals
    .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
    .join(" ")
  const area = n > 0 ? `${line} L${W.toFixed(1)},${H} L0,${H} Z` : ""

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-44" preserveAspectRatio="none">
      <path d={area} fill={fill} opacity={0.15} />
      <path d={line} fill="none" stroke={stroke} strokeWidth={2} vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function LayeredAreaChart({ series }: { series: SolarSeriesPoint[] }) {
  const totals = series.map((p) => p.self_consumed_kwh + p.exported_kwh)
  const n = series.length
  const max = Math.max(...totals, 1)
  const x = (i: number) => (n <= 1 ? 0 : (i / (n - 1)) * W)
  const y = (v: number) => H - (v / max) * (H - 8)

  const totalLine = series
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.self_consumed_kwh + p.exported_kwh).toFixed(1)}`)
    .join(" ")
  const totalArea = n > 0 ? `${totalLine} L${W.toFixed(1)},${H} L0,${H} Z` : ""

  const selfLine = series
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.self_consumed_kwh).toFixed(1)}`)
    .join(" ")
  const selfArea = n > 0 ? `${selfLine} L${W.toFixed(1)},${H} L0,${H} Z` : ""

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-44" preserveAspectRatio="none">
      <path d={totalArea} fill={AMBER} opacity={0.12} />
      <path d={totalLine} fill="none" stroke={AMBER} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
      <path d={selfArea} fill={EMERALD} opacity={0.2} />
      <path d={selfLine} fill="none" stroke={EMERALD} strokeWidth={2} vectorEffect="non-scaling-stroke" />
    </svg>
  )
}
