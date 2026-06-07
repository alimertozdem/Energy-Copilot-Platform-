import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ building_id: string; token_id: string }> }
) {
  const { building_id, token_id } = await params
  return proxyToBackend(
    "DELETE",
    `/buildings/${encodeURIComponent(building_id)}/agent-tokens/${encodeURIComponent(token_id)}`
  )
}
