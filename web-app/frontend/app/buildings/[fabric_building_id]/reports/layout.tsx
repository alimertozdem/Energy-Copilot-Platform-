/**
 * Layout for a building's report section.
 *
 * This layout PERSISTS across the [page] children, so the Power BI embed it
 * renders (via ReportSectionShell) mounts ONCE. Navigating between report pages
 * is then in-place (setActive) instead of a full re-embed + token re-fetch on
 * every click. Day 22 shipped per-page routes that re-embedded; Day 24 makes
 * the embed persistent.
 *
 * Server component: auth + fetch the building once, then hand off to the client
 * ReportSectionShell which owns the chrome + nav + the persistent embed and
 * reads the active page from the pathname.
 */
import { notFound, redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { fetchBuilding } from "@/lib/api/buildings"
import { authOptions } from "@/lib/auth/options"

import { ReportSectionShell } from "./ReportSectionShell"

type LayoutProps = {
  children: React.ReactNode
  params: Promise<{ fabric_building_id: string }>
}

export default async function ReportsLayout({ children, params }: LayoutProps) {
  const { fabric_building_id } = await params

  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchBuilding(session.accessToken, fabric_building_id)
  if (!result.ok) {
    // 404 covers both "doesn't exist" and "not authorized" (backend doesn't
    // distinguish, preventing enumeration).
    notFound()
  }

  return (
    <ReportSectionShell building={result.data}>{children}</ReportSectionShell>
  )
}
