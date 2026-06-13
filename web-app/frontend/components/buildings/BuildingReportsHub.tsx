/**
 * BuildingReportsHub -- one place on a building's home page to reach every
 * report for that building.
 *
 * Consolidates what used to be scattered across the ReportNav "Documents" group
 * (per-building CO2 / GEG / EPC) and the portfolio /compliance page (ESRS, GHG,
 * EnEfG). Each report is a card carrying its scope (Building vs Portfolio -- the
 * latter org-wide, surfaced here for quick access) and an honest status:
 *   * Available    -- openable now
 *   * Data pending -- this building isn't linked to Fabric data yet
 *   * Locked       -- needs a module the building hasn't enabled
 *
 * Pure presentational (server) component: it only links into existing routes,
 * no new data fetch. "Select -> continue" = pick a card to open the report; you
 * don't have to enter a report to see what's on offer. Module gating mirrors the
 * web-app access layer (reportPages.isPageLocked); Power BI RLS is the data
 * layer and does not gate page visibility.
 */
import Link from "next/link"
import {
  ArrowRight,
  Building2,
  ClipboardList,
  Factory,
  FileDown,
  Gauge,
  FileText,
  Globe,
  Home,
  LayoutGrid,
  Leaf,
  Lock,
  TrendingDown,
  TrendingUp,
  type LucideIcon,
} from "lucide-react"

import type { Building, ModuleKey } from "@/lib/api/buildings"
import {
  DEFAULT_REPORT_SLUG,
  REPORT_PAGES,
  isPageLocked,
} from "@/lib/config/reportPages"
import { cn } from "@/lib/utils"

type Scope = "Building" | "Portfolio"

type ReportEntry = {
  key: string
  title: string
  description: string
  href: string
  scope: Scope
  icon: LucideIcon
  /** Print/PDF routes open in a new tab (matches the ReportNav pattern). */
  external?: boolean
  /** When set, the card locks unless the building has that module enabled. */
  requiredModule?: ModuleKey
  /** Optional muted line under the description (e.g. locked-page hint). */
  subnote?: string
}

type Group = { heading: string; note?: string; entries: ReportEntry[] }

function buildGroups(
  fabricId: string,
  energySubnote: string | undefined,
  isResidential: boolean
): Group[] {
  const b = `/buildings/${encodeURIComponent(fabricId)}`
  // Portfolio ESG reports open SCOPED to this building (the report routes honour
  // ?building_id); empty when the building has no Fabric id yet (portfolio-wide).
  const esgQuery = fabricId ? `?building_id=${encodeURIComponent(fabricId)}` : ""
  // The 10 Power BI pages are built on the COMMERCIAL gold model; residential
  // buildings populate gold_residential_unit_kpi instead, so the PBI embed is
  // (correctly) sparse for them. Lead residential buildings to their purpose-built
  // dashboard and label the commercial embed honestly.
  const energyCard: ReportEntry = {
    key: "energy",
    title: isResidential ? "Energy dashboards (Power BI)" : "Energy dashboards",
    description: isResidential
      ? "Commercial portfolio metrics — limited for residential buildings."
      : "Interactive Power BI — portfolio overview, anomalies, forecast, HVAC and more.",
    href: `${b}/reports/${DEFAULT_REPORT_SLUG}`,
    scope: "Building",
    icon: LayoutGrid,
    subnote: energySubnote,
  }
  const dashboards: ReportEntry[] = isResidential
    ? [
        {
          key: "residential",
          title: "Residential dashboard",
          description:
            "Per-unit EUI (climate-adjusted), EPC mix and UVI metering compliance for this building.",
          href: `${b}/residential`,
          scope: "Building",
          icon: Home,
        },
        energyCard,
      ]
    : [energyCard]
  const summaryCard: ReportEntry = isResidential
    ? {
        key: "summary",
        title: "Residential summary (PDF)",
        description:
          "Per-unit EUI (climate-adjusted), EPC mix and HKVO/UVI metering coverage, ready to print.",
        href: `${b}/residential-report`,
        scope: "Building",
        icon: FileDown,
        external: true,
      }
    : {
        key: "summary",
        title: "Building summary (PDF)",
        description:
          "One-page overview of this building's KPIs, actions and alerts, ready to print.",
        href: `${b}/report`,
        scope: "Building",
        icon: FileDown,
        external: true,
      }
  return [
    {
      heading: "Dashboards",
      entries: dashboards,
    },
    {
      heading: "Building documents",
      note: "German-mandatory screening reports for this building.",
      entries: [
        {
          key: "co2",
          title: "CO₂ Cost Split",
          description:
            "Landlord/tenant CO₂ cost allocation under the CO2KostAufG (Est., area pro-rata).",
          href: `${b}/co2-report`,
          scope: "Building",
          icon: Leaf,
          external: true,
        },
        {
          key: "geg",
          title: "GEG conformity",
          description:
            "Heating (§71) and envelope U-value screening under the Building Energy Act.",
          href: `${b}/geg-report`,
          scope: "Building",
          icon: Building2,
          external: true,
        },
        {
          key: "epc",
          title: "EPC pre-assessment",
          description:
            "Indicative Energieausweis efficiency class — screening, not a registered certificate.",
          href: `${b}/epc-report`,
          scope: "Building",
          icon: TrendingUp,
          external: true,
        },
        summaryCard,
      ],
    },
    {
      heading: "Portfolio ESG",
      note: "Organisation-wide reports — surfaced here for quick access.",
      entries: [
        {
          key: "esrs",
          title: "ESRS E-1 (Climate)",
          description:
            "Climate-change disclosure E1-1…E1-9, ESRS-aligned (Scope 1/2/3 auto-filled).",
          href: `/compliance/esrs-report${esgQuery}`,
          scope: "Portfolio",
          icon: Globe,
          external: true,
        },
        {
          key: "ghg",
          title: "GHG Inventory",
          description:
            "Scope 1/2/3 greenhouse-gas inventory in GHG Protocol framing.",
          href: `/compliance/ghg-report${esgQuery}`,
          scope: "Portfolio",
          icon: Factory,
          external: true,
        },
        {
          key: "enefg",
          title: "EnEfG plan",
          description:
            "Energy-efficiency measures plan (Maßnahmenplan) covering the economic actions.",
          href: `/compliance/enefg-report${esgQuery}`,
          scope: "Portfolio",
          icon: ClipboardList,
          external: true,
        },
        {
          key: "vsme",
          title: "VSME report",
          description:
            "Voluntary SME standard (Basic Module) — B3 energy & GHG auto-filled, rest guided.",
          href: `/compliance/vsme-report${esgQuery}`,
          scope: "Portfolio",
          icon: FileText,
          external: true,
        },
        {
          key: "crrem",
          title: "CRREM stranding",
          description:
            "Transition-risk: per-asset stranding year vs a 1.5°C pathway (indicative).",
          href: `/compliance/crrem-report${esgQuery}`,
          scope: "Portfolio",
          icon: TrendingDown,
          external: true,
        },
        {
          key: "gresb",
          title: "GRESB readiness",
          description:
            "GRESB Performance readiness — energy & GHG indicators populated, rest a checklist.",
          href: `/compliance/gresb-report${esgQuery}`,
          scope: "Portfolio",
          icon: Gauge,
          external: true,
        },
      ],
    },
  ]
}

