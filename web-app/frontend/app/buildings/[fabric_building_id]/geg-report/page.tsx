/**
 * /buildings/[fabric_building_id]/geg-report — GEG conformity PDF.
 *
 * Server component, force-dynamic, auth-guarded. Reads the per-building GEG screening
 * (GET /compliance/geg/{id}) and wraps GegConformityReportDocument in the shared
 * ReportFrame. Screening / decision-support — no new Fabric work.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { GegConformityReportDocument } from "@/components/report/GegConformityReportDocument"
import { ReportFrame } from "@/components/report/reportKit"
import { fetchGegConformity } from "@/lib/api/geg"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

type PageProps = {
  params: Promise<{ fabric_building_id: string }>
}

export default async function GegReportPage({ params }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { fabric_building_id } = await params
  const id = decodeURIComponent(fabric_building_id)

  const result = await fetchGegConformity(session.accessToken, id)
  const data = result.ok ? result.data : null
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

  const metaLine = data
    ? `${data.building_name}${data.country_code ? ` · ${data.country_code}` : ""}`
    : id

  return (
    <ReportFrame
      backHref={`/buildings/${encodeURIComponent(id)}`}
      backLabel="Back to building"
      title="GEG Conformity — Gebäudeenergiegesetz"
      generatedAt={generatedAt}
      metaLine={metaLine}
      footerCenter="GEG §71 + §48 / Anlage 7 — screening"
    >
      <GegConformityReportDocument data={data} error={error} />
    </ReportFrame>
  )
}
