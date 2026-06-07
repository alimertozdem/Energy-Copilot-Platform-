/**
 * BuildingCard -- presentational tile for the /buildings grid.
 *
 * Two modes:
 *   * Default (navigate): renders as a <Link> -> /buildings/[fabric_id]
 *   * Selectable (compare): renders as a <button> that toggles selection
 *
 * Selection state is owned by the parent (BuildingsListClient); this card
 * just visualises it via a checkmark badge and accent border. A faint city
 * silhouette (tinted by building type) sits behind the content for warmth.
 *
 * For buildings still pending a Fabric bridge that have an uploaded consumption
 * baseline, BuildingBaselineStrip lights up indicative KPIs + a top advisor
 * insight inline (bridged buildings get live KPIs on their report page).
 */
"use client"
import Link from "next/link"
import { CircleFlag } from "react-circle-flags"
import { ArrowUpRight, Battery, Check, Lock, Wifi, Zap } from "lucide-react"

import type { Building, BuildingModule, ModuleKey } from "@/lib/api/buildings"

import { BuildingBaselineStrip } from "./BuildingBaselineStrip"

/** Per-building-type accent (left stripe + type badge + silhouette tint). */
const TYPE_ACCENTS: Record<string, { stripe: string; badge: string; tint: string }> = {
  Office: { stripe: "bg-accent-blue", badge: "border-accent-blue/40 text-accent-blue", tint: "text-accent-blue" },
  Retail: { stripe: "bg-accent-orange", badge: "border-accent-orange/40 text-accent-orange", tint: "text-accent-orange" },
  Logistics: { stripe: "bg-accent-cyan", badge: "border-accent-cyan/40 text-accent-cyan", tint: "text-accent-cyan" },
  Hotel: { stripe: "bg-accent-purple", badge: "border-accent-purple/40 text-accent-purple", tint: "text-accent-purple" },
  Healthcare: { stripe: "bg-accent-red", badge: "border-accent-red/40 text-accent-red", tint: "text-accent-red" },
  Education: { stripe: "bg-accent-yellow", badge: "border-accent-yellow/40 text-accent-yellow", tint: "text-accent-yellow" },
  Data_Center: { stripe: "bg-brand-emerald", badge: "border-brand-emerald/40 text-brand-emerald", tint: "text-brand-emerald" },
  Lab: { stripe: "bg-brand-mint", badge: "border-brand-mint/40 text-brand-mint", tint: "text-brand-mint" },
}

const DEFAULT_ACCENT = {
  stripe: "bg-border-subtle",
  badge: "border-border-subtle text-text-muted",
  tint: "text-text-muted",
}

function isModuleEnabled(modules: BuildingModule[], key: ModuleKey): boolean {
  return modules.find((m) => m.module_key === key)?.enabled ?? false
}

type BuildingCardProps = {
  building: Building
  /** When true, card becomes a button that toggles selection (no navigation). */
  selectable?: boolean
  /** Highlights the card when in selectable mode. */
  selected?: boolean
  /** Called when card is clicked in selectable mode. */
  onToggle?: () => void
}

