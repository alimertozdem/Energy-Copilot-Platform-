/**
 * Browser-facing proxy for the org settings resource.
 *   GET   -> FastAPI GET   /settings/organization   (client refetch / reconcile)
 *   PATCH -> FastAPI PATCH /settings/organization   (edit org profile)
 *
 * Forwards the NextAuth session token to FastAPI as Bearer; keeps
 * BACKEND_URL out of the browser bundle.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function GET() {
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
    const res = await fetch(`${base}/settings/organization`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      cache: "no-store",
    })
    const body = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(body, { status: res.status })
  } catch (err) {
    console.error("[/api/settings/organization GET] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}

export async function PATCH(request: NextRequest) {
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
    const res = await fetch(`${base}/settings/organization`, {
      method: "PATCH",
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
    console.error("[/api/settings/organization PATCH] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
