/**
 * Server-only helper. Called from NextAuth Credentials provider's
 * authorize() callback to verify email/password against backend.
 *
 * Returns ok:true with user info on success, ok:false on any failure.
 * The authorize() callback maps ok:false -> null so NextAuth rejects login.
 */

type LoginPayload = {
  email: string
  password: string
}

type LoginResponse = {
  user_id: string
  organization_id: string
  email: string
  display_name: string | null
  avatar_url: string | null
  // JWT used by frontend to call protected backend endpoints.
  access_token: string
}

export async function loginWithCredentials(
  payload: LoginPayload
): Promise<{ ok: true; data: LoginResponse } | { ok: false; error: string }> {
  const backendUrl = process.env.BACKEND_URL
  const apiKey = process.env.INTERNAL_API_KEY

  if (!backendUrl || !apiKey) {
    console.error("[loginWithCredentials] Missing BACKEND_URL or INTERNAL_API_KEY")
    return { ok: false, error: "Server misconfigured" }
  }

  try {
    const res = await fetch(`${backendUrl}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Api-Key": apiKey,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    })

    if (res.status === 401) {
      // Generic invalid creds -- expected on wrong password, don't spam logs.
      return { ok: false, error: "Invalid credentials" }
    }

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      console.error(
        `[loginWithCredentials] Backend error: ${res.status} ${res.statusText} — ${body}`
      )
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as LoginResponse
    return { ok: true, data }
  } catch (err) {
    console.error("[loginWithCredentials] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}
