/**
 * Resident session BFF — exchanges a magic-link token for an httpOnly cookie.
 *
 *   POST   { token } -> backend /residence/auth/consume -> set `el_resident` cookie
 *   DELETE           -> clear the cookie (resident sign-out)
 *
 * Separate from NextAuth: a DISTINCT cookie (`el_resident`) holding a resident
 * session JWT (issuer energylens-resident). The NextAuth B2B cookie/flow is never
 * touched. The backend consume endpoint validates the single-use magic-link token.
 */
import { NextRequest, NextResponse } from "next/server"

const COOKIE = "el_resident"

function getBackendUrl(): string {
  return process.env.BACKEND_URL || "http://127.0.0.1:8000"
}

export async function POST(request: NextRequest) {
  let body: { token?: string }
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }
  const token = body?.token?.trim()
  if (!token) {
    return NextResponse.json({ detail: "Missing token" }, { status: 400 })
  }

  try {
    const res = await fetch(`${getBackendUrl()}/residence/auth/consume`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ token }),
      cache: "no-store",
    })
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status })
    }

    const resp = NextResponse.json({ ok: true })
    resp.cookies.set({
      name: COOKIE,
      value: data.resident_token,
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: (data.expires_in_hours ?? 24) * 3600,
    })
    return resp
  } catch (err) {
    console.error("[/api/residence/session POST] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}

export async function DELETE() {
  const resp = NextResponse.json({ ok: true })
  resp.cookies.set({
    name: COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  })
  return resp
}
