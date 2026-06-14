/**
 * /alerts — portfolio-wide anomaly monitoring page.
 *
 * Server component. Auth-guarded (mirrors /actions, /portfolio).
 *
 * Optional `?building_id=` scopes the view to one building (deep-linked from
 * the /portfolio anomaly count and the building ReportNav). The backend
 * GET /alerts already supports the building_id filter; counts come back scoped.
 *
 * Data flow: /alerts GET = Fabric gold_anomaly_log (read) + Postgres
 * alert_status acknowledge overlay (Day 31).
 *
 * The initial fetch loads the default triage view (resolution=unresolved). The
 * client shell re-fetches from /api/alerts when the severity or resolution
 * filter changes, so the table + counts stay accurate under the row cap.
 */
import Link from "next/link"
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingSlicer } from "@/components/BuildingSlicer"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { PageIntro } from "@/components/PageIntro"
import { DataMatrixMotif } from "@/components/motifs/DataMatrixMotif"
import { authOptions } from "@/lib/auth/options"
import { fetchAlerts } from "@/lib/api/alerts"
import { fetchBuildings } from "@/lib/api/buildings"

import { AlertsShell } from "./AlertsShell"

// Section accent — matches PBI Page 3 "Anomalies & Alerts" (accent-orange).
const ALERTS_ACCENT = "#F97316"

type PageProps = {
  searchParams: Promise<{ building_id?: string }>
}

export default async function AlertsPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0

  const [result, buildingsResult] = await Promise.all([
    fetchAlerts(session.accessToken, {
      limit: 500,
      resolution: "unresolved",
      ...(scoped ? { building_id } : {}),
    }),
    fetchBuildings(session.accessToken),
  ])
  const slicerBuildings = buildingsResult.ok
    ? buildingsResult.data.buildings
        .filter((b) => b.fabric_building_id)
        .map((b) => ({ id: b.fabric_building_id as string, name: b.name }))
    : []

  const unresolved = result.ok ? result.data.severity_counts.unresolved_total : 0
  const subtitle = result.ok ? subtitleFor(unresolved, scoped) : "Couldn't load alerts"
  const buildingName =
    scoped && result.ok ? result.data.alerts[0]?.building_name ?? building_id : null

  return (
    <AppChrome
      breadcrumb={
        scoped
          ? [
              { label: "Alerts", href: "/alerts" },
              { label: buildingName ?? building_id ?? "" },
            ]
          : [{ label: "Alerts" }]
      }
      pageTitle="Alerts"
      subtitle={subtitle}
      accentColor={ALERTS_ACCENT}
      backHref={scoped ? `/buildings/${encodeURIComponent(building_id!)}` : "/portfolio"}
      backLabel={scoped ? "Building" : "Portfolio"}
    >
      <DataMatrixMotif />

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto">
        <PageIntro id="alerts">
          Automated fault detection across your buildings. Recurring anomalies are
          grouped into one ongoing issue — not one alert per day — so the list stays
          actionable. Click a row for what it means, how often it has recurred, and
          what to check. Filter by building if needed.
        </PageIntro>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
          <BuildingSlicer buildings={slicerBuildings} value={scoped ? building_id! : null} />
          <Link
            href="/alerts/report"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export PDF
          </Link>
        </div>

        {scoped && (
          <div className="mb-4 flex items-center justify-between gap-3 rounded-lg border border-orange-500/30 bg-orange-500/5 px-4 py-2.5">
            <div className="text-sm text-text-primary">
              Filtered to{" "}
              <span className="font-medium">{buildingName ?? building_id}</span>
              <span className="ml-1.5 text-xs text-text-muted">{building_id}</span>
            </div>
            <Link
              href="/alerts"
              className="shrink-0 text-xs text-text-muted hover:text-brand-emerald transition-colors"
            >
              Clear filter
            </Link>
          </div>
        )}

        {!result.ok ? (
          <FetchErrorNotice error={result.error} label="alerts" />
        ) : (
          <AlertsShell
            initial={result.data}
            buildingId={scoped ? building_id : undefined}
          />
        )}
      </div>
    </AppChrome>
  )
}

function subtitleFor(unresolved: number, scoped: boolean): string {
  const where = scoped ? "for this building" : "across the portfolio"
  if (unresolved === 0) {
    return `No open issues ${where}`
  }
  return `${unresolved} open ${unresolved === 1 ? "issue" : "issues"} ${where}`
}
