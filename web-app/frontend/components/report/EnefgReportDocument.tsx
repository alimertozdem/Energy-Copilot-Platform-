/**
 * EnefgReportDocument — body of the EnEfG energy-audit / implementation-plan report.
 *
 * German Energieeffizienzgesetz (EnEfG): companies above the energy-consumption
 * thresholds must run an energy audit (DIN EN 16247) or an EnMS, and PUBLISH an
 * externally-reviewed implementation plan (Umsetzungsplan) of the ECONOMIC saving
 * measures. This report does the scope check (total energy vs thresholds) and lists the
 * economic measures from the recommendations engine as the basis for that plan.
 *
 * Portfolio-grain (EnEfG is company-level). Reuses the ESRS energy total + the actions
 * (recommendations). A measure is treated as "economic" when its NPV is positive (proxy
 * for the EnEfG test: net present value positive within 50% of the useful life). The
 * full DIN EN 16247 audit + the per-measure end-energy (kWh) quantification need a
 * qualified auditor — this is reporting support, not the audit itself.
 */
import type { ActionItem } from "@/lib/api/actions"
import type { EsrsReport } from "@/lib/api/esrs"

import {
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

// EnEfG / EDL-G thresholds (2026 Novelle; GWh of total final energy per year).
const GWH_UMSETZUNGSPLAN = 2.5 // §9 implementation-plan publication duty
const GWH_AUDIT = 2.77 // §8 / EDL-G energy audit (DIN EN 16247) unless certified EnMS
const GWH_ENMS = 23.6 // EnMS (ISO 50001) / EMAS duty

const eur = (v: number | null): string => (v === null ? "—" : "€" + fmtInt(v))

function dutyChip(active: boolean): { text: string; color: string } {
  return active ? { text: "Required", color: DANGER } : { text: "Not required", color: GOOD }
}

export function EnefgReportDocument({
  esrs,
  esrsError,
  actions,
  actionsError,
}: {
  esrs: EsrsReport | null
  esrsError: string | null
  actions: ActionItem[]
  actionsError: string | null
}) {
  if (esrsError && actionsError) {
    return <Notice error={esrsError} label="EnEfG data" />
  }

  const totalMwh = esrs?.energy_total_mwh ?? null
  const gwh = totalMwh != null ? totalMwh / 1000 : null
  const inUmsetzung = gwh != null && gwh >= GWH_UMSETZUNGSPLAN
  const inAudit = gwh != null && gwh >= GWH_AUDIT
  const inEnMS = gwh != null && gwh >= GWH_ENMS

  // Economic measures (NPV-positive) = the implementation-plan content.
  const economic = actions
    .filter((a) => a.npv_eur != null && a.npv_eur > 0)
    .sort((a, b) => (b.npv_eur ?? 0) - (a.npv_eur ?? 0))
  const nonEconomic = actions.filter((a) => a.npv_eur != null && a.npv_eur <= 0)

  const totalSaving = economic.reduce((s, a) => s + (a.annual_saving_eur ?? 0), 0)
  const totalCapex = economic.reduce((s, a) => s + (a.net_capex_eur ?? a.capex_eur ?? 0), 0)
  const totalCo2 = economic.reduce((s, a) => s + (a.co2_saving_kg ?? 0), 0)

  return (
    <div>
      <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="EnEfG — Energieeffizienzgesetz" color={EMERALD} />
        <Chip label="Audit support + Umsetzungsplan" color={MUTED} />
        {esrs?.reporting_year != null && <Chip label={`Year ${esrs.reporting_year}`} color={INK} />}
      </div>

      {/* Scope check */}
      <SectionTitle>Scope — total final energy vs EnEfG thresholds</SectionTitle>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Total energy"
          value={gwh != null ? `${gwh.toFixed(2)} GWh` : "—"}
          hint="portfolio final energy / yr"
        />
        <StatCard label="Implementation plan (§9)" value={dutyChip(inUmsetzung).text} color={dutyChip(inUmsetzung).color} hint="> 2.5 GWh" />
        <StatCard label="Energy audit (§8)" value={dutyChip(inAudit).text} color={dutyChip(inAudit).color} hint="> 2.77 GWh — DIN EN 16247" />
        <StatCard label="EnMS / ISO 50001" value={dutyChip(inEnMS).text} color={dutyChip(inEnMS).color} hint="> 23.6 GWh" />
      </div>
      {esrsError && (
        <div style={{ marginTop: 6 }}>
          <Notice error={esrsError} label="energy total" />
        </div>
      )}
      <div style={{ marginTop: 8, fontSize: 11, color: INK, lineHeight: 1.6 }}>
        {gwh == null ? (
          "Connect portfolio energy to determine EnEfG scope."
        ) : inEnMS ? (
          <>This portfolio exceeds <strong>23.6 GWh/yr</strong> — an energy- or environmental-management system (ISO 50001 / EMAS) <strong>and</strong> a published implementation plan are required.</>
        ) : inAudit ? (
          <>This portfolio exceeds <strong>2.77 GWh/yr</strong> — a certified energy audit (DIN EN 16247) every four years <strong>and</strong> a published implementation plan of the economic measures are required.</>
        ) : inUmsetzung ? (
          <>This portfolio exceeds <strong>2.5 GWh/yr</strong> — a published, externally-reviewed implementation plan of the economic measures is required.</>
        ) : (
          <>This portfolio is below <strong>2.5 GWh/yr</strong>, so the EnEfG audit / plan duties do not currently apply. The measures below are still a voluntary efficiency roadmap.</>
        )}
      </div>
      <div style={{ marginTop: 4, fontSize: 10.5, color: MUTED, lineHeight: 1.5 }}>
        EnEfG enforcement is by BAFA (a nationwide control wave began March 2026). The first
        audit under the new rules is due by ~11 Oct 2026; the implementation plan must be
        published within three months of the audit / certification and is externally reviewed.
      </div>

      {/* Umsetzungsplan — economic measures */}
      <SectionTitle>Implementation plan (Umsetzungsplan) — economic measures</SectionTitle>
      {actionsError ? (
        <Notice error={actionsError} label="measures" />
      ) : economic.length === 0 ? (
        <div style={{ fontSize: 12, color: MUTED }}>
          No NPV-positive measures on record yet. Run the recommendations engine to populate
          the plan.
        </div>
      ) : (
        <>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 8 }}>
            <StatCard label="Economic measures" value={economic.length} hint="NPV-positive" />
            <StatCard label="Annual saving" value={eur(totalSaving)} color={GOOD} hint="€/yr (sum)" />
            <StatCard label="Investment" value={eur(totalCapex)} hint="net capex (sum)" />
            <StatCard label="CO₂ saving" value={`${fmtInt(totalCo2 / 1000)} t`} color={GOOD} hint="tCO₂e/yr (sum)" />
          </div>
          <div style={{ fontSize: 10, color: MUTED, marginBottom: 8 }}>
            Figures sum independent per-measure estimates; overlapping measures are
            capped to a realistic share of actual energy cost and emissions, so totals
            are indicative, not strictly additive.
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
            <thead>
              <tr style={{ backgroundColor: "#f1f5f9" }}>
                <th style={thStyle("left")}>Measure</th>
                <th style={thStyle("left")}>Building</th>
                <th style={thStyle("right")}>Saving €/yr</th>
                <th style={thStyle("right")}>CO₂ t/yr</th>
                <th style={thStyle("right")}>Net capex</th>
                <th style={thStyle("right")}>Payback</th>
                <th style={thStyle("right")}>NPV</th>
              </tr>
            </thead>
            <tbody>
              {economic.map((a) => (
                <tr key={a.action_id}>
                  <td style={{ ...tdL, fontWeight: 600 }}>
                    {a.title || a.action_type || "—"}
                    {a.compliance_driver && (
                      <div style={{ fontSize: 9, color: FAINT }}>{a.compliance_driver}</div>
                    )}
                  </td>
                  <td style={tdL}>{a.building_name}</td>
                  <td style={tdR}>{eur(a.annual_saving_eur)}</td>
                  <td style={tdR}>{a.co2_saving_kg != null ? fmtInt(a.co2_saving_kg / 1000) : "—"}</td>
                  <td style={tdR}>{eur(a.net_capex_eur ?? a.capex_eur)}</td>
                  <td style={tdR}>{a.payback_years != null ? `${a.payback_years.toFixed(1)} yr` : "—"}</td>
                  <td style={{ ...tdR, color: (a.npv_eur ?? 0) > 0 ? GOOD : BAD, fontWeight: 600 }}>{eur(a.npv_eur)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {nonEconomic.length > 0 && (
        <div style={{ marginTop: 8, fontSize: 10.5, color: MUTED, lineHeight: 1.5 }}>
          {nonEconomic.length} further measure{nonEconomic.length === 1 ? "" : "s"} were assessed
          but are not currently economic (NPV ≤ 0) and are therefore excluded from the plan.
          BAFA sample-checks the non-economic exclusions, so retain the assessment.
        </div>
      )}

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        EnEfG §8/§9 support. A measure is treated as economic when its net present value is
        positive (proxy for the legal test: NPV positive within 50% of the useful life). The
        per-measure end-energy (kWh) saving and the formal audit are part of a DIN EN 16247
        audit by a qualified auditor; this document is the measure basis + economics, not the
        completed audit, and is not legal advice.
      </div>
    </div>
  )
}
