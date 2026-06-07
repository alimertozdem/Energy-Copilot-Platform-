/**
 * Shared server-side proxy: forwards a request to the FastAPI backend with the
 * NextAuth session token as a Bearer header (so the token never reaches the
 * browser). Used by the thin /api route handlers for devices/points/templates.
 */
import { getServerSession } from "next-auth/next"
import { NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function proxyToBackend(
  method: "GET" | "POST" | "PATCH" | "DELETE",
  backendPath: string,
  body?: unknown
): Promise<NextResponse> {
  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const session = await getServerSession(authOptions)
  const token = session?.accessToken
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }
  try {
    const res = await fetch(`${base}${backendPath}`, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      cache: "no-store",
    })
    if (res.status === 204) {
      return new NextResponse(null, { status: 204 })
    }
    const data = await res.json().catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    console.error(`[proxy ${method} ${backendPath}] Network error:`, err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
