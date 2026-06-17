/**
 * /financing/report — print-optimised subsidy application pack (Download as PDF).
 *
 * Server component, force-dynamic, auth-guarded. Reads /financing/summary (the
 * new finance_model engine — same data as the on-screen page). Wraps
 * FinancingReportDocument in the shared ReportFrame (print stylesheet + header).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { FinancingReportDocument } from "@/components/report/FinancingReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { authOptions } from "@/lib/auth/options"
import { fetchFinancingSummary } from "@/lib/api/financing"

export const dynamic = "force-dynamic"

export default async function FinancingReportPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchFinancingSummary(session.accessToken)

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  return (
    <ReportFrame
      backHref="/financing"
      backLabel="Back to financing"
      title="Subsidy Application Pack"
      generatedAt={generatedAt}
      metaLine="Indicative KfW / BAFA capture — support, not advice"
      footerCenter="Indicative — verify against the live programme"
    >
      <FinancingReportDocument
        summary={result.ok ? result.data : null}
        error={result.ok ? null : result.error}
      />
    </ReportFrame>
  )
}
