"use client"

/**
 * AppChrome -- shared top bar + page shell for authenticated routes.
 *
 * Top bar: LogoCard (left) + primary nav + breadcrumb/title + user menu (right).
 * Children render below in a flex-1 main area.
 * Client component: needs useSession() + signOut().
 */

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useSession } from "next-auth/react"
import { useEffect, useState } from "react"
import { ArrowLeft, ChevronRight, Menu, Search, X } from "lucide-react"

import { AccountMenu } from "@/components/AccountMenu"
import { CommandPalette } from "@/components/CommandPalette"
import { LogoCard } from "@/app/components/LogoCard"
import { NavMore } from "@/components/NavMore"
import { TourReturnButton } from "@/components/tour/TourReturnButton"
import { cn } from "@/lib/utils"

export type BreadcrumbItem = {
  label: string
  href?: string
}

type AppChromeProps = {
  breadcrumb: BreadcrumbItem[]
  pageTitle: string | null
  subtitle?: string
  backHref?: string
  backLabel?: string
  accentColor?: string
  children: React.ReactNode
}

export function AppChrome({
  breadcrumb,
  pageTitle,
  subtitle,
  backHref,
  backLabel = "Back",
  accentColor,
  children,
}: AppChromeProps) {
  const { data: session } = useSession()
  const email = session?.user?.email

  return (
    <div className="relative min-h-screen flex flex-col bg-bg-base bg-radial-emerald-glow">
      <TourReturnButton />
      <CommandPalette />
      <div className="absolute inset-0 bg-dot-grid pointer-events-none" aria-hidden />
      {accentColor && (
        <div
          className="absolute inset-0 pointer-events-none transition-all duration-700"
          aria-hidden
          style={{
            background: `radial-gradient(circle at 50% 0%, ${accentColor}1A 0%, transparent 45%)`,
          }}
        />
      )}
      <header className="sticky top-0 z-40 border-b border-border-subtle bg-bg-elevated/80 backdrop-blur-md">
        {/* Row 1 — brand + primary nav + account */}
        <div className="px-4 md:px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 md:gap-6 min-w-0">
            <LogoCard iconSize={72} className="shrink-0" />
            <MobileNav />
            <div className="hidden md:block min-w-0 overflow-x-auto">
              <PrimaryNav />
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => window.dispatchEvent(new Event("el:open-command"))}
              aria-label="Search (Ctrl/Cmd K)"
              title="Quick jump (Ctrl/Cmd + K)"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-md border border-border-subtle px-2.5 h-9 text-text-muted hover:border-brand-emerald hover:text-brand-emerald transition-colors"
            >
              <Search className="w-4 h-4" />
              <kbd className="text-[10px] text-text-faint">⌘K</kbd>
            </button>
            <AccountMenu email={email} />
          </div>
        </div>

        {/* Row 2 — context: back + breadcrumb + page title (room to breathe) */}
        {(backHref || (breadcrumb && breadcrumb.length > 0) || pageTitle !== null) && (
          <div className="border-t border-border-subtle/60 px-4 md:px-6 py-2.5 flex items-center gap-3 md:gap-4">
            {backHref && (
              <Link
                href={backHref}
                aria-label={backLabel}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border-subtle text-text-muted hover:border-brand-emerald hover:text-brand-emerald hover:bg-brand-emerald/5 transition-colors shrink-0"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span className="text-sm hidden sm:inline">{backLabel}</span>
              </Link>
            )}
            <div className="min-w-0">
              <Breadcrumb items={breadcrumb} />
              {pageTitle !== null && (
                <div className="flex items-center gap-2 mt-0.5">
                  {accentColor && (
                    <span className="relative inline-flex shrink-0 w-2 h-2" aria-hidden>
                      <span
                        className="absolute inset-0 rounded-full opacity-60 animate-ping"
                        style={{ backgroundColor: accentColor }}
                      />
                      <span
                        className="relative w-2 h-2 rounded-full"
                        style={{ backgroundColor: accentColor }}
                      />
                    </span>
                  )}
                  <h1 className="font-display text-xl font-semibold text-text-primary truncate">
                    {pageTitle}
                  </h1>
                  {subtitle && (
                    <span className="text-xs text-text-muted truncate hidden md:inline">· {subtitle}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      <main id="main-content" className="flex-1 relative">{children}</main>
    </div>
  )
}

function MobileNav() {
  const pathname = usePathname() ?? ""
  const [open, setOpen] = useState(false)
  const openActions = useOpenActionsCount()
  const openAlerts = useOpenAlertsCount()

  const items: {
    href: string
    label: string
    active: boolean
    badge: number | null
    badgeClass: string
  }[] = [
    { href: "/portfolio", label: "Portfolio", active: pathname.startsWith("/portfolio"), badge: null, badgeClass: "" },
    { href: "/buildings", label: "Buildings", active: pathname.startsWith("/buildings"), badge: null, badgeClass: "" },
    { href: "/residential", label: "Residential", active: pathname === "/residential" || pathname.startsWith("/residential/"), badge: null, badgeClass: "" },
    { href: "/connections", label: "Connections", active: pathname.startsWith("/connections"), badge: null, badgeClass: "" },
    { href: "/actions", label: "Actions", active: pathname.startsWith("/actions"), badge: openActions, badgeClass: "bg-amber-500/20 text-amber-200 border-amber-500/40" },
    { href: "/alerts", label: "Alerts", active: pathname.startsWith("/alerts"), badge: openAlerts, badgeClass: "bg-red-500/20 text-red-200 border-red-500/40" },
    { href: "/compliance", label: "Compliance", active: pathname.startsWith("/compliance"), badge: null, badgeClass: "" },
    { href: "/decarbonisation", label: "Decarbonise", active: pathname.startsWith("/decarbonisation"), badge: null, badgeClass: "" },
    { href: "/financing", label: "Financing", active: pathname.startsWith("/financing"), badge: null, badgeClass: "" },
    { href: "/copilot", label: "Copilot", active: pathname.startsWith("/copilot"), badge: null, badgeClass: "" },
    { href: "/solar", label: "Solar", active: pathname.startsWith("/solar"), badge: null, badgeClass: "" },
    { href: "/partners", label: "Partners", active: pathname.startsWith("/partners"), badge: null, badgeClass: "" },
  ]

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
            className="absolute left-0 top-11 z-50 w-52 rounded-lg border border-border-subtle bg-bg-elevated/95 backdrop-blur-sm p-1.5 shadow-xl"
          >
            {items.map((it) => (
              <Link
                key={it.href}
                href={it.href}
                onClick={() => setOpen(false)}
                aria-current={it.active ? "page" : undefined}
                className={cn(
                  "flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                  it.active
                    ? "bg-brand-emerald/10 text-brand-emerald"
                    : "text-text-muted hover:text-text-primary hover:bg-white/5"
                )}
              >
                <span>{it.label}</span>
                {it.badge !== null && it.badge > 0 && (
                  <span
                    className={cn(
                      "inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-semibold tabular-nums border",
                      it.badgeClass
                    )}
                  >
                    {it.badge > 99 ? "99+" : it.badge}
                  </span>
                )}
              </Link>
            ))}
          </nav>
        </>
      )}
    </div>
  )
}


function PrimaryNav() {
  const pathname = usePathname() ?? ""
  const isBuildings = pathname.startsWith("/buildings")
  const isResidential = pathname === "/residential" || pathname.startsWith("/residential/")
  const isPortfolio = pathname.startsWith("/portfolio")
  const isCopilot = pathname.startsWith("/copilot")
  const isActions = pathname.startsWith("/actions")
  const isSolar = pathname.startsWith("/solar")
  const isCompliance = pathname.startsWith("/compliance")
  const isDecarb = pathname.startsWith("/decarbonisation")
  const openActions = useOpenActionsCount()
  const isAlerts = pathname.startsWith("/alerts")
  const openAlerts = useOpenAlertsCount()

  return (
    <nav className="flex items-center gap-1" aria-label="Primary">
      <Link
        href="/portfolio"
        aria-current={isPortfolio ? "page" : undefined}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isPortfolio
            ? "bg-brand-emerald/10 text-brand-emerald"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
      >
        Portfolio
      </Link>
      <Link
        href="/buildings"
        aria-current={isBuildings ? "page" : undefined}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isBuildings
            ? "bg-brand-emerald/10 text-brand-emerald"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
      >
        Buildings
      </Link>
      <Link
        href="/residential"
        aria-current={isResidential ? "page" : undefined}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isResidential
            ? "bg-brand-emerald/10 text-brand-emerald"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
      >
        Residential
      </Link>
      <Link
        href="/actions"
        aria-current={isActions ? "page" : undefined}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
          isActions
            ? "bg-brand-emerald/10 text-brand-emerald"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
      >
        <span>Actions</span>
        {openActions !== null && openActions > 0 && (
          <span
            className={cn(
              "inline-flex items-center justify-center min-w-[18px] h-[18px]",
              "px-1 rounded-full text-[10px] font-semibold tabular-nums",
              "bg-amber-500/20 text-amber-200 border border-amber-500/40"
            )}
            aria-label={`${openActions} open recommendations`}
          >
            {openActions > 99 ? "99+" : openActions}
          </span>
        )}
      </Link>
      <Link
        href="/alerts"
        aria-current={isAlerts ? "page" : undefined}
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors",
          isAlerts
            ? "text-orange-300"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
        style={isAlerts ? { backgroundColor: "rgba(249, 115, 22, 0.12)" } : undefined}
      >
        <span>Alerts</span>
        {openAlerts !== null && openAlerts > 0 && (
          <span
            className={cn(
              "inline-flex items-center justify-center min-w-[18px] h-[18px]",
              "px-1 rounded-full text-[10px] font-semibold tabular-nums",
              "bg-red-500/20 text-red-200 border border-red-500/40"
            )}
            aria-label={`${openAlerts} unhandled critical or high alerts`}
          >
            {openAlerts > 99 ? "99+" : openAlerts}
          </span>
        )}
      </Link>
      <Link
        href="/compliance"
        aria-current={isCompliance ? "page" : undefined}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isCompliance
            ? "text-teal-300"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
        style={isCompliance ? { backgroundColor: "rgba(13, 148, 136, 0.14)" } : undefined}
      >
        Compliance
      </Link>
      <Link
        href="/decarbonisation"
        aria-current={isDecarb ? "page" : undefined}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isDecarb
            ? "bg-brand-emerald/10 text-brand-emerald"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
      >
        Decarbonise
      </Link>
      <Link
        href="/copilot"
        aria-current={isCopilot ? "page" : undefined}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isCopilot
            ? "text-white"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
        style={isCopilot ? { backgroundColor: "rgba(123, 91, 214, 0.15)", color: "#B499F0" } : undefined}
      >
        Copilot
      </Link>
      <Link
        href="/solar"
        aria-current={isSolar ? "page" : undefined}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm transition-colors",
          isSolar
            ? "text-amber-300"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
        style={isSolar ? { backgroundColor: "rgba(245, 158, 11, 0.12)" } : undefined}
      >
        Solar
      </Link>
      <NavMore />
    </nav>
  )
}

function useOpenActionsCount(): number | null {
  const pathname = usePathname()
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch("/api/actions?status=open&limit=1", {
      method: "GET",
      headers: { Accept: "application/json" },
    })
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
    fetch("/api/alerts?unresolved_only=true&limit=1", {
      method: "GET",
      headers: { Accept: "application/json" },
    })
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then(
        (data: {
          severity_counts?: { unhandled_critical?: number; unhandled_high?: number }
        }) => {
          if (cancelled) return
          const sc = data?.severity_counts
          const crit = typeof sc?.unhandled_critical === "number" ? sc.unhandled_critical : 0
          const high = typeof sc?.unhandled_high === "number" ? sc.unhandled_high : 0
          setCount(crit + high)
        }
      )
      .catch(() => {
        if (!cancelled) setCount(null)
      })
    return () => {
      cancelled = true
    }
  }, [pathname])

  return count
}


function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  if (items.length === 0) return null

  return (
    <nav aria-label="Breadcrumb" className="text-xs text-text-muted">
      <ol className="flex items-center gap-1 flex-wrap">
        {items.map((item, i) => {
          const isLast = i === items.length - 1
          return (
            <li key={`${item.label}-${i}`} className="flex items-center gap-1">
              {item.href && !isLast ? (
                <Link href={item.href} className="hover:text-brand-emerald transition-colors">
                  {item.label}
                </Link>
              ) : (
                <span className={isLast ? "text-text-primary" : ""}>{item.label}</span>
              )}
              {!isLast && (
                <ChevronRight className="w-3 h-3 text-text-faint" aria-hidden />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
