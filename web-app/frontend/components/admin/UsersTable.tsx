/**
 * UsersTable -- every platform user with linked auth providers, org count and
 * status flags (admin / demo / inactive). Server component, read-only.
 */
import { fmtDate } from "@/components/admin/adminFormat"
import type { AdminUserRow } from "@/lib/api/admin"
import { cn } from "@/lib/utils"

const PROVIDER_BADGE: Record<string, string> = {
  microsoft: "bg-sky-500/10 text-sky-300 border-sky-500/30",
  google: "bg-rose-500/10 text-rose-300 border-rose-500/30",
  email: "bg-white/5 text-text-muted border-border-subtle",
}

type UsersTableProps = {
  users: AdminUserRow[]
}

export function UsersTable({ users }: UsersTableProps) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60">
      <header className="flex items-center justify-between border-b border-border-subtle px-5 py-3">
        <h2 className="text-sm font-semibold text-text-primary">Users</h2>
        <span className="text-xs text-text-muted">{users.length} total</span>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-text-muted">
              <th className="px-5 py-2 font-medium">User</th>
              <th className="px-3 py-2 font-medium">Providers</th>
              <th className="px-3 py-2 font-medium text-right">Orgs</th>
              <th className="px-3 py-2 font-medium">Flags</th>
              <th className="px-3 py-2 font-medium text-right">Last login</th>
              <th className="px-5 py-2 font-medium text-right">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-white/5">
                <td className="px-5 py-2.5">
                  <div className="text-text-primary">
                    {u.display_name || u.email}
                  </div>
                  {u.display_name && (
                    <div className="text-xs text-text-faint">{u.email}</div>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {u.providers.length === 0 ? (
                      <span className="text-text-faint">—</span>
                    ) : (
                      u.providers.map((p) => (
                        <span
                          key={p}
                          className={cn(
                            "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize",
                            PROVIDER_BADGE[p] ??
                              "bg-white/5 text-text-muted border-border-subtle"
                          )}
                        >
                          {p}
                        </span>
                      ))
                    )}
                  </div>
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-text-primary">
                  {u.org_count}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {u.is_platform_admin && (
                      <span className="inline-flex items-center rounded-full border border-violet-500/30 bg-violet-500/10 px-2 py-0.5 text-[11px] font-medium text-violet-300">
                        admin
                      </span>
                    )}
                    {u.is_demo && (
                      <span className="inline-flex items-center rounded-full border border-border-subtle bg-white/5 px-2 py-0.5 text-[11px] font-medium text-text-muted">
                        demo
                      </span>
                    )}
                    {!u.is_active && (
                      <span className="inline-flex items-center rounded-full border border-accent-red/30 bg-accent-red/10 px-2 py-0.5 text-[11px] font-medium text-accent-red">
                        inactive
                      </span>
                    )}
                    {!u.is_platform_admin && !u.is_demo && u.is_active && (
                      <span className="text-text-faint">—</span>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2.5 text-right text-text-muted">
                  {u.last_login_at ? fmtDate(u.last_login_at) : "Never"}
                </td>
                <td className="px-5 py-2.5 text-right text-text-muted">
                  {fmtDate(u.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
