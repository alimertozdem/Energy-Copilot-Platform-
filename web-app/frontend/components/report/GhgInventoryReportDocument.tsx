/**
 * GhgInventoryReportDocument — body of the GHG Inventory (GHG Protocol) PDF.
 *
 * A corporate carbon inventory for the visible portfolio, structured per the GHG
 * Protocol Corporate Standard: organizational boundary, reporting period, Scope 1
 * (direct), Scope 2 (purchased electricity — BOTH location- and market-based, per the
 * Scope 2 Guidance), Scope 3 (value chain — estimated), facility breakdown, data
 * quality + methodology. Reuses the ESRS endpoint data (esrs_metrics). Body-only;
 * plugs into <ReportFrame>. Inline-styled, print-safe.
 *
 * Honesty: Scope 1+2 are disclosure-grade (from real building energy); Scope 3 is an
 * estimate covering Scope 3 categories 1, 3, 5, 6, 7 and 13. Not an audited or assured inventory.
 */
import type { EsrsReport } from "@/lib/api/esrs"

import {
  PartialYearNotice,
  BAD,
  Chip,
  DANGER,
  EMERALD,
  FAINT,
  fmtInt,
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

function num(v: number | null, d = 1): string {
  if (v === null || v === undefined) return "—"
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: d }).format(v)
}

