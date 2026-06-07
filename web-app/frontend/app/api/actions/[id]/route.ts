/**
 * Browser-facing proxy for PATCH /actions/{action_id}.
 *
 * Forwards the NextAuth session token to FastAPI as Bearer. Keeps
 * BACKEND_URL out of the browser bundle and prevents tokens from leaking
 * via direct-to-FastAPI fetches.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function PATCH(
  request: NextRequest,
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

  // Body is passed through verbatim — backend Pydantic does the validation.
  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      { detail: "Invalid JSON body" },
      { status: 400 }
    )
  }

  try {
    const res = await fetch(
      `${base}/actions/${encodeURIComponent(id)}`,
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
    console.error("[/api/actions/[id] PATCH] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
