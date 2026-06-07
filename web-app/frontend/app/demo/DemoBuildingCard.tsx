"use client"

/**
 * DemoBuildingCard -- a compact card in the /demo left rail.
 *
 * Shows: building name, country flag/code · city, building type, area,
 * EPC badge, 30d kWh. Selected state lights up the emerald border.
 *
 * The card is button-rendered so it's keyboard-accessible (Enter / Space
 * trigger selection just like the click handler).
 */

import { cn } from "@/lib/utils"

import type { DemoBuilding } from "@/lib/api/demo"

type DemoBuildingCardProps = {
  building: DemoBuilding
  selected: boolean
  onSelect: (fabric_building_id: string) => void
}

// EPC colour ramp -- matches the band most EU regulators publish.
function epcAccent(epc: string | null): string {
  switch (epc) {
    case "A":
    case "B":
      return "text-emerald-400 border-emerald-400/40 bg-emerald-400/10"
    case "C":
    case "D":
      return "text-amber-300 border-amber-300/40 bg-amber-300/10"
    case "E":
    case "F":
    case "G":
      return "text-red-300 border-red-300/40 bg-red-300/10"
    default:
      return "text-text-muted border-border-subtle bg-white/5"
  }
}

export function DemoBuildingCard({
  building,
  selected,
  onSelect,
}: DemoBuildingCardProps) {
  const kwh = building.kwh_30d.toLocaleString("en-US", {
    maximumFractionDigits: 0,
  })
  const area = building.floor_area_m2.toLocaleString("en-US", {
    maximumFractionDigits: 0,
  })

  return (
    <button
      type="button"
      onClick={() => onSelect(building.fabric_building_id)}
      aria-pressed={selected}
      className={cn(
        "w-full text-left rounded-lg border p-3 transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-emerald/60",
        selected
          ? "border-brand-emerald bg-brand-emerald/10 shadow-[0_0_18px_rgba(16,185,129,0.18)]"
          : "border-border-subtle bg-bg-elevated/40 hover:border-brand-emerald/40 hover:bg-white/5"
      )}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[11px] font-semibold tracking-wide text-text-muted">
          {building.fabric_building_id} · {building.country}
        </span>
        <span
          className={cn(
            "inline-flex items-center justify-center text-[10px] font-semibold",
            "px-1.5 py-0.5 rounded border",
            epcAccent(building.epc_class)
          )}
        >
          EPC {building.epc_class ?? "—"}
        </span>
      </div>
      <h3 className="text-sm font-semibold text-text-primary mt-1 leading-snug">
        {building.name}
      </h3>
      <p className="text-xs text-text-muted mt-0.5">
        {building.building_type} · {building.city}
      </p>
      <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-border-subtle">
        <span className="text-[11px] text-text-muted">{area} m²</span>
        <span className="text-[11px] font-mono text-text-primary">
          {kwh} kWh / 30d
        </span>
      </div>
    </button>
  )
}
