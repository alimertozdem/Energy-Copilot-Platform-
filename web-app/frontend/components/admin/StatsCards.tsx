/**
 * StatsCards -- headline platform counts for the admin dashboard.
 *
 * Server component. Four cards derived from PlatformStats: organizations,
 * users, buildings, and enabled premium modules. Each shows a primary count
 * plus a secondary breakdown.
 */
import { Boxes, Building2, Radio, Users } from "lucide-react"

import type { PlatformStats } from "@/lib/api/admin"

type StatsCardsProps = {
  stats: PlatformStats
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      icon: Boxes,
      label: "Organizations",
      value: stats.organizations_total,
      sub: `${stats.organizations_sample} sample`,
      accent: "#7B5BD6",
    },
    {
      icon: Users,
      label: "Users",
      value: stats.users_total,
      sub: `${stats.users_demo} demo`,
      accent: "#06B6D4",
    },
    {
      icon: Building2,
      label: "Buildings",
      value: stats.buildings_total,
      sub: `${stats.buildings_connected} connected to Fabric`,
      accent: "#1D9E75",
    },
    {
      icon: Radio,
      label: "Premium modules",
      value: stats.iot_enabled + stats.battery_enabled,
      sub: `${stats.iot_enabled} IoT · ${stats.battery_enabled} battery`,
      accent: "#3B82F6",
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => {
        const Icon = c.icon
        return (
          <div
            key={c.label}
            className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-4"
          >
            <div className="flex items-center gap-2">
              <span
                className="inline-flex h-8 w-8 items-center justify-center rounded-lg"
                style={{ backgroundColor: `${c.accent}1A`, color: c.accent }}
              >
                <Icon className="h-4 w-4" aria-hidden />
              </span>
              <span className="text-xs font-medium uppercase tracking-wide text-text-muted">
                {c.label}
              </span>
            </div>
            <div className="mt-3 text-3xl font-semibold tabular-nums text-text-primary">
              {c.value.toLocaleString("en-US")}
            </div>
            <div className="mt-0.5 text-xs text-text-muted">{c.sub}</div>
          </div>
        )
      })}
    </div>
  )
}
