/**
 * BuildingReportDocument — body of the /buildings/[id]/report PDF.
 *
 * A single-building client deliverable: an Overview block (headline 30-day
 * numbers + building meta) followed by that building's recommendations and
 * active alerts. The recommendations + alerts sections REUSE the existing
 * ActionsReportDocument / AlertsReportDocument (fed building-scoped data), so
 * the three reports stay visually consistent. Plugs into <ReportFrame>.
 */
import type { ActionItem, ActionStatusCounts } from "@/lib/api/actions"
import type { AlertItem, AlertSeverityCounts } from "@/lib/api/alerts"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import type { Insight, InsightSeverity } from "@/lib/insights/buildingAdvisor"

import { ActionsReportDocument } from "./ActionsReportDocument"
import { AlertsReportDocument } from "./AlertsReportDocument"
import {
  BAD,
  DANGER,
  FAINT,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  fmtCompact,
  fmtInt,
} from "./reportKit"

function euiColor(eui: number | null): string {
  if (eui === null || eui === 0) return MUTED
  if (eui <= 100) return GOOD
  if (eui <= 200) return BAD
  return DANGER
}

function sevColor(s: InsightSeverity): string {
  if (s === "action") return DANGER
  if (s === "watch") return BAD
  if (s === "good") return GOOD
  return MUTED
}

type Props = {
  building: PortfolioBuildingRow | null
  buildingError: string | null
  insights: Insight[]
  actions: ActionItem[]
  actionsCounts: ActionStatusCounts | null
  actionsError: string | null
  alerts: AlertItem[]
  alertsCounts: AlertSeverityCounts | null
  alertsError: string | null
}

export function BuildingReportDocument({
  building,
  buildingError,
  insights,
  actions,
  actionsCounts,
  actionsError,
  alerts,
  alertsCounts,
  alertsError,
}: Props) {
  if (buildingError) return <Notice error={buildingError} label="building" />
  if (!building) {
    return (
      <div style={{ fontSize: 12, color: MUTED, padding: "12px 0" }}>
        Building not found or not accessible.
      </div>
    )
  }

  const caps = [
    building.has_pv ? "Solar" : null,
    building.has_battery ? "Battery" : null,
    building.has_iot ? "IoT" : null,
  ].filter(Boolean)

  const meta = [
    building.building_type.replace(/_/g, " "),
    `${fmtInt(building.floor_area_m2)} m²`,
    building.epc_class ? `EPC ${building.epc_class}` : null,
    caps.length ? caps.join(" · ") : null,
  ]
    .filter(Boolean)
    .join("   ·   ")

  return (
    <>
      <SectionTitle>Overview</SectionTitle>
      <div style={{ fontSize: 12, color: MUTED, marginBottom: 10, textTransform: "capitalize" }}>
        {meta}
      </div>
      <div style={{ display: "flex", gap: 12 }}>
        <StatCard
          label="Energy 30d"
          value={`${fmtCompact(building.kwh_30d)} kWh`}
          hint="Total consumption"
        />
        <StatCard
          label="Cost 30d"
          value={`€${fmtCompact(building.cost_30d_eur)}`}
          hint="Energy spend"
        />
        <StatCard
          label="CO₂ 30d"
          value={`${fmtCompact(building.co2_30d_kg)} kg`}
          hint="Emissions"
        />
        <StatCard
          label="EUI"
          value={
            building.eui_kwh_m2_yr === null ? "—" : fmtCompact(building.eui_kwh_m2_yr, 0)
          }
          color={euiColor(building.eui_kwh_m2_yr)}
          hint="kWh/m²·yr"
        />
      </div>

      {insights.length > 0 && (
        <>
          <SectionTitle>Advisor Highlights</SectionTitle>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {insights.map((ins) => (
              <div key={ins.id} style={{ borderLeft: `3px solid ${sevColor(ins.severity)}`, paddingLeft: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: INK }}>{ins.title}</span>
                  {ins.metric && (
                    <span style={{ fontSize: 10, color: MUTED, whiteSpace: "nowrap" }}>{ins.metric}</span>
                  )}
                </div>
                <div style={{ fontSize: 11, color: MUTED, marginTop: 2 }}>{ins.detail}</div>
                {ins.range && (
                  <div style={{ fontSize: 11, fontWeight: 600, color: GOOD, marginTop: 2 }}>{ins.range}</div>
                )}
                {ins.recommendation && (
                  <div style={{ fontSize: 11, color: INK, marginTop: 2 }}>
                    <span style={{ fontWeight: 700, color: GOOD }}>→ </span>
                    {ins.recommendation}
                  </div>
                )}
                {ins.assumption && (
                  <div style={{ fontSize: 9, color: FAINT, marginTop: 2 }}>{ins.assumption}</div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      <ActionsReportDocument
        actions={actions}
        counts={actionsCounts}
        error={actionsError}
      />

      <AlertsReportDocument alerts={alerts} counts={alertsCounts} error={alertsError} />
    </>
  )
}
