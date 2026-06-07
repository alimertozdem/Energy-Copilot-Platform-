/**
 * MaccCurve — portfolio Marginal Abatement Cost Curve (server component).
 *
 * Classic decarbonization decision chart built from the recommendation catalog:
 * measures sorted by abatement cost (€/tCO₂), bar WIDTH = annual CO₂ abated, bar
 * HEIGHT = cost per tonne. Cost-negative bars (left, emerald) save money AND
 * carbon ("no-regret"); cost-positive bars (right, amber→orange) cost money.
 *
 * INDICATIVE — energy assumptions (stated, awaiting confirmation):
 *   * measure lifetimes by type (HVAC 15y, Lighting 12y, Envelope 30y,
 *     Controls 10y, Renewables 20y, default 15y);
 *   * NO discounting (simple undiscounted lifetime cost of conserved carbon);
 *   * abatement cost = (net capex − lifetime × annual saving) / (lifetime × tCO₂).
 * These are conservative defaults; refine per the customer's cost of capital.
 */
import type { ActionItem } from "@/lib/api/actions"

const LIFETIME: Record<string, number> = {
  HVAC: 15,
  Lighting: 12,
  Envelope: 30,
  Controls: 10,
  Renewables: 20,
}
const DEFAULT_LIFETIME = 15

type Measure = {
  title: string
  building: string
  type: string
  co2t: number
  cost: number
}

function computeMeasures(actions: ActionItem[]): Measure[] {
  const out: Measure[] = []
  for (const a of actions) {
    const co2t = (a.co2_saving_kg ?? 0) / 1000
    if (co2t <= 0) continue
    const life = LIFETIME[a.action_type ?? ""] ?? DEFAULT_LIFETIME
    const netCost = a.net_capex_eur ?? a.capex_eur ?? 0
    const annualSaving = a.annual_saving_eur ?? 0
    const cost = (netCost - life * annualSaving) / (life * co2t)
    out.push({
      title: a.title ?? "Measure",
      building: a.building_name,
      type: a.action_type ?? "—",
      co2t,
      cost,
    })
  }
  return out.sort((x, y) => x.cost - y.cost)
}

function barColor(cost: number): string {
  if (cost <= 0) return "#1D9E75"
  if (cost < 150) return "#EAB308"
  return "#F97316"
}

function fmt(n: number): string {
  return Math.round(n).toLocaleString("en-US")
}

export function MaccCurve({ actions }: { actions: ActionItem[] }) {
  const measures = computeMeasures(actions)
  if (measures.length === 0) return null

  const W = 820
  const H = 300
  const padL = 60
  const padR = 16
  const padT = 18
  const padB = 46
  const plotW = W - padL - padR
  const plotH = H - padT - padB

  const totalCo2 = measures.reduce((s, m) => s + m.co2t, 0)
  const noRegret = measures.filter((m) => m.cost <= 0)
  const noRegretCo2 = noRegret.reduce((s, m) => s + m.co2t, 0)

  const maxC = Math.max(0, ...measures.map((m) => m.cost))
  const minC = Math.min(0, ...measures.map((m) => m.cost))
  const range = maxC - minC || 1
  const yOf = (c: number) => padT + ((maxC - c) / range) * plotH
  const zeroY = yOf(0)

  let x = padL
  const bars = measures.map((m) => {
    const w = Math.max((m.co2t / totalCo2) * plotW, 1)
    const bx = x
    x += w
    const yc = yOf(m.cost)
    return {
      x: bx,
      w,
      top: Math.min(yc, zeroY),
      h: Math.max(Math.abs(yc - zeroY), 1),
      color: barColor(m.cost),
      m,
    }
  })

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">Marginal abatement cost curve</h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Decarbonization measures ranked by cost per tonne of CO₂ avoided.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[11px]">
          <span className="rounded-md bg-brand-emerald/10 px-2 py-1 text-brand-emerald">
            {noRegret.length} no-regret · {fmt(noRegretCo2)} tCO₂/yr
          </span>
          <span className="rounded-md bg-white/[0.04] px-2 py-1 text-text-muted">
            {fmt(totalCo2)} tCO₂/yr abatable
          </span>
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="mt-4 w-full" role="img" aria-label="Marginal abatement cost curve">
        {/* y grid + labels */}
        {[maxC, (maxC + minC) / 2, minC].map((c, i) => (
          <g key={i}>
            <line x1={padL} x2={W - padR} y1={yOf(c)} y2={yOf(c)} stroke="rgba(148,163,184,0.12)" strokeWidth="1" />
            <text x={padL - 8} y={yOf(c) + 3} textAnchor="end" fontSize="10" fill="#64748B">
              {fmt(c)}
            </text>
          </g>
        ))}
        {/* zero line */}
        <line x1={padL} x2={W - padR} y1={zeroY} y2={zeroY} stroke="rgba(148,163,184,0.4)" strokeWidth="1.5" />
        {/* bars */}
        {bars.map((b, i) => (
          <rect key={i} x={b.x} y={b.top} width={b.w} height={b.h} fill={b.color} opacity={0.9}>
            <title>{`${b.m.title} (${b.m.building}) · ${fmt(b.m.co2t)} tCO₂/yr · €${fmt(b.m.cost)}/tCO₂`}</title>
          </rect>
        ))}
        {/* axis labels */}
        <text x={padL} y={H - 8} fontSize="10" fill="#94A3B8">€0 line — measures left save money + carbon</text>
        <text x={W - padR} y={H - 8} textAnchor="end" fontSize="10" fill="#64748B">cumulative tCO₂/yr →</text>
        <text x="14" y={padT + 6} fontSize="10" fill="#94A3B8" transform={`rotate(-90 14 ${padT + 6})`}>€ / tCO₂</text>
      </svg>

      <p className="mt-3 text-[11px] leading-relaxed text-text-faint">
        Indicative. Assumes measure lifetimes (HVAC 15y · Lighting 12y · Envelope 30y · Controls 10y ·
        Renewables 20y) and no discounting; abatement cost = (net capex − lifetime × annual saving) ÷
        (lifetime × tCO₂). Refine against your cost of capital before investment decisions.
      </p>
    </div>
  )
}
