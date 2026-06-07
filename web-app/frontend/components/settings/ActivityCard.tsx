/**
 * ActivityCard -- recent organization activity (audit log) for /settings.
 * Admin-only (rendered inside SettingsShell's canManage block). Read-only list.
 */
import type { SettingsActivityRow } from "@/lib/api/settings"

const ACTION_LABEL: Record<string, string> = {
  "org.profile_updated": "Profile updated",
  "org_member.invited": "Member invited",
  "org_member.role_changed": "Role changed",
  "org_member.removed": "Member removed",
  "org_member.invite_revoked": "Invite revoked",
  "org_member.joined": "Member joined",
  "building.created": "Building added",
  "recommendation.status_changed": "Recommendation updated",
  "alert.status_changed": "Alert updated",
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
  if (!details || Object.keys(details).length === 0) return ""
  return Object.entries(details)
    .map(([k, v]) => `${k}: ${v === null ? "—" : String(v)}`)
    .join(" · ")
}

export function ActivityCard({ events }: { events: SettingsActivityRow[] }) {
  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-5">
      <header className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Activity</h2>
        <span className="text-xs text-text-muted">
          {events.length === 0 ? "no recent activity" : `last ${events.length}`}
        </span>
      </header>
      {events.length === 0 ? (
        <p className="py-3 text-sm text-text-muted">
          Member and organization changes will be logged here.
        </p>
      ) : (
        <ul className="divide-y divide-border-subtle">
          {events.map((e) => {
            const detail = fmtDetails(e.details)
            return (
              <li
                key={e.id}
                className="flex items-baseline justify-between gap-3 py-2.5"
              >
                <div className="min-w-0">
                  <div className="text-sm text-text-primary">
                    {ACTION_LABEL[e.action] ?? e.action}
                  </div>
                  <div className="truncate text-xs text-text-muted">
                    {e.actor_email ?? "—"}
                    {detail ? ` · ${detail}` : ""}
                  </div>
                </div>
                <span className="shrink-0 whitespace-nowrap text-xs text-text-faint">
                  {fmtDateTime(e.created_at)}
                </span>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
