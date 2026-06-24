import { NextRequest, NextResponse } from "next/server"

/**
 * Browser-facing proxy for backend POST /auth/reset-password.
 *
 * The backend endpoint requires INTERNAL_API_KEY, which must never touch the
 * browser. The reset-password form posts here with { token, password }; this
 * route adds the key server-side and forwards the request.
 *
 * Status forwarded as-is so the form can show specific errors:
 *   200 -> success
 *   400 -> invalid / expired / used token
 *   422 -> weak password (policy: >= 8 chars, 1 digit)
 *   500 -> server/network error
 */
export async function POST(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL
  const apiKey = process.env.INTERNAL_API_KEY

  if (!backendUrl || !apiKey) {
    console.error("[/api/auth/reset-password] Missing BACKEND_URL or INTERNAL_API_KEY")
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }

  try {
    const res = await fetch(`${backendUrl}/auth/reset-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Api-Key": apiKey,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    })
    const responseBody = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/auth/reset-password] Network/unknown error:", err)
    return NextResponse.json({ detail: "Server error, please try again" }, { status: 500 })
  }
}
