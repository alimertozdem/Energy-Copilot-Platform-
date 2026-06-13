/**
 * /compliance/crrem-report — CRREM-aligned stranding report PDF.
 *
 * Reuses the portfolio buildings + lib/crrem stranding method. Portfolio-wide by
 * default; pass ?building_id to scope the assessment to a single visible building.
 * Transition-risk screening with INDICATIVE 1.5°C pathways (not the licensed dataset).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { CrremReportDocument } from "@/components/report/CrremReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

export default async function CrremReportPage({
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

  const buildingsResult = await fetchPortfolioBuildings(session.accessToken)
  const buildingsAll = buildingsResult.ok ? buildingsResult.data.buildings : []
  const buildings = scoped
    ? buildingsAll.filter((b) => b.fabric_building_id === building_id)
    : buildingsAll
  const buildingsError = buildingsResult.ok ? null : buildingsResult.error

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const scopedName = scoped ? buildings[0]?.name ?? building_id : null
  const metaLine = buildingsError
    ? undefined
    : scoped
    ? `${scopedName} · single building`
    : `${buildings.length} ${buildings.length === 1 ? "building" : "buildings"}`

  return (
    <ReportFrame
      backHref="/compliance"
      backLabel="Back to compliance"
      title="CRREM — Stranding assessment"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="CRREM-aligned (indicative pathways) · reporting support (not audited)"
    >
      <CrremReportDocument buildings={buildings} buildingsError={buildingsError} />
    </ReportFrame>
  )
}
