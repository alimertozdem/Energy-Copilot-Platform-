/**
 * /compliance — Sustainability & Compliance hub (EU energy agenda).
 *
 * Server component, auth-guarded. Leads with a ComplianceHero scorecard (all
 * five dimensions at a glance, slicer-scoped) over the global EnergyParticles
 * field + a bespoke ComplianceMotif, then the detail sections:
 *   1. EPBD/MEPS renovation-risk radar (MepsRadar) — G→2030 / F→2033 split.
 *   2. CRREM-style stranding-risk view (CrremStranding) — per-building sparkline.
 *   3. Demand-side flexibility readiness (FlexibilityPanel) — controls-gated.
 *   4. EU Taxonomy alignment-indication (TaxonomyScreen) — activity 7.7 + EPC validity.
 *   5. ESRS-E1-aligned energy + Scope 1/2/3 GHG summary (EsrsSummary).
 * A sticky SectionNav jumps between the sections present on the page.
 * Export PDF -> /compliance/report (print-optimised: MEPS + CRREM + Taxonomy + ESRS-E1).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingSlicer } from "@/components/BuildingSlicer"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { PageIntro } from "@/components/PageIntro"
import { ComplianceHero, type ScoreItem } from "@/components/compliance/ComplianceHero"
import { CrremStranding } from "@/components/compliance/CrremStranding"
import { EsrsSummary } from "@/components/compliance/EsrsSummary"
import { FlexibilityPanel } from "@/components/compliance/FlexibilityPanel"
import { MepsRadar } from "@/components/compliance/MepsRadar"
import { SectionNav, type NavSection } from "@/components/compliance/SectionNav"
import { TaxonomyScreen } from "@/components/compliance/TaxonomyScreen"
import { ComplianceReportMenu } from "@/components/compliance/ComplianceReportMenu"
import { ComplianceScreeningSection } from "@/components/compliance/ComplianceScreeningSection"
import { fetchEsrsReport } from "@/lib/api/esrs"
import { fetchPortfolioBuildings } from "@/lib/api/portfolio"
import { fetchPortfolioEstimatesServer } from "@/lib/api/estimation"
import { authOptions } from "@/lib/auth/options"
import { summarizeCompliance } from "@/lib/compliance"
import { summarizeStranding } from "@/lib/crrem"
import { summarizeFlex } from "@/lib/flexibility"
import { summarizeTaxonomy } from "@/lib/taxonomy"

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

  const [buildingsResult, esrsResult, estimates] = await Promise.all([
    fetchPortfolioBuildings(session.accessToken),
    fetchEsrsReport(session.accessToken, scoped ? building_id : undefined),
    fetchPortfolioEstimatesServer(session.accessToken),
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

  // Section summaries (computed once; MepsRadar takes the compliance summary,
  // the others take buildings, and the hero scorecard reads all of them).
  const compliance = buildingsResult.ok ? summarizeCompliance(buildings) : null
  const stranding = buildingsResult.ok ? summarizeStranding(buildings) : null
  const flex = buildingsResult.ok ? summarizeFlex(buildings) : null
  const taxonomy = buildingsResult.ok ? summarizeTaxonomy(buildings) : null
  const esrsData = esrsResult.ok ? esrsResult.data : null

  const sections: NavSection[] = []
  if (buildingsResult.ok) {
    sections.push(
      { id: "meps", label: "MEPS" },
      { id: "crrem", label: "CRREM" },
      { id: "flexibility", label: "Flexibility" },
      { id: "taxonomy", label: "EU Taxonomy" }
    )
  }
  if (estimates && estimates.estimated_count > 0) {
    sections.push({ id: "screening", label: "Screening" })
  }
  if (esrsResult.ok) {
    sections.push({ id: "esrs", label: "ESRS-E1" })
  }

  // Hero scorecard — one cell per dimension, each links to its section.
  const scoreItems: ScoreItem[] = []
  if (compliance) {
    scoreItems.push({
      href: "#meps",
      label: "Renovation priority",
      value: String(compliance.counts.high),
      sub:
        compliance.counts.high > 0
          ? `G→2030: ${compliance.scope2030} · F→2033: ${compliance.scope2033}`
          : "none flagged",
      tone: compliance.counts.high > 0 ? "red" : "emerald",
    })
  }
  if (stranding) {
    scoreItems.push({
      href: "#crrem",
      label: "Stranded now",
      value: String(stranding.strandedNow),
      sub: `${stranding.strandedBy2030} strand by 2030 · ${stranding.assessed}/${buildings.length} assessed`,
      tone:
        stranding.strandedNow > 0
          ? "red"
          : stranding.strandedBy2030 > 0
            ? "amber"
            : "emerald",
    })
  }
  if (taxonomy) {
    scoreItems.push({
      href: "#taxonomy",
      label: "Taxonomy A-route",
      value: `${taxonomy.onRouteCount}/${taxonomy.total}`,
      sub:
        `${Math.round(taxonomy.onRouteAreaShare * 100)}% area` +
        (taxonomy.staleEpcCount > 0 ? ` · ${taxonomy.staleEpcCount} EPC to renew` : ""),
      tone: taxonomy.onRouteCount > 0 ? "emerald" : "amber",
    })
  }
  if (flex) {
    scoreItems.push({
      href: "#flexibility",
      label: "Flexibility-ready",
      value: String(flex.ready),
      sub: `${flex.partial} partial · ${flex.limited} limited`,
      tone: flex.ready > 0 ? "emerald" : "amber",
    })
  }
  scoreItems.push({
    href: "#esrs",
    label: "ESRS-E1",
    value: esrsResult.ok ? (esrsData?.has_data ? "Ready" : "Pending") : "—",
    sub: esrsResult.ok
      ? esrsData?.reporting_year
        ? `reporting ${esrsData.reporting_year}`
        : "reporting support"
      : "unavailable",
    tone: esrsResult.ok ? (esrsData?.has_data ? "emerald" : "amber") : "neutral",
  })

  const heroContext =
    scoped && buildings[0]
      ? `${buildings[0].name} — ${buildings[0].city}, ${buildings[0].country}. Indicative screening across the EU energy & climate rules.`
      : `${buildings.length} building${buildings.length === 1 ? "" : "s"} screened against the EU rules that increasingly drive building value — indicative, not a legal verdict.`

  return (
    <AppChrome
      breadcrumb={[{ label: "Compliance" }]}
      pageTitle="Compliance & Sustainability"
      subtitle="EPBD / MEPS · CRREM · flexibility · EU Taxonomy · ESRS-E1"
      accentColor={COMPLIANCE_ACCENT}
    >
      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto space-y-8">
        <PageIntro id="compliance">
          How your portfolio stands against the EU rules that increasingly drive
          building value — MEPS renovation risk, CRREM stranding, EU Taxonomy and
          ESRS-E1. Indicative screening, not a legal verdict.
        </PageIntro>

        <div className="flex flex-wrap items-center justify-between gap-2">
          <BuildingSlicer buildings={slicerBuildings} value={scoped ? building_id! : null} />
          <ComplianceReportMenu reportQuery={reportQuery} />
        </div>

        {buildingsResult.ok && (
          <ComplianceHero
            title="Compliance snapshot"
            context={heroContext}
            items={scoreItems}
            accent={COMPLIANCE_ACCENT}
          />
        )}

        <SectionNav sections={sections} />

        {!buildingsResult.ok ? (
          <FetchErrorNotice error={buildingsResult.error} label="buildings" />
        ) : (
          <>
            <section id="meps" className="scroll-mt-24">
              <MepsRadar summary={compliance!} />
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

        {estimates && estimates.estimated_count > 0 && (
          <section id="screening" className="scroll-mt-24">
            <ComplianceScreeningSection data={estimates} />
          </section>
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
