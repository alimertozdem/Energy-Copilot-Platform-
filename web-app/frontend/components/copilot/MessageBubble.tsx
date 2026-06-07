/**
 * One message in the chat thread.
 *
 * Three roles render differently:
 *   - user      → right-aligned, plain bubble
 *   - assistant → left-aligned, accent dot, glass bubble
 *   - tool      → collapsible "tool result" card (technical, dim)
 *
 * For assistant rows that carry tool_calls, we render a compact "called X"
 * pill above the text so the user can see what the AI looked up.
 */
"use client"

import { useState } from "react"

import { cn } from "@/lib/utils"
import type { MessageItem, ToolCall } from "@/lib/api/copilot"

type Props = {
  message: MessageItem
  accent: string
}

function normalizeToolCalls(raw: MessageItem["tool_calls"]): ToolCall[] {
  if (!raw) return []
  if (Array.isArray(raw)) return raw
  return [raw]
}

export function MessageBubble({ message, accent }: Props) {
  if (message.role === "user") {
    return <UserBubble content={message.content ?? ""} />
  }
  if (message.role === "tool") {
    return (
      <ToolResultBubble
        toolName={message.tool_name ?? "tool"}
        content={message.content ?? ""}
      />
    )
  }
  return (
    <AssistantBubble
      content={message.content ?? ""}
      toolCalls={normalizeToolCalls(message.tool_calls)}
      accent={accent}
    />
  )
}

// ----- variants --------------------------------------------------------

function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[78%] rounded-2xl rounded-tr-md bg-white/[0.08] border border-white/10 px-4 py-2.5 text-sm text-white whitespace-pre-wrap">
        {content}
      </div>
    </div>
  )
}

function AssistantBubble({
  content,
  toolCalls,
  accent,
}: {
  content: string
  toolCalls: ToolCall[]
  accent: string
}) {
  return (
    <div className="flex items-start gap-3">
      <span
        className="mt-2 size-2 rounded-full shrink-0"
        style={{ backgroundColor: accent }}
        aria-hidden
      />
      <div className="max-w-[80%] space-y-2">
        {toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {toolCalls.map((tc) => (
              <ToolCallPill
                key={tc.id || tc.name}
                name={tc.name}
                input={tc.input}
                accent={accent}
              />
            ))}
          </div>
        )}
        {content && (
          <div className="rounded-2xl rounded-tl-md bg-white/[0.04] border border-white/10 px-4 py-2.5 text-sm text-white whitespace-pre-wrap">
            {content}
          </div>
        )}
      </div>
    </div>
  )
}

function ToolCallPill({
  name,
  input,
  accent,
}: {
  name: string
  input: Record<string, unknown>
  accent: string
}) {
  const [open, setOpen] = useState(false)
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center gap-1.5 rounded-md border border-white/15 bg-white/[0.04] px-2 py-1 text-[11px] text-white/80 hover:bg-white/[0.08] transition"
      >
        <span
          className="size-1.5 rounded-full"
          style={{ backgroundColor: accent }}
        />
        <span className="font-mono">{name}</span>
        <span className="text-white/40">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <pre className="mt-1 rounded-md border border-white/10 bg-black/30 p-2 text-[10px] text-white/60 max-w-xl overflow-x-auto">
          {JSON.stringify(input, null, 2)}
        </pre>
      )}
    </div>
  )
}

function ToolResultBubble({
  toolName,
  content,
}: {
  toolName: string
  content: string
}) {
  const [open, setOpen] = useState(false)
  // Try to parse JSON for a prettier render
  let pretty = content
  let hasError = false
  try {
    const parsed = JSON.parse(content)
    pretty = JSON.stringify(parsed, null, 2)
    if (parsed && typeof parsed === "object" && "error" in parsed) {
      hasError = true
    }
  } catch {
    // leave as-is
  }
  return (
    <div className="pl-5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] transition",
          hasError
            ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
            : "border-white/10 bg-white/[0.03] text-white/50 hover:bg-white/[0.06]"
        )}
      >
        <span className="font-mono">{toolName} result</span>
        <span>{open ? "▾" : "▸"}</span>
        {hasError && <span className="ml-1 uppercase tracking-wider">error</span>}
      </button>
      {open && (
        <pre className="mt-1 rounded-md border border-white/10 bg-black/30 p-2 text-[10px] text-white/60 max-w-2xl max-h-64 overflow-auto whitespace-pre-wrap">
          {pretty}
        </pre>
      )}
    </div>
  )
}
