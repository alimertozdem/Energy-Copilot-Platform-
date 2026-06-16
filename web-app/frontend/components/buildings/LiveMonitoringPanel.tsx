/**
 * LiveMonitoringPanel — app-native live telemetry for a building.
 *
 * Latest value per sensor_type from bronze_iot_readings (via /monitoring), with
 * an honest basis badge (Live / Simulated) and freshness. Empty state guides the
 * user to connect a device or send a test reading. This is the web-app view; the
 * Power BI IoT page stays on the Fabric path.
 */
import Link from "next/link"
import { Activity, Cpu, RadioTower } from "lucide-react"

import type { BuildingMonitoring, MonitoringSensor } from "@/lib/api/baseline"

const LABELS: Record<string, string> = {
  building_kwh: "Building power",
  hvac_kwh: "HVAC power",
  lighting_kwh: "Lighting power",
  plug_load_kwh: "Plug-load power",
  building_energy_kwh: "Building energy",
  HVAC_temp: "Zone temp",
  HVAC_supply_temp: "Supply temp",
  HVAC_return_temp: "Return temp",
  humidity: "Humidity",
  CO2: "CO₂",
  occupancy: "Occupancy",
  voltage: "Voltage",
  current: "Current",
  chiller_cop: "Chiller COP",
  boiler_eff: "Boiler eff.",
  pump_pressure: "Pump pressure",
  fan_rpm: "Fan speed",
  heat_output_kwh: "Heat output",
  heatpump_elec_kwh: "Heat-pump elec.",
}

function pretty(st: string): string {
  return LABELS[st] ?? st.replace(/_/g, " ")
}

function relTime(iso: string | null): string {
  if (!iso) return ""
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return ""
  const mins = Math.floor((Date.now() - t) / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return new Date(iso).toLocaleDateString()
}

function fmt(v: number | null): string {
  if (v == null) return "—"
  return Math.abs(v) >= 100 ? Math.round(v).toLocaleString("en-US") : String(v)
}

export function LiveMonitoringPanel({
  monitoring,
  buildingId,
}: {
  monitoring: BuildingMonitoring
  buildingId: string
}) {
  const connectHref = `/connections?building_id=${encodeURIComponent(buildingId)}`

  if (monitoring.basis === "none" || monitoring.sensors.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border-subtle bg-bg-elevated/20 p-5 text-center">
        <RadioTower className="mx-auto mb-2 h-6 w-6 text-text-faint" aria-hidden />
        <div className="mb-1 text-sm text-text-primary">No live data yet</div>
        <div className="text-xs text-text-muted">
          Connect a device, then run an on-site agent — or{" "}
          <Link href={connectHref} className="text-brand-emerald hover:underline">
            add a device and send a test reading
          </Link>{" "}
          to see live telemetry here.
        </div>
      </div>
    )
  }

  const live = monitoring.basis === "live"
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/30 p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Activity className="h-4 w-4 text-brand-emerald" aria-hidden />
        <h2 className="text-sm font-semibold text-text-primary">Live monitoring</h2>
        <span
          className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${
            live
              ? "border-brand-emerald/30 bg-brand-emerald/5 text-brand-emerald"
              : "border-amber-400/30 bg-amber-400/5 text-amber-300"
          }`}
        >
          {live ? "Live" : "Simulated"}
        </span>
        <span className="ml-auto text-[11px] text-text-faint">
          last reading {relTime(monitoring.last_reading_at)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {monitoring.sensors.map((s: MonitoringSensor) => (
          <div
            key={`${s.sensor_type}-${s.zone ?? ""}`}
            className="rounded-lg border border-border-subtle bg-white/[0.02] p-3"
          >
            <div className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-text-faint">
              {pretty(s.sensor_type)}
              {s.simulated && <span className="h-1.5 w-1.5 rounded-full bg-amber-300" title="Simulated" />}
            </div>
            <div className="mt-1 text-xl font-semibold tabular-nums text-text-primary">
              {fmt(s.value)}
              {s.unit && <span className="ml-1 text-xs font-normal text-text-muted">{s.unit}</span>}
            </div>
            {s.zone && <div className="text-[11px] text-text-faint">@ {s.zone}</div>}
          </div>
        ))}
      </div>

      <p className="mt-3 flex items-center gap-1 text-[11px] text-text-faint">
        <Cpu className="h-3 w-3" aria-hidden />
        {monitoring.reading_count} readings in the last {monitoring.window_hours}h · manage points on{" "}
        <Link href={connectHref} className="text-brand-emerald hover:underline">Connections</Link>
      </p>
    </div>
  )
}
