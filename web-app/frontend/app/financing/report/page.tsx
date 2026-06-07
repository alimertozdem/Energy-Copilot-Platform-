/**
 * /financing/report — print-optimised subsidy application pack (Download as PDF).
 *
 * Server component, force-dynamic, auth-guarded. Reuses fetchActions — no new
 * backend, no Fabric change. Wraps FinancingReportDocument in the shared
 * ReportFrame (print stylesheet + branded header + PrintButton).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { FinancingReportDocument } from "@/components/report/FinancingReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { authOptions } from "@/lib/auth/options"
import { fetchActions } from "@/lib/api/actions"

export const dynamic = "force-dynamic"

export default async function FinancingReportPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchActions(session.accessToken, { limit: 500 })

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
        actions={result.ok ? result.data.actions : []}
        error={result.ok ? null : result.error}
      />
    </ReportFrame>
  )
}
