"use client"

/**
 * OrganizationsTable -- every org with interactive subscription controls.
 *   * tier   select (free / basic / monitor / enterprise)
 *   * status select (active / past_due / canceled)
 * Member + building counts stay read-only. Each change hits the
 * /api/admin/organizations/[id] proxy then router.refresh() re-reads the table.
 */
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"

import { fmtDate } from "@/components/admin/adminFormat"
import type { AdminOrgRow } from "@/lib/api/admin"
import { updateOrgSubscription } from "@/lib/api/adminMutations"

const TIERS = ["free", "basic", "monitor", "enterprise"] as const
const STATUSES = ["active", "past_due", "canceled"] as const

const SELECT_CLASS =
  "h-7 rounded-lg border border-input bg-bg-elevated px-2 text-xs capitalize text-text-primary outline-none focus-visible:border-ring disabled:opacity-50"

type OrganizationsTableProps = {
  organizations: AdminOrgRow[]
}

export function OrganizationsTable({ organizations }: OrganizationsTableProps) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60">
      <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
        <h2 className="text-sm font-semibold text-text-primary">Organizations</h2>
        <span className="text-xs text-text-muted">{organizations.length} total</span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-text-muted">
              <th className="px-5 py-2 font-medium">Name</th>
              <th className="px-3 py-2 font-medium">Tier</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Country</th>
              <th className="px-3 py-2 font-medium text-right">Members</th>
              <th className="px-3 py-2 font-medium text-right">Buildings</th>
              <th className="px-5 py-2 font-medium text-right">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {organizations.map((o) => (
              <OrgRow key={o.id} org={o} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function OrgRow({ org }: { org: AdminOrgRow }) {
  const router = useRouter()
  const [refreshing, startTransition] = useTransition()
  const [busy, setBusy] = useState<null | "tier" | "status">(null)
  const [error, setError] = useState<string | null>(null)

  const anyBusy = refreshing || busy !== null

  async function change(
    field: "tier" | "status",
    body: { subscription_tier?: string; subscription_status?: string }
  ) {
    setError(null)
    setBusy(field)
    const res = await updateOrgSubscription(org.id, body)
    setBusy(null)
    if (!res.ok) {
      setError(res.error)
      return
    }
    startTransition(() => router.refresh())
  }

  return (
    <>
      <tr className="hover:bg-white/5">
        <td className="px-5 py-2.5">
          <div className="flex items-center gap-2">
            <span className="text-text-primary">{org.name}</span>
            {org.is_sample && (
              <span className="rounded-full border border-border-subtle bg-white/5 px-1.5 py-0.5 text-[10px] font-medium text-text-muted">
                sample
              </span>
            )}
          </div>
          <div className="text-xs text-text-faint">{org.slug}</div>
        </td>
        <td className="px-3 py-2.5">
          <div className="flex items-center gap-1.5">
            <select
              value={org.subscription_tier}
              disabled={anyBusy}
              onChange={(e) =>
                change("tier", { subscription_tier: e.target.value })
              }
              aria-label={`Tier for ${org.name}`}
              className={SELECT_CLASS}
            >
              {TIERS.map((t) => (
                <option key={t} value={t} className="capitalize">
                  {t}
                </option>
              ))}
            </select>
            {busy === "tier" && (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-text-muted" />
            )}
          </div>
        </td>
        <td className="px-3 py-2.5">
          <div className="flex items-center gap-1.5">
            <select
              value={org.subscription_status}
              disabled={anyBusy}
              onChange={(e) =>
                change("status", { subscription_status: e.target.value })
              }
              aria-label={`Status for ${org.name}`}
              className={SELECT_CLASS}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s} className="capitalize">
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
            {busy === "status" && (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-text-muted" />
            )}
          </div>
        </td>
        <td className="px-3 py-2.5 text-text-muted">{org.country_code ?? "—"}</td>
        <td className="px-3 py-2.5 text-right tabular-nums text-text-primary">
          {org.member_count}
        </td>
        <td className="px-3 py-2.5 text-right tabular-nums text-text-primary">
          {org.building_count}
        </td>
        <td className="px-5 py-2.5 text-right text-text-muted">
          {fmtDate(org.created_at)}
        </td>
      </tr>
      {error && (
        <tr>
          <td colSpan={7} className="px-5 pb-2 text-xs text-accent-red">
            {error}
          </td>
        </tr>
      )}
    </>
  )
}
