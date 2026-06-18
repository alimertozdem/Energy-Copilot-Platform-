"use client"

/**
 * ReportCompanion — page-aware "how to read this" guide beside the embedded
 * Power BI report. Replaces the decorative right SidePanel.
 *
 * For the active PBI page it shows, from lib/config/reportPages:
 *   * a plain-language summary,
 *   * "What you're looking at" — each key chart -> what it tells you + what
 *     good/bad looks like (screening-grade, product-owner-approved thresholds),
 *   * the one thing to Watch,
 *   * an Act deep-link (where the page leads — Financing, Compliance, etc.).
 * Plus profile-based building takeaways (reuses lib/insights/buildingAdvisor —
 * EPC + heating, no extra fetch) and a glossary link.
 *
 * Collapsible; large-screen enhancement (hidden below lg).
 */
import { useState } from "react"
import Link from "next/link"
import { ArrowRight, BarChart3, BookOpen, ChevronLeft, ChevronRight, Eye, Lightbulb } from "lucide-react"

import type { Building } from "@/lib/api/buildings"
import { REPORT_PAGES } from "@/lib/config/reportPages"
import { buildAdvisorInsights, type Insight } from "@/lib/insights/buildingAdvisor"

const SEV_DOT: Record<Insight["severity"], string> = {
  action: "bg-red-400",
  watch: "bg-amber-400",
  info: "bg-sky-400",
  good: "bg-brand-emerald",
}

export function ReportCompanion({
  activePageName,
  building,
  accentColor,
}: {
  activePageName: string
  building: Building
  accentColor: string
}) {
  const [open, setOpen] = useState(true)
  const meta = REPORT_PAGES.find((p) => p.pbiDisplayName === activePageName) ?? REPORT_PAGES[0]
  const insights = buildAdvisorInsights({
    kpis: null,
    topActions: [],
    isResidential: false,
    profile: { epc_class: building.epc_class, heating_system: building.heating_system },
  }).slice(0, 3)

  // Resolve the Act deep-link: {id} -> fabric_building_id. If the link needs an
  // id the building doesn't have yet (data-pending), hide the Act button.
  const rawHref = meta.act?.href ?? ""
  const actHref = rawHref.includes("{id}")
    ? building.fabric_building_id
      ? rawHref.replace("{id}", building.fabric_building_id)
      : null
    : rawHref || null
  const showAct = Boolean(meta.act && actHref)

  if (!open) {
    return (
      <aside className="hidden lg:flex w-9 shrink-0 flex-col items-center pt-4">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Show report guide"
          className="rounded-md border border-border-subtle bg-bg-elevated/40 p-1.5 text-text-muted transition-colors hover:text-text-primary"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden />
        </button>
        <span
          className="mt-3 text-[10px] uppercase tracking-[0.25em] text-text-faint"
          style={{ writingMode: "vertical-rl" }}
        >
          Guide
        </span>
      </aside>
    )
  }

  return (
    <aside className="hidden lg:flex w-80 shrink-0 flex-col gap-3 overflow-y-auto border-l border-border-subtle bg-bg-elevated/20 px-4 py-4">
      <div className="flex items-center gap-2">
        <BookOpen className="h-4 w-4" style={{ color: accentColor }} aria-hidden />
        <h3 className="text-sm font-semibold text-text-primary">How to read this</h3>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Hide report guide"
          className="ml-auto text-text-faint transition-colors hover:text-text-primary"
        >
          <ChevronRight className="h-4 w-4" aria-hidden />
        </button>
      </div>

      {/* Active page summary */}
      <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
        <div className="text-xs font-medium" style={{ color: accentColor }}>
          {meta.title}
        </div>
        <p className="mt-1 text-[12px] leading-relaxed text-text-muted">{meta.summary}</p>
      </div>

      {/* What you're looking at — per-visual guide */}
      {meta.reads.length > 0 && (
        <div>
          <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-text-faint">
            <BarChart3 className="h-3 w-3" aria-hidden /> What you&apos;re looking at
          </div>
          <div className="space-y-1.5">
            {meta.reads.map((r) => (
              <div key={r.v} className="rounded-lg border border-border-subtle bg-white/[0.02] p-2.5">
                <div className="text-[12px] font-medium text-text-primary">{r.v}</div>
                <p className="mt-0.5 text-[11px] leading-relaxed text-text-faint">{r.m}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* The one thing to watch */}
      <div
        className="rounded-lg border p-2.5"
        style={{ borderColor: `${accentColor}40`, background: `${accentColor}0D` }}
      >
        <div className="flex items-start gap-1.5 text-[11px] leading-relaxed text-text-muted">
          <Eye className="mt-0.5 h-3.5 w-3.5 shrink-0" style={{ color: accentColor }} aria-hidden />
          <span>
            <span className="font-medium text-text-primary">Watch:</span> {meta.watch}
          </span>
        </div>
      </div>

      {/* Act — where this page leads */}
      {showAct && actHref && (
        <Link
          href={actHref}
          className="inline-flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-[12px] font-medium transition-colors"
          style={{ borderColor: `${accentColor}66`, color: accentColor }}
        >
          {meta.act?.label} <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
      )}

      {/* Building-specific takeaways (profile-based — EPC + heating) */}
      {insights.length > 0 && (
        <div>
          <div className="mb-1.5 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-text-faint">
            <Lightbulb className="h-3 w-3" aria-hidden /> For this building
          </div>
          <div className="space-y-2">
            {insights.map((ins) => (
              <div key={ins.id} className="rounded-lg border border-border-subtle bg-white/[0.02] p-2.5">
                <div className="flex items-center gap-1.5">
                  <span className={`h-1.5 w-1.5 rounded-full ${SEV_DOT[ins.severity]}`} aria-hidden />
                  <span className="text-[12px] font-medium text-text-primary">{ins.title}</span>
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-text-faint">{ins.detail}</p>
                {ins.href && ins.cta && (
                  <Link
                    href={ins.href}
                    className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium hover:underline"
                    style={{ color: accentColor }}
                  >
                    {ins.cta} <ArrowRight className="h-3 w-3" aria-hidden />
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="mt-auto pt-2 text-[10px] leading-relaxed text-text-faint">
        Screening-grade guidance; thresholds are indicative. New term?{" "}
        <Link href="/glossary" className="hover:underline" style={{ color: accentColor }}>
          Glossary
        </Link>
        .
      </p>
    </aside>
  )
}