export function BuildingReportsHub({ building }: { building: Building }) {
  const fabricId = building.fabric_building_id
  const lockedTitles = REPORT_PAGES.filter((p) => isPageLocked(building, p)).map(
    (p) => p.title
  )
  const energySubnote =
    lockedTitles.length > 0
      ? `${lockedTitles.length} page${
          lockedTitles.length > 1 ? "s" : ""
        } need a module (${lockedTitles.join(", ")})`
      : undefined
  const isResidential = (building.building_type ?? "")
    .toLowerCase()
    .includes("residential")
  const groups = buildGroups(fabricId ?? "", energySubnote, isResidential)

  return (
    <section aria-labelledby="reports-hub-heading" className="mt-8">
      <div className="flex items-baseline justify-between gap-3">
        <h2
          id="reports-hub-heading"
          className="text-base font-semibold text-text-primary"
        >
          Reports &amp; documents
        </h2>
        <p className="text-xs text-text-faint">Pick a report to open it</p>
      </div>

      {groups.map((group) => (
        <div key={group.heading} className="mt-5">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">
              {group.heading}
            </p>
            {group.note && (
              <span className="text-[11px] text-text-faint/80">
                — {group.note}
              </span>
            )}
          </div>
          <div className="mt-2 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {group.entries.map((entry) => (
              <ReportCard
                key={entry.key}
                entry={entry}
                building={building}
                // Building-scope reports depend on this building's Fabric link;
                // portfolio reports are org-wide and never "pending" here.
                dataPending={!fabricId && entry.scope === "Building"}
              />
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}

function ReportCard({
  entry,
  building,
  dataPending,
}: {
  entry: ReportEntry
  building: Pick<Building, "modules">
  dataPending: boolean
}) {
  const locked =
    entry.requiredModule !== undefined &&
    !building.modules.some(
      (m) => m.module_key === entry.requiredModule && m.enabled
    )
  const disabled = dataPending || locked
  const Icon = entry.icon

  const cardClass = cn(
    "block rounded-xl border p-4 transition-colors",
    disabled
      ? "cursor-not-allowed border-border-subtle bg-bg-elevated/30 opacity-70"
      : "border-border-subtle bg-bg-elevated/40 hover:border-brand-emerald/40 hover:bg-white/5"
  )

  const inner = (
    <>
      <div className="flex items-start gap-3">
        <span
          className={cn(
            "grid h-9 w-9 shrink-0 place-items-center rounded-lg border",
            disabled
              ? "border-white/10 bg-white/5 text-text-faint"
              : "border-brand-emerald/30 bg-brand-emerald/10 text-brand-emerald"
          )}
        >
          <Icon className="h-4 w-4" aria-hidden />
        </span>
        <div className="min-w-0">
          <h3 className="truncate text-sm font-medium text-text-primary">
            {entry.title}
          </h3>
          <p className="mt-1 text-xs leading-snug text-text-muted line-clamp-2">
            {entry.description}
          </p>
          {entry.subnote && (
            <p className="mt-1 text-[11px] text-amber-300/70">{entry.subnote}</p>
          )}
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className="inline-flex items-center rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-text-faint">
          {entry.scope}
        </span>
        <StatusPill locked={locked} dataPending={dataPending} />
      </div>
    </>
  )

  if (disabled) {
    return (
      <div className={cardClass} aria-disabled="true">
        {inner}
      </div>
    )
  }

  return (
    <Link
      href={entry.href}
      target={entry.external ? "_blank" : undefined}
      rel={entry.external ? "noopener noreferrer" : undefined}
      className={cardClass}
    >
      {inner}
    </Link>
  )
}

function StatusPill({
  locked,
  dataPending,
}: {
  locked: boolean
  dataPending: boolean
}) {
  if (locked) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] text-amber-300/80">
        <Lock className="h-3 w-3" aria-hidden /> Locked
      </span>
    )
  }
  if (dataPending) {
    return (
      <span className="text-[11px] text-amber-300/80">Data pending</span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-[11px] text-text-muted">
      Open <ArrowRight className="h-3 w-3" aria-hidden />
    </span>
  )
}
