/**
 * Browser-facing SSE proxy for POST /copilot/conversations/{id}/messages.
 *
 * The backend returns a text/event-stream of SSE chunks. We pipe the body
 * straight through as a ReadableStream so the browser sees one continuous
 * stream — no buffering, no JSON parsing on this layer.
 *
 * Why a proxy:
 *   The browser can't talk to the backend directly (BACKEND_URL is server-
 *   only, and the JWT is in an HTTP-only NextAuth cookie). This route reads
 *   the session, attaches the Bearer header, and forwards the request.
 *
 * Cancellation:
 *   When the client aborts (user navigates away), Next.js cancels this
 *   handler. We pass request.signal to the upstream fetch so the backend
 *   stream is also torn down.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

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

  let upstream: Response
  try {
    upstream = await fetch(
      `${base}/copilot/conversations/${encodeURIComponent(id)}/messages`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          Accept: "text/event-stream",
        },
        body: JSON.stringify(body),
        cache: "no-store",
        // Propagate client cancellation upstream — closes the backend stream
        // if the user navigates away mid-response.
        signal: request.signal,
      }
    )
  } catch (err) {
    console.error("[/api/copilot/.../messages POST] Network error:", err)
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 })
  }

  // Non-streaming error path — backend returned JSON instead of SSE.
  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "")
    return NextResponse.json(
      { detail: text || "Backend stream failed" },
      { status: upstream.status || 502 }
    )
  }

  // Pass the SSE stream through verbatim.
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  })
}
