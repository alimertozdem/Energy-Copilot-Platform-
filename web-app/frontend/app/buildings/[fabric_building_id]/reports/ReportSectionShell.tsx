"use client"

/**
 * ReportSectionShell -- persistent client shell for a building's report section.
 *
 * Rendered by reports/layout.tsx, so it stays mounted while the user navigates
 * between /reports/[page] routes. It reads the active page from the pathname
 * (usePathname) and drives a SINGLE Power BI embed via setActive -- no re-embed
 * or token re-fetch on page changes.
 *
 * States in the main area:
 *   * embed (persistent) -- mounted whenever the building has Fabric data.
 *     pageName drives in-place navigation; on a locked page pageName is
 *     undefined (the embed stays put) and a lock overlay covers it, so the
 *     embed never unmounts when stepping through locked pages.
 *   * DataPendingNotice -- building has no fabric_building_id yet.
 *
 * The [page] children only validate the slug (they render null); we still
 * render them (hidden) so Next treats them as part of the route tree.
 */
import { usePathname } from "next/navigation"

import { AppChrome } from "@/components/AppChrome"
import { LockedReportPreview } from "@/components/LockedReportPreview"
import { ReportNav } from "@/components/ReportNav"
import type { Building } from "@/lib/api/buildings"
import {
  DEFAULT_REPORT_SLUG,
  REPORT_PAGES,
  getReportPage,
  isPageLocked,
} from "@/lib/config/reportPages"

import { ReportClient } from "../ReportClient"

type ReportSectionShellProps = {
  building: Building
  children: React.ReactNode
}

function slugFromPath(pathname: string): string {
  const parts = pathname.split("/").filter(Boolean)
  const i = parts.indexOf("reports")
  return (i >= 0 && parts[i + 1]) || DEFAULT_REPORT_SLUG
}

export function ReportSectionShell({
  building,
  children,
}: ReportSectionShellProps) {
  const pathname = usePathname() ?? ""
  const page = getReportPage(slugFromPath(pathname)) ?? REPORT_PAGES[0]
  const fabricId = building.fabric_building_id
  const locked = isPageLocked(building, page)

  // Compact meta: "DE · Logistics · 12,000 m² · Built 2018"
  const metaParts = [
    building.country_code,
    building.building_type,
    building.floor_area_m2 != null
      ? `${building.floor_area_m2.toLocaleString("en-US")} m²`
      : null,
    building.construction_year != null
      ? `Built ${building.construction_year}`
      : null,
  ].filter(Boolean)

  // On a locked page, leave the embed on its current page (no setActive) and
  // cover it with the lock overlay -- keeps the embed mounted across locks.
  const embedPageName = locked ? undefined : page.pbiDisplayName

  return (
    <AppChrome
      breadcrumb={[
        { label: "Buildings", href: "/buildings" },
        {
          label: `${building.fabric_building_id ?? "—"} — ${building.name}`,
          href: fabricId ? `/buildings/${fabricId}` : "/buildings",
        },
        { label: page.title },
      ]}
      pageTitle={page.title}
      subtitle={metaParts.join(" · ")}
      backHref={fabricId ? `/buildings/${fabricId}` : "/buildings"}
      backLabel="Building"
      accentColor={page.accent}
    >
      <div className="relative z-10 flex h-[calc(100vh-7rem)]">
        <ReportNav
          fabricBuildingId={fabricId ?? ""}
          building={building}
          activeSlug={page.slug}
        />

        <div
          className="flex-1 min-w-0 flex items-center justify-center transition-all duration-500"
          style={{
            background: `radial-gradient(ellipse at center, ${page.accent}1A 0%, ${page.accent}0D 35%, transparent 70%)`,
          }}
        >
          {!fabricId ? (
            <DataPendingNotice accent={page.accent} />
          ) : (
            <div
              className="relative aspect-video max-h-full max-w-full w-full rounded-xl overflow-hidden bg-bg-base"
              style={{
                border: `1px solid ${page.accent}66`,
                boxShadow: `0 0 28px ${page.accent}1A, 0 8px 28px rgba(0,0,0,0.3)`,
              }}
            >
              {/* Persistent embed -- one mount; pageName drives setActive. */}
              <ReportClient
                buildingIds={[fabricId]}
                pageName={embedPageName}
                hidePageNav
              />
              {locked && (
                <div className="absolute inset-0 z-10 bg-bg-base/95 backdrop-blur-sm">
                  <LockedReportPreview
                    page={page}
                    buildingName={building.name}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* [page] children just validate the slug (render null); kept in the tree. */}
      <div className="hidden">{children}</div>
    </AppChrome>
  )
}

function DataPendingNotice({ accent }: { accent: string }) {
  return (
    <div className="flex h-full w-full items-center justify-center p-8">
      <div
        className="w-full max-w-md rounded-2xl border bg-bg-elevated/70 p-8 text-center backdrop-blur-sm"
        style={{ borderColor: `${accent}40` }}
      >
        <h2 className="text-lg font-semibold text-text-primary">
          Report data is being connected
        </h2>
        <p className="mt-2 text-sm text-text-muted">
          This building was added but isn&apos;t linked to live energy data yet.
          Reports will appear here once ingestion is connected.
        </p>
      </div>
    </div>
  )
}
