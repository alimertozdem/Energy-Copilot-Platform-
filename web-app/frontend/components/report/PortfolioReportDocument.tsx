/**
 * PortfolioReportDocument — body of the /portfolio/report PDF.
 *
 * Presentational; plugs into the shared <ReportFrame> (which owns the branded
 * header, footer, print stylesheet and toolbar). Renders the KPI summary, an
 * optional on-site solar row, and the buildings table.
 *
 * Shared palette / formatters / section / notice / table-cell styles come from
 * reportKit. The delta-aware KPI tile and the EUI/EPC/anomaly cell colouring
 * stay local because they are portfolio-specific (actions/alerts use StatCard).
 */
import type { CSSProperties } from "react"

import type {
  Direction,
  KPITile,
  PortfolioBuildingRow,
  PortfolioKPIs,
} from "@/lib/api/portfolio"

import {
  BAD,
  DEEP,
  EMERALD,
  FAINT,
  GOOD,
  INK,
  LINE,
  MUTED,
  Notice,
  SectionTitle,
  fmtCompact,
  fmtInt,
  tdC,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"
import { euiBandFor, isDatacenter } from "@/lib/insights/buildingAdvisor"

type Props = {
  kpis: PortfolioKPIs | null
  kpisError: string | null
  buildings: PortfolioBuildingRow[]
  buildingsError: string | null
}

// KPI value formatter (KPI-specific: compact >=10k, else 1 decimal for EUR/%/EUI).
function fmtValue(value: number, unit: string): string {
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

function deltaInfo(
  pct: number | null,
  direction: Direction,
  lowerIsBetter: boolean
): { text: string; color: string } | null {
  if (pct === null) return null
  const arrow = direction === "up" ? "▲" : direction === "down" ? "▼" : "→"
  const goodDir: Direction = lowerIsBetter ? "down" : "up"
  const color = direction === "neutral" ? MUTED : direction === goodDir ? GOOD : BAD
  return { text: `${arrow} ${Math.abs(pct).toFixed(1)}%`, color }
}

// EUI coloured against the type-specific public-benchmark band (the same bands the
// in-app advisor uses) rather than a flat threshold — so a hotel at 250 or a
// datacenter at 1500 is no longer mis-flagged "bad". Datacenters are excluded:
// per-area EUI is not a meaningful yardstick for them (PUE is).
function euiCell(type: string, eui: number | null): { color: string; suffix: string } {
  if (eui === null || eui === 0) return { color: FAINT, suffix: "" }
  if (isDatacenter((type || "").toLowerCase())) return { color: FAINT, suffix: " *" }
  const band = euiBandFor(type)
  if (eui < band.low) return { color: GOOD, suffix: "" }
  if (eui <= band.high) return { color: INK, suffix: "" }
  if (eui > band.high * 1.25) return { color: "#b91c1c", suffix: "" }
  return { color: BAD, suffix: "" }
}

function anomalyColor(n: number): string {
  if (n === 0) return FAINT
  if (n <= 3) return BAD
  return "#b91c1c"
}

const EPC_COLOR: Record<string, string> = {
  A: DEEP,
  B: DEEP,
  C: BAD,
  D: "#c2410c",
  E: "#b91c1c",
  F: "#b91c1c",
  G: "#b91c1c",
}

function epcChip(epc: string | null): CSSProperties {
  const c = epc && EPC_COLOR[epc] ? EPC_COLOR[epc] : FAINT
  return {
    display: "inline-block",
    minWidth: 16,
    padding: "2px 6px",
    border: `1px solid ${c}`,
    borderRadius: 4,
    color: c,
    fontWeight: 700,
    fontSize: 10,
  }
}

function KpiCard({
  label,
  tile,
  lowerIsBetter = true,
}: {
  label: string
  tile: KPITile
  lowerIsBetter?: boolean
}) {
  const d = deltaInfo(tile.delta_pct, tile.direction, lowerIsBetter)
  return (
    <div
      style={{
        flex: 1,
        minWidth: 0,
        backgroundColor: "#ffffff",
        border: `1px solid ${LINE}`,
        borderTop: `3px solid ${EMERALD}`,
        borderRadius: 8,
        padding: "12px 14px",
      }}
    >
      <div
        style={{
          fontSize: 10,
          letterSpacing: 1.2,
          textTransform: "uppercase",
          color: MUTED,
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
        <span style={{ fontSize: 22, fontWeight: 700, color: INK, fontVariantNumeric: "tabular-nums" }}>
          {fmtValue(tile.value, tile.unit)}
        </span>
        <span style={{ fontSize: 12, color: FAINT }}>{tile.unit}</span>
      </div>
      {d && (
        <div style={{ marginTop: 6, fontSize: 11, fontWeight: 600, color: d.color }}>
          {d.text} <span style={{ color: FAINT, fontWeight: 400 }}>vs prior 30d</span>
        </div>
      )}
    </div>
  )
}

export function PortfolioReportDocument({
  kpis,
  kpisError,
  buildings,
  buildingsError,
}: Props) {
  return (
    <>
      <SectionTitle>Portfolio KPIs</SectionTitle>
      {kpisError ? (
        <Notice error={kpisError} label="KPI" />
      ) : kpis ? (
        <div style={{ display: "flex", gap: 12 }}>
          <KpiCard label="Total Energy" tile={kpis.total_energy} />
          <KpiCard label="Avg EUI" tile={kpis.avg_eui} />
          <KpiCard label="Total Cost" tile={kpis.total_cost} />
          <KpiCard label="Total CO₂" tile={kpis.total_co2} />
        </div>
      ) : null}

      {kpis?.solar && (
        <>
          <SectionTitle>On-site Solar</SectionTitle>
          <div style={{ display: "flex", gap: 12 }}>
            <KpiCard label="Generated" tile={kpis.solar.generated} lowerIsBetter={false} />
            <KpiCard
              label="Renewable Rate"
              tile={kpis.solar.renewable_rate}
              lowerIsBetter={false}
            />
            <KpiCard label="Exported" tile={kpis.solar.exported} lowerIsBetter={false} />
            <KpiCard label="CO₂ Avoided" tile={kpis.solar.co2_avoided} lowerIsBetter={false} />
          </div>
        </>
      )}

      <SectionTitle>Buildings</SectionTitle>
      {buildingsError ? (
        <Notice error={buildingsError} label="buildings" />
      ) : buildings.length === 0 ? (
        <div style={{ fontSize: 12, color: MUTED, padding: "12px 0" }}>
          No buildings to display.
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ backgroundColor: "#f1f5f9" }}>
              <th style={thStyle("left")}>Building</th>
              <th style={thStyle("left")}>Location</th>
              <th style={thStyle("left")}>Type</th>
              <th style={thStyle("right")}>Area</th>
              <th style={thStyle("right")}>EUI</th>
              <th style={thStyle("right")}>Energy 30d</th>
              <th style={thStyle("right")}>Cost 30d</th>
              <th style={thStyle("right")}>CO₂ 30d</th>
              <th style={thStyle("right")}>Anomalies</th>
              <th style={thStyle("center")}>EPC</th>
            </tr>
          </thead>
          <tbody>
            {buildings.map((b) => (
              <tr key={b.fabric_building_id}>
                <td style={{ ...tdL, fontWeight: 600 }}>{b.name}</td>
                <td style={{ ...tdL, color: MUTED }}>
                  {b.city}, {b.country}
                </td>
                <td style={{ ...tdL, textTransform: "uppercase", fontSize: 10, color: MUTED }}>
                  {b.building_type.replace(/_/g, " ")}
                </td>
                <td style={tdR}>{fmtInt(b.floor_area_m2)} m²</td>
                {(() => {
                  const e = euiCell(b.building_type, b.eui_kwh_m2_yr)
                  return (
                    <td style={{ ...tdR, color: e.color, fontWeight: 600 }}>
                      {b.eui_kwh_m2_yr === null ? "—" : fmtCompact(b.eui_kwh_m2_yr, 0)}
                      {e.suffix}
                    </td>
                  )
                })()}
                <td style={tdR}>{fmtCompact(b.kwh_30d)} kWh</td>
                <td style={tdR}>€{fmtCompact(b.cost_30d_eur)}</td>
                <td style={tdR}>{fmtCompact(b.co2_30d_kg)} kg</td>
                <td
                  style={{
                    ...tdR,
                    color: anomalyColor(b.open_anomalies),
                    fontWeight: b.open_anomalies > 0 ? 600 : 400,
                  }}
                >
                  {b.open_anomalies}
                </td>
                <td style={tdC}>
                  <span style={epcChip(b.epc_class)}>{b.epc_class ?? "—"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {buildings.length > 0 && !buildingsError && (
        <div style={{ marginTop: 6, fontSize: 10, lineHeight: 1.5, color: FAINT }}>
          EUI is coloured against the typical public-benchmark band for each building type
          (indicative, not weather-corrected): green = below · neutral = within · amber/red =
          above. <strong>*</strong> Datacenters are excluded — per-area EUI is not a meaningful
          yardstick (track PUE instead).
        </div>
      )}
    </>
  )
}
