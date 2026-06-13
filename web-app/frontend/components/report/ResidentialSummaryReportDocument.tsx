/**
 * ResidentialSummaryReportDocument — body for a residential building's summary PDF.
 *
 * The residential counterpart of the commercial "Building summary": per-unit energy
 * (climate-adjusted EUI), the EPC mix, and HKVO/UVI metering coverage. Reuses the
 * manager residential endpoint (gold_residential_unit_kpi). Body-only; plugs into
 * <ReportFrame>. Decision-support, not an audited certificate.
 */
import type { ResidentialBuildingResponse } from "@/lib/api/residentialManager"

import {
  BAD,
  Chip,
  EMERALD,
  FAINT,
  fmtInt,
  fmtNum,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  tdC,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

const EPC_ORDER = ["A+", "A", "B", "C", "D", "E", "F", "G", "H"]

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

export function ResidentialSummaryReportDocument({
  data,
  error,
  buildingName,
}: {
  data: ResidentialBuildingResponse | null
  error: string | null
  buildingName: string
}) {
  if (error) {
    return <Notice error={error} label="residential summary" />
  }
  if (!data || data.units.length === 0) {
    return (
      <div style={{ fontSize: 13, color: MUTED, padding: "8px 0" }}>
        No residential unit data is available for this building yet.
      </div>
    )
  }

  const { rollup, units } = data
  const caf = rollup.climate_adjustment_factor
  const adj = rollup.building_avg_eui_climate_adjusted_kwh_m2_yr
  const isAdj = adj != null && caf != null && Math.abs(caf - 1) > 0.005

  const epcBands = EPC_ORDER.filter((b) => rollup.epc_distribution[b])
  const uviLatest =
    rollup.uvi.latest_year != null && rollup.uvi.latest_month != null
      ? `${MONTHS[(rollup.uvi.latest_month - 1) % 12] ?? rollup.uvi.latest_month} ${rollup.uvi.latest_year}`
      : "—"

  return (
    <div>
      <div style={{ marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="Residential summary" color={EMERALD} />
        <Chip label={buildingName} color={INK} />
        {isAdj && <Chip label={`Climate-adjusted ×${fmtNum(caf!)}`} color={MUTED} />}
      </div>

      <SectionTitle>Building rollup</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Units with data" value={`${rollup.units_with_data}`} hint="dwellings reported" />
        <StatCard
          label="Avg heating EUI"
          value={isAdj ? `${fmtInt(adj!)}` : rollup.building_avg_eui_kwh_m2_yr != null ? `${fmtInt(rollup.building_avg_eui_kwh_m2_yr)}` : "—"}
          hint={
            isAdj
              ? `kWh/m²·yr · climate-adjusted (raw ${fmtInt(rollup.building_avg_eui_kwh_m2_yr ?? 0)})`
              : "kWh/m²·yr (heating + hot water)"
          }
        />
        <StatCard
          label="UVI coverage"
          value={`${rollup.uvi.units_covered}/${rollup.units_with_data}`}
          color={rollup.uvi.units_covered >= rollup.units_with_data && rollup.units_with_data > 0 ? GOOD : BAD}
          hint={`latest reading ${uviLatest}`}
        />
        <StatCard
          label="EPC bands"
          value={epcBands.length ? epcBands.join(" · ") : "—"}
          hint="distribution across units"
        />
      </div>

      <SectionTitle>Per-unit energy</SectionTitle>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
        <thead>
          <tr style={{ backgroundColor: "#f1f5f9" }}>
            <th style={thStyle("left")}>Unit</th>
            <th style={thStyle("right")}>Area (m²)</th>
            <th style={thStyle("right")}>EUI</th>
            <th style={thStyle("right")}>EUI (adj)</th>
            <th style={thStyle("center")}>EPC</th>
            <th style={thStyle("right")}>vs building</th>
          </tr>
        </thead>
        <tbody>
          {units.map((u) => {
            const vs = u.vs_building_pct
            const vsColor = vs == null ? MUTED : vs > 0 ? BAD : GOOD
            return (
              <tr key={u.unit_id}>
                <td style={{ ...tdL, fontWeight: 600 }}>{u.unit_id}</td>
                <td style={tdR}>{u.area_m2 != null ? fmtInt(u.area_m2) : "—"}</td>
                <td style={tdR}>{u.eui_kwh_m2_yr != null ? fmtInt(u.eui_kwh_m2_yr) : "—"}</td>
                <td style={tdR}>
                  {u.eui_climate_adjusted_kwh_m2_yr != null ? fmtInt(u.eui_climate_adjusted_kwh_m2_yr) : "—"}
                </td>
                <td style={tdC}>{u.epc_band ?? "—"}</td>
                <td style={{ ...tdR, color: vsColor }}>
                  {vs != null ? `${vs > 0 ? "+" : ""}${fmtNum(vs)}%` : "—"}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <div style={{ marginTop: 6, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        EUI is heating + hot water per m² of living area (Wohnfläche). The climate-adjusted
        column normalises for the year&apos;s weather (HDD); &quot;vs building&quot; is the
        unit&apos;s deviation from the building average (positive = above average).
      </div>

      <SectionTitle>HKVO / UVI metering</SectionTitle>
      <div style={{ fontSize: 11.5, color: INK, lineHeight: 1.6 }}>
        Monthly consumption information (unterjährige Verbrauchsinformation, UVI) is
        mandatory under the Heizkostenverordnung from <strong>1 January 2027</strong> for
        buildings with remote-readable meters. This building currently has{" "}
        <strong>{rollup.uvi.units_covered}</strong> of{" "}
        <strong>{rollup.units_with_data}</strong> units covered (latest reading {uviLatest}).
        {rollup.uvi.units_covered < rollup.units_with_data
          ? " Closing the gap before the deadline avoids the §12 cost-reduction exposure."
          : " Coverage is on track for the deadline."}
      </div>

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Decision-support summary from metered residential data — not an audited certificate
        or a formal Energieausweis. Figures are estimates where consumption is allocated
        rather than separately metered.
      </div>
    </div>
  )
}
