/**
 * AlertsReportDocument — body of the /alerts/report PDF (active anomalies).
 *
 * Presentational; plugs into <ReportFrame>. Triage summary cards (unhandled by
 * severity) + an anomalies table. Fed the unresolved scope by the route. Uses
 * the shared reportKit for palette, formatters, chips and cell styles.
 */
import type { AlertItem, AlertSeverityCounts } from "@/lib/api/alerts"

import {
  Chip,
  DANGER,
  FAINT,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  fmtDateTime,
  fmtNum,
  tdC,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: "#b91c1c",
  HIGH: "#c2410c",
  MEDIUM: "#b45309",
  LOW: "#0369a1",
}

function sevColor(s: string | null): string {
  return SEVERITY_COLOR[(s ?? "").toUpperCase()] ?? FAINT
}

function sevLabel(s: string | null): string {
  const u = (s ?? "").toUpperCase()
  if (u === "CRITICAL") return "Critical"
  if (u === "HIGH") return "High"
  if (u === "MEDIUM") return "Medium"
  if (u === "LOW") return "Low"
  return "—"
}

const ACK_META: Record<string, { label: string; color: string }> = {
  new: { label: "New", color: "#2563eb" },
  acknowledged: { label: "Acknowledged", color: GOOD },
  dismissed: { label: "Dismissed", color: "#64748b" },
}

function deviation(pct: number | null): { text: string; color: string } {
  if (pct === null) return { text: "", color: MUTED }
  const sign = pct > 0 ? "+" : ""
  return { text: `${sign}${pct.toFixed(0)}%`, color: pct > 0 ? DANGER : GOOD }
}

export function AlertsReportDocument({
  alerts,
  counts,
  error,
}: {
  alerts: AlertItem[]
  counts: AlertSeverityCounts | null
  error: string | null
}) {
  if (error) return <Notice error={error} label="alerts" />

  return (
    <>
      <SectionTitle>Triage Summary</SectionTitle>
      <div style={{ display: "flex", gap: 12 }}>
        <StatCard
          label="Unhandled Critical"
          value={counts?.unhandled_critical ?? 0}
          color={DANGER}
          hint="Needs attention now"
        />
        <StatCard
          label="Unhandled High"
          value={counts?.unhandled_high ?? 0}
          color="#c2410c"
          hint="Investigate soon"
        />
        <StatCard
          label="Open & Unhandled"
          value={counts?.unhandled_total ?? 0}
          hint="Active triage queue"
        />
        <StatCard
          label="Acknowledged"
          value={counts?.acknowledged ?? 0}
          color={GOOD}
          hint="Owned by a human"
        />
      </div>

      <SectionTitle>Active Anomalies</SectionTitle>
      {alerts.length === 0 ? (
        <div style={{ fontSize: 12, color: MUTED, padding: "12px 0" }}>
          No active anomalies to display.
        </div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
          <thead>
            <tr style={{ backgroundColor: "#f1f5f9" }}>
              <th style={thStyle("left")}>Building</th>
              <th style={thStyle("center")}>Severity</th>
              <th style={thStyle("left")}>Anomaly</th>
              <th style={thStyle("left")}>Detected</th>
              <th style={thStyle("right")}>Reading</th>
              <th style={thStyle("center")}>State</th>
              <th style={thStyle("center")}>Triage</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a, i) => {
              const dev = deviation(a.deviation_pct)
              const ack = ACK_META[a.ack_status] ?? ACK_META.new
              return (
                <tr key={a.anomaly_id ?? `row-${i}`}>
                  <td style={{ ...tdL, fontWeight: 600 }}>{a.building_name}</td>
                  <td style={tdC}>
                    <Chip label={sevLabel(a.severity)} color={sevColor(a.severity)} />
                  </td>
                  <td style={tdL}>
                    <div style={{ fontWeight: 600, color: INK }}>{a.anomaly_type ?? "—"}</div>
                    {a.description && (
                      <div style={{ fontSize: 10, color: MUTED, marginTop: 2 }}>
                        {a.description}
                      </div>
                    )}
                  </td>
                  <td style={{ ...tdL, color: MUTED, whiteSpace: "nowrap" }}>
                    {fmtDateTime(a.detected_at)}
                  </td>
                  <td style={tdR}>
                    {a.metric_value === null && a.threshold_value === null ? (
                      "—"
                    ) : (
                      <>
                        <span style={{ color: INK }}>{fmtNum(a.metric_value)}</span>
                        <span style={{ color: FAINT }}> vs {fmtNum(a.threshold_value)}</span>
                        {dev.text && (
                          <span style={{ color: dev.color, fontWeight: 600, marginLeft: 6 }}>
                            {dev.text}
                          </span>
                        )}
                      </>
                    )}
                  </td>
                  <td style={tdC}>
                    {a.is_resolved ? (
                      <Chip label="Resolved" color={GOOD} />
                    ) : (
                      <Chip label="Open" color="#b45309" />
                    )}
                  </td>
                  <td style={tdC}>
                    <Chip label={ack.label} color={ack.color} />
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
