/**
 * Browser proxy: GET /buildings/{building_id}/bridge-readiness.
 * Forwards the NextAuth session token to FastAPI as Bearer. building_id = UUID.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const session = await getServerSession(authOptions)
  const token = session?.accessToken
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }
  try {
    const res = await fetch(
      `${base}/buildings/${encodeURIComponent(building_id)}/bridge-readiness`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error("[/api/buildings/:id/bridge-readiness GET] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
