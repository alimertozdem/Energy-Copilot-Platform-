/**
 * Browser-facing proxy for /buildings/{building_id}/consumption (GET + POST).
 *
 * Forwards the NextAuth session token to FastAPI as a Bearer header so it never
 * reaches the browser. building_id is the building's Postgres UUID.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

function backendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

async function getAccessToken(): Promise<string | null> {
  const session = await getServerSession(authOptions)
  return session?.accessToken ?? null
}

async function forward(
  method: "GET" | "POST",
  buildingId: string,
  body?: unknown
): Promise<NextResponse> {
  const base = backendUrl()
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const token = await getAccessToken()
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }
  try {
    const res = await fetch(
      `${base}/buildings/${encodeURIComponent(buildingId)}/consumption`,
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
    console.error(`[/api/buildings/:id/consumption ${method}] Network error:`, err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  return forward("GET", building_id)
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ building_id: string }> }
) {
  const { building_id } = await params
  const body = await request.json().catch(() => ({}))
  return forward("POST", building_id, body)
}
