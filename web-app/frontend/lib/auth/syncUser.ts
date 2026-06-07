/**
 * Server-only helper. Called from NextAuth signIn callback to upsert the user
 * into the backend Postgres via POST /auth/sync.
 *
 * Returns true on success, false on any failure (network, auth, validation).
 * On false, the signIn callback should reject the login.
 */

type SyncPayload = {
  email: string
  display_name: string | null
  avatar_url: string | null
  provider: "microsoft" | "google" | "email"
  provider_user_id: string
  email_verified: boolean
}

type SyncResponse = {
  user_id: string
  organization_id: string
  is_new_user: boolean
  is_new_provider_link: boolean
  // JWT used by frontend to call protected backend endpoints (e.g. /buildings).
  // Forwarded as Authorization: Bearer <token>.
  access_token: string
}

export async function syncUserToBackend(
  payload: SyncPayload
): Promise<{ ok: true; data: SyncResponse } | { ok: false; error: string }> {
  const backendUrl = process.env.BACKEND_URL
  const apiKey = process.env.INTERNAL_API_KEY

  if (!backendUrl || !apiKey) {
    console.error("[syncUserToBackend] Missing BACKEND_URL or INTERNAL_API_KEY")
    return { ok: false, error: "Server misconfigured" }
  }

  try {
    const res = await fetch(`${backendUrl}/auth/sync`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Api-Key": apiKey,
      },
      body: JSON.stringify(payload),
      // Server-to-server localhost call — no caching, fail fast.
      cache: "no-store",
    })

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      console.error(
        `[syncUserToBackend] Backend rejected sync: ${res.status} ${res.statusText} — ${body}`
      )
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as SyncResponse
    console.log(
      `[syncUserToBackend] Synced user=${data.user_id} provider=${payload.provider} new_user=${data.is_new_user} new_link=${data.is_new_provider_link}`
    )
    return { ok: true, data }
  } catch (err) {
    console.error("[syncUserToBackend] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}
