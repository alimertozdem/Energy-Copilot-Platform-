/**
 * FinancingReportDocument — body of the /financing/report PDF (subsidy + financing
 * application pack). Presentational; plugs into <ReportFrame>.
 *
 * Mirrors the on-screen FinancingView 1:1 (same /financing/summary data): unit-aware
 * subsidy ranges, three-scenario discounted NPV, indicative EPC value uplift, and a
 * transparent method block with a currency stamp. SUPPORT, NOT ADVICE.
 */
import type { FinancingSummary } from "@/lib/api/financing"

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
function eurRange(lo: number | null, hi: number | null): string {
  if (lo == null && hi == null) return "—"
  if (lo === hi || hi == null) return eur(lo)
  if (lo == null) return eur(hi)
  return `${eur(lo)}–${eur(hi)}`
}

const SCEN_LABEL: Record<string, string> = {
  conservative: "Conservative",
  base: "Base",
  high: "Policy-tight",
}

export function FinancingReportDocument({
  summary,
  error,
}: {
  summary: FinancingSummary | null
  error: string | null
}) {
  if (error) return <Notice error={error} label="financing summary" />
  if (!summary) return <Notice error="No data" label="financing summary" />

  const p = summary.portfolio
  const a = summary.assumptions as Record<string, unknown>
  const carbon2030 = (a.carbon_2030_eur_t ?? {}) as Record<string, number>

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
        Indicative financing <strong>support</strong>, not financial advice. Programmes
        (KfW&nbsp;458 · BAFA&nbsp;BEG&nbsp;EM · KfW&nbsp;261) and carbon prices change — verify against
        the live programme, and <strong>apply before signing any contract</strong> (signing first
        forfeits the subsidy). Rates verified {String(a.rates_verified ?? "")}.
      </div>

      <SectionTitle>Indicative Capture</SectionTitle>
      <div style={{ display: "flex", gap: 12 }}>
        <StatCard label="Indicative grant" value={eurRange(p.total_grant_low_eur, p.total_grant_high_eur)} color={EMERALD} hint="Rate range, eligible measures" />
        <StatCard label="Eligible measures" value={p.eligible_measure_count} hint="Grant-mapped" />
        <StatCard label="Gross capex" value={eur(p.total_capex_gross_eur)} hint="Before subsidy" />
        <StatCard label="Net after grant" value={eur(p.total_net_after_grant_eur)} hint="Grant-midpoint" />
      </div>

      {p.scenarios.length > 0 && (
        <>
          <SectionTitle>Lifetime Value — Discounted, by Scenario</SectionTitle>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
            <thead>
              <tr style={{ backgroundColor: "#f1f5f9" }}>
                <th style={thStyle("left")}>Scenario</th>
                <th style={thStyle("right")}>Portfolio NPV</th>
                <th style={thStyle("right")}>Carbon @2030</th>
                <th style={thStyle("right")}>Energy inflation</th>
              </tr>
            </thead>
            <tbody>
              {p.scenarios.map((s) => (
                <tr key={s.scenario}>
                  <td style={{ ...tdL, fontWeight: 600, color: INK }}>{SCEN_LABEL[s.scenario] ?? s.scenario}</td>
                  <td style={{ ...tdR, fontWeight: 700, color: s.total_npv_eur >= 0 ? EMERALD : "#b91c1c" }}>{eur(s.total_npv_eur)}</td>
                  <td style={tdR}>€{s.carbon_2030_eur_t}/t</td>
                  <td style={tdR}>+{s.energy_inflation_pct}%/yr</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 6, fontSize: 10, lineHeight: 1.5, color: FAINT }}>
            Portfolio NPV of the eligible measures over their service life, discounted at{" "}
            {String(a.discount_rate_pct ?? "")}%/yr, net of the grant. Today €{String(a.carbon_now_eur_t ?? "")}/t →
            €{carbon2030.conservative}–€{carbon2030.high}/t by 2030. Positive NPV = pays back over its life.
          </div>
        </>
      )}

      {p.value_uplift && p.value_uplift.priority_buildings > 0 && (
        <div
          style={{
            marginTop: 12,
            padding: "8px 12px",
            borderRadius: 6,
            fontSize: 11,
            border: "1px solid #bae6fd",
            backgroundColor: "#f0f9ff",
            color: "#075985",
          }}
        >
          <strong>Indicative value uplift: +{p.value_uplift.uplift_low_pct}–{p.value_uplift.uplift_high_pct}%</strong>{" "}
          for {p.value_uplift.priority_buildings} renovation-priority building(s) if improved ~
          {p.value_uplift.assumed_band_jump} EPC classes. {p.value_uplift.note}
        </div>
      )}

      <SectionTitle>Application Pack</SectionTitle>
      {summary.measures.length === 0 ? (
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
              <th style={thStyle("right")}>Grant (range)</th>
              <th style={thStyle("right")}>Payback</th>
              <th style={thStyle("right")}>NPV (base)</th>
            </tr>
          </thead>
          <tbody>
            {summary.measures.map((m, i) => (
              <tr key={i}>
                <td style={{ ...tdL, fontWeight: 600, color: INK }}>
                  {m.title}
                  <div style={{ fontSize: 10, color: MUTED, fontWeight: 400, marginTop: 2 }}>{m.subsidy_note}</div>
                </td>
                <td style={{ ...tdL, color: MUTED }}>{m.building_name}</td>
                <td style={tdL}>{m.program}</td>
                <td style={tdR}>
                  {m.rate_low_pct}{m.rate_high_pct > m.rate_low_pct ? `–${m.rate_high_pct}` : ""}%
                </td>
                <td style={{ ...tdR, fontWeight: 700, color: EMERALD }}>{eurRange(m.grant_low_eur, m.grant_high_eur)}</td>
                <td style={tdR}>{m.simple_payback_years != null ? `${m.simple_payback_years} yr` : "—"}</td>
                <td style={{ ...tdR, color: m.npv_base_eur != null && m.npv_base_eur < 0 ? "#b91c1c" : INK }}>
                  {m.npv_base_eur != null ? eur(m.npv_base_eur) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: 14, fontSize: 10, lineHeight: 1.5, color: FAINT }}>
        <strong>Method &amp; assumptions.</strong> {String(a.subsidy_note ?? "")} {String(a.carbon_note ?? "")}{" "}
        {String(a.value_uplift_note ?? "")} Residential subsidy caps apply per dwelling unit (estimated
        from floor area where not declared). Forward figures are scenario ranges, not forecasts; a
        financing-partner referral is not a lending offer.
      </div>
    </>
  )
}
