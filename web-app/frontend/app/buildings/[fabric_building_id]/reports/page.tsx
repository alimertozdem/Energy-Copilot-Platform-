/**
 * /buildings/[fabric_building_id]/reports -- index. Redirects to the default
 * report page so the bare /reports URL always lands somewhere useful.
 */
import { redirect } from "next/navigation"

import { DEFAULT_REPORT_SLUG } from "@/lib/config/reportPages"

type PageProps = {
  params: Promise<{ fabric_building_id: string }>
}

export default async function ReportsIndex({ params }: PageProps) {
  const { fabric_building_id } = await params
  redirect(`/buildings/${fabric_building_id}/reports/${DEFAULT_REPORT_SLUG}`)
}
