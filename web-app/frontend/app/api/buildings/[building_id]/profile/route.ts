/**
 * Browser-facing proxy for PATCH /buildings/{id}/profile.
 * Lets a building manager supply screening inputs (year / EPC / heating / area)
 * to sharpen the estimate. B2B session → backend (manage-gated there).
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const session = await getServerSession(authOptions)
  const token = session?.accessToken
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }
  const { building_id } = await params

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }

  try {
    const res = await fetch(
      `${base}/buildings/${encodeURIComponent(building_id)}/profile`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(body),
        cache: "no-store",
      }
    )
    const responseBody = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/buildings/[id]/profile PATCH] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
