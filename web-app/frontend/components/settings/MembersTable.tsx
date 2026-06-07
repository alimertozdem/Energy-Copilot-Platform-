"use client"

/**
 * MembersTable — list of org members with inline role control + removal.
 *
 * Viewers/managers see a read-only list. Admins get a role <select> and a
 * remove button on every row except their own (self-management is kept
 * simple in V1; the backend's last-admin guard is the real safety net).
 */
import { Loader2, Trash2, UserCircle2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { type OrgMemberItem, type OrgRole } from "@/lib/api/settings"

const ROLE_OPTIONS: OrgRole[] = ["admin", "manager", "viewer"]

const ROLE_BADGE: Record<OrgRole, string> = {
  admin: "bg-brand-emerald/10 text-brand-emerald border-brand-emerald/30",
  manager: "bg-sky-500/10 text-sky-300 border-sky-500/30",
  viewer: "bg-white/5 text-text-muted border-border-subtle",
}

type MembersTableProps = {
  members: OrgMemberItem[]
  canManage: boolean
  pendingUserId: string | null
  onRoleChange: (userId: string, role: OrgRole) => void
  onRemove: (userId: string) => void
}

export function MembersTable({
  members,
  canManage,
  pendingUserId,
  onRoleChange,
  onRemove,
}: MembersTableProps) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-5">
      <header className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <UserCircle2 className="w-4 h-4 text-brand-emerald" />
          <h2 className="text-sm font-semibold text-text-primary">Members</h2>
        </div>
        <span className="text-xs text-text-muted">
          {members.length} {members.length === 1 ? "member" : "members"}
        </span>
      </header>

      <div className="divide-y divide-border-subtle">
        {members.map((m) => {
          const busy = pendingUserId === m.user_id
          return (
            <div key={m.user_id} className="flex items-center gap-3 py-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-text-primary truncate">
                    {m.display_name || m.email}
                  </span>
                  {m.is_self && (
                    <span className="rounded-full bg-brand-emerald/10 px-1.5 py-0.5 text-[10px] font-medium text-brand-emerald">
                      You
                    </span>
                  )}
                  {m.is_pending && (
                    <span className="rounded-full bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-300">
                      Pending
                    </span>
                  )}
                </div>
                {m.display_name && (
                  <div className="text-xs text-text-muted truncate">
                    {m.email}
                  </div>
                )}
              </div>

              {canManage && !m.is_self ? (
                <select
                  value={m.role}
                  disabled={busy}
                  onChange={(e) =>
                    onRoleChange(m.user_id, e.target.value as OrgRole)
                  }
                  aria-label={`Role for ${m.email}`}
                  className="h-7 rounded-lg border border-input bg-bg-elevated px-2 text-xs capitalize text-text-primary outline-none focus-visible:border-ring disabled:opacity-50"
                >
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r} value={r} className="capitalize">
                      {r}
                    </option>
                  ))}
                </select>
              ) : (
                <span
                  className={cn(
                    "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize",
                    ROLE_BADGE[m.role]
                  )}
                >
                  {m.role}
                </span>
              )}

              {canManage && !m.is_self && (
                <button
                  type="button"
                  onClick={() => onRemove(m.user_id)}
                  disabled={busy}
                  aria-label={`Remove ${m.email}`}
                  className="inline-flex h-7 w-7 items-center justify-center rounded-md text-text-muted transition-colors hover:bg-accent-red/10 hover:text-accent-red disabled:opacity-50"
                >
                  {busy ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
