/**
 * /compliance/enefg-report — EnEfG energy-audit / implementation-plan PDF.
 *
 * Reuses the ESRS energy total (scope check) + actions (the economic measures).
 * Portfolio-wide by default; pass ?building_id to scope to a single building.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { EnefgReportDocument } from "@/components/report/EnefgReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchActions } from "@/lib/api/actions"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

export default async function EnefgReportPage({
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

  const [esrsResult, actionsResult] = await Promise.all([
    fetchEsrsReport(session.accessToken, scoped ? building_id : undefined),
    fetchActions(session.accessToken, {
      limit: 500,
      building_id: scoped ? building_id : undefined,
    }),
  ])

  const esrs = esrsResult.ok ? esrsResult.data : null
  const esrsError = esrsResult.ok ? null : esrsResult.error
  const actions = actionsResult.ok ? actionsResult.data.actions : []
  const actionsError = actionsResult.ok ? null : actionsResult.error

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
      title="EnEfG — Energy Audit & Implementation Plan"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="EnEfG §8 / §9 — reporting support"
    >
      <EnefgReportDocument
        esrs={esrs}
        esrsError={esrsError}
        actions={actions}
        actionsError={actionsError}
      />
    </ReportFrame>
  )
}
