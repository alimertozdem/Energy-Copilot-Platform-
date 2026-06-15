"use client"

/**
 * BuildingReportShell -- client wrapper around AppChrome + ReportClient.
 *
 * Layout v3:
 *   * AppChrome top bar carries everything (logo + back + breadcrumb +
 *     compact title + meta subtitle + user). HeroBand is gone — PBI's own
 *     page backgrounds already display a big title, so doubling it up was
 *     redundant.
 *   * Embed frame fills the rest of the viewport. bg-bg-base behind it so
 *     any FitToPage letterbox bars match the app's dark navy instead of
 *     defaulting to white.
 *   * Per-page motif set still applies, but at opacity 0.15 for a more
 *     elegant, visible-but-quiet watermark.
 *
 * Page-awareness:
 *   PowerBIReport fires onPageChanged(displayName) on every PBI tab click.
 *   We map that name -> (title, accent color, motif preset) via
 *   lib/config/pageAccents.
 */
import { useState } from "react"

import { AppChrome } from "@/components/AppChrome"
import { ReportNav } from "@/components/ReportNav"
import { SidePanel } from "@/components/SidePanels"
import type { Building } from "@/lib/api/buildings"
import { DEFAULT_PAGE_CONFIG, PAGE_CONFIG } from "@/lib/config/pageAccents"
import { REPORT_PAGES } from "@/lib/config/reportPages"

import { ReportClient } from "./ReportClient"

type BuildingReportShellProps = {
  building: Building
}

export function BuildingReportShell({ building }: BuildingReportShellProps) {
  const [activePageName, setActivePageName] = useState<string>("")

  const config = PAGE_CONFIG[activePageName] ?? DEFAULT_PAGE_CONFIG

  // Highlight the ReportNav item matching the PBI tab the user is on. PBI
  // reports displayName via onPageChanged; we map it back to a manifest slug.
  const activeSlug =
    REPORT_PAGES.find((p) => p.pbiDisplayName === activePageName)?.slug ?? ""

  // Compact meta: "DE · Logistics · 12,000 m² · Built 2018"
  // (Building id + name already render in the breadcrumb above.)
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

  return (
    <AppChrome
      breadcrumb={[
        { label: "Buildings", href: "/buildings" },
        {
          label: `${building.fabric_building_id ?? "—"} — ${building.name}`,
        },
      ]}
      pageTitle={config.title}
      subtitle={metaParts.join(" · ")}
      backHref="/buildings"
      backLabel="All buildings"
      accentColor={config.color}
      quietBackdrop
    >
      {/* Per-page motif set, low-opacity ambient watermarks at the corners. */}
      {config.motifs.map((Motif, i) => (
        <Motif key={`${activePageName}-${i}`} opacity={0.12} />
      ))}

      {/* Flex layout: [left report nav] [embed (flex-1)] [right side panel]
          The nav + panel sit BESIDE the embed, not behind it -- so they're
          always visible regardless of z-index. */}
      <div className="relative z-10 flex h-[calc(100vh-7rem)]">
        <ReportNav
          fabricBuildingId={building.fabric_building_id ?? ""}
          building={building}
          activeSlug={activeSlug}
        />

        <div
          className="flex-1 min-w-0 flex items-center justify-center transition-all duration-500"
          style={{
            // Letterbox area painted with a soft page-accent radial. When the
            // 16:9 embed doesn't fill the wrapper, the leftover edges sit in
            // this colour instead of white / navy.
            background: `radial-gradient(ellipse at center,
              ${config.color}1A 0%,
              ${config.color}0D 35%,
              transparent 70%)`,
          }}
        >
          <div
            className="relative aspect-video max-h-full max-w-full w-full rounded-xl transition-all duration-500 overflow-hidden bg-bg-base"
            style={{
              border: `1px solid ${config.color}66`,
              boxShadow: `0 0 28px ${config.color}1A, 0 8px 28px rgba(0,0,0,0.3)`,
            }}
          >
            {/* Decorative corner brackets — thin accent L-marks */}
            <div
              className="absolute top-1.5 left-1.5 w-4 h-4 border-l border-t rounded-tl pointer-events-none z-10 transition-colors duration-500"
              style={{ borderColor: `${config.color}CC` }}
              aria-hidden
            />
            <div
              className="absolute top-1.5 right-1.5 w-4 h-4 border-r border-t rounded-tr pointer-events-none z-10 transition-colors duration-500"
              style={{ borderColor: `${config.color}CC` }}
              aria-hidden
            />
            <div
              className="absolute bottom-1.5 left-1.5 w-4 h-4 border-l border-b rounded-bl pointer-events-none z-10 transition-colors duration-500"
              style={{ borderColor: `${config.color}CC` }}
              aria-hidden
            />
            <div
              className="absolute bottom-1.5 right-1.5 w-4 h-4 border-r border-b rounded-br pointer-events-none z-10 transition-colors duration-500"
              style={{ borderColor: `${config.color}CC` }}
              aria-hidden
            />

            <ReportClient
              buildingIds={
                building.fabric_building_id
                  ? [building.fabric_building_id]
                  : undefined
              }
              onPageChanged={(name) => setActivePageName(name)}
            />
          </div>
        </div>

        <SidePanel side="right" accentColor={config.color} />
      </div>
    </AppChrome>
  )
}
