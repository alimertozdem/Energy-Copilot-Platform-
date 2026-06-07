/**
 * DecarbReportDocument — body of the /decarbonisation/report PDF (MACC plan).
 *
 * Presentational; plugs into <ReportFrame>. Portfolio CO₂ + cost summary cards
 * and the prioritised abatement table (measures sorted cheapest-first, €/tCO₂,
 * CapEx, cumulative CO₂). Uses the shared reportKit. The MAC assumption note is
 * printed so the PDF is self-explanatory and honest.
 */
import type { MaccResponse } from "@/lib/api/abatement"

import {
  EMERALD,
  FAINT,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  fmtInt,
  fmtMoney,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

export function DecarbReportDocument({
  data,
  error,
}: {
  data: MaccResponse | null
  error: string | null
}) {
  if (error || !data) return <Notice error={error ?? "unknown"} label="abatement data" />

  const t = data.totals

  return (
    <>
      <SectionTitle>Portfolio abatement summary</SectionTitle>
      <div style={{ display: "flex", gap: 12 }}>
        <StatCard
          label="Abatable CO₂"
          value={`${fmtInt(t.total_annual_co2_t)} t/yr`}
          hint={`${t.measure_count} measures`}
        />
        <StatCard
          label="No-regret CO₂"
          value={`${fmtInt(t.profitable_annual_co2_t)} t/yr`}
          color={GOOD}
          hint="Pays for itself"
        />
        <StatCard
          label="No-regret CapEx"
          value={fmtMoney(t.profitable_net_capex_eur)}
          color={GOOD}
          hint="Self-funding"
        />
        <StatCard
          label="Weighted avg cost"
          value={
            t.weighted_avg_mac_eur_per_t === null
              ? "—"
              : `€${fmtInt(t.weighted_avg_mac_eur_per_t)}/t`
          }
          hint="CO₂-weighted"
        />
      </div>

      <SectionTitle>Prioritised investment plan</SectionTitle>
      {data.measures.length === 0 ? (
        <div style={{ fontSize: 12, color: MUTED, padding: "12px 0" }}>
          No abating measures with quantified CO₂ savings.
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ backgroundColor: "#f1f5f9" }}>
              <th style={thStyle("left")}>#</th>
              <th style={thStyle("left")}>Measure</th>
              <th style={thStyle("left")}>Building</th>
              <th style={thStyle("right")}>€/tCO₂</th>
              <th style={thStyle("right")}>tCO₂/yr</th>
              <th style={thStyle("right")}>Net CapEx</th>
              <th style={thStyle("right")}>€/yr saved</th>
              <th style={thStyle("right")}>Σ tCO₂</th>
              <th style={thStyle("left")}>Driver</th>
            </tr>
          </thead>
          <tbody>
            {data.measures.map((m, i) => {
              const sub = [m.action_type, `~${m.assumed_lifetime_years}y life`]
                .filter(Boolean)
                .join(" · ")
              return (
                <tr key={m.action_id}>
                  <td style={{ ...tdL, color: FAINT }}>{i + 1}</td>
                  <td style={tdL}>
                    <div style={{ fontWeight: 600, color: INK }}>{m.title ?? "Measure"}</div>
                    {sub && <div style={{ fontSize: 10, color: MUTED, marginTop: 2 }}>{sub}</div>}
                  </td>
                  <td style={{ ...tdL, color: MUTED }}>{m.building_name}</td>
                  <td style={{ ...tdR, color: m.is_profitable ? EMERALD : INK, fontWeight: 600 }}>
                    {fmtMoney(m.mac_eur_per_t)}
                  </td>
                  <td style={tdR}>{fmtInt(m.annual_co2_t)}</td>
                  <td style={tdR}>{fmtMoney(m.net_capex_eur)}</td>
                  <td style={tdR}>{fmtMoney(m.annual_saving_eur)}</td>
                  <td style={{ ...tdR, color: FAINT }}>{fmtInt(m.cumulative_co2_t)}</td>
                  <td style={{ ...tdL, fontSize: 10, color: FAINT }}>
                    {m.compliance_driver ?? "—"}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>{data.note}</div>
    </>
  )
}
