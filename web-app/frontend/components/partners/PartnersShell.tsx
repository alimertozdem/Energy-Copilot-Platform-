"use client"

/**
 * PartnersShell -- interactive client component for /partners.
 *
 * Lists PartnerClientLink relationships touching the caller's org and exposes the
 * lifecycle actions: invite a client (partner orgs only), accept a pending invite
 * (client admins), revoke (either side). Mutations go through the /api/partners/*
 * proxy routes; on success we router.refresh() to re-read the server-rendered list.
 */
import { type FormEvent, useState } from "react"
import { useRouter } from "next/navigation"

import {
  acceptPartnerLink,
  createPartnerLink,
  lookupClientOrg,
  revokePartnerLink,
} from "@/lib/api/partnerMutations"
import type { PartnerLinkRow } from "@/lib/api/partners"

const STATUS_STYLE: Record<string, string> = {
  active: "bg-brand-emerald/10 text-brand-emerald border-brand-emerald/30",
  pending: "bg-amber-500/15 text-amber-200 border-amber-500/30",
  revoked: "bg-white/5 text-text-muted border-border-subtle",
  suspended: "bg-orange-500/15 text-orange-200 border-orange-500/30",
}

export function PartnersShell({
  links,
  error,
}: {
  links: PartnerLinkRow[] | null
  error: string | null
}) {
  const router = useRouter()
  const [clientOrgId, setClientOrgId] = useState("")
  const [scope, setScope] = useState("read_only")
  const [busy, setBusy] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  async function run(
    label: string,
    fn: () => Promise<{ ok: boolean; error?: string }>
  ) {
    setBusy(label)
    setNotice(null)
    const res = await fn()
    setBusy(null)
    if (!res.ok) {
      setNotice(res.error ?? "Request failed")
      return
    }
    router.refresh()
  }

  async function onInvite(e: FormEvent) {
    e.preventDefault()
    const input = clientOrgId.trim()
    if (!input) return
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(input)
    await run("invite", async () => {
      let orgId = input
      if (!isUuid) {
        const look = await lookupClientOrg(input)
        if (!look.ok) return { ok: false, error: look.error }
        orgId = look.data.organization_id
      }
      return createPartnerLink({ client_org_id: orgId, scope })
    })
    setClientOrgId("")
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 space-y-8">
      <p className="text-sm text-text-muted">
        A partner organisation manages client portfolios through delegated, revocable
        access — the client must consent before a link goes live, and either side can
        revoke at any time.
      </p>

      {notice && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          {notice}
        </div>
      )}

      <section className="rounded-lg border border-border-subtle bg-bg-elevated/60 p-4">
        <h2 className="mb-1 text-sm font-medium text-text-primary">Invite a client</h2>
        <p className="mb-3 text-xs text-text-muted">
          Partner organisations only. Enter the client&rsquo;s workspace ID (their slug, e.g.
          <code className="mx-1 rounded bg-white/5 px-1">acme-immobilien</code>) or a workspace UUID.
          They receive a pending request and must accept it before you gain access.
        </p>
        <form onSubmit={onInvite} className="flex flex-wrap items-end gap-3">
          <label className="min-w-[220px] flex-1 text-xs text-text-muted">
            Client workspace ID or slug
            <input
              value={clientOrgId}
              onChange={(e) => setClientOrgId(e.target.value)}
              placeholder="acme-immobilien"
              className="mt-1 w-full rounded-md border border-border-subtle bg-transparent px-3 py-2 text-sm text-text-primary placeholder:text-text-muted/60 focus:border-brand-emerald focus:outline-none"
            />
          </label>
          <label className="text-xs text-text-muted">
            Scope
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="mt-1 block rounded-md border border-border-subtle bg-transparent px-3 py-2 text-sm text-text-primary focus:border-brand-emerald focus:outline-none"
            >
              <option value="read_only">Read only</option>
              <option value="full_manage">Full manage</option>
            </select>
          </label>
          <button
            type="submit"
            disabled={busy === "invite" || clientOrgId.trim() === ""}
            className="rounded-md bg-brand-emerald/90 px-4 py-2 text-sm font-medium text-black hover:bg-brand-emerald disabled:opacity-50"
          >
            {busy === "invite" ? "Inviting…" : "Send invite"}
          </button>
        </form>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-text-primary">Relationships</h2>
        {error ? (
          <div className="rounded-md border border-border-subtle bg-white/5 px-3 py-2 text-sm text-text-muted">
            Couldn’t load partner relationships ({error}).
          </div>
        ) : !links || links.length === 0 ? (
          <div className="rounded-md border border-border-subtle bg-white/5 px-3 py-6 text-center text-sm text-text-muted">
            No partner relationships yet.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border-subtle">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-text-muted">
                <tr className="border-b border-border-subtle">
                  <th className="px-3 py-2 font-medium">Organisation</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Scope</th>
                  <th className="px-3 py-2 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {links.map((l) => {
                  const badge =
                    STATUS_STYLE[l.relationship_status] ?? STATUS_STYLE.revoked
                  const isLive = l.revoked_at === null
                  return (
                    <tr key={l.id} className="border-b border-border-subtle/60">
                      <td className="px-3 py-2 text-text-primary">
                        {l.counterparty_org_name}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`inline-flex rounded-full border px-2 py-0.5 text-[11px] ${badge}`}
                        >
                          {l.relationship_status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-text-muted">
                        {l.scope === "full_manage" ? "Full manage" : "Read only"}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <div className="flex justify-end gap-2">
                          {l.relationship_status === "pending" && (
                            <button
                              onClick={() =>
                                run(`accept-${l.id}`, () => acceptPartnerLink(l.id))
                              }
                              disabled={busy === `accept-${l.id}`}
                              className="rounded-md border border-brand-emerald/40 px-2.5 py-1 text-xs text-brand-emerald hover:bg-brand-emerald/10 disabled:opacity-50"
                            >
                              Accept
                            </button>
                          )}
                          {isLive && (
                            <button
                              onClick={() =>
                                run(`revoke-${l.id}`, () => revokePartnerLink(l.id))
                              }
                              disabled={busy === `revoke-${l.id}`}
                              className="rounded-md border border-border-subtle px-2.5 py-1 text-xs text-text-muted hover:bg-white/5 hover:text-text-primary disabled:opacity-50"
                            >
                              Revoke
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
