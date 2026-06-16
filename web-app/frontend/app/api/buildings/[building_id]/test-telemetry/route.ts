import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  return proxyToBackend(
    "POST",
    `/buildings/${encodeURIComponent(building_id)}/test-telemetry`
  )
}
