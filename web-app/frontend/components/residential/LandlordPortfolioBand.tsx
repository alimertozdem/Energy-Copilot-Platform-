/**
 * LandlordPortfolioBand — portfolio-wide landlord investment potential (R3b).
 *
 * The portfolio counterpart of LandlordInvestmentCase: aggregates the recommended
 * measures across the manager's RESIDENTIAL buildings into one owner-economics
 * summary — total net CapEx, subsidy, the Modernisierungsumlage rent uplift the
 * owner can pass on, and the tenant energy saving. Frontend-only; reads the same
 * /actions catalogue, filtered to residential buildings. Indicative.
 */
import { InfoTip } from "@/components/ui/info-tip"
import type { ActionItem } from "@/lib/api/actions"
import type { TermKey } from "@/lib/glossary"

const MODERNISIERUNG_RATE = 0.08 // §559 BGB, general case (see LandlordInvestmentCase)

function eur(n: number): string {
  return "€" + Math.round(n).toLocaleString("en-US")
}

function netCapexOf(a: ActionItem): number {
  if (a.net_capex_eur != null) return a.net_capex_eur
  return Math.max((a.capex_eur ?? 0) - (a.grant_eur ?? 0), 0)
}

export function LandlordPortfolioBand({
  actions,
  residentialIds,
}: {
  actions: ActionItem[]
  residentialIds: string[]
}) {
  const idSet = new Set(residentialIds)
  const measures = actions.filter(
    (a) => idSet.has(a.fabric_building_id) && (a.capex_eur ?? a.net_capex_eur ?? 0) > 0
  )
  if (measures.length === 0) return null

  const netCapex = measures.reduce((s, a) => s + netCapexOf(a), 0)
  const subsidy = measures.reduce((s, a) => s + (a.grant_eur ?? 0), 0)
  const tenantSaving = measures.reduce((s, a) => s + (a.annual_saving_eur ?? 0), 0)
  const rentUplift = netCapex * MODERNISIERUNG_RATE
  const buildings = new Set(measures.map((a) => a.fabric_building_id)).size

  const stats: { label: string; value: string; sub: string; tone: string; term?: TermKey }[] = [
    { label: "Net investment", value: eur(netCapex), sub: "after subsidy", tone: "text-text-primary" },
    { label: "Subsidy", value: eur(subsidy), sub: "BAFA / KfW", tone: "text-brand-emerald", term: "subsidy" },
    { label: "Rent uplift", value: `${eur(rentUplift)}/yr`, sub: "Modernisierungsumlage", tone: "text-brand-emerald" },
    { label: "Tenant saving", value: `${eur(tenantSaving)}/yr`, sub: "energy", tone: "text-text-primary", term: "retrofit_saving" },
  ]

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
      <div>
        <h2 className="text-sm font-semibold text-text-primary">Investment potential</h2>
        <p className="mt-0.5 text-xs text-text-muted">
          Across {buildings} residential {buildings === 1 ? "building" : "buildings"} with
          recommended measures — the owner&rsquo;s economics, not just tenant bills.
        </p>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2.5">
            <div className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-text-faint">{s.label}{s.term && <InfoTip term={s.term} />}</div>
            <div className={`mt-0.5 text-lg font-semibold ${s.tone}`}>{s.value}</div>
            <div className="text-[10px] text-text-muted">{s.sub}</div>
          </div>
        ))}
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-text-faint">
        Indicative. Modernisierungsumlage per §559 BGB (8% of net cost/yr, statutory caps
        apply; heating upgrades have special limits). Open a building for its detailed case.
      </p>
    </section>
  )
}
