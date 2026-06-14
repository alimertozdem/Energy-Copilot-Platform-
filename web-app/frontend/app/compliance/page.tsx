/**
 * /compliance — Sustainability & Compliance hub (EU energy agenda).
 *
 * Server component, auth-guarded. Sections:
 *   1. EPBD/MEPS renovation-risk radar (MepsRadar) — from /portfolio data.
 *   2. CRREM-style stranding-risk view (CrremStranding) — from /portfolio data.
 *   3. Demand-side flexibility readiness (FlexibilityPanel) — from asset flags.
 *   4. EU Taxonomy alignment-indication (TaxonomyScreen) — activity 7.7
 *      SC-mitigation, from EPC/portfolio data. Indicative, never a verdict.
 *   5. ESRS-E1-aligned energy + Scope 1/2/3 GHG summary (EsrsSummary) — from the
 *      backend /compliance/esrs endpoint (gold_ghg_scope). Degrades on its own if
 *      the GHG pipeline isn't populated / Fabric is unavailable.
 * A sticky SectionNav jumps between the sections present on the page.
 * Export PDF -> /compliance/report (print-optimised: MEPS + CRREM + Taxonomy + ESRS-E1).
 */
import Link from "next/link"
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingSlicer } from "@/components/BuildingSlicer"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { PageIntro } from "@/components/PageIntro"
import { CrremStranding } from "@/components/compliance/CrremStranding"
import { EsrsSummary } from "@/components/compliance/EsrsSummary"
import { FlexibilityPanel } from "@/components/compliance/FlexibilityPanel"
import { MepsRadar } from "@/components/compliance/MepsRadar"
import { SectionNav, type NavSection } from "@/components/compliance/SectionNav"
import { TaxonomyScreen } from "@/components/compliance/TaxonomyScreen"
import { ComplianceReportMenu } from "@/components/compliance/ComplianceReportMenu"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { authOptions } from "@/lib/auth/options"
import { summarizeCompliance } from "@/lib/compliance"

const COMPLIANCE_ACCENT = "#0D9488" // teal — sustainability / compliance

export default async function CompliancePage({
  searchParams,
}: {
  searchParams: Promise<{ building_id?: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0
  // When a building is selected in the slicer, the standalone report links open
  // scoped to it (the report routes honour ?building_id).
  const reportQuery = building_id
    ? `?building_id=${encodeURIComponent(building_id)}`
    : ""

  const [buildingsResult, esrsResult] = await Promise.all([
    fetchPortfolioBuildings(session.accessToken),
    fetchEsrsReport(session.accessToken, scoped ? building_id : undefined),
  ])

  // Building list rows already carry per-building compliance signals, so the
  // slicer is a client-side filter. ESRS now scopes server-side via ?building_id
  // (one-element list), so the whole page reflects the selected building.
  const allBuildings = buildingsResult.ok ? buildingsResult.data.buildings : []
  const slicerBuildings = allBuildings
    .filter((b) => b.fabric_building_id)
    .map((b) => ({ id: b.fabric_building_id as string, name: b.name }))
  const buildings = scoped
    ? allBuildings.filter((b) => b.fabric_building_id === building_id)
    : allBuildings

  const sections: NavSection[] = []
  if (buildingsResult.ok) {
    sections.push(
      { id: "meps", label: "MEPS" },
      { id: "crrem", label: "CRREM" },
      { id: "flexibility", label: "Flexibility" },
      { id: "taxonomy", label: "EU Taxonomy" }
    )
  }
  if (esrsResult.ok) {
    sections.push({ id: "esrs", label: "ESRS-E1" })
  }

  return (
    <AppChrome
      breadcrumb={[{ label: "Compliance" }]}
      pageTitle="Compliance & Sustainability"
      subtitle="EPBD / MEPS · CRREM · flexibility · EU Taxonomy · ESRS-E1"
      accentColor={COMPLIANCE_ACCENT}
    >
      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto space-y-10">
        <PageIntro id="compliance">
          How your portfolio stands against the EU rules that increasingly drive
          building value — MEPS renovation risk, CRREM stranding, EU Taxonomy and
          ESRS-E1. Indicative screening, not a legal verdict.
        </PageIntro>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <BuildingSlicer buildings={slicerBuildings} value={scoped ? building_id! : null} />
          <ComplianceReportMenu reportQuery={reportQuery} />
        </div>

        <SectionNav sections={sections} />

        {!buildingsResult.ok ? (
          <FetchErrorNotice error={buildingsResult.error} label="buildings" />
        ) : (
          <>
            <section id="meps" className="scroll-mt-24">
              <MepsRadar summary={summarizeCompliance(buildings)} />
            </section>
            <section id="crrem" className="scroll-mt-24">
              <CrremStranding buildings={buildings} />
            </section>
            <section id="flexibility" className="scroll-mt-24">
              <FlexibilityPanel buildings={buildings} />
            </section>
            <section id="taxonomy" className="scroll-mt-24">
              <TaxonomyScreen buildings={buildings} />
            </section>
          </>
        )}

        {!esrsResult.ok ? (
          <FetchErrorNotice error={esrsResult.error} label="ESRS report" />
        ) : (
          <section id="esrs" className="scroll-mt-24">
            <EsrsSummary report={esrsResult.data} />
          </section>
        )}
      </div>
    </AppChrome>
  )
}
