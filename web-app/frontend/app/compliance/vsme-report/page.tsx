/**
 * /compliance/vsme-report — VSME (Voluntary SME standard) Basic Module report PDF.
 *
 * Portfolio-wide by default; pass ?building_id to scope B3 (energy & GHG) to a single
 * building. The narrative disclosures are company-level regardless.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { VsmeReportDocument } from "@/components/report/VsmeReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { fetchEsrsNarrativeServer, narrativeMap } from "@/lib/api/esrsNarrative"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

export default async function VsmeReportPage({
  searchParams,
}: {
  searchParams: Promise<{ building_id?: string; level?: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id, level } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0
  const comprehensive = level === "comprehensive"

  const [esrsResult, buildingsResult, narrativeResult] = await Promise.all([
    fetchEsrsReport(session.accessToken, scoped ? building_id : undefined),
    fetchPortfolioBuildings(session.accessToken),
    fetchEsrsNarrativeServer(session.accessToken),
  ])

  const esrs = esrsResult.ok ? esrsResult.data : null
  const esrsError = esrsResult.ok ? null : esrsResult.error
  const buildingsAll = buildingsResult.ok ? buildingsResult.data.buildings : []
  const buildings = scoped
    ? buildingsAll.filter((b) => b.fabric_building_id === building_id)
    : buildingsAll
  const buildingsError = buildingsResult.ok ? null : buildingsResult.error
  const narrative = narrativeResult.ok ? narrativeMap(narrativeResult.data.items) : {}

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const scopedName = scoped ? esrs?.rows?.[0]?.name ?? building_id : null
  const metaLine = scoped
    ? `${scopedName} · single building${esrs?.reporting_year ? ` · ${esrs.reporting_year}` : ""}`
    : esrs
    ? `${esrs.buildings_total} ${esrs.buildings_total === 1 ? "building" : "buildings"}${
        esrs.reporting_year ? ` · ${esrs.reporting_year}` : ""
      }`
    : undefined

  return (
    <ReportFrame
      backHref="/compliance"
      backLabel="Back to compliance"
      title={comprehensive ? "VSME — Basic + Comprehensive" : "VSME — Basic Module"}
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="VSME Basic Module · reporting support (not audited)"
    >
      <VsmeReportDocument
        esrs={esrs}
        esrsError={esrsError}
        buildings={buildings}
        buildingsError={buildingsError}
        narrative={narrative}
        comprehensive={comprehensive}
      />
    </ReportFrame>
  )
}
