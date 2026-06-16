/**
 * Browser-facing proxy for GET /partners/org-lookup?slug=...
 * Resolves a client workspace slug to its org id + name (partner invite helper).
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
  const slug = request.nextUrl.searchParams.get("slug") ?? ""
  try {
    const res = await fetch(
      `${base}/partners/org-lookup?slug=${encodeURIComponent(slug)}`,
      {
        method: "GET",
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    const body = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(body, { status: res.status })
  } catch (err) {
    console.error("[/api/partners/org-lookup GET] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
