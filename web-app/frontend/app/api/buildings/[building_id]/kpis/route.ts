/**
 * Browser-facing proxy for GET /buildings/{building_id}/kpis.
 *
 * Forwards the NextAuth session token to FastAPI as a Bearer header so it never
 * reaches the browser. building_id is the building's Postgres UUID, so this
 * works for buildings still pending a Fabric bridge (fabric_building_id NULL) —
 * the baseline-KPI path (KPIs computed from uploaded monthly consumption).
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

function backendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

async function getAccessToken(): Promise<string | null> {
  const session = await getServerSession(authOptions)
  return session?.accessToken ?? null
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const base = backendUrl()
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const token = await getAccessToken()
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }
  const { building_id } = await params
  try {
    const res = await fetch(
      `${base}/buildings/${encodeURIComponent(building_id)}/kpis`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
        cache: "no-store",
      }
    )
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error("[/api/buildings/:id/kpis GET] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
