/**
 * Client-side root for /copilot — owns all chat state.
 *
 * Layout:
 *   [ ConversationList ] [ thread + input ]
 *
 * State machine:
 *   idle      → user types, optionally picks a conversation
 *   sending   → user message sent, SSE stream open
 *   streaming → backend is emitting deltas (text + tool_call + tool_result)
 *   complete  → stream done; we re-fetch the conversation history so the
 *               local message list matches the canonical Postgres state
 *               (turn boundaries, persisted tool_call/tool_result rows).
 */
"use client"

import { useCallback, useEffect, useRef, useState } from "react"

import { MessageBubble } from "@/components/copilot/MessageBubble"
import { ConversationList } from "@/components/copilot/ConversationList"
import { cn } from "@/lib/utils"
import { streamCopilotMessage } from "@/lib/copilot/sseClient"
import type {
  ConversationDetail,
  ConversationItem,
  MessageItem,
  SSEEvent,
} from "@/lib/api/copilot"

type Props = {
  initialConversations: ConversationItem[]
  accent: string
  /** When set (deep-linked from a building's "Ask the advisor"), open or reuse
   *  a conversation focused on this Fabric building id. */
  focusBuildingId?: string | null
}

type StreamingState = {
  text: string
  toolCalls: { id: string; name: string; input: Record<string, unknown> }[]
  toolResults: { tool: string; preview: string; isError: boolean }[]
  errorMessage: string | null
}

const EMPTY_STREAM: StreamingState = {
  text: "",
  toolCalls: [],
  toolResults: [],
  errorMessage: null,
}

