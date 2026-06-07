"use client"

/**
 * SettingsShell — client root for /settings.
 *
 * Owns the org profile, member list, and pending invites in state so the
 * page can update optimistically:
 *   - role change / remove   -> optimistic + rollback on error
 *   - invite                 -> prepend to pending list on success
 *   - revoke                 -> remove from pending list on success
 *
 * Mutations go through lib/api/settings (Next.js proxies -> FastAPI). Admin
 * gating is enforced server-side; canManage just shapes what we render. The
 * Activity feed is admin-only (server-gated), shown in the canManage block.
 */
import { useState } from "react"

import {
  type OrganizationProfile,
  type OrgMemberItem,
  type OrgRole,
  type OrgSettingsResponse,
  type PendingInviteItem,
  type SettingsActivityRow,
  changeMemberRole,
  removeMember,
} from "@/lib/api/settings"

import { ActivityCard } from "@/components/settings/ActivityCard"
import { InviteMemberForm } from "@/components/settings/InviteMemberForm"
import { MembersTable } from "@/components/settings/MembersTable"
import { OrgProfileCard } from "@/components/settings/OrgProfileCard"
import { PendingInvitesList } from "@/components/settings/PendingInvitesList"
import { SubscriptionCard } from "@/components/settings/SubscriptionCard"

type SettingsShellProps = {
  initial: OrgSettingsResponse
  activity?: SettingsActivityRow[]
}

export function SettingsShell({ initial, activity }: SettingsShellProps) {
  const [org, setOrg] = useState<OrganizationProfile>(initial.organization)
  const [members, setMembers] = useState<OrgMemberItem[]>(initial.members)
  const [invites, setInvites] = useState<PendingInviteItem[]>(
    initial.pending_invites
  )
  const [pendingUserId, setPendingUserId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const canManage = initial.can_manage

  async function handleRoleChange(userId: string, role: OrgRole) {
    setError(null)
    const original = members.find((m) => m.user_id === userId)
    if (!original || original.role === role) return
    const prevRole = original.role

    setPendingUserId(userId)
    setMembers((ms) =>
      ms.map((m) => (m.user_id === userId ? { ...m, role } : m))
    )

    const result = await changeMemberRole(userId, role)
    if (!result.ok) {
      setMembers((ms) =>
        ms.map((m) => (m.user_id === userId ? { ...m, role: prevRole } : m))
      )
      setError(result.error)
    } else {
      setMembers((ms) => ms.map((m) => (m.user_id === userId ? result.data : m)))
    }
    setPendingUserId(null)
  }

  async function handleRemove(userId: string) {
    setError(null)
    const snapshot = members
    setPendingUserId(userId)
    setMembers((ms) => ms.filter((m) => m.user_id !== userId))

    const result = await removeMember(userId)
    setPendingUserId(null)
    if (!result.ok) {
      setMembers(snapshot) // rollback
      setError(result.error)
    }
  }

  function handleInvited(invite: PendingInviteItem) {
    setInvites((list) => [invite, ...list])
  }

  function handleRevoked(id: string) {
    setInvites((list) => list.filter((i) => i.id !== id))
  }

  return (
    <div className="space-y-6">
      <OrgProfileCard org={org} canManage={canManage} onUpdated={setOrg} />
      <SubscriptionCard org={org} canManage={canManage} />

      {error && (
        <div className="rounded-lg border border-accent-red/30 bg-accent-red/5 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}

      <MembersTable
        members={members}
        canManage={canManage}
        pendingUserId={pendingUserId}
        onRoleChange={handleRoleChange}
        onRemove={handleRemove}
      />

      {canManage && (
        <>
          <InviteMemberForm onInvited={handleInvited} />
          <PendingInvitesList invites={invites} onRevoked={handleRevoked} />
          <ActivityCard events={activity ?? []} />
        </>
      )}
    </div>
  )
}
