/**
 * Browser-facing proxy for /copilot/conversations (GET + POST).
 *
 * - GET  → backend GET /copilot/conversations (list user's threads)
 * - POST → backend POST /copilot/conversations (create empty thread)
 *
 * Why a proxy:
 *   The backend uses Bearer JWT auth. We pull session.accessToken on the
 *   server (NextAuth cookie is HTTP-only) and forward it, so the token
 *   never reaches the browser.
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

export async function GET(request: NextRequest) {
  const base = backendUrl()
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const token = await getAccessToken()
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  // Forward query params (limit, include_archived).
  const search = request.nextUrl.search

  try {
    const res = await fetch(`${base}/copilot/conversations${search}`, {
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
    console.error("[/api/copilot/conversations GET] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  const base = backendUrl()
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const token = await getAccessToken()
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    body = {} // empty body is valid — backend will use defaults
  }

  try {
    const res = await fetch(`${base}/copilot/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    })
    const responseBody = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/copilot/conversations POST] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
