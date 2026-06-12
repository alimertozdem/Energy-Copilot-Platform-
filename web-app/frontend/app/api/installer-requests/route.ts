/**
 * Browser-facing proxy for POST /installer-requests.
 * A logged-in customer asks to be connected with an installer for a measure
 * (Execution Marketplace Phase 0 — founder-brokered).
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function POST(request: NextRequest) {
  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const session = await getServerSession(authOptions)
  const token = session?.accessToken
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  let body: {
    fabric_building_id?: string
    action_type?: string | null
    measure_label?: string | null
    source?: string | null
  }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }
  const bid = body?.fabric_building_id?.trim()
  if (!bid) {
    return NextResponse.json(
      { detail: "fabric_building_id is required" },
      { status: 400 }
    )
  }

  try {
    const res = await fetch(`${base}/installer-requests`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        fabric_building_id: bid,
        action_type: body.action_type ?? null,
        measure_label: body.measure_label ?? null,
        source: body.source ?? null,
      }),
      cache: "no-store",
    })
    const responseBody = await res
      .json()
      .catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/installer-requests POST] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
