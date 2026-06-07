import { NextRequest } from "next/server"

import { proxyToBackend } from "@/lib/server/backendProxy"

export async function GET(_req: NextRequest) {
  return proxyToBackend("GET", "/device-templates")
}
