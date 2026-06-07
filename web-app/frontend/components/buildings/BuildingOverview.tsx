/**
 * BuildingOverview — the building "home" screen (server component).
 *
 * Landing for /buildings/[id]: a meta strip (type · location · area · year · EPC
 * + sample/read-only badge), headline KPI cards, and section tiles that lead one
 * click deeper (full Power BI report, alerts, recommendations, PDF, solar, and —
 * for residential buildings — the per-unit residential view). NO embed here; the
 * report lives at /buildings/[id]/reports.
 *
 * KPI sourcing (all real, no fabricated fields):
 *   * Commercial: the building's row from /portfolio (EUI, 30d energy/cost/CO2,
 *     open anomalies, open recommendations) + EPC class. EUI is an annualized
 *     run-rate from the last 30 days — NOT weather-corrected (stated on the card).
 *   * Residential: the building rollup from /residential (units, avg heating EUI,
 *     EPC mix, UVI status).
 */
import Link from "next/link"
import {
  ArrowRight,
  BatteryCharging,
  Bell,
  BarChart3,
  CheckCircle2,
  Clock,
  FileDown,
  Home,
  Leaf,
  Lightbulb,
  Lock,
  Sun,
  Wifi,
  Zap,
  type LucideIcon,
} from "lucide-react"

import type { Building } from "@/lib/api/buildings"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import type { ResidentialBuildingResponse } from "@/lib/api/residentialManager"

