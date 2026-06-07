/**
 * /portfolio/report — print-optimised portfolio report (Download as PDF).
 *
 * Server component, force-dynamic, auth-guarded. Reuses the portfolio fetchers
 * (no new backend, no Fabric change) and wraps PortfolioReportDocument in the
 * shared ReportFrame (print stylesheet + branded header/footer + PrintButton).
 *
 * Why a separate route (not @media print on /portfolio): the interactive page
 * is dark navy + AppChrome + motifs + embeds, a poor fit for paper.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { PortfolioReportDocument } from "@/components/report/PortfolioReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { authOptions } from "@/lib/auth/options"
import {
  fetchPortfolioBuildings,
  fetchPortfolioKPIs,
} from "@/lib/api/portfolio"

export const dynamic = "force-dynamic"

export default async function PortfolioReportPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const [kpisResult, buildingsResult] = await Promise.all([
    fetchPortfolioKPIs(session.accessToken),
    fetchPortfolioBuildings(session.accessToken),
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

  const kpis = kpisResult.ok ? kpisResult.data : null
  const buildings = buildingsResult.ok ? buildingsResult.data.buildings : []

  const metaLine = kpis
    ? `${buildings.length} ${buildings.length === 1 ? "building" : "buildings"} · ${kpis.period.days}-day window`
    : undefined
  const footerCenter = kpis
    ? `Period ${kpis.period.start_date} – ${kpis.period.end_date} (${kpis.period.days} days)`
    : ""

  return (
    <ReportFrame
      backHref="/portfolio"
      backLabel="Back to portfolio"
      title="Portfolio Energy Report"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter={footerCenter}
    >
      <PortfolioReportDocument
        kpis={kpis}
        kpisError={kpisResult.ok ? null : kpisResult.error}
        buildings={buildings}
        buildingsError={buildingsResult.ok ? null : buildingsResult.error}
      />
    </ReportFrame>
  )
}
