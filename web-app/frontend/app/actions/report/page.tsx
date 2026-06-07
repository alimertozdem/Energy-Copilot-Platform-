/**
 * /actions/report — print-optimised recommendations report (Download as PDF).
 *
 * Server component, force-dynamic, auth-guarded. Reuses fetchActions — no new
 * backend, no Fabric change. Wraps ActionsReportDocument in the shared
 * ReportFrame (print stylesheet + branded header + PrintButton).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { ActionsReportDocument } from "@/components/report/ActionsReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { authOptions } from "@/lib/auth/options"
import { fetchActions } from "@/lib/api/actions"

export const dynamic = "force-dynamic"

type PageProps = {
  searchParams: Promise<{ building_id?: string }>
}

export default async function ActionsReportPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0

  const result = await fetchActions(session.accessToken, {
    limit: 500,
    ...(scoped ? { building_id } : {}),
  })

  const generatedAt = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  }).format(new Date())

  const counts = result.ok ? result.data.status_counts : null
  const total = counts?.total ?? (result.ok ? result.data.actions.length : 0)
  const open = counts?.open ?? 0

  return (
    <ReportFrame
      backHref={scoped ? `/actions?building_id=${encodeURIComponent(building_id!)}` : "/actions"}
      backLabel="Back to actions"
      title="Recommendations Report"
      generatedAt={generatedAt}
      metaLine={
        result.ok ? `${total} recommendation${total === 1 ? "" : "s"} · ${open} open` : undefined
      }
      footerCenter={result.ok ? `${total} recommendations` : ""}
    >
      <ActionsReportDocument
        actions={result.ok ? result.data.actions : []}
        counts={counts}
        error={result.ok ? null : result.error}
      />
    </ReportFrame>
  )
}
