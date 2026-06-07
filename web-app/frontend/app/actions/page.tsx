/**
 * /actions — recommendation tracking page.
 *
 * Server component. Auth-guarded (mirrors /portfolio).
 *
 * Why a separate page when Page 5 of Power BI already shows recommendations?
 *   PBI Page 5 is read-only catalog. This page is the WRITE layer — each row
 *   carries an editable status (open / in_progress / completed / dismissed)
 *   that's persisted in Postgres recommendation_status. Decision support →
 *   decision tracking.
 *
 * Optional `?building_id=` scopes the whole view to one building (deep-linked
 * from the building overview "Recommendations" tile). The backend GET /actions
 * already supports the building_id filter; the MACC curve, the table and the
 * status-count chips all narrow to that building because they read the same
 * server-scoped payload. A "Filtered to X / Clear" banner + a back-to-building
 * button make the scoped state obvious and reversible.
 *
 * Data flow (Karar 10 — third read path off the same Lakehouse):
 *   * /actions GET = Fabric SQL Analytics Endpoint (catalog) +
 *     Postgres recommendation_status (overlay)
 *   * Optimistic UI updates Postgres directly via PATCH.
 */
import Link from "next/link"
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingSlicer } from "@/components/BuildingSlicer"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { PageIntro } from "@/components/PageIntro"
import { SustainabilityMotif } from "@/components/SustainabilityMotif"
import { authOptions } from "@/lib/auth/options"
import { fetchActions } from "@/lib/api/actions"
import { fetchBuildings } from "@/lib/api/buildings"

import { MaccCurve } from "@/components/actions/MaccCurve"

import { ActionsShell } from "./ActionsShell"

// Section accent — emerald variant matching the brand's "action" hue.
const ACTIONS_ACCENT = "#10b981"

type PageProps = {
  searchParams: Promise<{ building_id?: string }>
}

export default async function ActionsPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0

  const [result, buildingsResult] = await Promise.all([
    fetchActions(session.accessToken, {
      limit: 500,
      ...(scoped ? { building_id } : {}),
    }),
    fetchBuildings(session.accessToken),
  ])
  const slicerBuildings = buildingsResult.ok
    ? buildingsResult.data.buildings
        .filter((b) => b.fabric_building_id)
        .map((b) => ({ id: b.fabric_building_id as string, name: b.name }))
    : []

  const count = result.ok ? result.data.actions.length : 0
  const buildingName =
    scoped && result.ok ? result.data.actions[0]?.building_name ?? building_id : null
  const totalLabel = result.ok
    ? `${count} recommendation${count === 1 ? "" : "s"} ${
        scoped ? "for this building" : "across the portfolio"
      }`
    : "Couldn't load recommendations"
  const reportHref = scoped
    ? `/actions/report?building_id=${encodeURIComponent(building_id!)}`
    : "/actions/report"

  return (
    <AppChrome
      breadcrumb={
        scoped
          ? [
              { label: "Actions", href: "/actions" },
              { label: buildingName ?? building_id ?? "" },
            ]
          : [{ label: "Actions" }]
      }
      pageTitle="Recommendations"
      subtitle={totalLabel}
      accentColor={ACTIONS_ACCENT}
      backHref={scoped ? `/buildings/${encodeURIComponent(building_id!)}` : "/portfolio"}
      backLabel={scoped ? "Building" : "Portfolio"}
    >
      <SustainabilityMotif />

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto">
        <PageIntro id="actions">
          Recommended improvements with savings, cost and payback. Set each one&rsquo;s
          status to track progress. Open <span className="text-text-primary">Decarbonisation</span> for
          the CO₂ investment view, or filter by building.
        </PageIntro>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
          <BuildingSlicer buildings={slicerBuildings} value={scoped ? building_id! : null} />
          <div className="flex flex-wrap items-center gap-2">
          <Link
            href="/decarbonisation"
            className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-3 py-1.5 text-sm font-medium text-text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
          >
            Decarbonisation plan →
          </Link>
          <Link
            href={reportHref}
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
        </div>

        {scoped && (
          <div className="mb-4 flex items-center justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-2.5">
            <div className="text-sm text-text-primary">
              Filtered to{" "}
              <span className="font-medium">{buildingName ?? building_id}</span>
              <span className="ml-1.5 text-xs text-text-muted">{building_id}</span>
            </div>
            <Link
              href="/actions"
              className="shrink-0 text-xs text-text-muted hover:text-brand-emerald transition-colors"
            >
              Clear filter
            </Link>
          </div>
        )}

        {!result.ok ? (
          <FetchErrorNotice error={result.error} label="recommendations" />
        ) : (
          <div className="space-y-6">
            <MaccCurve actions={result.data.actions} />
            <ActionsShell initial={result.data} />
          </div>
        )}
      </div>
    </AppChrome>
  )
}