export function CopilotShell({ initialConversations, accent, focusBuildingId = null }: Props) {
  const [conversations, setConversations] =
    useState<ConversationItem[]>(initialConversations)
  const [activeId, setActiveId] = useState<string | null>(
    initialConversations[0]?.id ?? null
  )
  const [messages, setMessages] = useState<MessageItem[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  const [input, setInput] = useState("")
  const [streaming, setStreaming] = useState<StreamingState | null>(null)
  const [topError, setTopError] = useState<string | null>(null)

  const cancelStreamRef = useRef<(() => void) | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // ----- effects -----

  // Auto-scroll to bottom when messages or streaming text changes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages, streaming?.text, streaming?.toolCalls.length])

  // Load history whenever active conversation changes
  useEffect(() => {
    if (!activeId) {
      setMessages([])
      return
    }
    let cancelled = false
    setIsLoadingHistory(true)
    setTopError(null)
    fetch(`/api/copilot/conversations/${encodeURIComponent(activeId)}`, {
      cache: "no-store",
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`Backend ${res.status}`)
        return (await res.json()) as ConversationDetail
      })
      .then((detail) => {
        if (cancelled) return
        setMessages(detail.messages)
      })
      .catch((err: Error) => {
        if (cancelled) return
        setTopError(`Failed to load conversation: ${err.message}`)
        setMessages([])
      })
      .finally(() => {
        if (!cancelled) setIsLoadingHistory(false)
      })
    return () => {
      cancelled = true
    }
  }, [activeId])

  // Abort any in-flight stream on unmount
  useEffect(() => {
    return () => {
      cancelStreamRef.current?.()
    }
  }, [])

  // Deep-link focus: when arriving from a building's "Ask the advisor"
  // (/copilot?building_id=…), reuse the most recent non-archived conversation
  // focused on that building, or create a fresh focused one. Ref-guarded so
  // React StrictMode's double-mount can't create two. Self-contained — does NOT
  // touch handleNewChat (which is wired to child onNewChat handlers).
  const focusInitRef = useRef(false)
  useEffect(() => {
    if (!focusBuildingId || focusInitRef.current) return
    focusInitRef.current = true

    const existing = initialConversations.find(
      (c) => c.fabric_building_id === focusBuildingId && !c.is_archived
    )
    if (existing) {
      setActiveId(existing.id)
      return
    }

    let cancelled = false
    ;(async () => {
      setIsCreating(true)
      setTopError(null)
      try {
        const res = await fetch("/api/copilot/conversations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fabric_building_id: focusBuildingId }),
        })
        if (cancelled || !res.ok) return
        const created = (await res.json()) as { id: string; title: string }
        const newItem: ConversationItem = {
          id: created.id,
          title: created.title,
          provider: "claude",
          model: null,
          fabric_building_id: focusBuildingId,
          is_archived: false,
          last_message_at: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        setConversations((prev) => [newItem, ...prev])
        setActiveId(created.id)
        setMessages([])
      } catch {
        // swallow — the user can start a chat manually
      } finally {
        if (!cancelled) setIsCreating(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [focusBuildingId, initialConversations])

  // ----- handlers -----

  const handleNewChat = useCallback(async () => {
    setIsCreating(true)
    setTopError(null)
    try {
      const res = await fetch("/api/copilot/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Backend ${res.status}`)
      }
      const created = (await res.json()) as { id: string; title: string }
      // Build a minimal ConversationItem for the list
      const newItem: ConversationItem = {
        id: created.id,
        title: created.title,
        provider: "claude",
        model: null,
        fabric_building_id: null,
        is_archived: false,
        last_message_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setConversations((prev) => [newItem, ...prev])
      setActiveId(created.id)
      setMessages([])
    } catch (err) {
      setTopError(`Could not create conversation: ${(err as Error).message}`)
    } finally {
      setIsCreating(false)
    }
  }, [])

  const refetchActiveHistory = useCallback(async () => {
    if (!activeId) return
    try {
      const res = await fetch(
        `/api/copilot/conversations/${encodeURIComponent(activeId)}`,
        { cache: "no-store" }
      )
      if (!res.ok) return
      const detail = (await res.json()) as ConversationDetail
      setMessages(detail.messages)
      // Bump conversation's last_message_at in the sidebar
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeId ? { ...c, last_message_at: new Date().toISOString() } : c
        )
      )
    } catch {
      // swallow — UI will catch up on next nav
    }
  }, [activeId])

  const handleSend = useCallback(() => {
    const content = input.trim()
    if (!content || !activeId || streaming) return

    setInput("")
    setStreaming({ ...EMPTY_STREAM })
    setTopError(null)

    // Optimistic user message — backend will also persist it; we'll
    // re-fetch on complete so timestamps + UUIDs reconcile.
    const optimisticUser: MessageItem = {
      id: `optimistic-${Date.now()}`,
      role: "user",
      content,
      tool_calls: null,
      tool_call_id: null,
      tool_name: null,
      tokens_input: null,
      tokens_output: null,
      latency_ms: null,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimisticUser])

    const cancel = streamCopilotMessage({
      conversationId: activeId,
      content,
      onEvent: (ev: SSEEvent) => {
        setStreaming((prev) => {
          if (!prev) return prev
          return applyEventToStreaming(prev, ev)
        })
      },
      onError: (err) => {
        setStreaming((prev) =>
          prev ? { ...prev, errorMessage: err.message } : prev
        )
      },
      onClose: () => {
        cancelStreamRef.current = null
        // After the stream closes, sync local state with DB. This replaces
        // the optimistic user message + streaming buffer with persisted rows.
        void refetchActiveHistory().finally(() => setStreaming(null))
      },
    })
    cancelStreamRef.current = cancel
  }, [input, activeId, streaming, refetchActiveHistory])

  const handleStop = useCallback(() => {
    cancelStreamRef.current?.()
    cancelStreamRef.current = null
    setStreaming(null)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // ----- render -----

  return (
    <div className="relative z-10 flex h-[calc(100vh-128px)] max-w-6xl mx-auto border border-white/10 rounded-2xl overflow-hidden bg-black/20 backdrop-blur-sm">
      <ConversationList
        conversations={conversations}
        activeId={activeId}
        accent={accent}
        onSelect={(id) => setActiveId(id)}
        onNewChat={handleNewChat}
        isCreating={isCreating}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {topError && (
          <div className="px-6 py-2 border-b border-amber-500/30 bg-amber-500/10 text-xs text-amber-200">
            {topError}
          </div>
        )}

        {!activeId ? (
          <EmptyState onNewChat={handleNewChat} accent={accent} />
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
              {isLoadingHistory && messages.length === 0 ? (
                <div className="text-center text-xs text-white/40 py-10">
                  Loading conversation...
                </div>
              ) : messages.length === 0 && !streaming ? (
                <div className="py-8 text-center">
                  <p className="text-xs text-white/40">
                    Start the conversation — or try one of these:
                  </p>
                  <div className="mt-3 flex flex-wrap justify-center gap-2">
                    {COPILOT_SUGGESTIONS.map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => setInput(q)}
                        className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-white/70 transition-colors hover:border-white/30 hover:text-white"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((m) => (
                  <MessageBubble key={m.id} message={m} accent={accent} />
                ))
              )}

              {streaming && <StreamingBubble streaming={streaming} accent={accent} />}

              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-white/10 bg-black/20 p-3">
              <div className="flex items-end gap-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about a building (e.g. 'B001 anomalies last 30 days')..."
                  rows={2}
                  disabled={!!streaming}
                  className={cn(
                    "flex-1 resize-none rounded-lg border border-white/10",
                    "bg-white/[0.04] px-3 py-2 text-sm text-white placeholder:text-white/30",
                    "focus:outline-none focus:border-white/30 focus:bg-white/[0.06]",
                    "disabled:opacity-50"
                  )}
                />
                {streaming ? (
                  <button
                    type="button"
                    onClick={handleStop}
                    className="rounded-lg border border-white/15 bg-white/[0.04] hover:bg-white/[0.08] px-4 py-2 text-sm font-medium text-white transition"
                  >
                    Stop
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={!input.trim()}
                    className="rounded-lg px-4 py-2 text-sm font-medium text-white transition disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{ backgroundColor: accent }}
                  >
                    Send
                  </button>
                )}
              </div>
              <div className="mt-1.5 text-[10px] text-white/30">
                Enter to send · Shift+Enter for newline
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

// ----- helpers --------------------------------------------------------

function applyEventToStreaming(
  prev: StreamingState,
  ev: SSEEvent
): StreamingState {
  switch (ev.type) {
    case "text":
      return { ...prev, text: prev.text + ev.data.text }
    case "tool_call":
      return {
        ...prev,
        toolCalls: [
          ...prev.toolCalls,
          { id: ev.data.tool_use_id, name: ev.data.tool, input: ev.data.input },
        ],
      }
    case "tool_result":
      return {
        ...prev,
        toolResults: [
          ...prev.toolResults,
          {
            tool: ev.data.tool,
            preview: ev.data.result_preview,
            isError: ev.data.is_error,
          },
        ],
      }
    case "error":
      return { ...prev, errorMessage: ev.data.message }
    case "tool_call_start":
    case "user_message_persisted":
    case "complete":
    default:
      return prev
  }
}

function StreamingBubble({
  streaming,
  accent,
}: {
  streaming: StreamingState
  accent: string
}) {
  const hasContent =
    streaming.text || streaming.toolCalls.length > 0 || streaming.toolResults.length > 0
  return (
    <div className="flex items-start gap-3">
      <span
        className="mt-2 size-2 rounded-full shrink-0 animate-pulse"
        style={{ backgroundColor: accent }}
        aria-hidden
      />
      <div className="max-w-[80%] space-y-2">
        {streaming.toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {streaming.toolCalls.map((tc) => (
              <span
                key={tc.id}
                className="inline-flex items-center gap-1.5 rounded-md border border-white/15 bg-white/[0.04] px-2 py-1 text-[11px] text-white/80"
              >
                <span
                  className="size-1.5 rounded-full"
                  style={{ backgroundColor: accent }}
                />
                <span className="font-mono">{tc.name}</span>
              </span>
            ))}
          </div>
        )}
        {streaming.toolResults.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {streaming.toolResults.map((tr, i) => (
              <span
                key={`${tr.tool}-${i}`}
                className={cn(
                  "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px]",
                  tr.isError
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                    : "border-emerald-500/20 bg-emerald-500/5 text-emerald-200/80"
                )}
              >
                {tr.isError ? "✕" : "✓"} {tr.tool}
              </span>
            ))}
          </div>
        )}
        {streaming.text ? (
          <div className="rounded-2xl rounded-tl-md bg-white/[0.04] border border-white/10 px-4 py-2.5 text-sm text-white whitespace-pre-wrap">
            {streaming.text}
            <span className="inline-block ml-1 w-1.5 h-3.5 bg-white/60 animate-pulse align-middle" />
          </div>
        ) : !hasContent ? (
          <div className="text-xs text-white/40 italic">Thinking...</div>
        ) : null}
        {streaming.errorMessage && (
          <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
            {streaming.errorMessage}
          </div>
        )}
      </div>
    </div>
  )
}

// Suggested starter prompts — grounded in real capabilities (portfolio EUI,
// abatement, anomalies, battery). Shown when a conversation is open but empty;
// clicking one fills the composer so the presenter can edit or send.
const COPILOT_SUGGESTIONS = [
  "Which buildings have the worst EUI?",
  "What's our total abatable CO₂ per year?",
  "Show the no-regret measures that pay for themselves",
  "B001 anomalies in the last 30 days",
] as const

function EmptyState({
  onNewChat,
  accent,
}: {
  onNewChat: () => void
  accent: string
}) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
      <span
        className="size-3 rounded-full mb-4"
        style={{ backgroundColor: accent }}
      />
      <h2 className="text-lg font-medium text-white mb-1">EnergyLens Copilot</h2>
      <p className="text-sm text-white/50 max-w-sm mb-6">
        Ask about your buildings — energy, cost, anomalies, recommendations,
        battery scenarios. Try "B001 anomalies last 30 days".
      </p>
      <button
        type="button"
        onClick={onNewChat}
        className="rounded-lg px-4 py-2 text-sm font-medium text-white transition"
        style={{ backgroundColor: accent }}
      >
        Start a conversation
      </button>
    </div>
  )
}
