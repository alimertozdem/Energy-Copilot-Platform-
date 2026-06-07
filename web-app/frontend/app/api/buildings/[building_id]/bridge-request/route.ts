/**
 * Browser proxy: POST + DELETE /buildings/{building_id}/bridge-request.
 * POST files a self-serve bridge request; DELETE cancels the pending one.
 * Forwards the NextAuth session token to FastAPI as Bearer. building_id = UUID.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

async function forward(
  method: "POST" | "DELETE",
  buildingId: string,
  body?: unknown
): Promise<NextResponse> {
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
      `${base}/buildings/${encodeURIComponent(buildingId)}/bridge-request`,
      {
        method,
        headers: {
          Authorization: `Bearer ${token}`,
          ...(method === "POST" ? { "Content-Type": "application/json" } : {}),
          Accept: "application/json",
        },
        ...(method === "POST" ? { body: JSON.stringify(body ?? {}) } : {}),
        cache: "no-store",
      }
    )
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error(`[/api/buildings/:id/bridge-request ${method}] Network error:`, err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  const body = await request.json().catch(() => ({}))
  return forward("POST", building_id, body)
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  return forward("DELETE", building_id)
}
