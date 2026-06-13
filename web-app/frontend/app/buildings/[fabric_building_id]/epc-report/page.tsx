/**
 * /buildings/[fabric_building_id]/epc-report — Energieausweis pre-assessment PDF.
 *
 * Server component, force-dynamic, auth-guarded. Reuses the portfolio buildings fetch to
 * find this building's row (EPC class + EUI) and wraps EpcReportDocument in the shared
 * ReportFrame. A pre-assessment / rating estimate — NOT the legal certificate. No new backend.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { EpcReportDocument } from "@/components/report/EpcReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

type PageProps = {
  params: Promise<{ fabric_building_id: string }>
}

export default async function EpcReportPage({ params }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { fabric_building_id } = await params
  const id = decodeURIComponent(fabric_building_id)

  const result = await fetchPortfolioBuildings(session.accessToken)
  const building = result.ok
    ? result.data.buildings.find((b) => b.fabric_building_id === id) ?? null
    : null
  const error = result.ok ? null : result.error

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const metaLine = building
    ? `${building.name} · ${building.city}, ${building.country}`
    : id

  return (
    <ReportFrame
      backHref={`/buildings/${encodeURIComponent(id)}`}
      backLabel="Back to building"
      title="Energieausweis — Pre-assessment (EPC)"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="Energy rating estimate — not the legal certificate"
    >
      <EpcReportDocument building={building} error={error} />
    </ReportFrame>
  )
}
