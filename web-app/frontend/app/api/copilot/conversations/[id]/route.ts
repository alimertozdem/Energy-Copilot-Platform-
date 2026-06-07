/**
 * Browser-facing proxy for GET /copilot/conversations/{id}.
 *
 * Returns the full conversation header + message history.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function GET(
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
      `${base}/copilot/conversations/${encodeURIComponent(id)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
        cache: "no-store",
      }
    )
    const body = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(body, { status: res.status })
  } catch (err) {
    console.error("[/api/copilot/conversations/[id] GET] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
