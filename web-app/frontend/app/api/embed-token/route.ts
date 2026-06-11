import { NextResponse } from "next/server"

// Server-side proxy for the Power BI embed token (logged-in app). Forwards to
// the backend using server-only BACKEND_URL (Azure in prod, localhost in dev),
// fixing the previous client-side hardcoded "http://127.0.0.1:8000" that broke
// on the live site. The backend /embed/token endpoint is public (RLS is applied
// client-side via the building-id filter), so no auth header is forwarded here.
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(req: Request) {
  let body = "{}"
  try {
    const text = await req.text()
    if (text) body = text
  } catch {
    /* empty body is fine */
  }

  const res = await fetch(`${BACKEND}/embed/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    cache: "no-store",
  })

  const data = await res.text()
  return new NextResponse(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  })
}
