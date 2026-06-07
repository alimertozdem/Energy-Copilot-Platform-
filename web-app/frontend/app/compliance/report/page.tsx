/**
 * /compliance/report — print-optimised compliance & sustainability report.
 *
 * Server component, force-dynamic, auth-guarded. Reuses the /compliance fetchers
 * (portfolio buildings + ESRS endpoint) and wraps ComplianceReportDocument in
 * the shared ReportFrame (print stylesheet + branded header/footer + PrintButton).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { ComplianceReportDocument } from "@/components/report/ComplianceReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

export default async function ComplianceReportPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const [buildingsResult, esrsResult] = await Promise.all([
    fetchPortfolioBuildings(session.accessToken),
    fetchEsrsReport(session.accessToken),
  ])

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const buildings = buildingsResult.ok ? buildingsResult.data.buildings : []
  const esrs = esrsResult.ok ? esrsResult.data : null

  const metaLine = `${buildings.length} ${buildings.length === 1 ? "building" : "buildings"}${
    esrs?.reporting_year ? ` · GHG ${esrs.reporting_year}` : ""
  }`

  return (
    <ReportFrame
      backHref="/compliance"
      backLabel="Back to compliance"
      title="Compliance & Sustainability Report"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="EPBD/MEPS · CRREM · ESRS-E1 — indicative"
    >
      <ComplianceReportDocument
        buildings={buildings}
        buildingsError={buildingsResult.ok ? null : buildingsResult.error}
        esrs={esrs}
        esrsError={esrsResult.ok ? null : esrsResult.error}
      />
    </ReportFrame>
  )
}