export function GhgInventoryReportDocument({
  esrs,
  esrsError,
}: {
  esrs: EsrsReport | null
  esrsError: string | null
}) {
  if (esrsError) {
    return <Notice error={esrsError} label="GHG inventory" />
  }
  if (!esrs || !esrs.has_data) {
    return (
      <div style={{ fontSize: 13, color: MUTED, padding: "8px 0" }}>
        No GHG data is available for the reporting period yet. Once building energy is
        connected, the inventory fills in automatically.
      </div>
    )
  }

  const g = esrs.ghg

  // Operational carbon = Scope 1 + Scope 2 (the building's own energy footprint).
  // This is the EPBD / CRREM basis. Full inventory (incl. value-chain Scope 3 such
  // as commuting & business travel) is shown separately below.
  const operationalLoc = g.scope1_tco2e + g.scope2_location_tco2e
  const operationalIntensityKg =
    esrs.floor_area_m2 > 0 ? (operationalLoc * 1000) / esrs.floor_area_m2 : null

  return (
    <div>
      <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="GHG Protocol Corporate Standard" color={EMERALD} />
        <Chip label="Scope 1+2 disclosure-grade · Scope 3 estimated" color={MUTED} />
        {esrs.reporting_year != null && (
          <Chip label={`Reporting year ${esrs.reporting_year}`} color={INK} />
        )}
      </div>

      {/* ---- Inventory scope & boundary ---- */}
      <PartialYearNotice months={esrs?.reporting_months} year={esrs?.reporting_year} />
      <SectionTitle>Inventory scope &amp; boundary</SectionTitle>
      <div style={{ fontSize: 11.5, color: INK, lineHeight: 1.6 }}>
        <strong>Reporting entity:</strong> portfolio of {esrs.buildings_total}{" "}
        building{esrs.buildings_total === 1 ? "" : "s"} ({fmtInt(esrs.floor_area_m2)} m²).{" "}
        <strong>Organizational boundary:</strong> operational control (buildings the
        organization operates).{" "}
        <strong>Reporting period:</strong>{" "}
        {esrs.reporting_year ?? "latest available year"}.{" "}
        <strong>Scope 2 reporting:</strong> dual — location-based and market-based, per the
        GHG Protocol Scope 2 Guidance.{" "}
        <strong>Base year:</strong>{" "}
        {esrs.reporting_year ?? "[set the first complete year]"} (first complete reporting
        year; recalculate on a structural change ≥ 5%).{" "}
        <strong>Gases &amp; GWP:</strong> the Kyoto-basket gases reported as CO₂e using IPCC
        AR6 GWP-100; building emissions are predominantly CO₂.{" "}
        <strong>Consolidation:</strong> 100% of operated assets (operational-control approach).
      </div>

      {/* ---- Operational carbon (the building-energy basis) ---- */}
      <SectionTitle>Operational carbon — Scope 1 + 2 (tCO₂e)</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Operational total"
          value={num(operationalLoc)}
          color={INK}
          hint="Scope 1 + 2 — building energy"
        />
        <StatCard
          label="Operational intensity"
          value={operationalIntensityKg != null ? num(operationalIntensityKg, 1) : "—"}
          color={INK}
          hint="kg CO₂e/m²·yr — EPBD / CRREM basis"
        />
      </div>
      <div style={{ marginTop: 6, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Operational carbon is the building&rsquo;s own energy footprint (on-site
        combustion + purchased electricity) — the basis for EPBD and CRREM. The full
        inventory below adds estimated value-chain (Scope 3) emissions such as employee
        commuting and business travel.
      </div>

      {/* ---- Emissions by scope ---- */}
      <SectionTitle>Emissions by scope (tCO₂e)</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Scope 1 — direct" value={num(g.scope1_tco2e)} hint="on-site fuel combustion" />
        <StatCard label="Scope 2 — location" value={num(g.scope2_location_tco2e)} hint="grid-average electricity" />
        <StatCard label="Scope 2 — market" value={num(g.scope2_market_tco2e)} hint="contractual / supplier" />
        <StatCard label="Scope 3 — value chain" value={num(g.scope3_tco2e)} color={BAD} hint="estimated value chain — incl. commuting & travel" />
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
        <StatCard
          label="Total (location-based)"
          value={num(g.total_location_tco2e)}
          color={BAD}
          hint="Scope 1 + 2(loc) + 3"
        />
        <StatCard
          label="Total (market-based)"
          value={num(g.total_market_tco2e)}
          color={BAD}
          hint="Scope 1 + 2(mkt) + 3"
        />
        <StatCard
          label="GHG intensity"
          value={esrs.ghg_intensity_tco2e_m2 != null ? num(esrs.ghg_intensity_tco2e_m2, 3) : "—"}
          hint="tCO₂e/m² — incl. value chain"
        />
        <StatCard
          label="Renewable electricity"
          value={esrs.energy_renewable_pct != null ? `${num(esrs.energy_renewable_pct, 1)} %` : "—"}
          color={GOOD}
          hint="on-site solar self-consumed"
        />
      </div>

      {/* ---- Scope definitions ---- */}
      <SectionTitle>What each scope covers here</SectionTitle>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={thStyle("left")}>Scope</th>
            <th style={thStyle("left")}>Included</th>
            <th style={thStyle("left")}>Grade</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ ...tdL, fontWeight: 600 }}>Scope 1</td>
            <td style={tdL}>Direct on-site combustion — natural gas + heating oil/diesel</td>
            <td style={{ ...tdL, color: GOOD }}>Disclosure-grade</td>
          </tr>
          <tr>
            <td style={{ ...tdL, fontWeight: 600 }}>Scope 2</td>
            <td style={tdL}>
              Purchased electricity — location-based (grid factor) and market-based
              (supplier / Guarantees of Origin)
            </td>
            <td style={{ ...tdL, color: GOOD }}>Disclosure-grade</td>
          </tr>
          <tr>
            <td style={{ ...tdL, fontWeight: 600 }}>Scope 3</td>
            <td style={tdL}>
              Value chain — screening estimate spanning purchased goods/embodied (Cat 1),
              fuel &amp; energy (Cat 3), waste (Cat 5), business travel (Cat 6), employee
              commuting (Cat 7) and downstream leased assets (Cat 13).
            </td>
            <td style={{ ...tdL, color: BAD }}>Estimated — not disclosure-grade</td>
          </tr>
        </tbody>
      </table>

      {/* ---- Facility breakdown ---- */}
      {esrs.rows.length > 0 && (
        <>
          <SectionTitle>Facility breakdown (tCO₂e)</SectionTitle>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
            <thead>
              <tr style={{ backgroundColor: "#f1f5f9" }}>
                <th style={thStyle("left")}>Building</th>
                <th style={thStyle("right")}>Scope 1</th>
                <th style={thStyle("right")}>Scope 2 (loc)</th>
                <th style={thStyle("right")}>Scope 2 (mkt)</th>
                <th style={thStyle("right")}>Scope 3</th>
                <th style={thStyle("right")}>Total (loc)</th>
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
                  <td style={tdR}>{num(r.scope1_tco2e)}</td>
                  <td style={tdR}>{num(r.scope2_location_tco2e)}</td>
                  <td style={tdR}>{num(r.scope2_market_tco2e)}</td>
                  <td style={tdR}>{num(r.scope3_tco2e)}</td>
                  <td style={{ ...tdR, fontWeight: 700 }}>{num(r.total_location_tco2e)}</td>
                  <td style={tdR}>
                    {r.ghg_intensity_tco2e_m2 != null ? num(r.ghg_intensity_tco2e_m2, 3) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {/* ---- Data quality & methodology ---- */}
      <SectionTitle>Data quality &amp; methodology</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Buildings reported" value={`${esrs.buildings_reported} / ${esrs.buildings_total}`} hint="with GHG data" />
        <StatCard label="Complete" value={esrs.data_quality.complete} color={GOOD} hint="metered" />
        <StatCard label="Estimated" value={esrs.data_quality.estimated} color={BAD} hint="modelled" />
        <StatCard label="Missing gas" value={esrs.data_quality.missing_gas} color={DANGER} hint="needs fuel data" />
      </div>
      <div style={{ marginTop: 10, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Prepared with reference to the GHG Protocol Corporate Accounting and Reporting
        Standard and the Scope 2 Guidance (location- and market-based). Emission factors:
        national grid factors (Scope 2 location), supplier/GoO factors where available
        (Scope 2 market), BEHG/standard fuel factors (Scope 1), each at the most recent published vintage for the
        reporting year (state the exact factor source year in the final report). Scope 3 is a screening
        estimate spanning categories 1, 3, 5, 6, 7 and 13 (incl. business travel and
        employee commuting) and is not disclosure-grade; biogenic CO₂ and removals are excluded. This inventory is reporting
        support — it has not been independently verified or assured.
      </div>
    </div>
  )
}
