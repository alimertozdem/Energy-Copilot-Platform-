/**
 * ActivityTable -- recent admin actions (audit log, admin.* events), newest
 * first. Server component, read-only. Each row is one AuditLog entry written by
 * a /admin mutation.
 */
import type { AdminAuditRow } from "@/lib/api/admin"

const ACTION_LABEL: Record<string, string> = {
  "admin.org.subscription_updated": "Subscription updated",
  "admin.building.module_updated": "Module updated",
  "admin.building.fabric_linked": "Fabric link updated",
}

function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function fmtDetails(details: Record<string, unknown> | null): string {
  if (!details || Object.keys(details).length === 0) return "—"
  return Object.entries(details)
    .map(([k, v]) => `${k}: ${v === null ? "—" : String(v)}`)
    .join(" · ")
}

type ActivityTableProps = {
  events: AdminAuditRow[]
}

export function ActivityTable({ events }: ActivityTableProps) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60">
      <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
        <h2 className="text-sm font-semibold text-text-primary">Activity</h2>
        <span className="text-xs text-text-muted">
          {events.length === 0 ? "no recent actions" : `last ${events.length}`}
        </span>
      </header>
      {events.length === 0 ? (
        <p className="px-5 py-6 text-sm text-text-muted">
          Admin actions (tier changes, module toggles, fabric links) will appear
          here.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted">
                <th className="px-5 py-2 font-medium">When</th>
                <th className="px-3 py-2 font-medium">Actor</th>
                <th className="px-3 py-2 font-medium">Action</th>
                <th className="px-3 py-2 font-medium">Target</th>
                <th className="px-5 py-2 font-medium">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {events.map((e) => (
                <tr key={e.id} className="hover:bg-white/5">
                  <td className="px-5 py-2.5 whitespace-nowrap text-text-muted">
                    {fmtDateTime(e.created_at)}
                  </td>
                  <td className="px-3 py-2.5 text-text-muted">
                    {e.actor_email ?? "—"}
                  </td>
                  <td className="px-3 py-2.5 text-text-primary">
                    {ACTION_LABEL[e.action] ?? e.action}
                  </td>
                  <td className="px-3 py-2.5 text-text-muted">
                    {e.entity_type ?? "—"}
                    {e.entity_id ? (
                      <span className="text-text-faint">
                        {" · "}
                        {e.entity_id.slice(0, 8)}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-5 py-2.5 text-text-muted">
                    {fmtDetails(e.details)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
