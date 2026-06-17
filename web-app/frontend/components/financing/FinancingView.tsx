/**
 * FinancingView — portfolio financing & subsidy (decision-support).
 *
 * Consumes GET /financing/summary (finance_model): unit-aware subsidy ranges,
 * three-scenario discounted NPV (energy + carbon escalation), indicative EPC value
 * uplift, and a transparent method panel with a currency stamp. SUPPORT, NOT ADVICE.
 */
import Link from "next/link"
import { Landmark, TrendingUp, Building2, Info } from "lucide-react"

import type { FinancingSummary, FinancingScenario } from "@/lib/api/financing"
import { InfoTip } from "@/components/ui/info-tip"
import type { TermKey } from "@/lib/glossary"

function eur(n: number | null): string {
  if (n === null || Number.isNaN(n)) return "—"
  const abs = Math.abs(n)
  const s = abs >= 10000
    ? new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n)
    : new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
  return "€" + s
}
function eurRange(lo: number | null, hi: number | null): string {
  if (lo == null && hi == null) return "—"
  if (lo === hi || hi == null) return eur(lo)
  if (lo == null) return eur(hi)
  return `${eur(lo)}–${eur(hi)}`
}

const SCEN_LABEL: Record<string, string> = {
  conservative: "Conservative",
  base: "Base",
  high: "Policy-tight",
}

function Card({ label, value, hint, tone, term }: {
  label: string; value: string; hint?: string; tone?: "good"; term?: TermKey
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-elevated/40 p-4">
      <p className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
        {label}
        {term && <InfoTip term={term} />}
      </p>
      <p className={`mt-1.5 text-2xl font-semibold ${tone === "good" ? "text-brand-emerald" : "text-text-primary"}`}>{value}</p>
      {hint && <p className="mt-1 text-[11px] text-text-faint">{hint}</p>}
    </div>
  )
}

function ScenarioCard({ s }: { s: FinancingScenario }) {
  const positive = s.total_npv_eur >= 0
  return (
    <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-4">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
        {SCEN_LABEL[s.scenario] ?? s.scenario}
      </div>
      <div className={`mt-1 text-xl font-semibold tabular-nums ${positive ? "text-brand-emerald" : "text-red-300"}`}>
        {eur(s.total_npv_eur)}
      </div>
      <div className="mt-0.5 text-[11px] text-text-faint">portfolio NPV</div>
      <div className="mt-2 text-[11px] text-text-faint">
        carbon €{s.carbon_2030_eur_t}/t @2030 · energy +{s.energy_inflation_pct}%/yr
      </div>
    </div>
  )
}

