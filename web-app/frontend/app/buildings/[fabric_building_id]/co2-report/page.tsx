/**
 * /buildings/[fabric_building_id]/co2-report — CO₂ cost-allocation PDF.
 *
 * Server component, force-dynamic, auth-guarded. Reads the per-building CO2KostAufG
 * split (GET /compliance/co2-cost/{id}) plus the building's recommendations (for the
 * decarbonisation path) and wraps Co2CostReportDocument in the shared ReportFrame.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { Co2CostReportDocument } from "@/components/report/Co2CostReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchActions } from "@/lib/api/actions"
import { fetchCo2CostAllocation } from "@/lib/api/co2cost"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

type PageProps = {
  params: Promise<{ fabric_building_id: string }>
}

export default async function Co2CostReportPage({ params }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { fabric_building_id } = await params
  const id = decodeURIComponent(fabric_building_id)

  const [result, actionsResult] = await Promise.all([
    fetchCo2CostAllocation(session.accessToken, id),
    fetchActions(session.accessToken, { building_id: id, limit: 50 }),
  ])
  const data = result.ok ? result.data : null
  const error = result.ok ? null : result.error
  const actions = actionsResult.ok ? actionsResult.data.actions : []

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
    ? `${data.building_name}${data.country_code ? ` · ${data.country_code}` : ""}`
    : id

  return (
    <ReportFrame
      backHref={`/buildings/${encodeURIComponent(id)}`}
      backLabel="Back to building"
      title="CO₂ Cost Allocation — CO2KostAufG"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter={
        data?.reporting_year != null ? `Reporting year ${data.reporting_year}` : undefined
      }
    >
      <Co2CostReportDocument data={data} error={error} actions={actions} />
    </ReportFrame>
  )
}
