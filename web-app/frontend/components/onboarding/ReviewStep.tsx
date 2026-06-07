"use client"

/**
 * Step 4 — review the collected details, then create the building.
 * Submit + error state live in the wizard; this step renders the full summary
 * (profile + systems + IoT config + data method) and wires the buttons.
 */
import { Loader2 } from "lucide-react"

import {
  type OnboardingData,
  COOLING_SYSTEMS,
  DATA_METHODS,
  HEATING_SYSTEMS,
  IOT_PROTOCOLS,
  IOT_SENSOR_TYPES,
  OCCUPANCY_PATTERNS,
} from "@/app/onboarding/types"

function labelFrom(
  list: readonly { value: string; label: string }[],
  value: string,
  fallback = "—"
): string {
  if (!value) return fallback
  return list.find((o) => o.value === value)?.label ?? value
}

export function ReviewStep({
  data,
  onSubmit,
  onBack,
  submitting,
  error,
}: {
  data: OnboardingData
  onSubmit: () => void
  onBack: () => void
  submitting: boolean
  error: string | null
}) {
  const isResidential = data.building_type === "Residential"

  const systems: string[] = ["Energy meters"]
  if (data.has_iot) systems.push("IoT sensors")
  if (data.has_battery) systems.push("Battery storage")
  if (data.has_solar) {
    systems.push(data.pv_capacity_kwp ? `Solar PV (${data.pv_capacity_kwp} kWp)` : "Solar PV")
  }

  const location =
    [data.city, data.country_code].filter((v) => v.trim()).join(", ") || "—"

  const heating =
    data.heating_system === "other"
      ? data.heating_other || "Other"
      : labelFrom(HEATING_SYSTEMS, data.heating_system)
  const cooling =
    data.cooling_system === "other"
      ? data.cooling_other || "Other"
      : labelFrom(COOLING_SYSTEMS, data.cooling_system)
  const occupancy = labelFrom(OCCUPANCY_PATTERNS, data.occupancy_pattern)
  const dataMethod = labelFrom(DATA_METHODS, data.data_method, "Decide later")

  const iotProtocols = data.iot_protocols
    .map((v) => labelFrom(IOT_PROTOCOLS, v))
    .filter(Boolean)
    .join(", ")
  const iotSensors = data.iot_sensor_types
    .map((v) => labelFrom(IOT_SENSOR_TYPES, v))
    .filter(Boolean)
    .join(", ")

  return (
    <div>
      <h2 className="font-display text-2xl font-bold text-text-primary mb-1 tracking-tight">Review</h2>
      <p className="text-text-muted text-sm mb-6">Check the details, then create your building.</p>

      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
        <ReviewRow label="Name" value={data.name || "—"} />
        <ReviewRow label="Type" value={data.building_type || "—"} />
        <ReviewRow label="Location" value={location} />
        <ReviewRow label="Floor area" value={data.floor_area_m2 ? `${data.floor_area_m2} m²` : "—"} />
        <ReviewRow label="Year" value={data.construction_year || "—"} />
        <ReviewRow label="EPC class" value={data.epc_class || "Unknown"} />
        <ReviewRow label="Heating" value={heating} />
        <ReviewRow label="Cooling" value={cooling} />
        <ReviewRow label="Occupancy" value={occupancy} />
        <ReviewRow
          label="Floors / occupants"
          value={
            [
              data.floors_above_ground ? `${data.floors_above_ground} floors` : null,
              data.typical_occupants ? `${data.typical_occupants} occupants` : null,
            ]
              .filter(Boolean)
              .join(" · ") || "—"
          }
        />
        {isResidential && (
          <ReviewRow label="Residential units" value={data.residential_units || "—"} />
        )}
        <ReviewRow label="Data method" value={dataMethod} />
      </dl>

      <div className="mt-4">
        <dt className="text-xs text-text-muted mb-1.5">Systems</dt>
        <div className="flex flex-wrap gap-1.5">
          {systems.map((s) => (
            <span
              key={s}
              className="inline-flex items-center rounded-full border border-brand-emerald/30 bg-brand-emerald/5 px-2 py-0.5 text-[11px] text-brand-emerald"
            >
              {s}
            </span>
          ))}
        </div>
      </div>

      {data.has_iot && (iotProtocols || iotSensors || data.iot_zones) && (
        <div className="mt-4 rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2.5 text-xs text-text-muted">
          <span className="text-text-primary font-medium">IoT setup: </span>
          {[
            iotProtocols && `Protocols — ${iotProtocols}`,
            iotSensors && `Sensors — ${iotSensors}`,
            data.iot_zones && `${data.iot_zones} zones`,
          ]
            .filter(Boolean)
            .join(" · ")}
        </div>
      )}

      {error && (
        <div className="mt-5 text-sm text-accent-red bg-accent-red/10 border border-accent-red/30 rounded-md px-3 py-2">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between mt-8">
        <button
          type="button"
          onClick={onBack}
          disabled={submitting}
          className="text-sm text-text-muted hover:text-text-primary transition-colors disabled:opacity-50"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={onSubmit}
          disabled={submitting}
          className="inline-flex items-center gap-2 bg-brand-emerald hover:bg-brand-deep disabled:bg-brand-deep disabled:opacity-60 text-white font-medium px-6 py-2.5 rounded-md transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
        >
          {submitting && <Loader2 size={16} className="animate-spin" />}
          {submitting ? "Creating…" : "Create building"}
        </button>
      </div>
    </div>
  )
}

function ReviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-text-muted">{label}</dt>
      <dd className="mt-0.5 text-sm text-text-primary">{value}</dd>
    </div>
  )
}
