/**
 * Browser-facing proxy for POST /billing/checkout.
 *
 * Forwards the NextAuth session JWT as Bearer to FastAPI and returns the
 * Stripe Checkout URL. Keeps BACKEND_URL out of the client bundle.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function POST(request: NextRequest) {
  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const session = await getServerSession(authOptions)
  const token = session?.accessToken
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  const body = await request.text()

  try {
    const res = await fetch(`${base}/billing/checkout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body,
      cache: "no-store",
    })
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error("[/api/billing/checkout] error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
