import { NextRequest, NextResponse } from "next/server"

/**
 * Browser-facing proxy for backend POST /auth/register.
 *
 * Why a proxy:
 *   The backend endpoint requires INTERNAL_API_KEY, which must never
 *   touch the browser. The signup form posts to this Next.js route,
 *   which adds the key server-side and forwards the request.
 *
 * Body forwarded as-is: { email, password, display_name }
 * Status code forwarded as-is so the frontend can show specific errors:
 *   201 -> success
 *   409 -> email already registered
 *   422 -> validation failure (e.g. password missing digit)
 *   500 -> server/network error
 */
export async function POST(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL
  const apiKey = process.env.INTERNAL_API_KEY

  if (!backendUrl || !apiKey) {
    console.error("[/api/auth/register] Missing BACKEND_URL or INTERNAL_API_KEY")
    return NextResponse.json(
      { detail: "Server misconfigured" },
      { status: 500 }
    )
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json(
      { detail: "Invalid JSON body" },
      { status: 400 }
    )
  }

  try {
    const res = await fetch(`${backendUrl}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Api-Key": apiKey,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    })

    // Forward the backend's response verbatim (status + body).
    const responseBody = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/auth/register] Network/unknown error:", err)
    return NextResponse.json(
      { detail: "Server error, please try again" },
      { status: 500 }
    )
  }
}
