/**
 * /buildings/[fabric_building_id]/reports/[page]
 *
 * The route exists so every report page has its own deep-link URL. All
 * rendering -- chrome, nav, and the PERSISTENT Power BI embed -- is owned by
 * the section layout (reports/layout.tsx + ReportSectionShell), which reads the
 * active slug from the pathname. This page only validates the slug so unknown
 * report names 404.
 */
import { notFound } from "next/navigation"

import { getReportPage } from "@/lib/config/reportPages"

type PageProps = {
  params: Promise<{ fabric_building_id: string; page: string }>
}

export default async function BuildingReportPage({ params }: PageProps) {
  const { page } = await params
  if (!getReportPage(page)) {
    notFound()
  }
  return null
}
