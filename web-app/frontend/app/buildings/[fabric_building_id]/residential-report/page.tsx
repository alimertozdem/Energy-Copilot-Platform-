/**
 * /buildings/[fabric_building_id]/residential-report — residential building summary PDF.
 *
 * Server component, force-dynamic, auth-guarded. The residential counterpart of the
 * commercial /report summary: per-unit energy + EPC mix + HKVO/UVI coverage, from the
 * manager residential endpoint. Wraps ResidentialSummaryReportDocument in ReportFrame.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { ResidentialSummaryReportDocument } from "@/components/report/ResidentialSummaryReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchBuilding } from "@/lib/api/buildings"
import { fetchBuildingResidential } from "@/lib/api/residentialManager"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

export default async function ResidentialSummaryReportPage({
  params,
}: {
  params: Promise<{ fabric_building_id: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }
  const { fabric_building_id } = await params

  const [buildingResult, residentialResult] = await Promise.all([
    fetchBuilding(session.accessToken, fabric_building_id),
    fetchBuildingResidential(session.accessToken, fabric_building_id),
  ])

  const buildingName = buildingResult.ok ? buildingResult.data.name : fabric_building_id
  const data = residentialResult.ok ? residentialResult.data : null
  const error = residentialResult.ok ? null : residentialResult.error

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const metaLine = data
    ? `${buildingName} · ${data.units.length} ${data.units.length === 1 ? "unit" : "units"}`
    : buildingName

  return (
    <ReportFrame
      backHref={`/buildings/${encodeURIComponent(fabric_building_id)}`}
      backLabel="Back to building"
      title="Residential summary"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="Residential metering summary · reporting support (not audited)"
    >
      <ResidentialSummaryReportDocument
        data={data}
        error={error}
        buildingName={buildingName}
      />
    </ReportFrame>
  )
}
