/**
 * PartnerOverview — the consultant cockpit on /partners.
 *
 * One glance across ALL active clients: who carries the most EPBD/MEPS exposure
 * (EPC F/G), who has assessment gaps (missing EPC), and a quick drill into each
 * client's portfolio. Server-rendered (links only). Renders nothing for orgs
 * with no active clients, so ordinary customers never see it.
 *
 * Honest by design: this is a METADATA triage (EPC class), not a performance
 * claim — EUI/CRREM detail is one click away in the client's portfolio.
 */
import type { ReactNode } from "react"
import Link from "next/link"
import { AlertTriangle, Building2, FileQuestion, Users } from "lucide-react"

import type {
  PartnerClientOverviewRow,
  PartnerOverviewResponse,
} from "@/lib/api/partners"

function fmtArea(m2: number): string {
  if (m2 >= 1_000_000) return `${(m2 / 1_000_000).toFixed(1)}M m²`
  if (m2 >= 1_000) return `${(m2 / 1_000).toFixed(0)}k m²`
  return `${Math.round(m2)} m²`
}

function Stat({
  icon,
  label,
  value,
  tone = "default",
}: {
  icon: ReactNode
  label: string
  value: string
  tone?: "default" | "risk" | "warn"
}) {
  const valueColor =
    tone === "risk" ? "text-red-300" : tone === "warn" ? "text-amber-300" : "text-text-primary"
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-text-faint">
        {icon}
        {label}
      </div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${valueColor}`}>{value}</div>
    </div>
  )
}

function Cell({ n, tone }: { n: number; tone?: "risk" | "warn" }) {
  if (n === 0) return <span className="text-text-faint">—</span>
  const c = tone === "risk" ? "text-red-300" : tone === "warn" ? "text-amber-300" : "text-text-primary"
  return <span className={`tabular-nums ${c}`}>{n}</span>
}

export function PartnerOverview({ overview }: { overview: PartnerOverviewResponse }) {
  const { clients, totals } = overview
  if (clients.length === 0) return null

  return (
    <section className="mb-8 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-text-primary">Client portfolio overview</h2>
        <p className="text-xs text-text-muted">
          EPBD/MEPS triage across your active clients — most attention first. EPC F/G are the
          renovation-priority bands (G by 2030, F by 2033); a missing EPC is an assessment gap.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat icon={<Users className="h-3 w-3" />} label="Clients" value={String(totals.client_count)} />
        <Stat icon={<Building2 className="h-3 w-3" />} label="Buildings" value={String(totals.building_count)} />
        <Stat
          icon={<AlertTriangle className="h-3 w-3" />}
          label="EPC F/G"
          value={String(totals.epc_high_risk)}
          tone="risk"
        />
        <Stat
          icon={<FileQuestion className="h-3 w-3" />}
          label="EPC missing"
          value={String(totals.epc_missing)}
          tone="warn"
        />
      </div>

      <div className="overflow-x-auto rounded-lg border border-border-subtle">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-text-muted">
            <tr className="border-b border-border-subtle">
              <th className="px-3 py-2 font-medium">Client</th>
              <th className="px-3 py-2 font-medium">Scope</th>
              <th className="px-3 py-2 text-right font-medium">Buildings</th>
              <th className="px-3 py-2 text-right font-medium">Area</th>
              <th className="px-3 py-2 text-right font-medium">EPC F/G</th>
              <th className="px-3 py-2 text-right font-medium">Missing</th>
              <th className="px-3 py-2 text-right font-medium">On track</th>
              <th className="px-3 py-2 text-right font-medium"> </th>
            </tr>
          </thead>
          <tbody>
            {clients.map((c: PartnerClientOverviewRow) => (
              <tr key={c.organization_id} className="border-b border-border-subtle/60">
                <td className="px-3 py-2">
                  <div className="text-text-primary">{c.name}</div>
                  {c.attention > 0 && (
                    <div className="text-[11px] text-amber-300">{c.attention} need attention</div>
                  )}
                </td>
                <td className="px-3 py-2 text-text-muted">
                  {c.scope === "full_manage" ? "Full manage" : "Read only"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-text-primary">{c.building_count}</td>
                <td className="px-3 py-2 text-right text-text-muted">{fmtArea(c.total_area_m2)}</td>
                <td className="px-3 py-2 text-right"><Cell n={c.epc_high_risk} tone="risk" /></td>
                <td className="px-3 py-2 text-right"><Cell n={c.epc_missing} tone="warn" /></td>
                <td className="px-3 py-2 text-right"><Cell n={c.epc_on_track} /></td>
                <td className="px-3 py-2 text-right">
                  <Link
                    href={`/portfolio?client=${encodeURIComponent(c.organization_id)}`}
                    className="text-brand-emerald hover:underline"
                  >
                    Open
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
