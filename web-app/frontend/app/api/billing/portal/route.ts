/**
 * Browser-facing proxy for POST /billing/portal.
 *
 * Forwards the NextAuth session JWT as Bearer to FastAPI and returns the
 * Stripe Customer Portal URL.
 */
import { getServerSession } from "next-auth/next"
import { NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function POST() {
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
    const res = await fetch(`${base}/billing/portal`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error("[/api/billing/portal] error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
