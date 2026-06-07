/**
 * /decarbonisation/report — print-optimised decarbonisation plan (Download as PDF).
 *
 * Server component, force-dynamic, auth-guarded. Reuses fetchMacc — no new
 * backend. Wraps DecarbReportDocument in the shared ReportFrame.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { DecarbReportDocument } from "@/components/report/DecarbReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { authOptions } from "@/lib/auth/options"
import { fetchMacc } from "@/lib/api/abatement"

export const dynamic = "force-dynamic"

export default async function DecarbReportPage({
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
  const result = await fetchMacc(session.accessToken, {
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

  const count = result.ok ? result.data.totals.measure_count : 0
  const co2 = result.ok ? Math.round(result.data.totals.total_annual_co2_t) : 0

  return (
    <ReportFrame
      backHref="/decarbonisation"
      backLabel="Back to decarbonisation"
      title="Decarbonisation Plan"
      generatedAt={generatedAt}
      metaLine={result.ok ? `${count} measures · ${co2} tCO₂/yr abatable` : undefined}
      footerCenter={result.ok ? `${count} measures` : ""}
    >
      <DecarbReportDocument
        data={result.ok ? result.data : null}
        error={result.ok ? null : result.error}
      />
    </ReportFrame>
  )
}
