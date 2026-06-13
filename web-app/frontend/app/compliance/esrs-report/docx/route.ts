/**
 * GET /compliance/esrs-report/docx — the ESRS E-1 report as an editable Word (.doc).
 *
 * Renders the SAME EsrsE1ReportDocument to static HTML and returns it with the Word
 * content-type. Honors ?building_id for a single-building scope (like the print route).
 */
import { createElement } from "react"
import { getServerSession } from "next-auth"

import { EsrsE1ReportDocument } from "@/components/report/EsrsE1ReportDocument"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { fetchEsrsNarrativeServer, narrativeMap } from "@/lib/api/esrsNarrative"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"
import { wordResponse } from "@/lib/report/wordDoc"

export const dynamic = "force-dynamic"
export const runtime = "nodejs"

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    return new Response("Unauthorized", { status: 401 })
  }

  const buildingId = new URL(req.url).searchParams.get("building_id") || undefined

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

  return await wordResponse(
    "ESRS-E1",
    "ESRS E-1 — Climate Change",
    subtitle,
    createElement(EsrsE1ReportDocument, {
      esrs,
      esrsError: e.ok ? null : e.error,
      buildings,
      buildingsError: b.ok ? null : b.error,
      narrative,
    })
  )
}
