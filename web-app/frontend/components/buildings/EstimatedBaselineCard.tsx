/**
 * EstimatedBaselineCard — provisional, clearly-labeled baseline shown on a
 * building that has metadata (type + area) but no uploaded consumption yet.
 *
 * Pure presentational. Every figure is a RANGE (low–high) and the card is
 * explicitly tagged "Estimated" so it can never be mistaken for measured data —
 * it disappears the moment a real baseline is uploaded. Cost/CO₂ apply the real
 * tariff + grid factor to the energy range, with the honest electricity-
 * equivalent caveat for mixed-fuel buildings.
 */
import { Sparkles } from "lucide-react"

import type { BaselineEstimate } from "@/lib/api/baseline"

function fmtEnergy(kwh: number): string {
  if (kwh >= 1_000_000) return `${(kwh / 1_000_000).toFixed(1)} GWh`
  if (kwh >= 1_000) return `${(kwh / 1_000).toFixed(0)} MWh`
  return `${Math.round(kwh)} kWh`
}
function fmtCo2(kg: number): string {
  return kg >= 1_000 ? `${(kg / 1_000).toFixed(1)} t` : `${Math.round(kg)} kg`
}
function eur(n: number): string {
  return "€" + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}

function RangeTile({ label, low, high, unit }: { label: string; low: string; high: string; unit?: string }) {
  return (
    <div className="rounded-xl border border-amber-400/20 bg-amber-400/[0.03] p-4">
      <div className="text-[11px] uppercase tracking-wide text-text-faint">{label}</div>
      <div className="mt-1 text-lg font-semibold text-text-primary tabular-nums">
        {low}
        <span className="mx-1 text-text-faint">–</span>
        {high}
        {unit && <span className="ml-1 text-xs font-normal text-text-muted">{unit}</span>}
      </div>
    </div>
  )
}

export function EstimatedBaselineCard({ estimate }: { estimate: BaselineEstimate }) {
  const e = estimate
  return (
    <div className="rounded-xl border border-amber-400/30 bg-amber-400/[0.04] p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-amber-300" aria-hidden />
          <h3 className="text-sm font-semibold text-text-primary">Estimated preview</h3>
        </div>
        <span className="rounded border border-amber-400/40 bg-amber-400/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-300">
          Estimated
        </span>
      </div>

      <p className="mb-3 text-xs text-text-muted">
        No data uploaded yet — this is a rough estimate from your building type and floor area, so
        you can see what to expect. Upload a bill or meter CSV to replace it with your real figures.
      </p>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <RangeTile label="EUI" low={String(Math.round(e.eui_low))} high={String(Math.round(e.eui_high))} unit="kWh/m²·yr" />
        <RangeTile label="Energy / yr" low={fmtEnergy(e.annual_kwh_low)} high={fmtEnergy(e.annual_kwh_high)} />
        <RangeTile label="CO₂ / yr" low={fmtCo2(e.annual_co2_kg_low)} high={fmtCo2(e.annual_co2_kg_high)} />
        <RangeTile label="Cost / yr" low={eur(e.annual_cost_eur_low)} high={eur(e.annual_cost_eur_high)} />
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-text-faint">
        Estimated from a typical {e.building_type ?? "building"} intensity × floor area.
        {" "}Cost &amp; CO₂ apply the {e.country_code ?? "local"} {e.year} electricity tariff &amp; grid
        factor as an electricity-equivalent proxy — a mixed-fuel building (e.g. gas heating) will differ
        once a bill is on file.
        {!e.type_modeled && " Your building type isn't separately modelled, so a general typical was used."}
      </p>
    </div>
  )
}
