"use client"

/**
 * NavClusters — clustered primary navigation (design audit P0-1, 2026-06-15).
 *
 * Collapses the former flat 9+ item bar into intent groups:
 *   Monitor · Act · Compliance · Copilot  (+ a small More for setup/relationship routes).
 * Single-item clusters render as a direct link; multi-item clusters as a dropdown.
 * Pending counts (open actions / unhandled alerts) surface on the cluster button so
 * triage stays glanceable without opening the menu. Routes are unchanged — pure IA.
 *
 * Exports DesktopNav (md+) and MobileNav (hamburger) used by AppChrome.
 */

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useRef, useState } from "react"
import { ChevronDown, Menu, X } from "lucide-react"

import { cn } from "@/lib/utils"

type Badge = "actions" | "alerts"
type NavItem = { href: string; label: string; badge?: Badge }
type Cluster = { id: string; label: string; items: NavItem[] }

const CLUSTERS: Cluster[] = [
  {
    id: "monitor",
    label: "Monitor",
    items: [
      { href: "/portfolio", label: "Portfolio" },
      { href: "/buildings", label: "Buildings" },
      { href: "/residential", label: "Residential" },
      { href: "/alerts", label: "Alerts", badge: "alerts" },
      { href: "/solar", label: "Solar" },
    ],
  },
  {
    id: "act",
    label: "Act",
    items: [
      { href: "/actions", label: "Actions", badge: "actions" },
      { href: "/decarbonisation", label: "Decarbonise" },
      { href: "/financing", label: "Financing" },
    ],
  },
  { id: "comply", label: "Compliance", items: [{ href: "/compliance", label: "Compliance" }] },
  { id: "assist", label: "Copilot", items: [{ href: "/copilot", label: "Copilot" }] },
  {
    id: "more",
    label: "More",
    items: [
      { href: "/connections", label: "Connections" },
      { href: "/partners", label: "Partners" },
    ],
  },
]

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(href + "/")
}

function Pill({ count, tone }: { count: number; tone: "amber" | "red" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-semibold tabular-nums border",
        tone === "red"
          ? "bg-red-500/20 text-red-200 border-red-500/40"
          : "bg-amber-500/20 text-amber-200 border-amber-500/40"
      )}
    >
      {count > 99 ? "99+" : count}
    </span>
  )
}

// ---------- desktop (md+) ----------

export function DesktopNav() {
  const openActions = useOpenActionsCount()
  const openAlerts = useOpenAlertsCount()
  return (
    <nav className="flex items-center gap-1" aria-label="Primary">
      {CLUSTERS.map((c) =>
        c.items.length === 1 ? (
          <DirectLink key={c.id} item={c.items[0]} />
        ) : (
          <ClusterMenu key={c.id} cluster={c} openActions={openActions} openAlerts={openAlerts} />
        )
      )}
    </nav>
  )
}

function DirectLink({ item }: { item: NavItem }) {
  const pathname = usePathname() ?? ""
  const active = isActive(pathname, item.href)
  return (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "px-3 py-1.5 rounded-md text-sm transition-colors",
        active
          ? "bg-brand-emerald/10 text-brand-emerald"
          : "text-text-muted hover:text-text-primary hover:bg-white/5"
      )}
    >
      {item.label}
    </Link>
  )
}

