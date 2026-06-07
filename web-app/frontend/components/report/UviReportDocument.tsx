/**
 * UviReportDocument — body for the resident monthly consumption statement (UVI).
 *
 * This is the EED / HKVO "unterjährige Verbrauchsinformation" artifact: the
 * monthly consumption information a building must provide to tenants. Body-only;
 * it plugs into <ReportFrame> (shared print chrome). One section per unit (a
 * resident usually has one). Inline-styled, print-safe — no app theme classes.
 *
 * Data comes from the same resident summary the /residence page uses; the
 * benchmark is the anonymized building average (no neighbour data).
 */
import type { ResidenceMonthlyPoint, ResidenceSummary, ResidenceUnit } from "@/lib/api/residence"

import {
  BAD,
  Chip,
  DANGER,
  EMERALD,
  FAINT,
  fmtInt,
  fmtMoney,
  fmtNum,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

const MONTHS = [
  "",
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
]

function epcColor(band: string | null): string {
  switch (band) {
    case "A":
      return EMERALD
    case "B":
      return GOOD
    case "C":
    case "D":
      return BAD
    case "E":
      return DANGER
    default:
      return MUTED
  }
}

type Row = {
  year: number
  month: number
  heating: number | null
  dhw: number | null
  total: number
  cost: number | null
  buildingAvg: number | null
}

function pivotMonths(points: ResidenceMonthlyPoint[]): Row[] {
  const m = new Map<string, Row>()
  for (const p of points) {
    const key = `${p.year}-${String(p.month).padStart(2, "0")}`
    const r =
      m.get(key) ??
      { year: p.year, month: p.month, heating: null, dhw: null, total: 0, cost: null, buildingAvg: null }
    if (p.kwh !== null && p.kwh !== undefined) {
      r.total += p.kwh
      if (p.energy_type === "heating") r.heating = (r.heating ?? 0) + p.kwh
      else if (p.energy_type === "dhw") r.dhw = (r.dhw ?? 0) + p.kwh
    }
    if (p.cost_eur !== null && p.cost_eur !== undefined) r.cost = (r.cost ?? 0) + p.cost_eur
    if (p.building_avg_kwh !== null && p.building_avg_kwh !== undefined)
      r.buildingAvg = (r.buildingAvg ?? 0) + p.building_avg_kwh
    m.set(key, r)
  }
  return [...m.values()].sort((a, b) => a.year - b.year || a.month - b.month)
}

function vsCell(total: number, buildingAvg: number | null): { text: string; color: string } {
  if (buildingAvg === null || buildingAvg <= 0) return { text: "—", color: MUTED }
  const pct = (total / buildingAvg - 1) * 100
  if (Math.abs(pct) < 0.5) return { text: "~0%", color: MUTED }
  const sign = pct < 0 ? "-" : "+"
  return { text: `${sign}${fmtNum(Math.abs(pct))}%`, color: pct < 0 ? GOOD : BAD }
}

function UnitStatement({ unit, asOf }: { unit: ResidenceUnit; asOf: string }) {
  const k = unit.kpi
  const c = unit.common_area
  const rows = pivotMonths(unit.monthly)
  const band = k?.epc_band ?? null
  const sharePct = c?.allocation_share != null ? c.allocation_share * 100 : null

  return (
    <div style={{ marginBottom: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: INK }}>
          Unit {unit.unit_id}
          {unit.area_m2 != null ? ` · ${fmtNum(unit.area_m2)} m² living area` : ""}
        </div>
        <div style={{ fontSize: 11, color: MUTED }}>As of {asOf}</div>
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 8, flexWrap: "wrap" }}>
        <StatCard
          label="Efficiency (EUI)"
          value={fmtNum(k?.eui_kwh_m2_yr ?? null)}
          hint="kWh/m²·yr (heating + hot water)"
        />
        <StatCard
          label="Annual heating + hot water"
          value={fmtInt(k?.heating_dhw_kwh_annual ?? null)}
          hint="kWh/yr (annualized)"
        />
        <StatCard
          label="Shared-area share"
          value={fmtInt(c?.unit_allocated_kwh ?? null)}
          hint={sharePct != null ? `kWh · ${fmtNum(sharePct)}% of building` : "kWh"}
        />
        <StatCard
          label="Energy rating"
          value={band ?? "—"}
          color={epcColor(band)}
          hint="EPC band (residential scale)"
        />
      </div>

      <SectionTitle>Monthly consumption</SectionTitle>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={thStyle("left")}>Month</th>
            <th style={thStyle("right")}>Heating kWh</th>
            <th style={thStyle("right")}>Hot water kWh</th>
            <th style={thStyle("right")}>Total kWh</th>
            <th style={thStyle("right")}>Cost</th>
            <th style={thStyle("right")}>Building avg kWh</th>
            <th style={thStyle("right")}>vs avg</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td style={tdL} colSpan={7}>
                No monthly readings available yet.
              </td>
            </tr>
          ) : (
            rows.map((r) => {
              const vs = vsCell(r.total, r.buildingAvg)
              return (
                <tr key={`${r.year}-${r.month}`}>
                  <td style={tdL}>
                    {MONTHS[r.month]} {r.year}
                  </td>
                  <td style={tdR}>{fmtInt(r.heating)}</td>
                  <td style={tdR}>{fmtInt(r.dhw)}</td>
                  <td style={{ ...tdR, fontWeight: 600 }}>{fmtInt(r.total)}</td>
                  <td style={tdR}>{fmtMoney(r.cost)}</td>
                  <td style={tdR}>{fmtInt(r.buildingAvg)}</td>
                  <td style={{ ...tdR, color: vs.color, fontWeight: 600 }}>{vs.text}</td>
                </tr>
              )
            })
          )}
        </tbody>
      </table>
    </div>
  )
}

export function UviReportDocument({
  summary,
  error,
}: {
  summary: ResidenceSummary | null
  error: string | null
}) {
  if (error) {
    return <Notice error={error} label="consumption" />
  }
  if (!summary || summary.units.length === 0) {
    return (
      <div style={{ fontSize: 13, color: MUTED, padding: "8px 0" }}>
        No consumption data is available for this home yet.
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 14 }}>
        <Chip label="EED / HKVO consumption information" color={EMERALD} />
      </div>

      {summary.units.map((u) => (
        <UnitStatement key={u.unit_id} unit={u} asOf={summary.as_of} />
      ))}

      <div style={{ marginTop: 8, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        This statement provides your monthly consumption information under the German
        Heating Costs Ordinance (Heizkostenverordnung) and the EU Energy Efficiency
        Directive. Figures are informational and based on metered and allocated readings;
        they are not a final bill. Shared heating and hot water are allocated 70% by
        consumption and 30% by floor area (HKVO default). You only ever see your own home
        plus an anonymized building average.
      </div>
    </div>
  )
}
