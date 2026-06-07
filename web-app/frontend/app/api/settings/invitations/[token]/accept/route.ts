/**
 * Browser-facing proxy for POST /settings/invitations/{token}/accept.
 * Requires the user to be signed in; forwards the session token as Bearer.
 * On success the backend creates the OrgMember and marks the invite accepted.
 */
import { getServerSession } from "next-auth/next"
import { NextRequest, NextResponse } from "next/server"

import { authOptions } from "@/lib/auth/options"

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  const { token } = await params

  const base = process.env.BACKEND_URL
  if (!base) {
    return NextResponse.json({ detail: "Server misconfigured" }, { status: 500 })
  }
  const session = await getServerSession(authOptions)
  const sessionToken = session?.accessToken
  if (!sessionToken) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 })
  }

  try {
    const res = await fetch(
      `${base}/settings/invitations/${encodeURIComponent(token)}/accept`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionToken}`,
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
    console.error("[/api/settings/invitations/[token]/accept POST] error:", err)
    return NextResponse.json({ detail: "Server error" }, { status: 500 })
  }
}
