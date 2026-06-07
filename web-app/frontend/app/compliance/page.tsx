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

  const [buildingsResult, esrsResult] = await Promise.all([
    fetchPortfolioBuildings(session.accessToken),
    fetchEsrsReport(session.accessToken),
  ])

  // Building list rows already carry per-building compliance signals, so the
  // slicer is a client-side filter — no backend change. (ESRS is a portfolio
  // GHG aggregate; it stays portfolio-level.)
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
          <Link
            href="/compliance/report"
            target="_blank"
            rel="noopener noreferrer"
            title="Print-ready PDF: MEPS, CRREM, EU Taxonomy and ESRS-E1"
            className="inline-flex items-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export PDF
          </Link>
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
