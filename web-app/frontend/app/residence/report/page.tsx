/**
 * /residence/report — print-optimised monthly consumption statement (UVI).
 *
 * PUBLIC route. Identity from the resident session cookie `el_resident` (magic
 * link), or the ?resident= dev param when RESIDENT_DEV_MODE=1. Reuses the resident
 * summary fetcher + the shared ReportFrame. "Download as PDF" = window.print.
 */
import { cookies } from "next/headers"

import { fetchResidenceSummary } from "@/lib/api/residence"
import { UviReportDocument } from "@/components/report/UviReportDocument"
import { ReportFrame } from "@/components/report/reportKit"

export const dynamic = "force-dynamic"

export default async function ResidenceReportPage({
  searchParams,
}: {
  searchParams: Promise<{ resident?: string }>
}) {
  const { resident } = await searchParams
  const devResidentId = resident?.trim() || null

  const cookieStore = await cookies()
  const token = cookieStore.get("el_resident")?.value || null

  const hasIdentity = Boolean(token || devResidentId)
  const result = hasIdentity ? await fetchResidenceSummary({ token, devResidentId }) : null
  const summary = result?.ok ? result.data : null
  const error = result && !result.ok ? result.error : null

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const backHref = devResidentId
    ? `/residence?resident=${encodeURIComponent(devResidentId)}`
    : "/residence"
  const metaLine = summary ? `As of ${summary.as_of}` : undefined

  return (
    <ReportFrame
      backHref={backHref}
      backLabel="Back to my home"
      title="Monthly Consumption (UVI)"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="EED / HKVO consumption information"
    >
      <UviReportDocument summary={summary} error={error} />
    </ReportFrame>
  )
}
