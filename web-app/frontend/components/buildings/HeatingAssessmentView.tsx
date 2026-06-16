/**
 * HeatingAssessmentView — the demand + envelope + retrofit-ROI core of the
 * Heating & HVAC page. Honest by design: every figure is screening-grade, the
 * basis (measured vs estimated) is shown, and the assumptions are surfaced.
 */
import { Flame, Snowflake, Square } from "lucide-react"

import type { HeatingAssessment, HeatingMeasure } from "@/lib/api/heating"

function fmtEnergy(kwh: number): string {
  if (kwh >= 1_000_000) return `${(kwh / 1_000_000).toFixed(1)} GWh`
  if (kwh >= 1_000) return `${(kwh / 1_000).toFixed(0)} MWh`
  return `${Math.round(kwh)} kWh`
}
function eur(n: number): string {
  return "€" + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}
function tco2(kg: number): string {
  return `${(kg / 1000).toFixed(1)} t`
}

const EL_LABEL: Record<string, string> = { wall: "Walls", roof: "Roof", window: "Windows" }

function Tile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <div className="text-[11px] uppercase tracking-wide text-text-faint">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums text-text-primary">{value}</div>
      {sub && <div className="mt-0.5 text-[11px] text-text-faint">{sub}</div>}
    </div>
  )
}

function EnvChip({ el }: { el: HeatingAssessment["envelope"][number] }) {
  const tone =
    el.status === "pass"
      ? "border-brand-emerald/30 bg-brand-emerald/5 text-brand-emerald"
      : el.status === "fail"
        ? "border-red-400/30 bg-red-400/5 text-red-300"
        : "border-border-subtle bg-white/[0.02] text-text-muted"
  return (
    <div className={`rounded-lg border px-3 py-2 text-xs ${tone}`}>
      <div className="flex items-center gap-1.5 font-medium">
        <Square className="h-3 w-3" aria-hidden /> {EL_LABEL[el.element] ?? el.element}
      </div>
      <div className="mt-1 tabular-nums">
        {el.u_current != null ? `U ${el.u_current}` : "U —"}
        <span className="text-text-faint"> / target {el.u_target}</span>
      </div>
      <div className="text-[10px] uppercase tracking-wide">
        {el.status === "pass" ? "GEG ok" : el.status === "fail" ? "above limit" : "unknown"}
      </div>
    </div>
  )
}

export function HeatingAssessmentView({ data }: { data: HeatingAssessment }) {
  const d = data.demand
  const s = data.supply
  const estimated = d.basis !== "measured"

  return (
    <div className="space-y-6">
      {/* Demand + supply hero */}
      <section>
        <div className="mb-3 flex items-center gap-2">
          <Flame className="h-4 w-4 text-amber-300" aria-hidden />
          <h2 className="text-sm font-semibold text-text-primary">Heat demand &amp; cost</h2>
          <span
            className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${
              estimated
                ? "border-amber-400/30 bg-amber-400/5 text-amber-300"
                : "border-brand-emerald/30 bg-brand-emerald/5 text-brand-emerald"
            }`}
          >
            {estimated ? "Estimated" : "From your data"}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Tile label="Heating energy / yr" value={fmtEnergy(d.heating_kwh)} sub={`${d.heating_share_pct}% of total`} />
          <Tile label="Heating intensity" value={d.heating_eui_kwh_m2 != null ? String(d.heating_eui_kwh_m2) : "—"} sub="kWh/m²·yr" />
          <Tile label="Heat cost / yr" value={eur(s.heat_cost_eur)} sub={`${s.fuel_type} · ${s.price_eur_kwh} €/kWh`} />
          <Tile label="Heat CO₂ / yr" value={tco2(s.heat_co2_kg)} sub={`${s.co2_factor_kg_kwh} kg/kWh`} />
        </div>
      </section>

      {/* Envelope vs GEG */}
      <section>
        <div className="mb-2 flex items-center gap-2">
          <Snowflake className="h-4 w-4 text-sky-300" aria-hidden />
          <h2 className="text-sm font-semibold text-text-primary">Envelope vs GEG</h2>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {data.envelope.map((el) => (
            <EnvChip key={el.element} el={el} />
          ))}
        </div>
        <p className="mt-2 text-[11px] text-text-faint">
          GEG Anlage 7 component limits (apply when a component is renovated). Unknown = U-value not
          on file; add it on the building&rsquo;s envelope details to sharpen the figures.
        </p>
      </section>

      {/* Retrofit measures */}
      <section>
        <h2 className="mb-2 text-sm font-semibold text-text-primary">Retrofit measures — by payback</h2>
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full text-xs">
            <thead className="text-left text-text-faint">
              <tr className="border-b border-border-subtle">
                <th className="px-3 py-2 font-medium">Measure</th>
                <th className="px-3 py-2 font-medium">Tier</th>
                <th className="px-3 py-2 text-right font-medium">Saves / yr</th>
                <th className="px-3 py-2 text-right font-medium">€ / yr</th>
                <th className="px-3 py-2 text-right font-medium">CO₂ / yr</th>
                <th className="px-3 py-2 text-right font-medium">Net CapEx</th>
                <th className="px-3 py-2 text-right font-medium">Payback</th>
              </tr>
            </thead>
            <tbody>
              {data.measures.map((m: HeatingMeasure) => (
                <tr key={m.key} className="border-b border-border-subtle/60">
                  <td className="px-3 py-2">
                    <div className="text-text-primary">{m.label}</div>
                    <div className="text-[10px] text-text-faint">{m.note}</div>
                  </td>
                  <td className="px-3 py-2 text-text-muted">{m.tier}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-muted">
                    {m.saving_kwh != null ? fmtEnergy(m.saving_kwh) : "switch"}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-brand-emerald">{eur(m.saving_eur)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-muted">{tco2(m.saving_co2_kg)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-muted">{eur(m.capex_net)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-primary">
                    {m.payback_years != null ? `${m.payback_years} yr` : "—"}
                  </td>
                </tr>
              ))}
              {data.measures.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-4 text-center text-text-faint">
                    Add floor area + envelope details to compute retrofit measures.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-text-faint">
          {data.package.note} Net CapEx is after subsidy. {data.assumptions.subsidy} {data.assumptions.method}{" "}
          <span className="text-text-muted">{data.assumptions.grade}</span>
        </p>
      </section>
    </div>
  )
}
