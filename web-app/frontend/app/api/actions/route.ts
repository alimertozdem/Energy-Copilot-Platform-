/**
 * Browser-facing proxy for GET /actions.
 *
 * Used by AppChrome to fetch the live open-count badge on the nav link.
 * Forwards the NextAuth session JWT as Bearer to FastAPI.
 *
 * Page-level reads (the /actions Server Component) talk to FastAPI directly
 * with the session token; this proxy exists so client components can fetch
 * without ever seeing BACKEND_URL.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function GET(request: NextRequest) {
  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const session = await getServerSession(authOptions)
  const token = session?.accessToken
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  // Pass through query params verbatim (status, building_id, category, limit)
  const search = request.nextUrl.search // includes leading '?'
  const url = `${base}/actions${search}`

  try {
    const res = await fetch(url, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })
    const body = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(body, { status: res.status })
  } catch (err) {
    console.error("[/api/actions GET] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
