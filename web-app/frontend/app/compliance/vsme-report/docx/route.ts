/**
 * GET /compliance/vsme-report/docx — the VSME Basic Module report as an editable Word (.doc).
 *
 * Renders the SAME VsmeReportDocument to static HTML and returns it with the Word
 * content-type. Honors ?building_id to scope B3 (energy & GHG) to one building.
 */
import { createElement } from "react"
import { getServerSession } from "next-auth"

import { VsmeReportDocument } from "@/components/report/VsmeReportDocument"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { fetchEsrsNarrativeServer, narrativeMap } from "@/lib/api/esrsNarrative"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"
import { wordResponse } from "@/lib/report/wordDoc"

export const dynamic = "force-dynamic"

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    return new Response("Unauthorized", { status: 401 })
  }

  const url = new URL(req.url)
  const buildingId = url.searchParams.get("building_id") || undefined
  const comprehensive = url.searchParams.get("level") === "comprehensive"

  const [e, b, n] = await Promise.all([
    fetchEsrsReport(session.accessToken, buildingId),
    fetchPortfolioBuildings(session.accessToken),
    fetchEsrsNarrativeServer(session.accessToken),
  ])
  const esrs = e.ok ? e.data : null
  const all = b.ok ? b.data.buildings : []
  const buildings = buildingId ? all.filter((x) => x.fabric_building_id === buildingId) : all
  const narrative = n.ok ? narrativeMap(n.data.items) : {}

  const subtitle = buildingId
    ? `${esrs?.rows?.[0]?.name ?? buildingId} · single building`
    : esrs
    ? `${esrs.buildings_total} building${esrs.buildings_total === 1 ? "" : "s"}`
    : null

  return wordResponse(
    comprehensive ? "VSME-Basic-Comprehensive" : "VSME-Basic-Module",
    comprehensive ? "VSME — Basic + Comprehensive" : "VSME — Basic Module",
    subtitle,
    createElement(VsmeReportDocument, {
      esrs,
      esrsError: e.ok ? null : e.error,
      buildings,
      buildingsError: b.ok ? null : b.error,
      narrative,
      comprehensive,
    })
  )
}
