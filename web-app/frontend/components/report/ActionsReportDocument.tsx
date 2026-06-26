/**
 * ActionsReportDocument — body of the /actions/report PDF (recommendations).
 *
 * Presentational; plugs into <ReportFrame>. Status summary cards + a
 * recommendations table (savings / capex / payback / status). Uses the shared
 * reportKit for palette, formatters, chips and cell styles.
 */
import type {
  ActionItem,
  ActionStatus,
  ActionStatusCounts,
} from "@/lib/api/actions"

import {
  BAD,
  Chip,
  FAINT,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  fmtCompact,
  fmtMoney,
  tdC,
  tdL,
  tdR,
  thStyle,
  fmtPayback,
} from "./reportKit"

const STATUS_META: Record<ActionStatus, { label: string; color: string }> = {
  open: { label: "Open", color: "#2563eb" },
  in_progress: { label: "In Progress", color: BAD },
  completed: { label: "Completed", color: GOOD },
  dismissed: { label: "Dismissed", color: "#64748b" },
  not_applicable: { label: "N/A", color: FAINT },
}

function payback(yrs: number | null): string {
  // Delegated to the shared guard (null / negative / >= MAX_PLAUSIBLE_PAYBACK_YEARS -> "—").
  return fmtPayback(yrs)
}

export function ActionsReportDocument({
  actions,
  counts,
  error,
}: {
  actions: ActionItem[]
  counts: ActionStatusCounts | null
  error: string | null
}) {
  if (error) return <Notice error={error} label="recommendations" />

  return (
    <>
      <SectionTitle>Status Summary</SectionTitle>
      <div style={{ display: "flex", gap: 12 }}>
        <StatCard label="Open" value={counts?.open ?? 0} color="#2563eb" hint="Awaiting action" />
        <StatCard label="In Progress" value={counts?.in_progress ?? 0} color={BAD} hint="Underway" />
        <StatCard label="Completed" value={counts?.completed ?? 0} color={GOOD} hint="Done" />
        <StatCard
          label="Total"
          value={counts?.total ?? actions.length}
          hint="All recommendations"
        />
      </div>

      <SectionTitle>Recommendations</SectionTitle>
      {actions.length === 0 ? (
        <div style={{ fontSize: 12, color: MUTED, padding: "12px 0" }}>
          No recommendations to display.
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ backgroundColor: "#f1f5f9" }}>
              <th style={thStyle("left")}>Building</th>
              <th style={thStyle("left")}>Recommendation</th>
              <th style={thStyle("left")}>Priority</th>
              <th style={thStyle("right")}>Annual Saving</th>
              <th style={thStyle("right")}>CO₂ Saving</th>
              <th style={thStyle("right")}>CapEx</th>
              <th style={thStyle("right")}>Payback</th>
              <th style={thStyle("center")}>Status</th>
            </tr>
          </thead>
          <tbody>
            {actions.map((a) => {
              const meta = STATUS_META[a.status] ?? STATUS_META.open
              const sub = [a.action_type, a.compliance_driver].filter(Boolean).join(" · ")
              return (
                <tr key={a.action_id}>
                  <td style={{ ...tdL, fontWeight: 600 }}>{a.building_name}</td>
                  <td style={tdL}>
                    <div style={{ fontWeight: 600, color: INK }}>
                      {a.title ?? a.action_type ?? "—"}
                    </div>
                    {sub && <div style={{ fontSize: 10, color: MUTED, marginTop: 2 }}>{sub}</div>}
                  </td>
                  <td style={{ ...tdL, color: MUTED }}>{a.priority_label ?? "—"}</td>
                  <td style={tdR}>{fmtMoney(a.annual_saving_eur)}</td>
                  <td style={tdR}>
                    {a.co2_saving_kg === null ? "—" : `${fmtCompact(a.co2_saving_kg)} kg`}
                  </td>
                  <td style={tdR}>{fmtMoney(a.capex_eur)}</td>
                  <td style={tdR}>{payback(a.payback_years)}</td>
                  <td style={tdC}>
                    <Chip label={meta.label} color={meta.color} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </>
  )
}
