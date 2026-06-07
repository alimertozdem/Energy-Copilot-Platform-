/** Shared formatting helpers + badge palettes for the admin tables. */

export function fmtDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export const TIER_BADGE: Record<string, string> = {
  free: "bg-white/5 text-text-muted border-border-subtle",
  basic: "bg-sky-500/10 text-sky-300 border-sky-500/30",
  monitor: "bg-brand-emerald/10 text-brand-emerald border-brand-emerald/30",
  enterprise: "bg-violet-500/10 text-violet-300 border-violet-500/30",
}

export const STATUS_BADGE: Record<string, string> = {
  active: "bg-brand-emerald/10 text-brand-emerald border-brand-emerald/30",
  past_due: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  canceled: "bg-accent-red/10 text-accent-red border-accent-red/30",
}
