import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

type Ctx = {
  params: Promise<{ building_id: string; device_id: string; point_id: string }>
}

export async function PATCH(req: NextRequest, { params }: Ctx) {
  const { building_id, device_id, point_id } = await params
  const body = await req.json().catch(() => ({}))
  return proxyToBackend(
    "PATCH",
    `/buildings/${encodeURIComponent(building_id)}/devices/${encodeURIComponent(device_id)}/points/${encodeURIComponent(point_id)}`,
    body
  )
}

export async function DELETE(_req: NextRequest, { params }: Ctx) {
  const { building_id, device_id, point_id } = await params
  return proxyToBackend(
    "DELETE",
    `/buildings/${encodeURIComponent(building_id)}/devices/${encodeURIComponent(device_id)}/points/${encodeURIComponent(point_id)}`
  )
}
