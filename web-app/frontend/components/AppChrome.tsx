"use client"

/**
 * AppChrome -- shared top bar + page shell for authenticated routes.
 *
 * Top bar: LogoCard (left) + clustered primary nav + breadcrumb/title + user menu (right).
 * Nav lives in NavClusters (design audit P0-1). Children render below in a flex-1 main area.
 * Client component: needs useSession().
 */

import Link from "next/link"
import { useSession } from "next-auth/react"
import { ArrowLeft, ChevronRight, Search } from "lucide-react"

import { AccountMenu } from "@/components/AccountMenu"
import { CommandPalette } from "@/components/CommandPalette"
import { LogoCard } from "@/app/components/LogoCard"
import { DesktopNav, MobileNav } from "@/components/NavClusters"
import { TourReturnButton } from "@/components/tour/TourReturnButton"

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
              <DesktopNav />
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
