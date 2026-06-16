/**
 * CopCard — heat-pump COP for a building, honest about how it's known.
 *
 *  • measured         → COP from a heat meter ÷ the pump's electricity
 *  • device_reported  → COP the controller reports directly
 *  • needs_heat_meter → electricity alone can't give COP; prompt to add a heat
 *                       meter on Connections (never invents a number)
 *
 * Pure presentational. The page decides when to show it (heat-pump buildings, or
 * any building that already has COP telemetry).
 */
import Link from "next/link"
import { Cpu, Gauge, Thermometer } from "lucide-react"

import type { BuildingCop } from "@/lib/api/baseline"

export function CopCard({ cop, buildingId }: { cop: BuildingCop; buildingId: string }) {
  const connectHref = `/connections?building_id=${encodeURIComponent(buildingId)}`

  if (cop.status === "needs_heat_meter") {
    return (
      <div className="rounded-xl border border-amber-400/30 bg-amber-400/[0.04] p-4">
        <div className="mb-1 flex items-center gap-2">
          <Thermometer className="h-4 w-4 text-amber-300" aria-hidden />
          <h3 className="text-sm font-semibold text-text-primary">Heat-pump COP</h3>
          <span className="rounded border border-amber-400/40 bg-amber-400/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-300">
            Needs heat meter
          </span>
        </div>
        <p className="text-xs text-text-muted">
          COP can&rsquo;t be derived from electricity alone — it&rsquo;s delivered heat ÷ electricity in.
          Add a heat meter (<code className="rounded bg-white/5 px-1">heat_output_kwh</code>) and the
          pump&rsquo;s electricity (<code className="rounded bg-white/5 px-1">heatpump_elec_kwh</code>) on{" "}
          <Link href={connectHref} className="text-brand-emerald hover:underline">Connections</Link>{" "}
          to measure it. Electricity alone still gives consumption, cost and carbon.
        </p>
        {cop.elec_kwh != null && (
          <p className="mt-2 text-[11px] text-text-faint">
            Electricity seen: {cop.elec_kwh} kWh{cop.heat_kwh != null ? ` · heat: ${cop.heat_kwh} kWh` : ""} (last {cop.window_days}d)
          </p>
        )}
      </div>
    )
  }

  const measured = cop.status === "measured"
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <div className="mb-2 flex items-center gap-2">
        {measured ? (
          <Gauge className="h-4 w-4 text-brand-emerald" aria-hidden />
        ) : (
          <Cpu className="h-4 w-4 text-brand-emerald" aria-hidden />
        )}
        <h3 className="text-sm font-semibold text-text-primary">Heat-pump COP</h3>
        <span className="rounded border border-brand-emerald/30 bg-brand-emerald/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-brand-emerald">
          {measured ? "Measured" : "Device-reported"}
        </span>
        {cop.simulated && (
          <span className="rounded border border-amber-400/30 bg-amber-400/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-300">
            Simulated
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-semibold tabular-nums text-text-primary">
          {cop.cop != null ? cop.cop.toFixed(2) : "—"}
        </span>
        <span className="text-xs text-text-muted">COP{measured ? ` (SPF, last ${cop.window_days}d)` : ""}</span>
      </div>
      <p className="mt-1.5 text-[11px] text-text-faint">
        {measured && cop.heat_kwh != null && cop.elec_kwh != null
          ? `${cop.heat_kwh} kWh heat / ${cop.elec_kwh} kWh electricity`
          : cop.basis ?? ""}
      </p>
    </div>
  )
}
