/**
 * /compliance/esrs-report — ESRS E-1 (Climate Change) report PDF.
 *
 * Server component, force-dynamic, auth-guarded. Portfolio-wide by default; pass
 * ?building_id=<fabric id> to scope the whole report to a single building (the
 * backend /compliance/esrs honours it; portfolio buildings are filtered to match).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { EsrsE1ReportDocument } from "@/components/report/EsrsE1ReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { fetchEsrsNarrativeServer, narrativeMap } from "@/lib/api/esrsNarrative"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

export default async function EsrsE1ReportPage({
  searchParams,
}: {
  searchParams: Promise<{ building_id?: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0

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
      title="ESRS E-1 — Climate Change"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="ESRS-E1-aligned · reporting support (not audited)"
    >
      <EsrsE1ReportDocument
        esrs={esrs}
        esrsError={esrsError}
        buildings={buildings}
        buildingsError={buildingsError}
        narrative={narrative}
      />
    </ReportFrame>
  )
}
