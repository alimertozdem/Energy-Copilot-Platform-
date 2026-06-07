/**
 * MaccChart — portfolio Marginal Abatement Cost Curve (server component).
 *
 * Consumes the backend-computed measures (already sorted cheapest-first with a
 * cumulative CO₂ running total), so the browser does NO recomputation — the
 * energy assumption lives server-side in services/abatement.py (single source of
 * truth). Bar WIDTH = annual tCO₂ abated, HEIGHT = €/tCO₂. Cost-negative bars
 * (left, emerald) are "no-regret"; cost-positive bars (amber → orange) cost money.
 *
 * Distinct from components/actions/MaccCurve.tsx (which recomputes from the
 * /actions payload in-browser); this one renders the authoritative server data.
 */
import type { MaccMeasure } from "@/lib/api/abatement"

function barColor(cost: number): string {
  if (cost <= 0) return "#1D9E75"
  if (cost < 150) return "#EAB308"
  return "#F97316"
}

function fmt(n: number): string {
  return Math.round(n).toLocaleString("en-US")
}

export function MaccChart({ measures }: { measures: MaccMeasure[] }) {
  if (measures.length === 0) return null

  const W = 900
  const H = 320
  const padL = 64
  const padR = 16
  const padT = 18
  const padB = 48
  const plotW = W - padL - padR
  const plotH = H - padT - padB

  const totalCo2 = measures.reduce((s, m) => s + m.annual_co2_t, 0) || 1
  const maxC = Math.max(0, ...measures.map((m) => m.mac_eur_per_t))
  const minC = Math.min(0, ...measures.map((m) => m.mac_eur_per_t))
  const range = maxC - minC || 1
  const yOf = (c: number) => padT + ((maxC - c) / range) * plotH
  const zeroY = yOf(0)

  let x = padL
  const bars = measures.map((m) => {
    const w = Math.max((m.annual_co2_t / totalCo2) * plotW, 1)
    const bx = x
    x += w
    const yc = yOf(m.mac_eur_per_t)
    return {
      x: bx,
      w,
      top: Math.min(yc, zeroY),
      h: Math.max(Math.abs(yc - zeroY), 1),
      color: barColor(m.mac_eur_per_t),
      m,
    }
  })

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      role="img"
      aria-label="Portfolio marginal abatement cost curve"
    >
      {/* y grid + labels */}
      {[maxC, (maxC + minC) / 2, minC].map((c, i) => (
        <g key={i}>
          <line
            x1={padL}
            x2={W - padR}
            y1={yOf(c)}
            y2={yOf(c)}
            stroke="rgba(148,163,184,0.12)"
            strokeWidth="1"
          />
          <text x={padL - 8} y={yOf(c) + 3} textAnchor="end" fontSize="10" fill="#64748B">
            {fmt(c)}
          </text>
        </g>
      ))}
      {/* zero line */}
      <line
        x1={padL}
        x2={W - padR}
        y1={zeroY}
        y2={zeroY}
        stroke="rgba(148,163,184,0.4)"
        strokeWidth="1.5"
      />
      {/* bars */}
      {bars.map((b, i) => (
        <rect key={i} x={b.x} y={b.top} width={b.w} height={b.h} fill={b.color} opacity={0.9}>
          <title>{`${b.m.title ?? "Measure"} (${b.m.building_name}) · ${fmt(
            b.m.annual_co2_t
          )} tCO₂/yr · €${fmt(b.m.mac_eur_per_t)}/tCO₂`}</title>
        </rect>
      ))}
      {/* axis labels */}
      <text x={padL} y={H - 8} fontSize="10" fill="#94A3B8">
        €0 line — measures to the left save money + carbon
      </text>
      <text x={W - padR} y={H - 8} textAnchor="end" fontSize="10" fill="#64748B">
        cumulative tCO₂/yr →
      </text>
      <text
        x="14"
        y={padT + 6}
        fontSize="10"
        fill="#94A3B8"
        transform={`rotate(-90 14 ${padT + 6})`}
      >
        € / tCO₂
      </text>
    </svg>
  )
}
