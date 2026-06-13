/**
 * /compliance/ghg-report — GHG Inventory (GHG Protocol) PDF.
 *
 * Reuses the ESRS endpoint (Scope 1/2/3). Portfolio-wide by default; pass
 * ?building_id to scope the inventory to a single visible building.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { GhgInventoryReportDocument } from "@/components/report/GhgInventoryReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

export default async function GhgInventoryReportPage({
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

  const esrsResult = await fetchEsrsReport(session.accessToken, scoped ? building_id : undefined)
  const esrs = esrsResult.ok ? esrsResult.data : null
  const esrsError = esrsResult.ok ? null : esrsResult.error

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
      title="GHG Inventory — GHG Protocol"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="Scope 1+2 disclosure-grade · Scope 3 estimated"
    >
      <GhgInventoryReportDocument esrs={esrs} esrsError={esrsError} />
    </ReportFrame>
  )
}
