"use client"

/**
 * CompareReportShell -- multi-building variant of BuildingReportShell.
 *
 * Same Layout v3 as the single-building shell: AppChrome top bar carries
 * everything (no HeroBand), embed frame fills the rest. Subtitle lists the
 * selected buildings + country mix; PowerBIReport receives multiple
 * buildingIds so its basic filter uses operator "In" with multiple values.
 *
 * Title accent still reacts to PBI tab navigation -- the same page configs
 * apply, just with a "— Comparison" suffix in the title so users know
 * they're looking at a multi-building view.
 */
import { useState } from "react"

import { AppChrome } from "@/components/AppChrome"
import { ComparePageNav } from "@/components/ComparePageNav"
import { SidePanel } from "@/components/SidePanels"
import type { Building } from "@/lib/api/buildings"
import { DEFAULT_PAGE_CONFIG, PAGE_CONFIG } from "@/lib/config/pageAccents"

import { ReportClient } from "../[fabric_building_id]/ReportClient"

const DEFAULT_CONFIG = {
  ...DEFAULT_PAGE_CONFIG,
  title: "Portfolio Comparison",
}

type CompareReportShellProps = {
  /** Buildings selected for comparison (already resolved server-side). */
  buildings: Building[]
}

export function CompareReportShell({ buildings }: CompareReportShellProps) {
  const [activePageName, setActivePageName] = useState<string>("")
  // Page the left ComparePageNav navigated the embed to (PBI displayName).
  // Kept separate from activePageName (what the embed reports back): a click
  // sets targetPage to drive setActive(), the reported state drives the title
  // accent + nav highlight. With the left nav as the sole page-switcher the
  // two stay in sync, so plain value-equality navigation is enough.
  const [targetPage, setTargetPage] = useState<string>("")

  const config = PAGE_CONFIG[activePageName] ?? DEFAULT_CONFIG

  const fabricIds = buildings
    .map((b) => b.fabric_building_id)
    .filter((id): id is string => Boolean(id))

  // Subtitle lists building IDs + count + unique country mix.
  const countries = Array.from(
    new Set(buildings.map((b) => b.country_code).filter(Boolean))
  ).join("/")

  const subtitleParts = [
    fabricIds.join(" · "),
    `${buildings.length} buildings`,
    countries || null,
  ].filter(Boolean)

  const titleText = activePageName
    ? `${config.title} — Comparison`
    : "Portfolio Comparison"

  return (
    <AppChrome
      breadcrumb={[
        { label: "Buildings", href: "/buildings" },
        { label: `Compare (${buildings.length} buildings)` },
      ]}
      pageTitle={titleText}
      subtitle={subtitleParts.join(" · ")}
      backHref="/buildings"
      backLabel="All buildings"
      accentColor={config.color}
      quietBackdrop
    >
      {config.motifs.map((Motif, i) => (
        <Motif key={`${activePageName}-${i}`} opacity={0.12} />
      ))}

      {/* Same flex layout as single-building shell. */}
      <div className="relative z-10 flex h-[calc(100vh-7rem)]">
        <ComparePageNav
          activePageName={activePageName}
          onSelect={setTargetPage}
        />

        <div
          className="flex-1 min-w-0 flex items-center justify-center transition-all duration-500"
          style={{
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
              buildingIds={fabricIds}
              pageName={targetPage || undefined}
              hidePageNav
              onPageChanged={(name) => setActivePageName(name)}
            />
          </div>
        </div>

        <SidePanel side="right" accentColor={config.color} />
      </div>
    </AppChrome>
  )
}
