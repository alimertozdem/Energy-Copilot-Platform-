import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ building_id: string; device_id: string }> }
) {
  const { building_id, device_id } = await params
  const body = await req.json().catch(() => ({}))
  return proxyToBackend(
    "POST",
    `/buildings/${encodeURIComponent(building_id)}/devices/${encodeURIComponent(device_id)}/points`,
    body
  )
}
