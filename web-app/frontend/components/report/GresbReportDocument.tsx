/**
 * GresbReportDocument — body for the GRESB-aligned Performance readiness report.
 *
 * The GRESB Real Estate Performance Component scores asset performance across energy
 * (EN1), GHG (GH1), water (WT1), waste (WS1) and building certifications (BC). EnergyLens
 * can populate the ENERGY and GHG indicators from metered data; the rest is shown as a
 * readiness checklist. Reuses the ESRS endpoint (esrs_metrics). Body-only; plugs into
 * <ReportFrame>.
 *
 * Honesty: this is an INDICATIVE readiness view, NOT an official GRESB score or a GRESB
 * submission (which requires GRESB membership and the GRESB portal). Data coverage must
 * reach GRESB's 75% (by area × time) threshold to fairly represent a building.
 */
import type { EsrsReport } from "@/lib/api/esrs"

import {
  PartialYearNotice,
  BAD,
  Chip,
  EMERALD,
  FAINT,
  fmtInt,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  tdC,
  tdL,
  thStyle,
} from "./reportKit"

const AMBER = "#b45309"

function num(v: number | null, d = 1): string {
  if (v === null || v === undefined) return "—"
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: d }).format(v)
}

type Readiness = { indicator: string; asks: string; status: "ready" | "partial" | "missing"; note: string }

const CHECKLIST: Readiness[] = [
  { indicator: "EN1 · Energy", asks: "Energy consumption + intensity, with ≥75% data coverage", status: "ready", note: "Metered energy + intensity available" },
  { indicator: "GH1 · GHG", asks: "Scope 1/2/3 emissions + intensity", status: "ready", note: "Scope 1+2 metered, Scope 3 estimated" },
  { indicator: "BC1/BC2 · Certifications & ratings", asks: "Building certifications + energy ratings (EPC)", status: "partial", note: "EPC pre-assessment available; formal certificates to add" },
  { indicator: "WT1 · Water", asks: "Water withdrawal + intensity", status: "missing", note: "Not tracked by EnergyLens" },
  { indicator: "WS1 · Waste", asks: "Waste generated + diversion", status: "missing", note: "Not tracked by EnergyLens" },
  { indicator: "Management · Targets / risk / tenant engagement", asks: "Policies, targets, risk management, tenant engagement", status: "partial", note: "Targets + risk via ESRS narrative / CRREM; tenant engagement to provide" },
]

function statusChip(s: Readiness["status"]): { text: string; color: string } {
  if (s === "ready") return { text: "Ready", color: GOOD }
  if (s === "partial") return { text: "Partial", color: AMBER }
  return { text: "Missing", color: BAD }
}

export function GresbReportDocument({
  esrs,
  esrsError,
}: {
  esrs: EsrsReport | null
  esrsError: string | null
}) {
  if (esrsError) {
    return <Notice error={esrsError} label="GRESB readiness" />
  }
  if (!esrs || !esrs.has_data) {
    return (
      <div style={{ fontSize: 13, color: MUTED, padding: "8px 0" }}>
        No performance data is available for the reporting period yet. Once building energy
        is connected, the energy + GHG indicators populate automatically.
      </div>
    )
  }

  const g = esrs.ghg
  const energyIntensity = esrs.floor_area_m2 > 0 ? (esrs.energy_total_mwh * 1000) / esrs.floor_area_m2 : null
  const coveragePct = esrs.buildings_total > 0 ? (esrs.buildings_reported / esrs.buildings_total) * 100 : null

  return (
    <div>
      <div style={{ marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="GRESB-aligned · Performance readiness" color={EMERALD} />
        <Chip label="Indicative — not an official GRESB score or submission" color={AMBER} />
        {esrs.reporting_year != null && <Chip label={`Reporting year ${esrs.reporting_year}`} color={INK} />}
      </div>

      <div style={{ fontSize: 11, color: MUTED, lineHeight: 1.5, marginBottom: 4 }}>
        The GRESB Real Estate <strong>Performance Component</strong> scores asset performance
        across energy, GHG, water, waste and building certifications (28 indicators).
        EnergyLens populates the <strong>energy (EN1)</strong> and <strong>GHG (GH1)</strong>
        indicators from your metered data; the readiness of the rest is shown below. This is
        not an official GRESB score — a GRESB result requires GRESB membership and submission
        through the GRESB portal, with data coverage meeting the 75% (area × time) threshold.
      </div>

      <PartialYearNotice months={esrs?.reporting_months} year={esrs?.reporting_year} />
      <SectionTitle>Data coverage</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Assets reported" value={`${esrs.buildings_reported}/${esrs.buildings_total}`} hint="with performance data" />
        <StatCard
          label="Coverage"
          value={coveragePct != null ? `${num(coveragePct, 0)} %` : "—"}
          color={coveragePct != null && coveragePct >= 75 ? GOOD : AMBER}
          hint="GRESB threshold ≥ 75%"
        />
        <StatCard label="Floor area" value={`${fmtInt(esrs.floor_area_m2)} m²`} hint="reporting boundary" />
        <StatCard label="Metered" value={`${esrs.data_quality.complete}`} color={GOOD} hint="rest estimated" />
      </div>

      <SectionTitle>EN1 · Energy</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Total energy" value={`${num(esrs.energy_total_mwh)} MWh`} hint="metered consumption" />
        <StatCard label="Energy intensity" value={energyIntensity != null ? `${num(energyIntensity, 0)}` : "—"} hint="kWh/m²·yr" />
        <StatCard
          label="Renewable share"
          value={esrs.energy_renewable_pct != null ? `${num(esrs.energy_renewable_pct, 1)} %` : "—"}
          color={GOOD}
          hint="on-site solar self-consumed"
        />
      </div>

      <SectionTitle>GH1 · GHG emissions</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Scope 1" value={num(g.scope1_tco2e)} hint="tCO₂e — direct" />
        <StatCard label="Scope 2 (location)" value={num(g.scope2_location_tco2e)} hint="tCO₂e — grid" />
        <StatCard label="Scope 3 (est.)" value={num(g.scope3_tco2e)} color={BAD} hint="tCO₂e — value chain" />
        <StatCard
          label="GHG intensity"
          value={esrs.ghg_intensity_tco2e_m2 != null ? num(esrs.ghg_intensity_tco2e_m2, 3) : "—"}
          hint="tCO₂e/m²"
        />
      </div>

      <SectionTitle>Indicator readiness</SectionTitle>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
        <thead>
          <tr style={{ backgroundColor: "#f1f5f9" }}>
            <th style={thStyle("left")}>Indicator</th>
            <th style={thStyle("left")}>What GRESB asks</th>
            <th style={thStyle("center")}>Status</th>
            <th style={thStyle("left")}>Note</th>
          </tr>
        </thead>
        <tbody>
          {CHECKLIST.map((r) => {
            const st = statusChip(r.status)
            return (
              <tr key={r.indicator}>
                <td style={{ ...tdL, fontWeight: 600 }}>{r.indicator}</td>
                <td style={tdL}>{r.asks}</td>
                <td style={{ ...tdC, color: st.color, fontWeight: 700 }}>{st.text}</td>
                <td style={{ ...tdL, color: MUTED }}>{r.note}</td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Prepared as a GRESB Performance readiness view from metered energy + the GHG
        inventory. It is indicative and is not an official GRESB score, rating or submission;
        a GRESB result requires GRESB membership and the GRESB portal, with the assessment&apos;s
        own methodology, like-for-like (year-on-year) reporting and data-coverage thresholds.
        Water, waste and formal building certifications are out of scope here.
      </div>
    </div>
  )
}
