/**
 * Browser proxy: PATCH /installer-requests/admin/{request_id} (founder queue).
 * Forwards the NextAuth session token to FastAPI as Bearer (platform-admin gated).
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ request_id: string }> }
) {
  const { request_id } = await params
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
    const res = await fetch(
      `${base}/installer-requests/admin/${encodeURIComponent(request_id)}`,
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
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error("[/api/installer-requests/admin/[id] PATCH] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
