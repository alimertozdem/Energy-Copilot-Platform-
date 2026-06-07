/**
 * Left-rail conversation list for /copilot.
 *
 * Stateless presenter — parent owns the list and the active id.
 * Click → onSelect(id). "New chat" button → onNewChat().
 */
"use client"

import { cn } from "@/lib/utils"
import type { ConversationItem } from "@/lib/api/copilot"

type Props = {
  conversations: ConversationItem[]
  activeId: string | null
  accent: string
  onSelect: (id: string) => void
  onNewChat: () => void
  isCreating: boolean
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return ""
  const ts = new Date(iso).getTime()
  if (Number.isNaN(ts)) return ""
  const diff = Date.now() - ts
  const m = Math.floor(diff / 60_000)
  if (m < 1) return "just now"
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h`
  const d = Math.floor(h / 24)
  if (d < 7) return `${d}d`
  return new Date(iso).toLocaleDateString()
}

export function ConversationList({
  conversations,
  activeId,
  accent,
  onSelect,
  onNewChat,
  isCreating,
}: Props) {
  return (
    <aside className="w-72 shrink-0 border-r border-white/10 bg-white/[0.02] flex flex-col">
      <div className="p-3 border-b border-white/10">
        <button
          type="button"
          onClick={onNewChat}
          disabled={isCreating}
          className={cn(
            "w-full inline-flex items-center justify-center gap-2 rounded-lg",
            "border border-white/15 bg-white/[0.04] hover:bg-white/[0.08]",
            "px-3 py-2 text-sm font-medium text-white transition",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          <span
            className="size-1.5 rounded-full"
            style={{ backgroundColor: accent }}
          />
          {isCreating ? "Creating..." : "New chat"}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {conversations.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-white/40">
            No conversations yet.<br />Start one above.
          </div>
        ) : (
          <ul className="space-y-0.5 px-2">
            {conversations.map((c) => {
              const active = c.id === activeId
              return (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => onSelect(c.id)}
                    className={cn(
                      "w-full text-left rounded-md px-3 py-2 transition",
                      "hover:bg-white/[0.05]",
                      active && "bg-white/[0.08]"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {active && (
                        <span
                          className="size-1.5 rounded-full shrink-0"
                          style={{ backgroundColor: accent }}
                        />
                      )}
                      <div className="text-sm font-medium text-white truncate">
                        {c.title || "Untitled"}
                      </div>
                    </div>
                    <div className="mt-0.5 flex items-center gap-2 text-[11px] text-white/40">
                      {c.fabric_building_id && (
                        <span className="font-mono">{c.fabric_building_id}</span>
                      )}
                      <span>{formatRelativeTime(c.last_message_at ?? c.created_at)}</span>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </aside>
  )
}
