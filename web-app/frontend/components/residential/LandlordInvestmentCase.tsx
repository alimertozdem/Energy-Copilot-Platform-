/**
 * LandlordInvestmentCase — the residential "why invest" lens (R3 upsell).
 *
 * Solves the split-incentive problem: the tenant gets the energy savings, so the
 * landlord needs a different reason to invest. This card frames the OWNER's
 * economics from the building's recommended measures (reused from /actions):
 *   • subsidy (BAFA/KfW grant) cuts the upfront cost,
 *   • Modernisierungsumlage (§559 BGB) lets the owner pass ~8%/yr of the net
 *     modernisation cost onto rent — recovering the investment,
 *   • a poor EPC band flags MEPS stranding risk (lettability + asset value).
 *
 * Frontend-only: computed from the actions payload + the building's EPC. All
 * figures are indicative decision-support, not legal/financial advice.
 */
import type { ActionItem } from "@/lib/api/actions"

// §559 BGB: the landlord may raise annual rent by up to 8% of the modernisation
// cost (after deducting public subsidies). Stated assumption — caps apply.
const MODERNISIERUNG_RATE = 0.08
const STRANDING_BANDS = new Set(["D", "E", "F", "G"])

function eur(n: number | null): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—"
  return "€" + Math.round(n).toLocaleString("en-US")
}

function netCapexOf(a: ActionItem): number {
  if (a.net_capex_eur != null) return a.net_capex_eur
  const gross = a.capex_eur ?? 0
  const grant = a.grant_eur ?? 0
  return Math.max(gross - grant, 0)
}

export function LandlordInvestmentCase({
  actions,
  epcClass,
}: {
  actions: ActionItem[]
  epcClass: string | null
}) {
  const measures = actions.filter(
    (a) => (a.capex_eur ?? a.net_capex_eur ?? 0) > 0
  )
  const stranding = epcClass != null && STRANDING_BANDS.has(epcClass.toUpperCase())

  // Nothing to compute and no stranding signal → don't show an empty card.
  if (measures.length === 0 && !stranding) return null

  const grossCapex = measures.reduce((s, a) => s + (a.capex_eur ?? netCapexOf(a)), 0)
  const subsidy = measures.reduce((s, a) => s + (a.grant_eur ?? 0), 0)
  const netCapex = measures.reduce((s, a) => s + netCapexOf(a), 0)
  const tenantSaving = measures.reduce((s, a) => s + (a.annual_saving_eur ?? 0), 0)
  const rentUplift = netCapex * MODERNISIERUNG_RATE
  const recoveryYears = rentUplift > 0 ? netCapex / rentUplift : null

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-text-primary">Landlord investment case</h2>
          <p className="mt-0.5 text-xs text-text-muted">
            Why the owner invests — even though tenants get the energy savings.
          </p>
        </div>
        {stranding && (
          <span className="shrink-0 rounded-full border border-amber-400/30 bg-amber-400/10 px-2.5 py-1 text-[11px] font-medium text-amber-300">
            EPC {epcClass?.toUpperCase()} · MEPS stranding risk
          </span>
        )}
      </div>

      {measures.length === 0 ? (
        <p className="mt-4 text-sm text-text-muted">
          No quantified measures yet for this building. Once recommendations carry a
          CapEx figure, the subsidy, rent uplift and recovery appear here.
        </p>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Metric label="Investment" value={eur(grossCapex)} sub="gross CapEx" />
            <Metric label="Subsidy" value={eur(subsidy)} sub="BAFA / KfW" tone="text-brand-emerald" />
            <Metric label="Net cost" value={eur(netCapex)} sub="after subsidy" />
            <Metric
              label="Rent uplift"
              value={`${eur(rentUplift)}/yr`}
              sub="Modernisierungsumlage"
              tone="text-brand-emerald"
            />
          </div>

          <div className="mt-4 space-y-2 text-sm text-text-primary/90">
            <Line>
              <span className="text-text-muted">The owner can pass </span>
              ~{eur(rentUplift)}/yr
              <span className="text-text-muted">
                {" "}onto rent (§559, 8% of net cost){recoveryYears
                  ? ` — recovering the net cost in about ${Math.round(recoveryYears)} years`
                  : ""}.
              </span>
            </Line>
            <Line>
              <span className="text-text-muted">Tenants save </span>
              {eur(tenantSaving)}/yr
              <span className="text-text-muted">
                {" "}on energy — lower bills ease the rent adjustment and reduce turnover.
              </span>
            </Line>
            {stranding && (
              <Line>
                <span className="text-text-muted">EPC {epcClass?.toUpperCase()} exposes the asset to </span>
                MEPS stranding
                <span className="text-text-muted">
                  {" "}— investing protects lettability and value as minimum standards tighten.
                </span>
              </Line>
            )}
          </div>
        </>
      )}

      <p className="mt-4 text-[11px] leading-relaxed text-text-faint">
        Indicative decision-support, not legal or financial advice. Modernisierungsumlage
        per §559 BGB: 8% of the net cost per year, subject to statutory caps
        (≈ €3/m² over 6 years; €2/m² below €7/m² rent). Heating upgrades have special
        limits (≈ €0.50/m²·6yr; a 10% rate with public funding under §559e). Subsidy and
        CapEx figures from the recommendation catalogue.
      </p>
    </section>
  )
}

function Metric({
  label,
  value,
  sub,
  tone = "text-text-primary",
}: {
  label: string
  value: string
  sub: string
  tone?: string
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2.5">
      <div className="text-[10px] uppercase tracking-wider text-text-faint">{label}</div>
      <div className={`mt-0.5 text-lg font-semibold ${tone}`}>{value}</div>
      <div className="text-[10px] text-text-muted">{sub}</div>
    </div>
  )
}

function Line({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex gap-2 leading-relaxed">
      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-emerald" aria-hidden />
      <span className="font-medium">{children}</span>
    </p>
  )
}
