/**
 * /decarbonisation — portfolio decarbonisation planning (CO₂-forward lens).
 *
 * Server component, auth-guarded (mirrors /actions, /portfolio). Elevates the
 * marginal abatement cost curve into a standalone planning view: portfolio CO₂
 * totals, the MACC chart, and a CapEx-prioritised investment table sorted
 * cheapest-first. Reads the server-authoritative GET /abatement/macc.
 *
 * Relationship to /actions: same gold_recommendations catalog, different lens.
 * /actions = status tracking (operational); here = CO₂ investment planning
 * (strategic). Cross-linked both ways.
 */
import Link from "next/link"
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { SustainabilityMotif } from "@/components/SustainabilityMotif"
import { MaccChart } from "@/components/abatement/MaccChart"
import { InfoTip } from "@/components/ui/info-tip"
import { BuildingSlicer } from "@/components/BuildingSlicer"
import { PageIntro } from "@/components/PageIntro"
import { authOptions } from "@/lib/auth/options"
import { fetchMacc, type MaccResponse } from "@/lib/api/abatement"
import { fetchBuildings } from "@/lib/api/buildings"

const ACCENT = "#1D9E75"

function fmt(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—"
  return Math.round(n).toLocaleString("en-US")
}

function eur(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—"
  return `€${Math.round(n).toLocaleString("en-US")}`
}

