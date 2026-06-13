/**
 * CrremReportDocument — body of the CRREM-aligned stranding report PDF.
 *
 * Per-asset transition-risk assessment: each building's annualised operational
 * carbon intensity (kgCO₂/m²·yr) is compared against a declining 1.5°C
 * decarbonisation pathway; the first year a held-flat intensity exceeds the
 * pathway is the "stranding year". Reuses lib/crrem (summarizeStranding +
 * pathwayValue) over the portfolio rows — no new data fetch.
 *
 * IMPORTANT honesty framing: the pathways are INDICATIVE, 1.5°C-aligned anchors,
 * NOT the official licensed CRREM dataset (embedding that needs a CRREM License
 * Partner agreement). Held-flat intensity is a conservative screening assumption.
 * Body-only; plugs into <ReportFrame>.
 */
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import {
  PATHWAY_END_YEAR,
  PATHWAY_START_YEAR,
  pathwayValue,
  summarizeStranding,
  type StrandingResult,
  type StrandingStatus,
} from "@/lib/crrem"

import {
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
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

const AMBER = "#b45309"

function num(v: number | null, d = 1): string {
  if (v === null || v === undefined) return "—"
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: d }).format(v)
}

function statusLabel(s: StrandingStatus, year: number | null): string {
  switch (s) {
    case "stranded_now":
      return "Stranded now"
    case "stranding":
      return year ? `Stranding ${year}` : "Stranding"
    case "on_track":
      return "On track"
    default:
      return "No data"
  }
}

function statusColor(s: StrandingStatus): string {
  switch (s) {
    case "stranded_now":
      return BAD
    case "stranding":
      return AMBER
    case "on_track":
      return GOOD
    default:
      return MUTED
  }
}

/** Worst first: stranded now, then earliest stranding year, then on-track, then unknown. */
function severity(r: StrandingResult): number {
  if (r.status === "stranded_now") return 0
  if (r.status === "stranding") return 1
  if (r.status === "on_track") return 3
  return 4
}

export function CrremReportDocument({
  buildings,
  buildingsError,
}: {
  buildings: PortfolioBuildingRow[]
  buildingsError: string | null
}) {
  if (buildingsError) {
    return <Notice error={buildingsError} label="CRREM stranding" />
  }

  const summary = summarizeStranding(buildings)
  const thisYear = new Date().getUTCFullYear()
  const rows = [...summary.results].sort(
    (a, b) =>
      severity(a) - severity(b) ||
      (a.strandingYear ?? 9999) - (b.strandingYear ?? 9999) ||
      (b.intensity ?? 0) - (a.intensity ?? 0)
  )

  return (
    <div>
      <div style={{ marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="CRREM-aligned stranding" color={EMERALD} />
        <Chip label="Indicative 1.5°C pathways — not the licensed CRREM dataset" color={AMBER} />
      </div>

      <div style={{ fontSize: 11, color: MUTED, lineHeight: 1.5, marginBottom: 4 }}>
        Transition-risk screening using the CRREM <strong>method</strong>: a building&apos;s
        annual operational carbon intensity is compared against a declining 1.5°C
        decarbonisation pathway, and the first year the (held-flat) intensity exceeds the
        pathway is its <strong>stranding year</strong>. The pathways here are indicative,
        1.5°C-aligned anchors by asset type — <strong>not</strong> the official licensed
        CRREM curves (which require a CRREM License Partner agreement) and not country-grid
        specific. Decision-support, not an assured disclosure.
      </div>

      <SectionTitle>Portfolio stranding summary</SectionTitle>
      {summary.assessed === 0 ? (
        <div style={{ fontSize: 12, color: MUTED }}>
          No building has enough recent carbon + area data to assess yet.
        </div>
      ) : (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <StatCard label="Assessed" value={`${summary.assessed}/${buildings.length}`} hint="buildings with data" />
          <StatCard label="Stranded now" value={`${summary.strandedNow}`} color={BAD} hint="above today's pathway" />
          <StatCard label="Stranding by 2030" value={`${summary.strandedBy2030}`} color={AMBER} hint="cumulative" />
          <StatCard label="Stranding by 2035" value={`${summary.strandedBy2035}`} color={AMBER} hint="cumulative" />
          <StatCard
            label="Avg stranding year"
            value={summary.avgStrandingYear ? `${summary.avgStrandingYear}` : "—"}
            hint="of stranded assets"
          />
        </div>
      )}

      <SectionTitle>Per-asset assessment</SectionTitle>
      {summary.assessed === 0 ? (
        <div style={{ fontSize: 12, color: MUTED }}>
          Connect recent energy + emissions data to populate the asset table.
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ backgroundColor: "#f1f5f9" }}>
              <th style={thStyle("left")}>Building</th>
              <th style={thStyle("right")}>Intensity</th>
              <th style={thStyle("right")}>Pathway {thisYear}</th>
              <th style={thStyle("right")}>Stranding year</th>
              <th style={thStyle("left")}>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const pathwayNow = pathwayValue(r.building.building_type, thisYear)
              return (
                <tr key={r.building.fabric_building_id}>
                  <td style={{ ...tdL, fontWeight: 600 }}>
                    {r.building.name}
                    <div style={{ fontSize: 9, color: FAINT, textTransform: "uppercase" }}>
                      {r.building.building_type.replace(/_/g, " ")}
                    </div>
                  </td>
                  <td style={tdR}>{r.intensity != null ? `${num(r.intensity)}` : "—"}</td>
                  <td style={{ ...tdR, color: MUTED }}>{num(pathwayNow)}</td>
                  <td style={tdR}>{r.strandingYear ?? "—"}</td>
                  <td style={{ ...tdL, color: statusColor(r.status), fontWeight: 600 }}>
                    {statusLabel(r.status, r.strandingYear)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      <div style={{ fontSize: 10, color: FAINT, marginTop: 6 }}>
        Intensity and pathway are in kgCO₂/m²·yr. Intensity is annualised from the latest
        ~30 days of operational emissions and held flat — a conservative screening view that
        does not credit planned decarbonisation. Improving efficiency or electrifying heat
        (see the recommendations) pushes the stranding year out.
      </div>

      <SectionTitle>Method &amp; assumptions</SectionTitle>
      <div style={{ fontSize: 11, color: INK, lineHeight: 1.6 }}>
        Pathways are linearly interpolated between indicative {PATHWAY_START_YEAR} and{" "}
        {PATHWAY_END_YEAR} anchors per asset type (1.5°C-aligned). A building is{" "}
        <strong>stranded now</strong> if its intensity already exceeds the{" "}
        {PATHWAY_START_YEAR} pathway, <strong>on track</strong> if it stays at or below the{" "}
        {PATHWAY_END_YEAR} endpoint, otherwise <strong>stranding</strong> in the first year
        the pathway falls below it. Swapping in the licensed CRREM curves (per type and
        country grid) is a single-module change once a License Partner agreement is in place.
      </div>

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Prepared using the CRREM methodology with indicative 1.5°C pathways. This is
        reporting support / transition-risk screening — it is not the official CRREM tool
        output, not audited or assured, and not investment advice. Confirm against the
        licensed CRREM dataset before external use.
      </div>
    </div>
  )
}
