/**
 * Browser-facing proxy for a single org member.
 *   PATCH  -> change member role
 *   DELETE -> remove member
 * Both forward the NextAuth session token to FastAPI as Bearer.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

async function authedBase(): Promise<
  { ok: true; base: string; token: string } | { ok: false; res: NextResponse }
> {
  const base = process.env.BACKEND_URL
  if (!base) {
    return {
      ok: false,
      res: NextResponse.json({ detail: "Server misconfigured" }, { status: 500 }),
    }
  }
  const session = await getServerSession(authOptions)
  const token = session?.accessToken
  if (!token) {
    return {
      ok: false,
      res: NextResponse.json({ detail: "Not authenticated" }, { status: 401 }),
    }
  }
  return { ok: true, base, token }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const { userId } = await params
  const auth = await authedBase()
  if (!auth.ok) return auth.res

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 })
  }

  try {
    const res = await fetch(
      `${auth.base}/settings/organization/members/${encodeURIComponent(userId)}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${auth.token}`,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(body),
        cache: "no-store",
      }
    )
    const responseBody = await res
      .json()
      .catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/settings/.../members/[userId] PATCH] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const { userId } = await params
  const auth = await authedBase()
  if (!auth.ok) return auth.res

  try {
    const res = await fetch(
      `${auth.base}/settings/organization/members/${encodeURIComponent(userId)}`,
      {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${auth.token}`,
          Accept: "application/json",
        },
        cache: "no-store",
      }
    )
    const responseBody = await res
      .json()
      .catch(() => ({ detail: "Empty response" }))
    return NextResponse.json(responseBody, { status: res.status })
  } catch (err) {
    console.error("[/api/settings/.../members/[userId] DELETE] Network error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