export default async function DecarbonisationPage({
  searchParams,
}: {
  searchParams: Promise<{ building_id?: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) redirect("/")

  const { building_id } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0

  const [result, buildingsResult] = await Promise.all([
    fetchMacc(session.accessToken, { limit: 500, ...(scoped ? { building_id } : {}) }),
    fetchBuildings(session.accessToken),
  ])

  // Slicer options = bridged buildings (only those can have abatement data).
  const slicerBuildings = buildingsResult.ok
    ? buildingsResult.data.buildings
        .filter((b) => b.fabric_building_id)
        .map((b) => ({ id: b.fabric_building_id as string, name: b.name }))
    : []
  const scopeName =
    scoped && slicerBuildings.find((b) => b.id === building_id)?.name

  const reportHref = scoped
    ? `/decarbonisation/report?building_id=${encodeURIComponent(building_id!)}`
    : "/decarbonisation/report"

  return (
    <AppChrome
      breadcrumb={[{ label: "Decarbonisation" }]}
      pageTitle="Decarbonisation planning"
      subtitle={
        scoped
          ? `${scopeName ?? building_id} · measures ranked cheapest-first`
          : "All buildings · measures ranked cheapest-first"
      }
      accentColor={ACCENT}
      backHref="/portfolio"
      backLabel="Portfolio"
    >
      <SustainabilityMotif />

      <div className="relative z-10 mx-auto max-w-7xl px-6 py-8 space-y-6">
        <PageIntro id="decarbonisation">
          Plan where to invest for the most CO₂ cut per euro. The curve ranks
          measures cheapest-first — green ones (below €0) pay for themselves. Use the
          building filter to focus on one building.
        </PageIntro>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <BuildingSlicer buildings={slicerBuildings} value={scoped ? building_id! : null} />
          <Link
            href={reportHref}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
          >
            Export PDF
          </Link>
        </div>

        {!result.ok ? (
          <FetchErrorNotice error={result.error} label="abatement data" />
        ) : result.data.measures.length === 0 ? (
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 px-5 py-8 text-sm text-text-muted">
            No abating measures with quantified CO₂ savings
            {scoped ? " for this building" : " yet"}. Recommendations with an annual CO₂
            figure appear here once your buildings are bridged into the analytics layer.
          </div>
        ) : (
          <DecarbBody data={result.data} scoped={scoped} />
        )}
      </div>
    </AppChrome>
  )
}

function DecarbBody({ data, scoped }: { data: MaccResponse; scoped: boolean }) {
  const t = data.totals
  const scopeWord = scoped ? "this building" : "the portfolio"
  const cards = [
    {
      label: "Abatable CO₂",
      value: `${fmt(t.total_annual_co2_t)} tCO₂/yr`,
      sub: `${t.measure_count} measures`,
      tone: "text-text-primary",
    },
    {
      label: "No-regret CO₂",
      value: `${fmt(t.profitable_annual_co2_t)} tCO₂/yr`,
      sub: "measures that pay for themselves",
      tone: "text-brand-emerald",
    },
    {
      label: "No-regret CapEx",
      value: eur(t.profitable_net_capex_eur),
      sub: "self-funding investment",
      tone: "text-brand-emerald",
    },
    {
      label: "Weighted avg cost",
      value:
        t.weighted_avg_mac_eur_per_t === null
          ? "—"
          : `€${fmt(t.weighted_avg_mac_eur_per_t)}/tCO₂`,
      sub: `CO₂-weighted across ${scopeWord}`,
      tone: "text-text-primary",
    },
  ]

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <div key={c.label} className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
            <div className="text-xs text-text-faint">{c.label}</div>
            <div className={`mt-1 text-xl font-semibold ${c.tone}`}>{c.value}</div>
            <div className="mt-0.5 text-[11px] text-text-muted">{c.sub}</div>
          </div>
        ))}
      </div>

      <p className="-mt-2 text-[11px] leading-relaxed text-text-faint">
        Abatable CO₂ sums each measure&apos;s independent estimate. Overlapping
        measures (CHP, BMS and heat recovery can target the same kWh) are scaled to a
        realistic share of {scopeWord}&apos;s actual emissions, so read this as an
        indicative plan — not the literal arithmetic sum, and not audited finance.
      </p>

      {/* MACC chart */}
      <section className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-text-primary">
              Marginal abatement cost curve
              <InfoTip term="abatement_cost" className="ml-1.5" />
            </h2>
            <p className="mt-0.5 max-w-2xl text-xs text-text-muted">
              Each bar is one improvement measure. <strong className="font-medium text-text-primary">Width</strong> = how
              much CO₂ it cuts per year; <strong className="font-medium text-text-primary">height</strong> = cost per
              tonne. Below the €0 line (green) the measure <strong className="font-medium text-text-primary">saves money</strong> over
              its life; above it (amber/orange) it costs money. Cheapest-to-abate on the left.
            </p>
          </div>
          <Link
            href="/actions"
            className="shrink-0 text-xs text-text-muted transition-colors hover:text-brand-emerald"
          >
            Track status in Actions →
          </Link>
        </div>
        <div className="mt-4">
          <MaccChart measures={data.measures} />
        </div>
      </section>

      {/* Prioritised investment table */}
      <section className="overflow-hidden rounded-xl border border-border-subtle bg-bg-elevated/40">
        <header className="border-b border-border-subtle px-5 py-3">
          <h2 className="text-sm font-semibold text-text-primary">
            Prioritised investment plan
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Cheapest abatement first. No-regret measures (green) fund themselves over
            their lifetime.
          </p>
        </header>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted">
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">Measure</th>
                <th className="px-3 py-2 font-medium">Building</th>
                <th className="px-3 py-2 font-medium text-right">€/tCO₂</th>
                <th className="px-3 py-2 font-medium text-right">tCO₂/yr</th>
                <th className="px-3 py-2 font-medium text-right">Net CapEx</th>
                <th className="px-3 py-2 font-medium text-right">€/yr saved</th>
                <th className="px-3 py-2 font-medium text-right">Σ tCO₂</th>
                <th className="px-3 py-2 font-medium">Driver</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {data.measures.map((m, i) => (
                <tr key={m.action_id} className="hover:bg-white/5">
                  <td className="px-3 py-2 text-text-faint">{i + 1}</td>
                  <td className="px-3 py-2">
                    <span className="text-text-primary">{m.title ?? "Measure"}</span>
                    {m.action_type && (
                      <span className="ml-1.5 text-[11px] text-text-faint">{m.action_type}</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-text-muted">{m.building_name}</td>
                  <td
                    className={`px-3 py-2 text-right font-medium ${
                      m.is_profitable ? "text-brand-emerald" : "text-text-primary"
                    }`}
                  >
                    {eur(m.mac_eur_per_t)}
                  </td>
                  <td className="px-3 py-2 text-right text-text-muted">{fmt(m.annual_co2_t)}</td>
                  <td className="px-3 py-2 text-right text-text-muted">{eur(m.net_capex_eur)}</td>
                  <td className="px-3 py-2 text-right text-text-muted">{eur(m.annual_saving_eur)}</td>
                  <td className="px-3 py-2 text-right text-text-faint">{fmt(m.cumulative_co2_t)}</td>
                  <td className="px-3 py-2 text-[11px] text-text-faint">
                    {m.compliance_driver ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="text-[11px] leading-relaxed text-text-faint">{data.note}</p>
    </div>
  )
}
