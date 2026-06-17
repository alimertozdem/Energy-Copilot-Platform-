"use client"

/**
 * ReportCompanion — page-aware "how to read this" guide beside the embedded
 * Power BI report. Replaces the decorative right SidePanel in BuildingReportShell.
 *
 * For the active PBI page it shows a plain-language summary + the one thing to
 * watch (from lib/config/reportPages), plus profile-based building takeaways
 * (reuses lib/insights/buildingAdvisor — EPC + heating, no extra fetch) and a
 * glossary link. Collapsible; large-screen enhancement (hidden below lg).
 */
import { useState } from "react"
import Link from "next/link"
import { ArrowRight, BookOpen, ChevronLeft, ChevronRight, Eye, Lightbulb } from "lucide-react"

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
    <aside className="hidden lg:flex w-72 shrink-0 flex-col gap-3 overflow-y-auto border-l border-border-subtle bg-bg-elevated/20 px-4 py-4">
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

      {/* Active page guide */}
      <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
        <div className="text-xs font-medium" style={{ color: accentColor }}>
          {meta.title}
        </div>
        <p className="mt-1 text-[12px] leading-relaxed text-text-muted">{meta.summary}</p>
        <div className="mt-2 flex items-start gap-1.5 text-[11px] leading-relaxed text-text-faint">
          <Eye className="mt-0.5 h-3 w-3 shrink-0" aria-hidden />
          <span>
            <span className="text-text-muted">Watch:</span> {meta.watch}
          </span>
        </div>
      </div>

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
        Screening-grade guidance. New term?{" "}
        <Link href="/glossary" className="hover:underline" style={{ color: accentColor }}>
          Glossary
        </Link>
        .
      </p>
    </aside>
  )
}
