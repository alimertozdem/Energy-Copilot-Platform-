"use client"

/**
 * BuildingBaselineStrip — lights up a PENDING building's card from its uploaded
 * consumption baseline (Tier-1). Client-fetches /api/buildings/{uuid}/kpis; when
 * the building has uploaded data it shows indicative KPI chips (EUI, annual
 * energy, CO₂) + an honest provenance label, plus the single most relevant AI
 * advisor insight (the same engine as the detail-page advisor, fed the baseline
 * KPIs). Renders nothing when there's no uploaded data — no clutter, no fakery.
 *
 * It sits inside the card's <Link>, so the insight is plain text (no nested
 * anchor / CTA). The full advisor lives on the detail page for bridged buildings.
 */
import { useEffect, useState } from "react"

import { fetchBuildingBaselineKpis, type BaselineKpis } from "@/lib/api/baseline"
import type { Building } from "@/lib/api/buildings"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import {
  buildAdvisorInsights,
  type Insight,
  type InsightSeverity,
} from "@/lib/insights/buildingAdvisor"

const SEV_DOT: Record<InsightSeverity, string> = {
  action: "bg-red-400",
  watch: "bg-amber-400",
  info: "bg-sky-400",
  good: "bg-brand-emerald",
}

function fmtEnergy(kwh: number): string {
  if (kwh >= 1_000_000) return `${(kwh / 1_000_000).toFixed(1)} GWh`
  if (kwh >= 1_000) return `${(kwh / 1_000).toFixed(0)} MWh`
  return `${Math.round(kwh)} kWh`
}

function fmtCo2(kg: number): string {
  if (kg >= 1_000) return `${(kg / 1_000).toFixed(1)} t`
  return `${Math.round(kg)} kg`
}

/** Map the baseline KPIs onto the advisor's commercial KPI row so the same
 *  insight engine runs (EUI benchmark, EPC, asset nudges). Counts are 0 (no
 *  live alerts/recommendations yet), so those insights stay silent. */
function toRow(b: Building, k: BaselineKpis): PortfolioBuildingRow {
  return {
    fabric_building_id: "",
    name: b.name,
    city: b.city ?? "",
    country: b.country_code ?? "",
    building_type: b.building_type ?? "",
    floor_area_m2: b.floor_area_m2 ?? 0,
    epc_class: b.epc_class,
    kwh_30d: k.kwh_30d ?? 0,
    cost_30d_eur: k.cost_30d_eur ?? 0,
    co2_30d_kg: k.co2_30d_kg ?? 0,
    eui_kwh_m2_yr: k.eui_kwh_m2_yr,
    open_anomalies: 0,
    open_recommendations: 0,
    has_pv: (b.pv_capacity_kwp ?? 0) > 0,
    has_battery: b.modules.some((m) => m.module_key === "battery" && m.enabled),
    has_iot: b.modules.some((m) => m.module_key === "iot" && m.enabled),
    subscription_tier: "Monitor",
  }
}

function provenance(k: BaselineKpis): string {
  const basis = k.is_annualized
    ? `${k.months_available} mo, annualized`
    : "trailing 12 mo"
  const cost = k.cost_basis === "actual" ? "actual cost" : "est. cost"
  return `Uploaded data · ${basis} · ${cost} · indicative`
}

export function BuildingBaselineStrip({ building }: { building: Building }) {
  const [kpis, setKpis] = useState<BaselineKpis | null>(null)

  useEffect(() => {
    let active = true
    fetchBuildingBaselineKpis(building.id).then((res) => {
      if (active && res.ok && res.data.has_data) setKpis(res.data)
    })
    return () => {
      active = false
    }
  }, [building.id])

  if (!kpis) return null

  const insights: Insight[] = buildAdvisorInsights({
    kpis: toRow(building, kpis),
    topActions: [],
    isResidential: false,
    profile: {
      epc_class: building.epc_class,
      heating_system: building.heating_system,
    },
  })
  const top = insights[0] ?? null

  return (
    <div className="mb-3 rounded-md border border-brand-emerald/20 bg-brand-emerald/[0.04] p-2.5">
      <div className="flex flex-wrap items-center gap-1.5">
        {kpis.eui_kwh_m2_yr != null && (
          <Chip label="EUI" value={`${Math.round(kpis.eui_kwh_m2_yr)}`} unit="kWh/m²·yr" />
        )}
        {kpis.annual_energy_kwh != null && (
          <Chip label="Energy" value={fmtEnergy(kpis.annual_energy_kwh)} unit="/yr" />
        )}
        {kpis.annual_co2_kg != null && (
          <Chip label="CO₂" value={fmtCo2(kpis.annual_co2_kg)} unit="/yr" />
        )}
      </div>

      <div className="mt-1.5 text-[10px] text-text-faint">{provenance(kpis)}</div>

      {top && (
        <div className="mt-1.5 flex items-start gap-1.5">
          <span
            className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${SEV_DOT[top.severity]}`}
            aria-hidden
          />
          <span className="text-[11px] leading-snug text-text-muted">{top.title}</span>
        </div>
      )}
    </div>
  )
}

function Chip({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <span className="inline-flex items-baseline gap-1 rounded border border-border-subtle bg-bg-elevated/60 px-1.5 py-0.5">
      <span className="text-[9px] uppercase tracking-wide text-text-faint">{label}</span>
      <span className="text-[11px] font-semibold tabular-nums text-text-primary">{value}</span>
      <span className="text-[9px] text-text-faint">{unit}</span>
    </span>
  )
}
