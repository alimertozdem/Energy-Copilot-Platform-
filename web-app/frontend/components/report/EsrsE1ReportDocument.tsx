/**
 * EsrsE1ReportDocument — body of the ESRS E-1 (Climate Change) report PDF.
 *
 * Full ESRS E-1 disclosure structure (E1-1 … E1-9). The QUANTITATIVE datapoints —
 * E1-5 (energy) and E1-6 (Scope 1/2/3 GHG) — are auto-filled from metered building
 * data (esrs_metrics). The NARRATIVE disclosures (E1-1..E1-4, E1-7..E1-9) render the
 * company's SAVED text when present (via the narrative editor), falling back to a
 * guided boilerplate draft with the available EnergyLens evidence — they are drafts to
 * complete, NOT auto-generated claims.
 *
 * Framing: ESRS-E1-aligned reporting SUPPORT, not an audited/assured disclosure or a
 * CSRD filing. Scope 3 is an estimate. Body-only; plugs into <ReportFrame>.
 */
import type { EsrsReport } from "@/lib/api/esrs"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import { summarizeStranding } from "@/lib/crrem"
import { E1_BY_CODE } from "@/lib/esrs/e1Disclosures"

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
  const d = E1_BY_CODE[code]
  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
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
      <div style={{ fontSize: 10.5, color: MUTED, marginTop: 3 }}>ESRS asks: {d.asks}</div>
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

