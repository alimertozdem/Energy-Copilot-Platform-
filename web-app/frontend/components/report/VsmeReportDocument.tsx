/**
 * VsmeReportDocument — body of the VSME (Voluntary SME standard) Basic Module report.
 *
 * VSME Basic Module = B1–B11. The ONE quantitative disclosure, B3 (Energy & GHG
 * emissions), is auto-filled from metered building data (esrs_metrics — the same
 * source as the ESRS E-1 report). The other disclosures (B1, B2, B4–B11) render the
 * company's SAVED narrative when present, falling back to a guided boilerplate draft —
 * they are drafts to complete, NOT auto-generated claims.
 *
 * Framing: VSME-aligned reporting SUPPORT, not an audited/assured disclosure. Scope 3
 * is an estimate. Body-only; plugs into <ReportFrame>. The Comprehensive Module
 * (C1–C9) is a later extension.
 */
import type { EsrsReport } from "@/lib/api/esrs"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import {
  PartialYearNotice, summarizeStranding } from "@/lib/crrem"
import { VSME_ALL_BY_CODE } from "@/lib/vsme/vsmeDisclosures"

import {
  BAD,
  Chip,
  EMERALD,
  FAINT,
  fmtInt,
  GOOD,
  INK,
  LINE,
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

function NarrativeSlot({
  code,
  evidence,
  content,
  saved,
}: {
  code: string
  evidence?: string
  content: string
  saved: boolean
}) {
  const d = VSME_ALL_BY_CODE[code]
  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: INK }}>{code}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color: INK }}>{d.title}</span>
        <span
          style={{
            fontSize: 9,
            fontWeight: 600,
            color: saved ? GOOD : BAD,
            border: `1px solid ${saved ? GOOD : BAD}`,
            borderRadius: 999,
            padding: "1px 6px",
          }}
        >
          {saved ? "Narrative — provided" : "Narrative — to complete"}
        </span>
      </div>
      <div style={{ fontSize: 10.5, color: MUTED, marginTop: 3 }}>VSME asks: {d.asks}</div>
      {evidence && (
        <div style={{ fontSize: 10.5, color: EMERALD, marginTop: 2 }}>
          EnergyLens evidence: {evidence}
        </div>
      )}
      <div
        style={{
          marginTop: 5,
          padding: "9px 11px",
          border: `1px dashed ${LINE}`,
          borderLeft: `3px solid ${saved ? GOOD : MUTED}`,
          borderRadius: 4,
          backgroundColor: "#f8fafc",
          fontSize: 11,
          color: INK,
          lineHeight: 1.55,
          whiteSpace: "pre-wrap",
        }}
      >
        {content}
      </div>
    </div>
  )
}