export function BuildingCard({
  building: b,
  selectable = false,
  selected = false,
  onToggle,
}: BuildingCardProps) {
  const fabricId = b.fabric_building_id ?? "—"
  // Pending buildings have no fabric id -> the UUID-addressed detail page
  // (so the card no longer links to the broken /buildings/—).
  const detailHref = b.fabric_building_id
    ? `/buildings/${encodeURIComponent(b.fabric_building_id)}`
    : `/buildings/by-id/${b.id}`
  const accent = TYPE_ACCENTS[b.building_type ?? ""] ?? DEFAULT_ACCENT
  const metersOn = isModuleEnabled(b.modules, "meters")
  const iotOn = isModuleEnabled(b.modules, "iot")
  const batteryOn = isModuleEnabled(b.modules, "battery")

  const sharedClasses = `group relative block overflow-hidden rounded-lg
                         border bg-bg-elevated/40 backdrop-blur-sm
                         transition-all duration-200
                         hover:scale-[1.02] ${
                           selected
                             ? "border-brand-emerald shadow-[0_8px_32px_rgba(29,158,117,0.4)]"
                             : "border-border-subtle hover:border-brand-emerald/60 hover:shadow-[0_8px_32px_rgba(29,158,117,0.25)]"
                         }`

  const inner = (
    <>
      {/* Decorative city silhouette (behind content, clipped by overflow). */}
      <CitySilhouette tint={accent.tint} />

      {/* Left accent stripe — colored by building type */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 z-10 ${accent.stripe}`}
        aria-hidden
      />

      <div className="relative z-10 p-5 pl-6">
        {/* Header: country flag + type badge + sample badge */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {b.country_code && (
              <CircleFlag
                countryCode={b.country_code.toLowerCase()}
                height="18"
                width="18"
              />
            )}
            <span
              className={`text-[11px] uppercase tracking-wider font-medium
                          px-2 py-0.5 rounded border ${accent.badge}`}
            >
              {b.building_type ?? "—"}
            </span>
          </div>
          {b.is_sample_org && !selectable && (
            <span
              className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded
                         border border-brand-mint/30 text-brand-mint/80"
            >
              Sample
            </span>
          )}
        </div>

        {/* Fabric ID + Name + City */}
        <div className="mb-4">
          <div className="text-[10px] uppercase tracking-wider text-text-faint mb-0.5">
            {fabricId}
          </div>
          <h3 className="text-base font-semibold text-text-primary leading-tight">
            {b.name}
          </h3>
          {b.city && (
            <div className="text-sm text-text-muted mt-0.5">{b.city}</div>
          )}
        </div>

        {/* Floor area — visually prominent */}
        {b.floor_area_m2 != null && (
          <div className="mb-3">
            <div className="text-2xl font-semibold text-brand-mint leading-none">
              {b.floor_area_m2.toLocaleString("en-US")}
              <span className="text-sm text-text-muted font-normal ml-1">m²</span>
            </div>
            {b.construction_year != null && (
              <div className="text-[11px] text-text-faint mt-1">
                Built {b.construction_year}
              </div>
            )}
          </div>
        )}

        {/* Baseline KPIs from uploaded data — only for buildings still pending a
            Fabric bridge (bridged buildings get live KPIs on their report). */}
        {!b.fabric_building_id && <BuildingBaselineStrip building={b} />}

        {/* Module unlock indicators */}
        <div className="flex items-center gap-3 mb-3 pt-3 border-t border-border-subtle/40">
          <ModuleIndicator Icon={Zap} enabled={metersOn} label="Meters" />
          <ModuleIndicator Icon={Wifi} enabled={iotOn} label="IoT Monitoring" />
          <ModuleIndicator Icon={Battery} enabled={batteryOn} label="Battery Strategy" />
        </div>

        {/* Hover action hint -- only in navigate mode */}
        {!selectable && (
          <div
            className="flex items-center gap-1 text-xs text-brand-emerald
                       opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          >
            <span>Open report</span>
            <ArrowUpRight className="w-3 h-3" />
          </div>
        )}
      </div>

      {/* Selection checkmark badge -- only in selectable mode */}
      {selectable && (
        <div
          className={`absolute top-3 right-3 z-10 w-6 h-6 rounded-full flex
                      items-center justify-center transition-all duration-200
                      ${
                        selected
                          ? "bg-brand-emerald border-2 border-brand-emerald scale-100"
                          : "bg-bg-elevated/80 border-2 border-border-subtle scale-90 group-hover:scale-100 group-hover:border-brand-emerald/60"
                      }`}
          aria-hidden
        >
          {selected && <Check className="w-3.5 h-3.5 text-white" />}
        </div>
      )}
    </>
  )

  if (selectable) {
    return (
      <button
        type="button"
        onClick={onToggle}
        aria-pressed={selected}
        className={`${sharedClasses} cursor-pointer text-left w-full`}
      >
        {inner}
      </button>
    )
  }

  return (
    <Link
      href={detailHref}
      className={sharedClasses}
    >
      {inner}
    </Link>
  )
}

/** Faint, decorative skyline anchored to the bottom edge of the card. */
function CitySilhouette({ tint }: { tint: string }) {
  return (
    <div
      className={`pointer-events-none absolute inset-x-0 bottom-0 z-0 h-16 opacity-[0.07] ${tint}`}
      aria-hidden
    >
      <svg viewBox="0 0 240 64" preserveAspectRatio="none" className="w-full h-full">
        <g fill="currentColor">
          <rect x="0" y="34" width="16" height="30" />
          <rect x="18" y="20" width="12" height="44" />
          <rect x="32" y="42" width="18" height="22" />
          <rect x="52" y="26" width="14" height="38" />
          <rect x="68" y="36" width="20" height="28" />
          <rect x="90" y="14" width="12" height="50" />
          <rect x="104" y="30" width="16" height="34" />
          <rect x="122" y="44" width="22" height="20" />
          <rect x="146" y="22" width="14" height="42" />
          <rect x="162" y="34" width="18" height="30" />
          <rect x="182" y="18" width="12" height="46" />
          <rect x="196" y="38" width="20" height="26" />
          <rect x="218" y="28" width="16" height="36" />
          <rect x="94" y="6" width="2" height="8" />
          <rect x="186" y="10" width="2" height="8" />
        </g>
      </svg>
    </div>
  )
}

type IconType = typeof Zap

function ModuleIndicator({
  Icon,
  enabled,
  label,
}: {
  Icon: IconType
  enabled: boolean
  label: string
}) {
  if (enabled) {
    return (
      <div
        title={`${label} enabled`}
        className="flex items-center text-brand-emerald"
      >
        <Icon className="w-3.5 h-3.5" />
      </div>
    )
  }
  return (
    <div
      title={`${label} locked`}
      className="relative flex items-center text-text-faint"
    >
      <Icon className="w-3.5 h-3.5 opacity-40" />
      <Lock className="absolute -bottom-0.5 -right-1.5 w-2 h-2" />
    </div>
  )
}
