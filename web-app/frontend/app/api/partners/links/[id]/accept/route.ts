/**
 * Browser-facing proxy for POST /partners/links/{id}/accept.
 * A client-org admin consents to a pending invite (-> active).
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
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
      `${base}/partners/links/${encodeURIComponent(id)}/accept`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
        cache: "no-store",
      }
    )
    const responseBody = await res
      .json()
      .catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/partners/links/[id]/accept POST] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
