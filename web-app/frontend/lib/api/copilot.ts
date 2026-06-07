/**
 * Types + server-only fetch helpers for /copilot endpoints.
 *
 * Stays in lockstep with backend app/schemas/copilot.py.
 *
 * Architecture:
 *   - Initial conversation list: server component fetches via fetchConversations()
 *     (same pattern as lib/api/portfolio.ts).
 *   - Create conversation + send message: client components call the
 *     /api/copilot/* proxy routes (Next.js route handlers forward to backend
 *     with the user's JWT). Keeps the access token off the client.
 *   - SSE streaming: see lib/copilot/sseClient.ts — also goes through the
 *     proxy so the backend URL never appears in browser network logs.
 */

// ============================================================================
// Wire types — match backend app/schemas/copilot.py
// ============================================================================

export type MessageRole = "user" | "assistant" | "tool"

export type ToolCall = {
  id: string
  name: string
  input: Record<string, unknown>
}

export type MessageItem = {
  id: string
  role: MessageRole
  content: string | null
  tool_calls: ToolCall[] | ToolCall | null
  tool_call_id: string | null
  tool_name: string | null
  tokens_input: number | null
  tokens_output: number | null
  latency_ms: number | null
  created_at: string // ISO datetime
}

export type ConversationItem = {
  id: string
  title: string
  provider: string
  model: string | null
  fabric_building_id: string | null
  is_archived: boolean
  last_message_at: string | null
  created_at: string
  updated_at: string
}

export type ConversationListResponse = {
  conversations: ConversationItem[]
}

export type ConversationDetail = ConversationItem & {
  messages: MessageItem[]
}

export type ConversationCreatedResponse = {
  id: string
  title: string
}

// ============================================================================
// SSE event shapes (frontend-facing — backend orchestrator emits these)
// ============================================================================

export type SSEEvent =
  | { type: "user_message_persisted"; data: { id: string } }
  | { type: "text"; data: { text: string } }
  | { type: "tool_call_start"; data: { tool_use_id: string; name: string } }
  | {
      type: "tool_call"
      data: { tool: string; tool_use_id: string; input: Record<string, unknown> }
    }
  | {
      type: "tool_result"
      data: {
        tool: string
        tool_use_id: string
        result_preview: string
        is_error: boolean
      }
    }
  | {
      type: "complete"
      data: {
        message_id: string | null
        stop_reason: string
        tokens_input?: number
        tokens_output?: number
        latency_ms?: number
        warning?: string
      }
    }
  | { type: "error"; data: { message: string } }

// ============================================================================
// Server-only helpers
// ============================================================================

type FetchResult<T> = { ok: true; data: T } | { ok: false; error: string }

function getBackendUrl(): string | null {
  return process.env.BACKEND_URL || null
}

function logError(scope: string, status: number, body: string) {
  console.error(`[${scope}] Backend ${status}: ${body.slice(0, 200)}`)
}

/**
 * GET /copilot/conversations — list user's recent conversations.
 *
 * Server-side only. Pass session.accessToken from a server component.
 */
export async function fetchConversations(
  accessToken: string
): Promise<FetchResult<ConversationListResponse>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchConversations] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }

  try {
    const res = await fetch(`${backendUrl}/copilot/conversations`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        Accept: "application/json",
      },
      cache: "no-store",
    })

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      logError("fetchConversations", res.status, body)
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as ConversationListResponse
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchConversations] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}

/**
 * GET /copilot/conversations/{id} — full conversation with message history.
 *
 * Returns ok:false with error="Not found" on 404 (conversation doesn't
 * exist OR user not authorized — backend conflates them).
 */
export async function fetchConversation(
  accessToken: string,
  conversationId: string
): Promise<FetchResult<ConversationDetail>> {
  const backendUrl = getBackendUrl()
  if (!backendUrl) {
    console.error("[fetchConversation] BACKEND_URL not configured")
    return { ok: false, error: "Server misconfigured" }
  }
  if (!accessToken) {
    return { ok: false, error: "Missing access token" }
  }

  try {
    const res = await fetch(
      `${backendUrl}/copilot/conversations/${encodeURIComponent(conversationId)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          Accept: "application/json",
        },
        cache: "no-store",
      }
    )

    if (res.status === 404) {
      return { ok: false, error: "Not found" }
    }

    if (!res.ok) {
      const body = await res.text().catch(() => "<no body>")
      logError("fetchConversation", res.status, body)
      return { ok: false, error: `Backend ${res.status}` }
    }

    const data = (await res.json()) as ConversationDetail
    return { ok: true, data }
  } catch (err) {
    console.error("[fetchConversation] Network/unknown error:", err)
    return { ok: false, error: "Network error" }
  }
}
