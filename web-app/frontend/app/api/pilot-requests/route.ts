/**
 * Public proxy: POST /pilot-requests (no auth — lead capture).
 * Forwards to FastAPI so the browser never sees BACKEND_URL.
 */
import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }
  try {
    const res = await fetch(`${base}/pilot-requests`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    })
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error("[/api/pilot-requests POST] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
