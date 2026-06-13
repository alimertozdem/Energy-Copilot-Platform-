"use client"

/**
 * ReportNav -- left sub-nav for a building's report section.
 *
 * Lists the 10 Power BI report pages as deep-link routes
 * (/buildings/[fabric_building_id]/reports/[slug]). The active page is
 * highlighted with its accent colour (kept in sync with pageAccents.ts).
 *
 * Module gating: pages whose required module is not enabled for this building
 * show a lock badge. They stay clickable -- the per-page route renders a
 * LockedReportPreview with an upgrade CTA (the SaaS upsell pattern; see
 * frontend_architecture "Module Unlock UX"). Page visibility is enforced at
 * the web-app layer, not Power BI RLS.
 */
import Link from "next/link"
import {
  BatteryCharging,
  Building2,
  FileDown,
  Home,
  LayoutGrid,
  Leaf,
  Lock,
  Radio,
  Sun,
  TrendingUp,
  TriangleAlert,
  Users,
  Wind,
  type LucideIcon,
} from "lucide-react"

import type { Building } from "@/lib/api/buildings"
import { REPORT_PAGES, isPageLocked } from "@/lib/config/reportPages"
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

type ReportNavProps = {
  fabricBuildingId: string
  building: Pick<Building, "modules" | "building_type">
  activeSlug: string
}

export function ReportNav({
  fabricBuildingId,
  building,
  activeSlug,
}: ReportNavProps) {
  return (
    <nav
      aria-label="Report pages"
      className="w-56 shrink-0 h-full overflow-y-auto border-r border-border-subtle bg-bg-elevated/40 backdrop-blur-sm py-3"
    >
      <p className="px-4 pb-2 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
        Reports
      </p>
      <ul className="space-y-0.5 px-2">
        {REPORT_PAGES.map((page) => {
          const Icon = ICONS[page.iconKey] ?? LayoutGrid
          const locked = isPageLocked(building, page)
          const isActive = page.slug === activeSlug
          return (
            <li key={page.slug}>
              <Link
                href={`/buildings/${encodeURIComponent(
                  fabricBuildingId
                )}/reports/${page.slug}`}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
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
                {locked && (
                  <Lock
                    className="w-3.5 h-3.5 shrink-0 text-text-faint group-hover:text-amber-300"
                    aria-label="Locked -- upgrade required"
                  />
                )}
              </Link>
            </li>
          )
        })}
      </ul>

      {building.building_type?.toLowerCase().includes("residential") && (
        <div className="mt-3 border-t border-border-subtle pt-3 px-2">
          <p className="px-2.5 pb-1 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
            Residential
          </p>
          <Link
            href={`/buildings/${encodeURIComponent(fabricBuildingId)}/residential`}
            className="group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors"
          >
            <Home className="w-4 h-4 shrink-0" style={{ color: "#10b981" }} aria-hidden />
            <span className="flex-1 truncate">Units &amp; UVI</span>
          </Link>
        </div>
      )}

      <div className="mt-3 border-t border-border-subtle pt-3 px-2">
        <p className="px-2.5 pb-1 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
          Monitoring
        </p>
        <Link
          href={`/alerts?building_id=${encodeURIComponent(fabricBuildingId)}`}
          className="group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors"
        >
          <TriangleAlert
            className="w-4 h-4 shrink-0"
            style={{ color: "#F97316" }}
            aria-hidden
          />
          <span className="flex-1 truncate">Alerts</span>
        </Link>
      </div>

      <div className="mt-3 border-t border-border-subtle pt-3 px-2">
        <p className="px-2.5 pb-1 text-[11px] font-semibold uppercase tracking-wider text-text-faint">
          Documents
        </p>
        <Link
          href={`/buildings/${encodeURIComponent(fabricBuildingId)}/report`}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors"
        >
          <FileDown
            className="w-4 h-4 shrink-0"
            style={{ color: "#1D9E75" }}
            aria-hidden
          />
          <span className="flex-1 truncate">Export PDF</span>
        </Link>
        <Link
          href={`/buildings/${encodeURIComponent(fabricBuildingId)}/co2-report`}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors"
        >
          <Leaf
            className="w-4 h-4 shrink-0"
            style={{ color: "#1D9E75" }}
            aria-hidden
          />
          <span className="flex-1 truncate">CO₂ Cost Split</span>
        </Link>
        <Link
          href={`/buildings/${encodeURIComponent(fabricBuildingId)}/geg-report`}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors"
        >
          <Building2
            className="w-4 h-4 shrink-0"
            style={{ color: "#1D9E75" }}
            aria-hidden
          />
          <span className="flex-1 truncate">GEG conformity</span>
        </Link>
        <Link
          href={`/buildings/${encodeURIComponent(fabricBuildingId)}/epc-report`}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-white/5 transition-colors"
        >
          <TrendingUp
            className="w-4 h-4 shrink-0"
            style={{ color: "#1D9E75" }}
            aria-hidden
          />
          <span className="flex-1 truncate">EPC pre-assessment</span>
        </Link>
      </div>
    </nav>
  )
}
