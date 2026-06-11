import { getServerSession } from "next-auth/next"
import { NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

// Server-side proxy for the Power BI embed token (logged-in app). The backend
// /embed/token is AUTHENTICATED: it mints an RLS-scoped token whose
// effectiveIdentity customData = the caller's visible Fabric building-ids, so
// the embedded report is server-side filtered per customer. We forward the
// NextAuth session token as Bearer. /demo keeps its own public path.
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions)
    const token = session?.accessToken
    if (!token) {
      console.error("[/api/embed-token] no session.accessToken -> 401")
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
    }

    let body = "{}"
    try {
      const text = await req.text()
      if (text) body = text
    } catch {
      /* empty body is fine */
    }

    const res = await fetch(`${BACKEND}/embed/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body,
      cache: "no-store",
    })

    const data = await res.text()
    if (!res.ok) {
      // Surface the backend's failure detail in the dev terminal so a 500 is
      // never opaque. (PowerBIReport only shows the status code.)
      console.error(`[/api/embed-token] backend ${res.status}: ${data.slice(0, 600)}`)
    }
    return new NextResponse(data, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    })
  } catch (err) {
    // Frontend-side failure (getServerSession, fetch network error, etc.).
    console.error("[/api/embed-token] proxy error:", err)
    return NextResponse.json(
      { detail: `embed-token proxy error: ${err instanceof Error ? err.message : String(err)}` },
      { status: 500 },
    )
  }
}
