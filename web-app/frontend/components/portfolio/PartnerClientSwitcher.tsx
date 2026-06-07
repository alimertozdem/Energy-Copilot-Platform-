"use client"

/**
 * PartnerClientSwitcher -- shown on /portfolio for partner (consultant) users.
 *
 * Lists the partner's active client orgs; selecting one scopes the portfolio
 * (KPIs + table) to that client via ?client=<org_id>. Renders nothing for
 * non-partner users (empty client list), so it's invisible to normal customers.
 */
import { useRouter } from "next/navigation"

import type { PartnerClientRow } from "@/lib/api/partners"

export function PartnerClientSwitcher({
  clients,
  active,
}: {
  clients: PartnerClientRow[]
  active: string | null
}) {
  const router = useRouter()
  if (clients.length === 0) return null

  return (
    <div className="mr-auto flex items-center gap-2 text-sm">
      <span className="text-text-muted">Client</span>
      <select
        value={active ?? ""}
        onChange={(e) => {
          const v = e.target.value
          router.push(v ? `/portfolio?client=${encodeURIComponent(v)}` : "/portfolio")
        }}
        className="rounded-md border border-border-subtle bg-transparent px-3 py-1.5 text-sm text-text-primary focus:border-brand-emerald focus:outline-none"
        aria-label="Filter portfolio by client"
      >
        <option value="">All clients</option>
        {clients.map((c) => (
          <option key={c.organization_id} value={c.organization_id}>
            {c.name}
          </option>
        ))}
      </select>
    </div>
  )
}
