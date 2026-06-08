"use client"

/**
 * ComparePageNav -- left page switcher for the multi-building compare view.
 *
 * The single-building report section (/buildings/[id]/reports) uses ReportNav,
 * whose items are per-building deep-link routes. Compare has no single building
 * to route to, so this sibling drives the *same* embed in place: clicking a
 * page calls onSelect(pbiDisplayName); CompareReportShell feeds that to the
 * embed's `pageName` prop, which navigates via setActive(). Styling mirrors
 * ReportNav (w-56, accent highlight) so the two experiences feel identical.
 *
 * No module-lock here: compare is a portfolio view spanning buildings with
 * mixed modules, and every PBI page is shown (data simply thins out for
 * buildings lacking a given system). Pages come from the same REPORT_PAGES
 * manifest, so anything added there (e.g. Solar) appears here automatically.
 */
import {
  BatteryCharging,
  Building2,
  LayoutGrid,
  Leaf,
  Radio,
  Sun,
  TrendingUp,
  TriangleAlert,
  Users,
  Wind,
  type LucideIcon,
} from "lucide-react"

import { REPORT_PAGES } from "@/lib/config/reportPages"
import { cn } from "@/lib/utils"

/** iconKey (string in the manifest) -> lucide component. */
const ICONS: Record<string, LucideIcon> = {
  LayoutGrid,
  Building2,
  TriangleAlert,
  TrendingUp,
  Users,
  Leaf,
  Wind,
  Radio,
  BatteryCharging,
  Sun,
}

type ComparePageNavProps = {
  /** PBI displayName of the currently active page (from the embed's onPageChanged). */
  activePageName: string
  /** Navigate the shared embed to this page, by PBI displayName. */
  onSelect: (pbiDisplayName: string) => void
}

export function ComparePageNav({
  activePageName,
  onSelect,
}: ComparePageNavProps) {
  return (
    <nav
      aria-label="Report pages"
      className="hidden md:block w-56 shrink-0 h-full overflow-y-auto border-r border-border-subtle bg-bg-elevated/40 backdrop-blur-sm py-3"
    >
      <p className="px-4 pb-2 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
        Pages
      </p>
      <ul className="space-y-0.5 px-2">
        {REPORT_PAGES.map((page) => {
          const Icon = ICONS[page.iconKey] ?? LayoutGrid
          const isActive = page.pbiDisplayName === activePageName
          return (
            <li key={page.slug}>
              <button
                type="button"
                onClick={() => onSelect(page.pbiDisplayName)}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "group flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm transition-colors",
                  isActive
                    ? "text-text-primary"
                    : "text-text-muted hover:text-text-primary hover:bg-white/5"
                )}
                style={
                  isActive
                    ? {
                        backgroundColor: `${page.accent}1A`,
                        boxShadow: `inset 2px 0 0 ${page.accent}`,
                      }
                    : undefined
                }
              >
                <Icon
                  className="w-4 h-4 shrink-0 transition-colors"
                  style={{ color: isActive ? page.accent : undefined }}
                  aria-hidden
                />
                <span className="flex-1 truncate">{page.title}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
