/**
 * Browser-facing proxy for POST /buildings (onboarding wizard creates a building).
 * Forwards the NextAuth session token to FastAPI as Bearer; keeps BACKEND_URL
 * out of the client bundle. Reads (GET /buildings) stay server-side in
 * lib/api/buildings.ts, so this proxy only needs POST.
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

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }

  try {
    const res = await fetch(`${base}/buildings`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    })
    const responseBody = await res
      .json()
      .catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/buildings POST] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
