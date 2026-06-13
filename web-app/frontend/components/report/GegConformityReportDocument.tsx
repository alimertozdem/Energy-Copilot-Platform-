/**
 * GegConformityReportDocument — body for the per-building GEG conformity report.
 *
 * German Gebäudeenergiegesetz (GEG) screening: §71 renewable-heating duty (65%, on the
 * municipal heat-planning timeline) and §48 / Anlage 7 envelope U-value limits (which
 * apply when a component is renovated). Body-only; plugs into <ReportFrame>. Inline-styled.
 *
 * Data: GET /compliance/geg/{id} (gold_compliance_results). Screening / decision-support,
 * not a formal Nachweis or legal advice — see the footer disclaimer.
 */
import type { GegConformity } from "@/lib/api/geg"

import {
  BAD,
  Chip,
  DANGER,
  EMERALD,
  FAINT,
  fmtNum,
  GOOD,
  INK,
  LINE,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  tdC,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

function yesNo(v: boolean | null): { text: string; color: string } {
  if (v === true) return { text: "Compliant", color: GOOD }
  if (v === false) return { text: "Not compliant", color: DANGER }
  return { text: "—", color: MUTED }
}

export function GegConformityReportDocument({
  data,
  error,
}: {
  data: GegConformity | null
  error: string | null
}) {
  if (error) {
    return <Notice error={error} label="GEG conformity" />
  }
  if (!data) {
    return (
      <div style={{ fontSize: 13, color: MUTED, padding: "8px 0" }}>
        No GEG conformity data is available for this building yet.
      </div>
    )
  }

  if (!data.has_data) {
    return (
      <div>
        <div style={{ marginBottom: 14, display: "flex", gap: 8 }}>
          <Chip label="GEG conformity (Gebäudeenergiegesetz)" color={EMERALD} />
        </div>
        <div
          style={{
            padding: "12px 14px",
            borderRadius: 6,
            border: `1px solid ${LINE}`,
            backgroundColor: "#f8fafc",
            fontSize: 12,
            color: MUTED,
          }}
        >
          Compliance has not been computed for this building yet. Once the compliance
          pipeline runs, this report fills in automatically.
        </div>
        <Disclaimer data={data} />
      </div>
    )
  }

  const heating = yesNo(data.heating_compliant)

  return (
    <div>
      <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="GEG conformity (Gebäudeenergiegesetz)" color={EMERALD} />
        {data.geg_status && <Chip label={data.geg_status} color={INK} />}
        {data.country_code && <Chip label={data.country_code} color={MUTED} />}
      </div>

      {!data.applies && (
        <div
          style={{
            marginBottom: 10,
            padding: "8px 11px",
            borderRadius: 6,
            border: `1px solid #fcd34d`,
            backgroundColor: "#fffbeb",
            fontSize: 11,
            color: "#92400e",
          }}
        >
          The GEG is German law; this building is in {data.country_code ?? "another country"}.
          Figures are shown for reference — the U-value limits reflect good practice, but the
          binding national requirements differ (e.g. OIB in Austria, Energielabel in the
          Netherlands).
        </div>
      )}

      {/* Headline */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="GEG score"
          value={data.geg_score != null ? fmtNum(data.geg_score) : "—"}
          hint="0–100 conformity screening"
        />
        <StatCard label="GEG status" value={data.geg_status ?? "—"} hint="overall band" />
        <StatCard
          label="Heating §71"
          value={heating.text}
          color={heating.color}
          hint="≥65% renewable system"
        />
        <StatCard
          label="Envelope §48"
          value={`${data.components_compliant} / ${data.components_total}`}
          color={data.components_compliant === data.components_total ? GOOD : BAD}
          hint="components within U-limit"
        />
      </div>

      {/* §71 Heating */}
      <SectionTitle>§71 · Renewable heating (65%)</SectionTitle>
      <div style={{ fontSize: 12, color: INK, lineHeight: 1.6 }}>
        Current heating system is{" "}
        <strong style={{ color: heating.color }}>
          {data.heating_compliant === true
            ? "already a renewable-compliant system"
            : data.heating_compliant === false
            ? "not yet a renewable-compliant system"
            : "unknown"}
        </strong>
        . {data.heating_compliant === false ? "Switching to a heat pump, district heat, biomass or a heat-network connection would satisfy §71 at the next heating replacement." : ""}
      </div>
      <div style={{ marginTop: 5, fontSize: 10.5, color: MUTED, lineHeight: 1.5 }}>
        {data.heating_note}
      </div>

      {/* §48 / Anlage 7 Envelope */}
      <SectionTitle>§48 / Anlage 7 · Envelope U-values (on renovation)</SectionTitle>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={thStyle("left")}>Component</th>
            <th style={thStyle("right")}>Current U</th>
            <th style={thStyle("right")}>GEG limit</th>
            <th style={thStyle("center")}>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.components.map((c) => {
            const st = yesNo(c.compliant)
            return (
              <tr key={c.component}>
                <td style={{ ...tdL, fontWeight: 600 }}>
                  {c.component}
                  {c.note && (
                    <div style={{ fontSize: 9, color: FAINT }}>{c.note}</div>
                  )}
                </td>
                <td style={tdR}>{c.current_u != null ? `${fmtNum(c.current_u)} W/m²K` : "—"}</td>
                <td style={tdR}>≤ {fmtNum(c.limit_u)}</td>
                <td style={{ ...tdC, color: st.color, fontWeight: 700 }}>{st.text}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <div style={{ marginTop: 6, fontSize: 10.5, color: MUTED, lineHeight: 1.5 }}>
        These limits apply when a component is renovated over more than 10% of its area
        (Anlage 7 / §48). §47 additionally requires insulating the top-floor ceiling (or
        roof) to ≤ 0.24 W/m²K within 24 months of purchase. Components above the limit are
        the priority for any planned refurbishment.
      </div>

      <Disclaimer data={data} />
    </div>
  )
}

function Disclaimer({ data }: { data: GegConformity }) {
  return (
    <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
      {data.note} Source: {data.data_source}. Decision-support, not a formal GEG Nachweis
      or legal advice.
    </div>
  )
}