export function EsrsE1ReportDocument({
  esrs,
  esrsError,
  buildings,
  buildingsError,
  narrative = {},
}: {
  esrs: EsrsReport | null
  esrsError: string | null
  buildings: PortfolioBuildingRow[]
  buildingsError: string | null
  narrative?: Record<string, string>
}) {
  const year = esrs?.reporting_year ?? null
  const g = esrs?.ghg ?? null
  const crrem = buildingsError ? null : summarizeStranding(buildings)

  const totalGhg = g ? num(g.total_location_tco2e) : "—"
  const operationalLoc = g ? g.scope1_tco2e + g.scope2_location_tco2e : null
  const operationalIntensityKg =
    g && esrs && esrs.floor_area_m2 > 0
      ? ((g.scope1_tco2e + g.scope2_location_tco2e) * 1000) / esrs.floor_area_m2
      : null
  const strandedNow = crrem?.strandedNow ?? null
  const strandedBy2030 = crrem?.strandedBy2030 ?? null
  const avgStrandYear = crrem?.avgStrandingYear ?? null

  const text = (code: string) => {
    const s = narrative[code]
    return s && s.trim() ? s : E1_BY_CODE[code].boilerplate
  }
  const isSaved = (code: string) => !!(narrative[code] && narrative[code].trim())

  return (
    <div>
      <div style={{ marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="ESRS E-1 Climate Change" color={EMERALD} />
        <Chip label="Quantitative auto-filled · narrative editable" color={MUTED} />
        {year != null && <Chip label={`Reporting year ${year}`} color={INK} />}
      </div>

      <div style={{ fontSize: 11, color: MUTED, lineHeight: 1.5, marginBottom: 4 }}>
        ESRS-E1-aligned reporting <strong>support</strong>. The quantitative datapoints
        (E1-5 energy, E1-6 GHG) are auto-filled from metered building data; the narrative
        disclosures (E1-1…E1-4, E1-7…E1-9) are written by the company in the narrative
        editor (a guided draft is shown until you save your own). Scope 3 is estimated.
        This is not an audited or assured disclosure, nor a CSRD filing.
      </div>

      <NarrativeSlot
        code="E1-1"
        evidence={
          crrem
            ? `${crrem.assessed} assets assessed; ${strandedNow ?? 0} already past the CRREM 1.5°C pathway, ${strandedBy2030 ?? 0} stranding by 2030${avgStrandYear ? ` (avg stranding year ${avgStrandYear})` : ""}.`
            : undefined
        }
        content={text("E1-1")}
        saved={isSaved("E1-1")}
      />
      <NarrativeSlot code="E1-2" content={text("E1-2")} saved={isSaved("E1-2")} />
      <NarrativeSlot
        code="E1-3"
        evidence="Decarbonisation measures identified by EnergyLens (heat pump, insulation, solar PV, LED, BMS) with per-building ROI are available in the recommendations engine."
        content={text("E1-3")}
        saved={isSaved("E1-3")}
      />
      <NarrativeSlot
        code="E1-4"
        evidence={g ? `Baseline gross emissions ${totalGhg} tCO₂e (Scope 1+2 location + 3, ${year ?? "latest year"}).` : undefined}
        content={text("E1-4")}
        saved={isSaved("E1-4")}
      />

      <SectionTitle>E1-5 · Energy consumption and mix {year ? `· ${year}` : ""}</SectionTitle>
      {esrsError ? (
        <Notice error={esrsError} label="energy" />
      ) : esrs && esrs.has_data ? (
        <>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <StatCard label="Total energy" value={`${num(esrs.energy_total_mwh)} MWh`} hint="metered consumption" />
          <StatCard
            label="Renewable share"
            value={esrs.energy_renewable_pct != null ? `${num(esrs.energy_renewable_pct, 1)} %` : "—"}
            color={GOOD}
            hint="on-site solar self-consumed"
          />
          <StatCard label="Floor area" value={`${fmtInt(esrs.floor_area_m2)} m²`} hint={`${esrs.buildings_reported}/${esrs.buildings_total} buildings`} />
          <StatCard
            label="Energy intensity"
            value={esrs.floor_area_m2 > 0 ? num((esrs.energy_total_mwh * 1000) / esrs.floor_area_m2, 0) : "—"}
            hint="kWh/m²·yr"
          />
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
          <StatCard
            label="Renewable energy"
            value={esrs.energy_renewable_pct != null ? `${num((esrs.energy_total_mwh * esrs.energy_renewable_pct) / 100)} MWh` : "—"}
            color={GOOD}
            hint="on-site solar self-consumed"
          />
          <StatCard
            label="Non-renewable energy"
            value={esrs.energy_renewable_pct != null ? `${num(esrs.energy_total_mwh * (1 - esrs.energy_renewable_pct / 100))} MWh` : "—"}
            hint="grid electricity + fossil heating"
          />
        </div>
        </>
      ) : (
        <div style={{ fontSize: 12, color: MUTED }}>No energy data for the period yet.</div>
      )}
      <div style={{ fontSize: 10, color: FAINT, marginTop: 6 }}>
        E1-5 disaggregation: renewable = on-site solar self-consumed; non-renewable = grid
        electricity + fossil heating fuel. A finer fossil split (coal / oil / gas) follows
        the fuel mix; nuclear is not applicable on-site. Purchased renewable electricity (green tariffs /
        Guarantees of Origin) is not counted here, so the renewable share is conservative.
        Energy intensity per net revenue
        (the E1-5 monetary datapoint) requires a revenue figure — [add company net revenue
        to complete].
      </div>

      <SectionTitle>E1-6 · Gross Scopes 1, 2, 3 and total GHG emissions {year ? `· ${year}` : ""}</SectionTitle>
      {esrsError ? (
        <Notice error={esrsError} label="GHG" />
      ) : esrs && esrs.has_data && g ? (
        <>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <StatCard label="Scope 1" value={num(g.scope1_tco2e)} hint="tCO₂e — direct combustion" />
            <StatCard label="Scope 2 (location)" value={num(g.scope2_location_tco2e)} hint="tCO₂e — grid" />
            <StatCard label="Scope 2 (market)" value={num(g.scope2_market_tco2e)} hint="tCO₂e — contractual" />
            <StatCard label="Scope 3 (est.)" value={num(g.scope3_tco2e)} color={BAD} hint="tCO₂e — value chain, incl. commuting (est.)" />
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
            <StatCard
              label="Operational (Scope 1+2)"
              value={operationalLoc != null ? num(operationalLoc) : "—"}
              color={INK}
              hint="tCO₂e — building energy (EPBD/CRREM basis)"
            />
            <StatCard
              label="Operational intensity"
              value={operationalIntensityKg != null ? num(operationalIntensityKg, 1) : "—"}
              color={INK}
              hint="kg CO₂e/m²·yr — building energy"
            />
          </div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 8 }}>
            <StatCard label="Total (location)" value={num(g.total_location_tco2e)} color={BAD} hint="S1+S2(loc)+S3" />
            <StatCard label="Total (market)" value={num(g.total_market_tco2e)} color={BAD} hint="S1+S2(mkt)+S3" />
            <StatCard
              label="GHG intensity"
              value={esrs.ghg_intensity_tco2e_m2 != null ? num(esrs.ghg_intensity_tco2e_m2, 3) : "—"}
              hint="tCO₂e/m² — incl. value chain"
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
            estimate (categories 1, 3, 5, 6, 7 and 13 — incl. business travel & employee commuting) and not disclosure-grade. Gross emissions are
            shown without netting (no removals or credits deducted). GHG is reported as CO₂e
            using IPCC AR6 GWP-100; building emissions are predominantly CO₂ (on-site
            combustion + grid electricity). No biogenic CO₂ arises in this portfolio (it is
            reported separately from the scopes if biomass is later used). GHG intensity per
            net revenue (the E1-6 monetary datapoint) requires a revenue figure — [add
            company net revenue]. Base year for target tracking: [set the first complete
            reporting year].
          </div>
        </>
      ) : (
        <div style={{ fontSize: 12, color: MUTED }}>No GHG data for the period yet.</div>
      )}

      <NarrativeSlot code="E1-7" content={text("E1-7")} saved={isSaved("E1-7")} />
      <NarrativeSlot code="E1-8" content={text("E1-8")} saved={isSaved("E1-8")} />
      <NarrativeSlot
        code="E1-9"
        evidence={
          crrem
            ? `Transition risk: ${strandedNow ?? 0} assets already past the 1.5°C pathway, ${strandedBy2030 ?? 0} stranding by 2030. Rising national CO₂ price (€55–65/t in 2026) and EU ETS2 from 2028 increase operating cost.`
            : "Rising CO₂ pricing (national nEHS 2026, EU ETS2 from 2028) increases heating operating cost."
        }
        content={text("E1-9")}
        saved={isSaved("E1-9")}
      />

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Prepared with reference to ESRS E-1 (Climate Change). Quantitative datapoints are
        auto-filled from metered energy + the GHG inventory (Scope 1+2 disclosure-grade,
        Scope 3 estimated). Narrative disclosures are written and approved by the company.
        This document is reporting support — it is not audited, assured, or a CSRD/ESRS
        filing, and the revised ESRS datapoint set should be confirmed against the final
        delegated act.
      </div>
    </div>
  )
}
