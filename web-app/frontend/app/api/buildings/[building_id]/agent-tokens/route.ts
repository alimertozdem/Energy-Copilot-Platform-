import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  return proxyToBackend("GET", `/buildings/${encodeURIComponent(building_id)}/agent-tokens`)
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  const body = await req.json().catch(() => ({}))
  return proxyToBackend("POST", `/buildings/${encodeURIComponent(building_id)}/agent-tokens`, body)
}
