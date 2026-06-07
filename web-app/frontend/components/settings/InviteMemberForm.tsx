"use client"

/**
 * InviteMemberForm — admin creates a pending invitation (email + role).
 *
 * On success the new invite is lifted to the parent (handleInvited), which
 * prepends it to the PendingInvitesList where the admin copies its link.
 * No email is sent in V1 -- sharing is "copy link" (SendGrid is V1.5).
 */
import { useState } from "react"
import { Loader2, UserPlus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  type InviteRole,
  type PendingInviteItem,
  inviteMember,
} from "@/lib/api/settings"

const INVITE_ROLES: InviteRole[] = ["manager", "viewer"]

export function InviteMemberForm({
  onInvited,
}: {
  onInvited: (invite: PendingInviteItem) => void
}) {
  const [email, setEmail] = useState("")
  const [role, setRole] = useState<InviteRole>("viewer")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [okMsg, setOkMsg] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!email.trim() || busy) return
    setBusy(true)
    setError(null)
    setOkMsg(null)
    const result = await inviteMember({ email: email.trim(), role })
    setBusy(false)
    if (!result.ok) {
      setError(result.error)
      return
    }
    onInvited(result.data.invite)
    setOkMsg(
      `Invitation created for ${result.data.invite.email}. Copy its link below to share.`
    )
    setEmail("")
  }

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-5">
      <header className="flex items-center gap-2 mb-4">
        <UserPlus className="w-4 h-4 text-brand-emerald" />
        <h2 className="text-sm font-semibold text-text-primary">
          Invite a member
        </h2>
      </header>

      <form onSubmit={submit} className="flex flex-col sm:flex-row gap-2">
        <Input
          type="email"
          required
          placeholder="teammate@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as InviteRole)}
          aria-label="Invite role"
          className="h-8 rounded-lg border border-input bg-bg-elevated px-2 text-sm capitalize text-text-primary outline-none focus-visible:border-ring"
        >
          {INVITE_ROLES.map((r) => (
            <option key={r} value={r} className="capitalize">
              {r}
            </option>
          ))}
        </select>
        <Button type="submit" disabled={busy}>
          {busy ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <UserPlus className="w-3.5 h-3.5" />
          )}
          Send invite
        </Button>
      </form>

      {error && <p className="mt-2 text-xs text-accent-red">{error}</p>}
      {okMsg && <p className="mt-2 text-xs text-brand-emerald">{okMsg}</p>}

      <p className="mt-3 text-xs text-text-faint">
        No account needed — invitees accept via the link and sign in. Invites
        expire after 7 days.
      </p>
    </section>
  )
}
