/**
 * EngineEstimateCard — the Tier-A screening estimate as a {low–point–high} band
 * with a confidence tier and the method that produced it.
 *
 * Honest by construction: tagged Estimated (amber) or Actual (emerald, once ≥12
 * months of bills exist), shows the confidence, the method chain, the cost/CO₂
 * fuel basis, and which inputs to edit to tighten the range. Pure presentational.
 * Mirrors lib/api/estimation.ts::EngineEstimate.
 */
import { BadgeCheck, Sparkles } from "lucide-react"
import { DataProvenanceBadge } from "@/components/ui/DataProvenanceBadge"

import type { EngineEstimate } from "@/lib/api/estimation"

const CONF: Record<string, { label: string; cls: string }> = {
  high: { label: "High confidence", cls: "border-emerald-400/40 bg-emerald-400/10 text-emerald-300" },
  medium: { label: "Medium confidence", cls: "border-amber-400/40 bg-amber-400/10 text-amber-300" },
  low: { label: "Low confidence", cls: "border-amber-400/40 bg-amber-400/10 text-amber-300" },
  very_low: { label: "Very low confidence", cls: "border-orange-400/40 bg-orange-400/10 text-orange-300" },
}

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

function Band({ label, low, point, high, unit }: { label: string; low: string; point: string; high: string; unit?: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="text-[11px] uppercase tracking-wide text-text-faint">{label}</div>
      <div className="mt-1 text-lg font-semibold text-text-primary tabular-nums">
        {point}
        {unit && <span className="ml-1 text-xs font-normal text-text-muted">{unit}</span>}
      </div>
      <div className="mt-0.5 text-[11px] text-text-faint tabular-nums">
        {low} <span className="text-text-faint">–</span> {high}
      </div>
    </div>
  )
}

export function EngineEstimateCard({ estimate: e }: { estimate: EngineEstimate }) {
  const actual = e.basis === "actual"
  const conf = CONF[e.confidence] ?? CONF.low
  const hasEnergy = e.annual_kwh_point != null
  const fuel = e.cost_basis?.startsWith("fuel_split")
    ? e.cost_basis.replace("fuel_split_", "").replace("_", " ")
    : null

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {actual ? (
            <BadgeCheck className="h-4 w-4 text-emerald-300" aria-hidden />
          ) : (
            <Sparkles className="h-4 w-4 text-amber-300" aria-hidden />
          )}
          <h3 className="text-sm font-semibold text-text-primary">
            {actual ? "Energy profile" : "Estimated preview"}
          </h3>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${conf.cls}`}>
            {conf.label}
          </span>
          <DataProvenanceBadge basis={actual ? "measured" : "estimated"} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {e.eui_point != null && (
          <Band label="EUI" low={String(Math.round(e.eui_low ?? 0))} point={String(Math.round(e.eui_point))} high={String(Math.round(e.eui_high ?? 0))} unit="kWh/m²·yr" />
        )}
        {hasEnergy && (
          <Band label="Energy / yr" low={fmtEnergy(e.annual_kwh_low ?? 0)} point={fmtEnergy(e.annual_kwh_point ?? 0)} high={fmtEnergy(e.annual_kwh_high ?? 0)} />
        )}
        {e.annual_co2_kg_point != null && (
          <Band label="CO₂ / yr" low={fmtCo2(e.annual_co2_kg_low ?? 0)} point={fmtCo2(e.annual_co2_kg_point ?? 0)} high={fmtCo2(e.annual_co2_kg_high ?? 0)} />
        )}
        {e.annual_cost_eur_point != null && (
          <Band label="Cost / yr" low={eur(e.annual_cost_eur_low ?? 0)} point={eur(e.annual_cost_eur_point ?? 0)} high={eur(e.annual_cost_eur_high ?? 0)} />
        )}
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-text-faint">
        {actual
          ? "Based on your uploaded consumption (≥12 months). "
          : "Screening estimate, refined by what we know about this building. "}
        Method: {e.method}.{" "}
        {fuel
          ? `Cost & CO₂ put the heating share on ${fuel} and the rest on electricity.`
          : "Cost & CO₂ use an electricity-equivalent proxy (heating fuel unknown)."}
        {!actual && e.editable_fields?.length > 0 && (
          <> Edit {e.editable_fields.slice(0, 3).join(", ")} to tighten the range.</>
        )}
      </p>
    </div>
  )
}