export function VsmeReportDocument({
  esrs,
  esrsError,
  buildings,
  buildingsError: _buildingsError,
  narrative = {},
  comprehensive = false,
}: {
  esrs: EsrsReport | null
  esrsError: string | null
  buildings: PortfolioBuildingRow[]
  buildingsError: string | null
  narrative?: Record<string, string>
  comprehensive?: boolean
}) {
  const year = esrs?.reporting_year ?? null
  const g = esrs?.ghg ?? null
  const crrem = comprehensive ? summarizeStranding(buildings) : null

  const text = (code: string) => {
    const s = narrative[code]
    return s && s.trim() ? s : VSME_ALL_BY_CODE[code].boilerplate
  }
  const isSaved = (code: string) => !!(narrative[code] && narrative[code].trim())

  return (
    <div>
      <div style={{ marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label={comprehensive ? "VSME — Basic + Comprehensive" : "VSME — Basic Module"} color={EMERALD} />
        <Chip label="B3 auto-filled · narrative to complete" color={MUTED} />
        {year != null && <Chip label={`Reporting year ${year}`} color={INK} />}
      </div>

      <div style={{ fontSize: 11, color: MUTED, lineHeight: 1.5, marginBottom: 4 }}>
        VSME-aligned reporting <strong>support</strong> (EFRAG Voluntary SME standard,
        Basic Module B1–B11). Disclosure <strong>B3</strong> (energy &amp; GHG) is
        auto-filled from metered building data; the remaining disclosures are written by
        the company (a guided draft is shown until your own text is saved). Scope 3 is
        estimated. This is not an audited or assured disclosure.
      </div>

      <PartialYearNotice months={esrs?.reporting_months} year={esrs?.reporting_year} />
      <SectionTitle>General information</SectionTitle>
      <NarrativeSlot code="B1" content={text("B1")} saved={isSaved("B1")} />
      <NarrativeSlot
        code="B2"
        evidence="Energy monitoring, anomaly detection and a prioritised retrofit roadmap (heat pump, insulation, solar PV, LED, BMS) with per-building ROI are maintained in EnergyLens."
        content={text("B2")}
        saved={isSaved("B2")}
      />

      <SectionTitle>
        B3 · Energy and greenhouse gas emissions {year ? `· ${year}` : ""}
      </SectionTitle>

      {esrsError ? (
        <Notice error={esrsError} label="energy" />
      ) : esrs && esrs.has_data ? (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <StatCard label="Total energy" value={`${num(esrs.energy_total_mwh)} MWh`} hint="metered consumption" />
          <StatCard
            label="Renewable share"
            value={esrs.energy_renewable_pct != null ? `${num(esrs.energy_renewable_pct, 1)} %` : "—"}
            color={GOOD}
            hint="on-site solar self-consumed"
          />
          <StatCard
            label="Floor area"
            value={`${fmtInt(esrs.floor_area_m2)} m²`}
            hint={`${esrs.buildings_reported}/${esrs.buildings_total} buildings`}
          />
          <StatCard
            label="Energy intensity"
            value={esrs.floor_area_m2 > 0 ? num((esrs.energy_total_mwh * 1000) / esrs.floor_area_m2, 0) : "—"}
            hint="kWh/m²·yr"
          />
        </div>
      ) : (
        <div style={{ fontSize: 12, color: MUTED }}>No energy data for the period yet.</div>
      )}

      {esrs && esrs.has_data && g ? (
        <>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
            <StatCard label="Scope 1" value={num(g.scope1_tco2e)} hint="tCO₂e — direct combustion" />
            <StatCard label="Scope 2 (location)" value={num(g.scope2_location_tco2e)} hint="tCO₂e — grid" />
            <StatCard label="Scope 2 (market)" value={num(g.scope2_market_tco2e)} hint="tCO₂e — contractual" />
            <StatCard label="Scope 3 (est.)" value={num(g.scope3_tco2e)} color={BAD} hint="tCO₂e — value chain" />
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
            <StatCard label="Total (location)" value={num(g.total_location_tco2e)} color={BAD} hint="S1+S2(loc)+S3" />
            <StatCard label="Total (market)" value={num(g.total_market_tco2e)} color={BAD} hint="S1+S2(mkt)+S3" />
            <StatCard
              label="GHG intensity"
              value={esrs.ghg_intensity_tco2e_m2 != null ? num(esrs.ghg_intensity_tco2e_m2, 3) : "—"}
              hint="tCO₂e/m²"
            />
            <StatCard
              label="Data quality"
              value={`${esrs.data_quality.complete}/${esrs.buildings_reported}`}
              hint="complete · rest estimated"
            />
          </div>
          {esrs.rows.length > 0 && (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, marginTop: 10 }}>
              <thead>
                <tr style={{ backgroundColor: "#f1f5f9" }}>
                  <th style={thStyle("left")}>Building</th>
                  <th style={thStyle("right")}>Scope 1</th>
                  <th style={thStyle("right")}>Scope 2 (loc)</th>
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
                    <td style={tdR}>{num(r.scope3_tco2e)}</td>
                    <td style={{ ...tdR, fontWeight: 700 }}>{num(r.total_location_tco2e)}</td>
                    <td style={tdR}>{r.ghg_intensity_tco2e_m2 != null ? num(r.ghg_intensity_tco2e_m2, 3) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div style={{ fontSize: 10, color: FAINT, marginTop: 6 }}>
            Scope 1+2 are disclosure-grade (metered building energy). Scope 3 is a screening
            estimate (categories 1, 3, 5, 6, 7 and 13 — incl. business travel & employee commuting) and not disclosure-grade. Energy and GHG per
            unit of revenue (VSME B3 datapoints) require a revenue figure — [add company
            revenue to complete].
          </div>
        </>
      ) : esrsError ? null : (
        <div style={{ fontSize: 12, color: MUTED, marginTop: 8 }}>No GHG data for the period yet.</div>
      )}

      <SectionTitle>Environmental — other</SectionTitle>
      <NarrativeSlot code="B4" content={text("B4")} saved={isSaved("B4")} />
      <NarrativeSlot code="B5" content={text("B5")} saved={isSaved("B5")} />
      <NarrativeSlot code="B6" content={text("B6")} saved={isSaved("B6")} />
      <NarrativeSlot code="B7" content={text("B7")} saved={isSaved("B7")} />

      <SectionTitle>Social</SectionTitle>
      <NarrativeSlot code="B8" content={text("B8")} saved={isSaved("B8")} />
      <NarrativeSlot code="B9" content={text("B9")} saved={isSaved("B9")} />
      <NarrativeSlot code="B10" content={text("B10")} saved={isSaved("B10")} />

      <SectionTitle>Governance</SectionTitle>
      <NarrativeSlot code="B11" content={text("B11")} saved={isSaved("B11")} />

      {comprehensive && (
        <>
          <SectionTitle>Comprehensive Module (C1–C9)</SectionTitle>
          <div style={{ fontSize: 10.5, color: MUTED, marginBottom: 2, lineHeight: 1.5 }}>
            The Comprehensive level adds the information banks and investors typically
            request. C3 and C4 draw on your EnergyLens data; the other disclosures prompt
            for the specific figures your company provides, and complete once entered.
          </div>
          <NarrativeSlot code="C1" content={text("C1")} saved={isSaved("C1")} />
          <NarrativeSlot code="C2" content={text("C2")} saved={isSaved("C2")} />
          <NarrativeSlot
            code="C3"
            evidence={
              g
                ? `Baseline gross emissions ${num(g.total_location_tco2e)} tCO₂e (${year ?? "latest year"}); decarbonisation levers + per-measure CO₂ / cost are in the recommendations.`
                : undefined
            }
            content={text("C3")}
            saved={isSaved("C3")}
          />
          <NarrativeSlot
            code="C4"
            evidence={
              crrem
                ? `${crrem.strandedNow ?? 0} assets already past the 1.5°C pathway, ${crrem.strandedBy2030 ?? 0} stranding by 2030 (CRREM); rising CO₂ price (nEHS 2026, EU ETS2 2028) raises operating cost.`
                : undefined
            }
            content={text("C4")}
            saved={isSaved("C4")}
          />
          <NarrativeSlot code="C5" content={text("C5")} saved={isSaved("C5")} />
          <NarrativeSlot code="C6" content={text("C6")} saved={isSaved("C6")} />
          <NarrativeSlot code="C7" content={text("C7")} saved={isSaved("C7")} />
          <NarrativeSlot code="C8" content={text("C8")} saved={isSaved("C8")} />
          <NarrativeSlot code="C9" content={text("C9")} saved={isSaved("C9")} />
        </>
      )}

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Prepared with reference to the VSME Basic Module (EFRAG Voluntary SME standard).
        Disclosure B3 is auto-filled from metered energy + the GHG inventory (Scope 1+2
        disclosure-grade, Scope 3 estimated). The remaining disclosures are written and
        approved by the company. This document is reporting support — it is not audited,
        assured, or a regulatory filing. At the Comprehensive level the C-module adds further company-provided disclosures.
      </div>
    </div>
  )
}
