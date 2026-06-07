/**
 * /alerts/report — print-optimised active-anomalies report (Download as PDF).
 *
 * Server component, force-dynamic, auth-guarded. Reuses fetchAlerts at the
 * unresolved (active) scope — no new backend, no Fabric change. Wraps
 * AlertsReportDocument in the shared ReportFrame.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AlertsReportDocument } from "@/components/report/AlertsReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { authOptions } from "@/lib/auth/options"
import { fetchAlerts } from "@/lib/api/alerts"

export const dynamic = "force-dynamic"

export default async function AlertsReportPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchAlerts(session.accessToken, {
    limit: 500,
    resolution: "unresolved",
  })

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const counts = result.ok ? result.data.severity_counts : null
  const unresolved = counts?.unresolved_total ?? 0

  return (
    <ReportFrame
      backHref="/alerts"
      backLabel="Back to alerts"
      title="Active Alerts Report"
      generatedAt={generatedAt}
      metaLine={
        result.ok
          ? `${unresolved} unresolved ${unresolved === 1 ? "anomaly" : "anomalies"}`
          : undefined
      }
      footerCenter="Unresolved anomalies"
    >
      <AlertsReportDocument
        alerts={result.ok ? result.data.alerts : []}
        counts={counts}
        error={result.ok ? null : result.error}
      />
    </ReportFrame>
  )
}
