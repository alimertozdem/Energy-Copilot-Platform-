import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  const limit = req.nextUrl.searchParams.get("limit") ?? "20"
  return proxyToBackend(
    "GET",
    `/buildings/${encodeURIComponent(building_id)}/recent-readings?limit=${encodeURIComponent(limit)}`
  )
}
