/**
 * CrremReportDocument — Executive Decarbonisation & CRREM Stranding Audit PDF.
 *
 * Per-asset transition-risk assessment: compares operational carbon intensity
 * (kgCO₂/m²·yr) against indicative 1.5°C Paris-aligned decarbonisation pathways.
 * Formatted as an institutional-grade ESG & capital allocation audit document.
 */

import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import {
  pathwayValue,
  summarizeStranding,
  type StrandingStatus,
} from "@/lib/crrem"

import {
  BAD,
  Chip,
  EMERALD,
  FAINT,
  fmtInt,
  GOOD,
  INK,
  MUTED,
  SectionTitle,
  StatCard,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

const AMBER = "#b45309"
const DANGER = "#b91c1c"

function num(v: number | null, d = 1): string {
  if (v === null || !Number.isFinite(v)) return "—"
  return v.toFixed(d)
}

function statusBadge(status: StrandingStatus, year: number | null) {
  if (status === "stranded_today") {
    return <Chip label="STRANDED TODAY" color={DANGER} />
  }
  if (status === "strands_by_2030") {
    return <Chip label={`CRITICAL RISK (${year})`} color={AMBER} />
  }
  if (status === "strands_after_2030") {
    return <Chip label={`Risk in ${year}`} color={MUTED} />
  }
  return <Chip label="COMPLIANT 2050" color={GOOD} />
}

export function CrremReportDocument({
  buildings,
}: {
  buildings: PortfolioBuildingRow[]
}) {
  const { results, summary } = summarizeStranding(buildings)
  const totalArea = buildings.reduce((acc, b) => acc + (b.floor_area_m2 || 0), 0)

  return (
    <div style={{ fontFamily: "Inter, -apple-system, BlinkMacSystemFont, sans-serif" }}>
      {/* Institutional Document Header Banner */}
      <div
        style={{
          borderBottom: `2px solid ${EMERALD}`,
          paddingBottom: "14px",
          marginBottom: "20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "10px",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: EMERALD,
              marginBottom: "4px",
            }}
          >
            Institutional Asset Management & Compliance Audit
          </div>
          <h1
            style={{
              fontSize: "22px",
              fontWeight: 800,
              color: INK,
              margin: 0,
              lineHeight: 1.2,
            }}
          >
            CRREM Stranding & 1.5°C Trajectory Audit
          </h1>
          <p style={{ fontSize: "11px", color: MUTED, margin: "4px 0 0" }}>
            Operational carbon intensity benchmarked against 1.5°C Paris Agreement decarbonisation pathways
          </p>
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              display: "inline-block",
              background: "#ecfdf5",
              border: `1px solid ${EMERALD}`,
              borderRadius: "4px",
              padding: "4px 8px",
              fontSize: "10px",
              fontWeight: 600,
              color: EMERALD,
            }}
          >
            Audited Scope: {buildings.length} Assets ({fmtInt(totalArea)} m²)
          </div>
          <div style={{ fontSize: "9px", color: FAINT, marginTop: "4px" }}>
            Regulatory Anchor: EPBD Recast (EU 2024/1275) & CSRD ESRS E1
          </div>
        </div>
      </div>

      {/* Executive Key Risk Metrics */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          marginBottom: "22px",
        }}
      >
        <StatCard
          label="Portfolio Carbon Intensity"
          value={
            summary.portfolio_intensity_kg_per_m2 !== null
              ? `${num(summary.portfolio_intensity_kg_per_m2)} kg`
              : "—"
          }
          hint="/m²·yr operational baseline"
          color={
            summary.portfolio_intensity_kg_per_m2 !== null &&
            summary.portfolio_intensity_kg_per_m2 > 35
              ? AMBER
              : GOOD
          }
        />
        <StatCard
          label="Stranded Today"
          value={summary.stranded_today_count}
          hint="Assets exceeding 2026 cap"
          color={summary.stranded_today_count > 0 ? DANGER : GOOD}
        />
        <StatCard
          label="High Risk (Pre-2030)"
          value={summary.strands_by_2030_count}
          hint="Strands within current cycle"
          color={summary.strands_by_2030_count > 0 ? AMBER : GOOD}
        />
        <StatCard
          label="Long-Term Compliant"
          value={summary.not_stranded_by_2050_count}
          hint="Aligned through 2050 pathway"
          color={GOOD}
        />
      </div>

      {/* Asset-by-Asset Audit Table */}
      <SectionTitle>
        Asset-Level Stranding Risk & Trajectory Timeline
      </SectionTitle>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: "11px",
          marginBottom: "24px",
        }}
      >
        <thead>
          <tr style={{ borderBottom: `1px solid ${MUTED}` }}>
            <th style={thStyle("left")}>Building / Asset Name</th>
            <th style={thStyle("left")}>Property Type</th>
            <th style={thStyle("left")}>Location</th>
            <th style={thStyle("right")}>Area (m²)</th>
            <th style={thStyle("right")}>Carbon (kg/m²·a)</th>
            <th style={thStyle("right")}>2030 Cap</th>
            <th style={thStyle("center")}>Stranding Year</th>
            <th style={thStyle("center")}>Risk Classification</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, idx) => {
            const cap2030 = pathwayValue(r.property_type, 2030)
            const isAbby = r.name.toLowerCase().includes("abby") || r.name.toLowerCase().includes("bdg2")
            return (
              <tr
                key={r.fabric_building_id}
                style={{
                  borderBottom: "1px solid #e5e7eb",
                  background: isAbby ? "#f0fdf4" : idx % 2 === 0 ? "#ffffff" : "#f9fafb",
                }}
              >
                <td style={tdL}>
                  <div style={{ fontWeight: 600, color: INK }}>{r.name}</div>
                  {isAbby && (
                    <div style={{ fontSize: "9px", color: EMERALD, fontWeight: 700 }}>
                      ★ ASHRAE Real Benchmark Reference Asset
                    </div>
                  )}
                </td>
                <td style={tdL}>{r.property_type}</td>
                <td style={tdL}>{r.city ? `${r.city}, ${r.country || ""}` : r.country || "—"}</td>
                <td style={tdR}>{fmtInt(r.floor_area_m2)}</td>
                <td style={{ ...tdR, fontWeight: 600 }}>{num(r.operational_intensity_kg_per_m2)}</td>
                <td style={{ ...tdR, color: MUTED }}>{num(cap2030)}</td>
                <td
                  style={{
                    ...tdR,
                    textAlign: "center",
                    fontWeight: 700,
                    color: r.stranding_year && r.stranding_year <= 2030 ? BAD : INK,
                  }}
                >
                  {r.stranding_year ?? "Aligned"}
                </td>
                <td style={{ textAlign: "center", padding: "6px 8px" }}>
                  {statusBadge(r.status, r.stranding_year)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {/* Strategic Audit Notes & Methodological Transparency */}
      <div
        style={{
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "6px",
          padding: "14px",
          marginTop: "16px",
        }}
      >
        <div style={{ fontSize: "11px", fontWeight: 700, color: INK, marginBottom: "6px" }}>
          Strategic Recommendations for Portfolio Decarbonisation:
        </div>
        <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "10.5px", color: MUTED, lineHeight: 1.6 }}>
          <li>
            <strong>Pre-2030 Stranding Assets:</strong> Immediate priority for Level-1 Heat Pump / Solar Capex retrofits
            to prevent valuation write-downs (Brown Discount) and maintain bank refinancing eligibility under EPBD.
          </li>
          <li>
            <strong>Off-Hours Energy Leak Optimization:</strong> Implement zero-capex thermostat setback and ventilation
            scheduling to lower baseline EUI by 12–25% before sizing capital retrofit equipment.
          </li>
          <li>
            <strong>Methodology Note:</strong> Pathways represent indicative 1.5°C Paris Agreement reduction curves
            interpolated to net-zero by 2050. Official third-party certification requires an active CRREM partner license.
          </li>
        </ul>
      </div>
    </div>
  )
}