function ClusterMenu({
  cluster,
  openActions,
  openAlerts,
}: {
  cluster: Cluster
  openActions: number | null
  openAlerts: number | null
}) {
  const pathname = usePathname() ?? ""
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const activeHere = cluster.items.some((i) => isActive(pathname, i.href))
  const hasAlerts = cluster.items.some((i) => i.badge === "alerts")
  const hasActions = cluster.items.some((i) => i.badge === "actions")
  const pending = (hasAlerts ? openAlerts ?? 0 : 0) + (hasActions ? openActions ?? 0 : 0)
  const pendingTone: "red" | "amber" = hasAlerts ? "red" : "amber"

  useEffect(() => {
    if (!open) return
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onDoc)
    return () => document.removeEventListener("mousedown", onDoc)
  }, [open])

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
          activeHere
            ? "bg-brand-emerald/10 text-brand-emerald"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
      >
        <span>{cluster.label}</span>
        {pending > 0 && <Pill count={pending} tone={pendingTone} />}
        <ChevronDown
          size={14}
          aria-hidden
          className={cn("transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <div
          role="menu"
          className="absolute left-0 mt-1 w-52 rounded-md border border-border-subtle bg-bg-elevated py-1 shadow-[0_8px_24px_rgba(0,0,0,0.4)] z-50"
        >
          {cluster.items.map((i) => {
            const active = isActive(pathname, i.href)
            const badgeCount = i.badge === "alerts" ? openAlerts : i.badge === "actions" ? openActions : null
            return (
              <Link
                key={i.href}
                href={i.href}
                role="menuitem"
                onClick={() => setOpen(false)}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center justify-between gap-2 px-3 py-2 text-sm transition-colors",
                  active
                    ? "text-brand-emerald bg-brand-emerald/5"
                    : "text-text-muted hover:text-text-primary hover:bg-white/5"
                )}
              >
                <span>{i.label}</span>
                {i.badge && badgeCount !== null && badgeCount > 0 && (
                  <Pill count={badgeCount} tone={i.badge === "alerts" ? "red" : "amber"} />
                )}
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ---------- mobile (hamburger) ----------

export function MobileNav() {
  const pathname = usePathname() ?? ""
  const [open, setOpen] = useState(false)
  const openActions = useOpenActionsCount()
  const openAlerts = useOpenAlertsCount()

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  return (
    <div className="relative md:hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close menu" : "Open menu"}
        aria-expanded={open}
        className="inline-flex items-center justify-center w-9 h-9 rounded-md border border-border-subtle text-text-muted hover:border-brand-emerald hover:text-brand-emerald transition-colors"
      >
        {open ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" aria-hidden onClick={() => setOpen(false)} />
          <nav
            aria-label="Primary"
            className="absolute left-0 top-11 z-50 w-60 max-h-[80vh] overflow-y-auto rounded-lg border border-border-subtle bg-bg-elevated/95 backdrop-blur-sm p-2 shadow-xl"
          >
            {CLUSTERS.map((c) => (
              <div key={c.id} className="mb-1.5 last:mb-0">
                <div className="px-3 pt-1.5 pb-1 text-[10px] font-semibold uppercase tracking-wider text-text-faint">
                  {c.label}
                </div>
                {c.items.map((i) => {
                  const active = isActive(pathname, i.href)
                  const badgeCount = i.badge === "alerts" ? openAlerts : i.badge === "actions" ? openActions : null
                  return (
                    <Link
                      key={i.href}
                      href={i.href}
                      onClick={() => setOpen(false)}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                        active
                          ? "bg-brand-emerald/10 text-brand-emerald"
                          : "text-text-muted hover:text-text-primary hover:bg-white/5"
                      )}
                    >
                      <span>{i.label}</span>
                      {i.badge && badgeCount !== null && badgeCount > 0 && (
                        <Pill count={badgeCount} tone={i.badge === "alerts" ? "red" : "amber"} />
                      )}
                    </Link>
                  )
                })}
              </div>
            ))}
          </nav>
        </>
      )}
    </div>
  )
}

// ---------- badge hooks (open actions / unhandled alerts) ----------

function useOpenActionsCount(): number | null {
  const pathname = usePathname()
  const [count, setCount] = useState<number | null>(null)
  useEffect(() => {
    let cancelled = false
    fetch("/api/actions?status=open&limit=1", { method: "GET", headers: { Accept: "application/json" } })
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then((data: { status_counts?: { open?: number } }) => {
        if (cancelled) return
        const c = data?.status_counts?.open
        setCount(typeof c === "number" ? c : null)
      })
      .catch(() => {
        if (!cancelled) setCount(null)
      })
    return () => {
      cancelled = true
    }
  }, [pathname])
  return count
}

function useOpenAlertsCount(): number | null {
  const pathname = usePathname()
  const [count, setCount] = useState<number | null>(null)
  useEffect(() => {
    let cancelled = false
    fetch("/api/alerts?unresolved_only=true&limit=1", { method: "GET", headers: { Accept: "application/json" } })
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then((data: { severity_counts?: { unhandled_critical?: number; unhandled_high?: number } }) => {
        if (cancelled) return
        const sc = data?.severity_counts
        const crit = typeof sc?.unhandled_critical === "number" ? sc.unhandled_critical : 0
        const high = typeof sc?.unhandled_high === "number" ? sc.unhandled_high : 0
        setCount(crit + high)
      })
      .catch(() => {
        if (!cancelled) setCount(null)
      })
    return () => {
      cancelled = true
    }
  }, [pathname])
  return count
}
