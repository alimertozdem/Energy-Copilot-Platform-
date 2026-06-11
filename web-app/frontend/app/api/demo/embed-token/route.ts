import { NextResponse } from "next/server"

// Server-side proxy for the public Power BI demo embed token.
// The browser calls this same-origin route; we forward to the backend using
// the server-only BACKEND_URL (Azure in prod, localhost in dev). This avoids
// the previous client-side hardcoded "http://127.0.0.1:8000" which only worked
// during local development and failed ("Failed to fetch") on the live site.
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(req: Request) {
  let body = "{}"
  try {
    const text = await req.text()
    if (text) body = text
  } catch {
    /* empty body is fine — the backend accepts {} */
  }

  const res = await fetch(`${BACKEND}/demo/embed/token`, {
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
