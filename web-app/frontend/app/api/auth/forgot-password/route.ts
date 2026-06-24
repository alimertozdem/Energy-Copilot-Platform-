import { NextRequest, NextResponse } from "next/server"

/**
 * Browser-facing proxy for backend POST /auth/forgot-password.
 *
 * The backend endpoint requires INTERNAL_API_KEY, which must never touch the
 * browser. The forgot-password form posts here; this route adds the key
 * server-side and forwards { email }.
 *
 * The backend always returns 200 (it never reveals whether the account exists),
 * so this route does too — the form shows the same "check your inbox" state
 * regardless, preventing email enumeration.
 */
export async function POST(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL
  const apiKey = process.env.INTERNAL_API_KEY

  if (!backendUrl || !apiKey) {
    console.error("[/api/auth/forgot-password] Missing BACKEND_URL or INTERNAL_API_KEY")
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }

  try {
    const res = await fetch(`${backendUrl}/auth/forgot-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Api-Key": apiKey,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    })
    const responseBody = await res.json().catch(() => ({ ok: true }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/auth/forgot-password] Network/unknown error:", err)
    return NextResponse.json({ detail: "Server error, please try again" }, { status: 500 })
  }
}