export function FinancingView({ summary }: { summary: FinancingSummary }) {
  const { measures, portfolio: p } = summary
  const a = summary.assumptions as Record<string, unknown>
  const carbon2030 = (a.carbon_2030_eur_t ?? {}) as Record<string, number>

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-xs leading-relaxed text-amber-200/90">
        <span>
          Indicative financing <span className="font-semibold">support</span> — not financial advice.
          Programmes &amp; carbon prices change; <span className="font-semibold">apply before signing any contract</span>.
        </span>
        <span className="ml-auto rounded border border-border-subtle/60 px-2 py-0.5 text-[10px] uppercase tracking-wide text-text-faint">
          Rates verified {String(a.rates_verified ?? "")}
        </span>
      </div>

      {/* Portfolio subsidy headline */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card label="Indicative grant" value={eurRange(p.total_grant_low_eur, p.total_grant_high_eur)} hint="rate range across eligible measures" tone="good" term="subsidy" />
        <Card label="Eligible measures" value={String(p.eligible_measure_count)} />
        <Card label="Gross capex" value={eur(p.total_capex_gross_eur)} />
        <Card label="Net after grant" value={eur(p.total_net_after_grant_eur)} hint="grant-midpoint" />
      </div>

      {/* Scenario NPV — the decision artifact */}
      {p.scenarios.length > 0 && (
        <section>
          <div className="mb-2 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-brand-emerald" aria-hidden />
            <h2 className="text-sm font-semibold text-text-primary">Lifetime value — discounted, by scenario</h2>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {p.scenarios.map((s) => <ScenarioCard key={s.scenario} s={s} />)}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-text-faint">
            Portfolio NPV of the eligible measures over their service life, discounted at{" "}
            {String(a.discount_rate_pct ?? "")}%/yr, net of the grant. Scenarios escalate energy prices and the
            carbon price (today €{String(a.carbon_now_eur_t ?? "")}/t → €{carbon2030.conservative}–€{carbon2030.high}/t by 2030).
            A positive NPV means the investment pays back over its life, including rising carbon costs avoided.
          </p>
        </section>
      )}

      {/* Value uplift */}
      {p.value_uplift && p.value_uplift.priority_buildings > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-sky-500/30 bg-sky-500/5 px-4 py-3 text-xs text-sky-200/90">
          <Building2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <div>
            <span className="font-medium">
              Indicative value uplift: +{p.value_uplift.uplift_low_pct}–{p.value_uplift.uplift_high_pct}%
            </span>{" "}
            for {p.value_uplift.priority_buildings} renovation-priority building(s) if improved ~{p.value_uplift.assumed_band_jump} EPC classes.
            <div className="mt-0.5 text-[11px] text-text-faint">{p.value_uplift.note}</div>
          </div>
        </div>
      )}

      {/* Measures table */}
      {measures.length === 0 ? (
        <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-6">
          <p className="text-sm font-semibold text-text-primary">No grant-eligible measures yet.</p>
          <p className="mt-1 text-sm text-text-muted">
            Heating, envelope and controls recommendations with a capex estimate map to KfW/BAFA here.
            Solar PV is funded separately (EEG).
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border-subtle bg-bg-elevated/40">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-wider text-text-muted">
                <th className="px-4 py-3 font-semibold">Measure</th>
                <th className="px-4 py-3 font-semibold">Building</th>
                <th className="px-4 py-3 font-semibold">Programme</th>
                <th className="px-4 py-3 text-right font-semibold">Rate</th>
                <th className="px-4 py-3 text-right font-semibold">Grant (range)</th>
                <th className="px-4 py-3 text-right font-semibold">Payback</th>
                <th className="px-4 py-3 text-right font-semibold">NPV (base)</th>
              </tr>
            </thead>
            <tbody>
              {measures.map((m, i) => (
                <tr key={i} className="border-b border-border-subtle/60 text-text-primary/90">
                  <td className="px-4 py-2.5">
                    <div className="font-medium">{m.title}</div>
                    <div className="text-[11px] text-text-faint">{m.subsidy_note}</div>
                  </td>
                  <td className="px-4 py-2.5 text-text-muted">{m.building_name}</td>
                  <td className="px-4 py-2.5">
                    {m.eligible ? (
                      <span className="rounded-md border border-brand-emerald/30 bg-brand-emerald/5 px-2 py-0.5 text-xs text-brand-emerald">{m.program}</span>
                    ) : (
                      <span className="text-xs text-text-faint">{m.program}</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-text-muted">
                    {m.rate_low_pct}{m.rate_high_pct > m.rate_low_pct ? `–${m.rate_high_pct}` : ""}%
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-brand-emerald">{eurRange(m.grant_low_eur, m.grant_high_eur)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-text-muted">{m.simple_payback_years != null ? `${m.simple_payback_years} yr` : "—"}</td>
                  <td className={`px-4 py-2.5 text-right tabular-nums ${m.npv_base_eur != null && m.npv_base_eur < 0 ? "text-red-300" : "text-text-primary"}`}>
                    {m.npv_base_eur != null ? eur(m.npv_base_eur) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Transparent method panel */}
      <details className="rounded-lg border border-border-subtle bg-bg-elevated/30 px-4 py-3">
        <summary className="flex cursor-pointer items-center gap-2 text-xs font-semibold text-text-muted">
          <Info className="h-3.5 w-3.5" aria-hidden /> Method &amp; assumptions
        </summary>
        <div className="mt-2 space-y-1.5 text-[11px] leading-relaxed text-text-faint">
          <p><span className="text-text-muted">Discount rate:</span> {String(a.discount_rate_pct ?? "")}%/yr real · general inflation {String(a.general_inflation_pct ?? "")}%/yr.</p>
          <p><span className="text-text-muted">Carbon:</span> {String(a.carbon_note ?? "")}</p>
          <p><span className="text-text-muted">Subsidy:</span> {String(a.subsidy_note ?? "")}</p>
          <p><span className="text-text-muted">Value uplift:</span> {String(a.value_uplift_note ?? "")}</p>
          <p><span className="text-text-muted">Rates verified:</span> {String(a.rates_verified ?? "")}. {summary.note}</p>
        </div>
      </details>

      <p className="text-[11px] text-text-faint">
        Subsidy &amp; financing detail:{" "}
        <Link href="/hvac" className="text-brand-emerald hover:underline">Heating &amp; HVAC</Link>{" "}
        · Portfolio CO₂ plan:{" "}
        <Link href="/decarbonisation" className="text-brand-emerald hover:underline">Decarbonisation</Link>
      </p>
    </div>
  )
}
