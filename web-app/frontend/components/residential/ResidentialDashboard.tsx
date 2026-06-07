/**
 * ResidentialDashboard — manager building-level residential view (server component).
 *
 * Rollup cards + a per-unit table for ONE building. Per-unit, NAMED (HKVO cost-
 * allocation context). Reads from /residential/buildings/{id}. NO Power BI embed.
 * Same gold tables as the resident view, so it shows the graceful "unavailable"
 * notice while the Fabric SQL endpoint is still syncing those tables.
 */
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import type {
  ResidentialBuildingResponse,
  UviStatus,
} from "@/lib/api/residentialManager"

const MONTHS = [
  "",
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
const EPC_COLORS: Record<string, string> = {
  A: "#10b981", B: "#34d399", C: "#a3e635", D: "#fbbf24", E: "#f87171",
}

function f(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—"
  return n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

function uviLabel(uvi: UviStatus): string {
  if (uvi.latest_year == null || uvi.latest_month == null) return "No data"
  return `${MONTHS[uvi.latest_month] ?? uvi.latest_month} ${uvi.latest_year} · ${uvi.units_covered} unit${uvi.units_covered === 1 ? "" : "s"}`
}

function EpcChip({ band }: { band: string | null }) {
  if (!band) return <span className="text-text-faint">—</span>
  const color = EPC_COLORS[band] ?? "#94a3b8"
  return (
    <span
      className="inline-flex h-6 w-6 items-center justify-center rounded text-xs font-bold text-bg-base"
      style={{ background: color }}
    >
      {band}
    </span>
  )
}

function Card({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-text-primary">{value}</p>
      {hint && <p className="mt-1 text-xs text-text-muted">{hint}</p>}
    </div>
  )
}

export function ResidentialDashboard({
  data,
  error,
}: {
  data: ResidentialBuildingResponse | null
  error: string | null
}) {
  if (error) {
    return <FetchErrorNotice error={error} label="residential data" />
  }
  if (!data || data.units.length === 0) {
    return (
      <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-6">
        <p className="text-sm font-semibold text-text-primary">No residential unit data yet.</p>
        <p className="mt-1 text-sm text-text-muted">
          Once this building&rsquo;s per-unit heat-cost readings are processed, unit KPIs
          and the monthly UVI status will appear here.
        </p>
      </div>
    )
  }

  const { rollup, units } = data
  const epcOrder = ["A", "B", "C", "D", "E"]

  return (
    <div className="space-y-6">
      {/* Rollup cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card label="Units with data" value={rollup.units_with_data} />
        <Card
          label="Building avg EUI"
          value={f(rollup.building_avg_eui_kwh_m2_yr)}
          hint="kWh/m²·yr (heating + hot water)"
        />
        <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">EPC mix</p>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {epcOrder.filter((b) => rollup.epc_distribution[b]).length === 0 ? (
              <span className="text-text-faint">—</span>
            ) : (
              epcOrder
                .filter((b) => rollup.epc_distribution[b])
                .map((b) => (
                  <span key={b} className="inline-flex items-center gap-1">
                    <EpcChip band={b} />
                    <span className="text-xs text-text-muted">{rollup.epc_distribution[b]}</span>
                  </span>
                ))
            )}
          </div>
        </div>
        <Card label="UVI status" value={uviLabel(rollup.uvi)} hint="Latest monthly consumption info" />
      </div>

      {/* Per-unit table */}
      <div className="overflow-x-auto rounded-xl border border-border-subtle bg-bg-elevated/40">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-wider text-text-muted">
              <th className="px-4 py-3 font-semibold">Unit</th>
              <th className="px-4 py-3 font-semibold text-right">Area m²</th>
              <th className="px-4 py-3 font-semibold text-right">EUI</th>
              <th className="px-4 py-3 font-semibold text-center">EPC</th>
              <th className="px-4 py-3 font-semibold text-right">vs building</th>
              <th className="px-4 py-3 font-semibold text-right">Heating+DHW/yr</th>
              <th className="px-4 py-3 font-semibold text-right">Shared kWh</th>
              <th className="px-4 py-3 font-semibold text-right">Coverage</th>
            </tr>
          </thead>
          <tbody>
            {units.map((u) => {
              const vs = u.vs_building_pct
              const vsColor =
                vs == null ? "text-text-muted" : vs < 0 ? "text-brand-emerald" : "text-amber-400"
              const vsText =
                vs == null ? "—" : `${vs < 0 ? "" : "+"}${f(vs)}%`
              return (
                <tr key={u.unit_id} className="border-b border-border-subtle/60 text-text-primary/90">
                  <td className="px-4 py-2.5 font-medium">{u.unit_id}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{f(u.area_m2)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{f(u.eui_kwh_m2_yr)}</td>
                  <td className="px-4 py-2.5 text-center"><EpcChip band={u.epc_band} /></td>
                  <td className={`px-4 py-2.5 text-right tabular-nums ${vsColor}`}>{vsText}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{f(u.heating_dhw_kwh_annual)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{f(u.common_allocated_kwh)}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums text-text-muted">
                    {u.cov_days != null ? `${f(u.cov_days)}d` : "—"}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <p className="text-[11px] leading-relaxed text-text-faint">
        Per-unit figures are shown for cost-allocation (HKVO) purposes. Shared heating &amp;
        hot water are allocated 70% by consumption / 30% by floor area. The monthly
        statement (UVI) per unit is available from the resident view / PDF export.
      </p>
    </div>
  )
}
