import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ building_id: string; device_id: string }> }
) {
  const { building_id, device_id } = await params
  const body = await req.json().catch(() => ({}))
  return proxyToBackend(
    "PATCH",
    `/buildings/${encodeURIComponent(building_id)}/devices/${encodeURIComponent(device_id)}`,
    body
  )
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ building_id: string; device_id: string }> }
) {
  const { building_id, device_id } = await params
  return proxyToBackend(
    "DELETE",
    `/buildings/${encodeURIComponent(building_id)}/devices/${encodeURIComponent(device_id)}`
  )
}
