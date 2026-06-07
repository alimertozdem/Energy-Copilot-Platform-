/**
 * ComplianceReportDocument — body of the /compliance/report PDF.
 *
 * Presentational; plugs into the shared <ReportFrame>. Three sections, all
 * indicative: EPBD/MEPS renovation risk, CRREM-style stranding, and the
 * ESRS-E1 energy + Scope 1/2/3 summary. Reuses the pure logic helpers
 * (lib/compliance, lib/crrem) + reportKit styles.
 */
import type { EsrsReport } from "@/lib/api/esrs"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import { RISK_BANDS, summarizeCompliance } from "@/lib/compliance"
import { summarizeStranding } from "@/lib/crrem"
import { summarizeTaxonomy } from "@/lib/taxonomy"

import {
  BAD,
  DANGER,
  FAINT,
  GOOD,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  fmtInt,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

type Props = {
  buildings: PortfolioBuildingRow[]
  buildingsError: string | null
  esrs: EsrsReport | null
  esrsError: string | null
}

function num(v: number, d = 0): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: d }).format(v)
}

export function ComplianceReportDocument({
  buildings,
  buildingsError,
  esrs,
  esrsError,
}: Props) {
  const meps = buildingsError ? null : summarizeCompliance(buildings)
  const crrem = buildingsError ? null : summarizeStranding(buildings)
  const tax = buildingsError ? null : summarizeTaxonomy(buildings)

  return (
    <>
      <div style={{ fontSize: 11, color: MUTED, margin: "4px 0 10px", lineHeight: 1.5 }}>
        Indicative compliance &amp; sustainability snapshot. EPBD/MEPS bands and
        CRREM pathways are indicative (national MEPS not finalised; illustrative
        1.5°C curves). ESRS-E1 figures are reporting support, not an audited
        disclosure; Scope 3 is estimated. EU Taxonomy figures indicate the activity-7.7 route only, not alignment (DNSH and minimum safeguards not assessed).
      </div>

      {/* ---- EPBD / MEPS ---- */}
      <SectionTitle>EPBD / MEPS renovation risk</SectionTitle>
      {buildingsError ? (
        <Notice error={buildingsError} label="buildings" />
      ) : meps ? (
        <>
          <div style={{ display: "flex", gap: 12 }}>
            <StatCard label="Renovation priority" value={meps.counts.high} color={DANGER} hint="EPC F–G" />
            <StatCard label="Watch" value={meps.counts.watch} color={BAD} hint="EPC D–E / high EUI" />
            <StatCard label="EPC needed" value={meps.counts.epc_needed} hint="no EPC on file" />
            <StatCard label="Lower risk" value={meps.counts.lower} color={GOOD} hint="EPC A–C" />
          </div>
          {meps.priority.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, marginTop: 10 }}>
              <thead>
                <tr style={{ backgroundColor: "#f1f5f9" }}>
                  <th style={thStyle("left")}>Building</th>
                  <th style={thStyle("left")}>Type</th>
                  <th style={thStyle("left")}>EPC</th>
                  <th style={thStyle("right")}>EUI</th>
                  <th style={thStyle("left")}>Why</th>
                </tr>
              </thead>
              <tbody>
                {meps.priority.map(({ building: b, band, reason }) => (
                  <tr key={b.fabric_building_id}>
                    <td style={{ ...tdL, fontWeight: 600 }}>
                      {b.name}
                      <div style={{ fontSize: 9, color: FAINT }}>{b.city}, {b.country}</div>
                    </td>
                    <td style={{ ...tdL, textTransform: "uppercase", fontSize: 10, color: MUTED }}>
                      {b.building_type.replace(/_/g, " ")}
                    </td>
                    <td style={{ ...tdL, fontWeight: 700, color: RISK_BANDS[band].key === "high" ? DANGER : MUTED }}>
                      {b.epc_class ?? "—"}
                    </td>
                    <td style={tdR}>{b.eui_kwh_m2_yr != null ? num(b.eui_kwh_m2_yr) : "—"}</td>
                    <td style={{ ...tdL, color: MUTED, fontSize: 10 }}>{reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      ) : null}

      {/* ---- CRREM stranding ---- */}
      <SectionTitle>CRREM stranding (illustrative 1.5°C)</SectionTitle>
      {buildingsError ? (
        <Notice error={buildingsError} label="buildings" />
      ) : crrem ? (
        <div style={{ display: "flex", gap: 12 }}>
          <StatCard label="Assessed" value={`${crrem.assessed} / ${buildings.length}`} hint="CO₂ + area data" />
          <StatCard label="Stranded now" value={crrem.strandedNow} color={DANGER} hint="above 2025 pathway" />
          <StatCard label="Strand by 2030" value={crrem.strandedBy2030} color={BAD} hint="this decade" />
          <StatCard label="Avg stranding yr" value={crrem.avgStrandingYear ?? "—"} hint="at-risk buildings" />
        </div>
      ) : null}

      {/* ---- EU Taxonomy ---- */}
      <SectionTitle>EU Taxonomy alignment (indicative, activity 7.7)</SectionTitle>
      {buildingsError ? (
        <Notice error={buildingsError} label="buildings" />
      ) : tax ? (
        <div style={{ display: "flex", gap: 12 }}>
          <StatCard label="On EPC-A route" value={`${tax.onRouteCount} / ${buildings.length}`} color={GOOD} hint="EPC A" />
          <StatCard label="Floor area on route" value={`${Math.round(tax.onRouteAreaShare * 100)} %`} color={GOOD} hint="area-weighted proxy" />
          <StatCard label="Potential (top-15%)" value={tax.counts.top15_potential} hint="EPC B-C, needs check" />
          <StatCard label="EPC needed" value={tax.counts.epc_needed} hint="no EPC on file" />
        </div>
      ) : null}

      {/* ---- ESRS-E1 ---- */}
      <SectionTitle>
        ESRS-E1 summary{esrs?.reporting_year ? ` · ${esrs.reporting_year}` : ""}
      </SectionTitle>
      {esrsError ? (
        <Notice error={esrsError} label="ESRS" />
      ) : esrs && esrs.has_data ? (
        <>
          <div style={{ display: "flex", gap: 12 }}>
            <StatCard label="Energy (E1-5)" value={`${num(esrs.energy_total_mwh)} MWh`} hint="total consumption" />
            <StatCard label="Total GHG" value={`${num(esrs.ghg.total_location_tco2e, 1)} tCO₂e`} color={BAD} hint="Scope 1+2+3 (location)" />
            <StatCard label="GHG intensity" value={esrs.ghg_intensity_tco2e_m2 != null ? num(esrs.ghg_intensity_tco2e_m2, 3) : "—"} hint="tCO₂e/m²" />
            <StatCard label="Renewable" value={esrs.energy_renewable_pct != null ? `${num(esrs.energy_renewable_pct, 1)} %` : "—"} color={GOOD} hint="solar self-consumed" />
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
            <StatCard label="Scope 1" value={num(esrs.ghg.scope1_tco2e, 1)} hint="tCO₂e — direct" />
            <StatCard label="Scope 2 (loc)" value={num(esrs.ghg.scope2_location_tco2e, 1)} hint="tCO₂e — grid" />
            <StatCard label="Scope 2 (mkt)" value={num(esrs.ghg.scope2_market_tco2e, 1)} hint="tCO₂e — contract" />
            <StatCard label="Scope 3 (est.)" value={num(esrs.ghg.scope3_tco2e, 1)} hint="tCO₂e — value chain" />
          </div>
          {esrs.rows.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, marginTop: 10 }}>
              <thead>
                <tr style={{ backgroundColor: "#f1f5f9" }}>
                  <th style={thStyle("left")}>Building</th>
                  <th style={thStyle("right")}>Scope 1</th>
                  <th style={thStyle("right")}>Scope 2 (loc)</th>
                  <th style={thStyle("right")}>Scope 2 (mkt)</th>
                  <th style={thStyle("right")}>Scope 3</th>
                  <th style={thStyle("right")}>Total</th>
                  <th style={thStyle("right")}>Intensity</th>
                </tr>
              </thead>
              <tbody>
                {esrs.rows.map((r) => (
                  <tr key={r.fabric_building_id}>
                    <td style={{ ...tdL, fontWeight: 600 }}>
                      {r.name}
                      <div style={{ fontSize: 9, color: FAINT, textTransform: "uppercase" }}>
                        {r.building_type.replace(/_/g, " ")}
                      </div>
                    </td>
                    <td style={tdR}>{num(r.scope1_tco2e, 1)}</td>
                    <td style={tdR}>{num(r.scope2_location_tco2e, 1)}</td>
                    <td style={tdR}>{num(r.scope2_market_tco2e, 1)}</td>
                    <td style={tdR}>{num(r.scope3_tco2e, 1)}</td>
                    <td style={{ ...tdR, fontWeight: 700 }}>{num(r.total_location_tco2e, 1)}</td>
                    <td style={tdR}>{r.ghg_intensity_tco2e_m2 != null ? num(r.ghg_intensity_tco2e_m2, 3) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div style={{ marginTop: 8, fontSize: 10, color: FAINT }}>
            Reported {esrs.buildings_reported} of {esrs.buildings_total} buildings ·{" "}
            {fmtInt(esrs.floor_area_m2)} m² · data quality: {esrs.data_quality.complete} complete,{" "}
            {esrs.data_quality.estimated} estimated, {esrs.data_quality.missing_gas} missing-gas.
          </div>
        </>
      ) : esrs && !esrs.has_data ? (
        <div style={{ fontSize: 12, color: MUTED, padding: "8px 0" }}>
          No GHG data for the reporting period yet.
        </div>
      ) : null}
    </>
  )
}
