/**
 * /portfolio — custom-rendered portfolio overview (no PBI embed).
 *
 * Server component. Auth-guarded + mandatory-onboarding guard (0 own
 * buildings -> /onboarding). Shows headline KPIs, an optional on-site solar
 * row (when the portfolio has PV), and the buildings table. A data-pending
 * banner appears when the user's buildings aren't connected to Fabric yet.
 *
 * Data path (Karar 10): Custom React + Fabric SQL Analytics Endpoint (ODBC).
 */
import Link from "next/link"
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { CitySkylineMotif } from "@/components/CitySkylineMotif"
import { DataPendingBanner } from "@/components/DataPendingBanner"
import { PageIntro } from "@/components/PageIntro"
import { SustainabilityMotif } from "@/components/SustainabilityMotif"
import { BuildingsTable } from "@/components/portfolio/BuildingsTable"
import { PortfolioAdvisor } from "@/components/portfolio/PortfolioAdvisor"
import { PortfolioKPIRow } from "@/components/portfolio/PortfolioKPIRow"
import { DataProvenanceBadge } from "@/components/ui/DataProvenanceBadge"
import { SolarKPIRow } from "@/components/portfolio/SolarKPIRow"
import {
  countOwnBuildings,
  fetchBuildings,
  ownBuildingsAllPending,
} from "@/lib/api/buildings"
import { authOptions } from "@/lib/auth/options"
import {
  fetchPortfolioBuildings,
  fetchPortfolioKPIs,
} from "@/lib/api/portfolio"
import { fetchPartnerClients } from "@/lib/api/partners"
import { PartnerClientSwitcher } from "@/components/portfolio/PartnerClientSwitcher"
import { PortfolioScreeningPanel } from "@/components/portfolio/PortfolioScreeningPanel"
import { fetchPortfolioEstimatesServer } from "@/lib/api/estimation"

const PORTFOLIO_ACCENT = "#1D9E75"

export default async function PortfolioPage({
  searchParams,
}: {
  searchParams: Promise<{ client?: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { client } = await searchParams
  const clientOrgId = client ?? null

  const [kpisResult, buildingsResult, ownBuildings, clientsResult, estimates] =
    await Promise.all([
      fetchPortfolioKPIs(session.accessToken, clientOrgId),
      fetchPortfolioBuildings(session.accessToken, clientOrgId),
      fetchBuildings(session.accessToken),
      fetchPartnerClients(session.accessToken),
      fetchPortfolioEstimatesServer(session.accessToken),
    ])

  if (ownBuildings.ok && countOwnBuildings(ownBuildings.data.buildings) === 0) {
    redirect("/onboarding")
  }

  const buildingCount = buildingsResult.ok
    ? buildingsResult.data.buildings.length
    : 0

  const showPending =
    ownBuildings.ok && ownBuildingsAllPending(ownBuildings.data.buildings)

  // Page-level data provenance: warn when the view includes demo/sample buildings
  // so the numbers are never mistaken for the user's own. (Measured is the silent
  // default; the pending banner already covers "own buildings not connected yet".)
  const visBuildings = buildingsResult.ok ? buildingsResult.data.buildings : []
  const sampleN = visBuildings.filter((b) => b.is_sample_org).length
  const portfolioBasis =
    visBuildings.length === 0
      ? null
      : sampleN === visBuildings.length
        ? ("sample" as const)
        : sampleN > 0
          ? ("mixed" as const)
          : null

  return (
    <AppChrome
      breadcrumb={[{ label: "Portfolio" }]}
      pageTitle="Portfolio Overview"
      subtitle={
        buildingsResult.ok
          ? `${buildingCount} ${buildingCount === 1 ? "building" : "buildings"} · last 30 days`
          : "Could not load portfolio"
      }
      accentColor={PORTFOLIO_ACCENT}
    >
      <SustainabilityMotif />
      <CitySkylineMotif />

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto space-y-8">
        <PageIntro id="portfolio">
          Your whole portfolio at a glance — energy intensity (EUI), cost and carbon
          per building, worst performers first. Click any building to drill into its
          reports, alerts and recommendations.
        </PageIntro>
        {portfolioBasis && (
          <DataProvenanceBadge
            basis={portfolioBasis}
            detail={portfolioBasis === "sample" ? "demo buildings" : `${sampleN} of ${visBuildings.length} are demo`}
          />
        )}
        <div className="flex items-center justify-end gap-3">
          {buildingsResult.ok &&
            buildingsResult.data.buildings.some((b) =>
              (b.building_type || "").toLowerCase().includes("residential")
            ) && (
              <Link
                href="/residential"
                className="inline-flex items-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
              >
                Residential portfolio
              </Link>
            )}
          <PartnerClientSwitcher
            clients={clientsResult.ok ? clientsResult.data.clients : []}
            active={clientOrgId}
          />
          <Link
            href="/portfolio/report"
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

        {showPending && <DataPendingBanner />}

        {!kpisResult.ok ? (
          <FetchErrorNotice error={kpisResult.error} label="KPIs" />
        ) : (
          <PortfolioKPIRow kpis={kpisResult.data} />
        )}

        {kpisResult.ok && kpisResult.data.solar && (
          <SolarKPIRow solar={kpisResult.data.solar} />
        )}

        {estimates && <PortfolioScreeningPanel data={estimates} />}

        {!buildingsResult.ok ? (
          <FetchErrorNotice error={buildingsResult.error} label="buildings" />
        ) : (
          <>
            <PortfolioAdvisor buildings={buildingsResult.data.buildings} />
            <BuildingsTable buildings={buildingsResult.data.buildings} />
          </>
        )}
      </div>
    </AppChrome>
  )
}