const MONTHS = [
  "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
const EPC_COLORS: Record<string, string> = {
  A: "#0F6E56", B: "#1D9E75", C: "#639922", D: "#BA7517", E: "#D85A30", F: "#A32D2D", G: "#791F1F",
}

function fmt(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—"
  return n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

// Map declared energy-profile enum values to human labels for the meta strip.
const PROFILE_LABELS: Record<string, string> = {
  gas_boiler: "Gas boiler",
  heat_pump: "Heat pump",
  district_heating: "District heating",
  electric: "Electric",
  oil: "Oil",
  biomass: "Biomass",
  split_ac: "Split AC",
  central_chiller: "Central chiller",
  district_cooling: "District cooling",
  none: "No cooling",
  standard_hours: "Standard hours",
  extended_hours: "Extended hours",
  always_on: "24/7",
  seasonal: "Seasonal",
  other: "Other",
}
function prettyProfile(v: string | null | undefined): string | null {
  if (!v) return null
  return PROFILE_LABELS[v] ?? v.replace(/_/g, " ")
}

function Metric({
  label,
  value,
  unit,
  hint,
  tone,
}: {
  label: string
  value: string
  unit?: string
  hint?: string
  tone?: "danger" | "warning"
}) {
  const valueColor =
    tone === "danger" ? "text-red-400" : tone === "warning" ? "text-amber-400" : "text-text-primary"
  return (
    <div className="rounded-lg border border-border-subtle bg-bg-elevated/40 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">{label}</p>
      <p className={`mt-1.5 text-2xl font-semibold ${valueColor}`}>
        {value}
        {unit && <span className="ml-1 text-xs font-normal text-text-muted">{unit}</span>}
      </p>
      {hint && <p className="mt-1 text-[11px] text-text-faint">{hint}</p>}
    </div>
  )
}

function EpcChip({ band }: { band: string | null | undefined }) {
  if (!band) return null
  const color = EPC_COLORS[band.toUpperCase()] ?? "#94a3b8"
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold text-bg-base"
      style={{ background: color }}
    >
      EPC {band.toUpperCase()}
    </span>
  )
}

function Tile({
  href,
  icon: Icon,
  iconColor,
  title,
  subtitle,
  featured,
}: {
  href: string
  icon: LucideIcon
  iconColor: string
  title: string
  subtitle: string
  featured?: boolean
}) {
  return (
    <Link
      href={href}
      className={`group flex items-center gap-3 rounded-xl border bg-bg-elevated/40 p-4 transition-colors hover:border-brand-emerald/50 ${
        featured ? "border-brand-emerald/60" : "border-border-subtle"
      }`}
    >
      <Icon className="h-5 w-5 shrink-0" style={{ color: iconColor }} aria-hidden />
      <div className="min-w-0">
        <div className="text-sm font-medium text-text-primary">{title}</div>
        <div className="text-xs text-text-muted">{subtitle}</div>
      </div>
      <ArrowRight className="ml-auto h-4 w-4 shrink-0 text-text-faint" aria-hidden />
    </Link>
  )
}

export function BuildingOverview({
  building,
  kpis,
  residential,
}: {
  building: Building
  kpis: PortfolioBuildingRow | null
  residential: ResidentialBuildingResponse | null
}) {
  const id = building.fabric_building_id ?? ""
  const isResidential = (building.building_type || "").toLowerCase().includes("residential")
  const enabledModules = new Set(
    (building.modules ?? []).filter((m) => m.enabled).map((m) => m.module_key)
  )
  const SYSTEM_LABELS: Record<string, string> = {
    meters: "Meters",
    iot: "IoT sensors",
    battery: "Battery",
    solar: "Solar",
  }
  const systemsSummary =
    [...enabledModules].map((k) => SYSTEM_LABELS[k] ?? k).join(" · ") || "Energy meters"

  const meta = [
    building.country_code,
    building.city,
    building.floor_area_m2 != null ? `${fmt(building.floor_area_m2)} m²` : null,
    building.floors_above_ground != null ? `${building.floors_above_ground} floors` : null,
    building.construction_year != null ? `built ${building.construction_year}` : null,
    building.typical_occupants != null ? `${fmt(building.typical_occupants)} occupants` : null,
  ].filter(Boolean)

  const uvi = residential?.rollup.uvi
  const uviText =
    uvi && uvi.latest_year && uvi.latest_month
      ? `${MONTHS[uvi.latest_month] ?? uvi.latest_month} ${uvi.latest_year}`
      : "No data"
  const epcBands = ["A", "B", "C", "D", "E"].filter((b) => residential?.rollup.epc_distribution[b])

  return (
    <div className="space-y-6">
      {/* Meta strip */}
      <div className="flex flex-wrap items-center gap-2">
        {building.building_type && (
          <span className="rounded-md border border-border-subtle px-2 py-0.5 text-xs text-text-muted">
            {building.building_type.replace(/_/g, " ")}
          </span>
        )}
        {!isResidential && <EpcChip band={kpis?.epc_class ?? building.epc_class} />}
        <span className="inline-flex items-center gap-1 rounded-md border border-brand-emerald/40 bg-brand-emerald/10 px-2 py-0.5 text-xs text-brand-emerald">
          <Leaf className="h-3 w-3" aria-hidden /> Smart building
        </span>
        {building.is_sample_org && (
          <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/15 px-2 py-0.5 text-xs text-amber-300">
            <Lock className="h-3 w-3" aria-hidden /> Sample · read-only
          </span>
        )}
        {meta.length > 0 && (
          <span className="text-xs text-text-muted">· {meta.join(" · ")}</span>
        )}
        {building.heating_system && (
          <span className="rounded-md border border-border-subtle px-2 py-0.5 text-xs text-text-muted">
            {prettyProfile(building.heating_system)} heating
          </span>
        )}
        {building.cooling_system && building.cooling_system !== "none" && (
          <span className="rounded-md border border-border-subtle px-2 py-0.5 text-xs text-text-muted">
            {prettyProfile(building.cooling_system)} cooling
          </span>
        )}
        {building.occupancy_pattern && (
          <span className="rounded-md border border-border-subtle px-2 py-0.5 text-xs text-text-muted">
            {prettyProfile(building.occupancy_pattern)}
          </span>
        )}
      </div>

      {/* KPI cards */}
      {isResidential && residential ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Metric label="Units" value={fmt(residential.rollup.units_with_data)} />
          <Metric
            label="Avg heating EUI"
            value={fmt(residential.rollup.building_avg_eui_kwh_m2_yr)}
            unit="kWh/m²·yr"
            hint="Heating + hot water · not climate-adjusted"
          />
          <div className="rounded-lg border border-border-subtle bg-bg-elevated/40 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">EPC mix</p>
            <div className="mt-2 flex flex-wrap items-center gap-1">
              {epcBands.length === 0 ? (
                <span className="text-text-faint">—</span>
              ) : (
                epcBands.map((b) => (
                  <span
                    key={b}
                    className="inline-flex h-5 items-center gap-0.5 rounded px-1 text-[10px] font-bold text-bg-base"
                    style={{ background: EPC_COLORS[b] ?? "#94a3b8" }}
                  >
                    {b}
                    <span className="font-normal">{residential.rollup.epc_distribution[b]}</span>
                  </span>
                ))
              )}
            </div>
          </div>
          <Metric label="UVI status" value={uviText} hint={uvi ? `${uvi.units_covered} units covered` : "Monthly info"} />
        </div>
      ) : kpis ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          <Metric
            label="Energy intensity (EUI)"
            value={fmt(kpis.eui_kwh_m2_yr)}
            unit="kWh/m²·yr"
            hint="Annualized run-rate · not weather-corrected"
          />
          <Metric
            label="Energy used · 30d"
            value={fmt(kpis.kwh_30d)}
            unit="kWh"
            hint="Total consumption · last 30 days"
          />
          <Metric
            label="Energy cost · 30d"
            value={`€${fmt(kpis.cost_30d_eur)}`}
            hint="Estimated · last 30 days"
          />
          <Metric
            label="Carbon · 30d"
            value={fmt(kpis.co2_30d_kg)}
            unit="kg CO₂e"
            hint="Scope 2 (grid) · last 30 days"
          />
          <Metric
            label="Open alerts"
            value={fmt(kpis.open_anomalies)}
            hint="High + critical"
            tone={kpis.open_anomalies > 0 ? "danger" : undefined}
          />
          <Metric
            label="Savings opportunities"
            value={fmt(kpis.open_recommendations)}
            hint="Open recommendations"
            tone={kpis.open_recommendations > 0 ? "warning" : undefined}
          />
        </div>
      ) : (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-6">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 shrink-0 text-amber-300" aria-hidden />
            <p className="text-sm font-semibold text-text-primary">
              Connecting {building.name}&rsquo;s energy data
            </p>
          </div>
          <p className="mt-1.5 text-sm text-text-muted">
            Setup is complete. KPIs, reports and the advisor populate automatically once the data
            source is connected.
          </p>

          <div className="mt-4 space-y-2.5">
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-emerald" aria-hidden />
              <div>
                <div className="text-sm font-medium text-text-primary">Building details saved</div>
                <div className="text-[11px] text-text-faint">
                  {meta.length > 0 ? meta.join(" · ") : building.building_type || "Profile complete"}
                </div>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-emerald" aria-hidden />
              <div>
                <div className="text-sm font-medium text-text-primary">Systems declared</div>
                <div className="text-[11px] text-text-faint">{systemsSummary}</div>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <Clock className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden />
              <div>
                <div className="text-sm font-medium text-text-primary">
                  Energy data — awaiting connection
                </div>
                <div className="text-[11px] text-text-faint">Metrics appear here once ingestion is live</div>
              </div>
            </div>
          </div>

          <Link
            href="/demo"
            className="mt-4 inline-flex items-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
          >
            Preview with the live demo
            <ArrowRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
        </div>
      )}

      {/* Section tiles */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {isResidential && (
          <Tile
            href={`/buildings/${encodeURIComponent(id)}/residential`}
            icon={Home}
            iconColor="#10b981"
            title="Residential units"
            subtitle="Per-unit KPIs + UVI"
            featured
          />
        )}
        <Tile
          href={`/buildings/${encodeURIComponent(id)}/reports`}
          icon={BarChart3}
          iconColor="#1D9E75"
          title="Energy report"
          subtitle="Open full Power BI report"
          featured={!isResidential}
        />
        <Tile
          href={`/alerts?building_id=${encodeURIComponent(id)}`}
          icon={Bell}
          iconColor="#D85A30"
          title="Alerts"
          subtitle={kpis ? `${fmt(kpis.open_anomalies)} open` : "Anomaly monitoring"}
        />
        <Tile
          href={`/actions?building_id=${encodeURIComponent(id)}`}
          icon={Lightbulb}
          iconColor="#BA7517"
          title="Recommendations"
          subtitle={kpis ? `${fmt(kpis.open_recommendations)} to review` : "Savings actions"}
        />
        {kpis?.has_pv ||
        (building.pv_capacity_kwp != null && building.pv_capacity_kwp > 0) ? (
          <Tile
            href="/solar"
            icon={Sun}
            iconColor="#EF9F27"
            title="Solar"
            subtitle="On-site generation"
          />
        ) : null}
        <Tile
          href={`/buildings/${encodeURIComponent(id)}/report`}
          icon={FileDown}
          iconColor="#534AB7"
          title="Export PDF"
          subtitle="Building report"
        />
      </div>

      {/* Module status */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] uppercase tracking-wider text-text-faint">Modules</span>
        {(
          [
            { key: "meters", label: "Meters", icon: Zap },
            { key: "iot", label: "IoT", icon: Wifi },
            { key: "battery", label: "Battery", icon: BatteryCharging },
          ] as const
        ).map(({ key, label, icon: Icon }) => {
          const on = enabledModules.has(key)
          return (
            <span
              key={key}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs ${
                on
                  ? "border-brand-emerald/40 bg-brand-emerald/10 text-brand-emerald"
                  : "border-border-subtle text-text-faint"
              }`}
            >
              <Icon className="h-3 w-3" aria-hidden /> {label}
            </span>
          )
        })}
      </div>
    </div>
  )
}
