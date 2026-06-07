/**
 * FinancingReportDocument — body of the /financing/report PDF (subsidy pack).
 *
 * Presentational; plugs into <ReportFrame>. Mirrors the on-screen FinancingView:
 * indicative KfW/BAFA grant capture from the recommendation catalog. Support,
 * not advice — carries the same legal framing and assumptions footnote.
 */
import type { ActionItem } from "@/lib/api/actions"
import { estimateSubsidy } from "@/lib/finance/subsidy"

import {
  EMERALD,
  FAINT,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  fmtMoney,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

function eur(n: number | null): string {
  return fmtMoney(n)
}

export function FinancingReportDocument({
  actions,
  error,
}: {
  actions: ActionItem[]
  error: string | null
}) {
  if (error) return <Notice error={error} label="recommendations" />

  const rows = actions
    .map((a) => {
      const capex = a.net_capex_eur ?? a.capex_eur ?? null
      return { a, capex, sub: estimateSubsidy(a.action_type, capex) }
    })
    .filter((r) => r.sub.eligible && r.sub.grantEur != null)
    .sort((x, y) => (y.sub.grantEur ?? 0) - (x.sub.grantEur ?? 0))

  const totalGrant = rows.reduce((s, r) => s + (r.sub.grantEur ?? 0), 0)
  const totalCapex = rows.reduce((s, r) => s + (r.capex ?? 0), 0)

  return (
    <>
      <div
        style={{
          padding: "8px 12px",
          borderRadius: 6,
          fontSize: 11,
          border: "1px solid #fcd34d",
          backgroundColor: "#fffbeb",
          color: "#92400e",
          marginTop: 4,
        }}
      >
        Indicative subsidy-application <strong>support</strong>, not financial advice. Programmes
        (KfW&nbsp;458 · BAFA&nbsp;BEG&nbsp;EM · KfW&nbsp;261) and bonus eligibility change — verify
        against the live programme, and <strong>apply before signing any contract</strong> (signing
        first forfeits the subsidy).
      </div>

      <SectionTitle>Indicative Capture</SectionTitle>
      <div style={{ display: "flex", gap: 12 }}>
        <StatCard label="Indicative subsidy" value={eur(totalGrant)} color={EMERALD} hint="Across eligible measures" />
        <StatCard label="Eligible measures" value={rows.length} hint="Grant-mapped" />
        <StatCard label="Capex (eligible)" value={eur(totalCapex)} hint="Before subsidy" />
        <StatCard label="Net after subsidy" value={eur(totalCapex - totalGrant)} hint="Indicative" />
      </div>

      <SectionTitle>Application Pack</SectionTitle>
      {rows.length === 0 ? (
        <div style={{ fontSize: 12, color: MUTED, padding: "12px 0" }}>
          No grant-eligible measures yet. Heating, envelope and controls recommendations with a capex
          estimate map to KfW/BAFA programmes. Solar PV is funded separately (EEG).
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ backgroundColor: "#f1f5f9" }}>
              <th style={thStyle("left")}>Measure</th>
              <th style={thStyle("left")}>Building</th>
              <th style={thStyle("left")}>Programme</th>
              <th style={thStyle("right")}>Rate</th>
              <th style={thStyle("right")}>Capex</th>
              <th style={thStyle("right")}>Indicative grant</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td style={{ ...tdL, fontWeight: 600, color: INK }}>
                  {r.a.title ?? r.a.action_type ?? "Measure"}
                  <div style={{ fontSize: 10, color: MUTED, fontWeight: 400, marginTop: 2 }}>
                    {r.sub.scheme}
                  </div>
                </td>
                <td style={{ ...tdL, color: MUTED }}>{r.a.building_name}</td>
                <td style={tdL}>{r.sub.program}</td>
                <td style={tdR}>
                  {r.sub.ratePct}%
                  {r.sub.maxRatePct > r.sub.ratePct ? `–${r.sub.maxRatePct}%` : ""}
                </td>
                <td style={tdR}>{eur(r.capex)}</td>
                <td style={{ ...tdR, fontWeight: 700, color: EMERALD }}>{eur(r.sub.grantEur)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: 14, fontSize: 10, lineHeight: 1.5, color: FAINT }}>
        Indicative grants apply each programme&rsquo;s base rate to capex capped per unit (KfW&nbsp;458
        ~€30k, BAFA&nbsp;BEG&nbsp;EM €30k). Actual amounts depend on bonuses (speed, income, iSFP), unit
        counts and the live programme. Treat as a planning estimate; a financing-partner referral is not
        a lending offer.
      </div>
    </>
  )
}
