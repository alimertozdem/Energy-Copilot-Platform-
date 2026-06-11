"use client"

/**
 * Step 3 — energy systems & data.
 *
 * Captures which modules the building has (meters always on; IoT/battery/solar
 * optional), the IoT connection details (protocols, sensor types, zones) when
 * IoT is present, an operating profile (heating/cooling/occupancy, with a
 * free-text "Other"), and HOW the data will arrive (live / upload / manual /
 * later). Conditional reveals keep the step light until a choice opens them.
 */
import { Battery, Cpu, Gauge, Sun } from "lucide-react"

import { cn } from "@/lib/utils"
import {
  type OnboardingData,
  COOLING_SYSTEMS,
  DATA_METHODS,
  DATA_SOURCES,
  HEATING_SYSTEMS,
  IOT_PROTOCOLS,
  IOT_SENSOR_TYPES,
  OCCUPANCY_PATTERNS,
} from "@/app/onboarding/types"

const inputCls =
  "w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent transition-all"
const labelCls = "block text-sm text-text-muted mb-1.5"

function toggleIn(list: string[], v: string): string[] {
  return list.includes(v) ? list.filter((x) => x !== v) : [...list, v]
}

export function SystemsStep({
  data,
  update,
  onNext,
  onBack,
}: {
  data: OnboardingData
  update: (patch: Partial<OnboardingData>) => void
  onNext: () => void
  onBack: () => void
}) {
  return (
    <div>
      <h2 className="font-display text-2xl font-bold text-text-primary mb-1 tracking-tight">
        Energy systems &amp; data
      </h2>
      <p className="text-text-muted text-sm mb-6">
        What this building has and how its data reaches us — this unlocks the right dashboards.
      </p>

      <div className="flex flex-col gap-2.5">
        {/* Meters are always included. */}
        <div className="flex items-center gap-3 rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2.5">
          <Gauge className="w-4 h-4 text-brand-emerald shrink-0" />
          <div className="flex-1 min-w-0">
            <div className="text-sm text-text-primary">Energy meters</div>
            <div className="text-xs text-text-muted">Consumption analytics (Pages 1–7)</div>
          </div>
          <span className="text-xs text-brand-emerald font-medium">Included</span>
        </div>

        <SystemToggle
          icon={<Cpu className="w-4 h-4" />}
          label="IoT sensors"
          desc="Live monitoring — temperature, CO₂, power (Page 8)"
          enabled={data.has_iot}
          onToggle={() => update({ has_iot: !data.has_iot })}
        />

        {/* IoT connection config — the infrastructure detail behind the toggle. */}
        {data.has_iot && (
          <div className="ml-7 space-y-3 border-l border-border-subtle pl-3 py-1">
            <div>
              <label className={labelCls}>
                Protocols in the building <span className="text-text-faint">(select all)</span>
              </label>
              <ChipMulti
                options={IOT_PROTOCOLS}
                selected={data.iot_protocols}
                onToggle={(v) => update({ iot_protocols: toggleIn(data.iot_protocols, v) })}
              />
            </div>
            <div>
              <label className={labelCls}>
                Sensor types present <span className="text-text-faint">(select all)</span>
              </label>
              <ChipMulti
                options={IOT_SENSOR_TYPES}
                selected={data.iot_sensor_types}
                onToggle={(v) => update({ iot_sensor_types: toggleIn(data.iot_sensor_types, v) })}
              />
            </div>
            <div>
              <label htmlFor="s-zones" className={labelCls}>
                Approx. zones / sensor groups
              </label>
              <input
                id="s-zones"
                type="number"
                min={0}
                value={data.iot_zones}
                onChange={(e) => update({ iot_zones: e.target.value })}
                placeholder="e.g. 12"
                className={`${inputCls} max-w-[180px]`}
              />
              <p className="mt-1 text-[11px] text-text-faint">
                A rough count helps us scope the live monitoring — refine it later.
              </p>
            </div>
          </div>
        )}

        <SystemToggle
          icon={<Battery className="w-4 h-4" />}
          label="Battery storage"
          desc="Dispatch strategy & ROI simulation (Page 9)"
          enabled={data.has_battery}
          onToggle={() => update({ has_battery: !data.has_battery })}
        />
        <SystemToggle
          icon={<Sun className="w-4 h-4" />}
          label="Solar PV"
          desc="On-site generation & self-consumption"
          enabled={data.has_solar}
          onToggle={() => update({ has_solar: !data.has_solar })}
        />

        {data.has_solar && (
          <div className="ml-7 pl-3 border-l border-border-subtle">
            <label htmlFor="s-pv" className={labelCls}>
              Installed PV capacity (kWp) <span className="text-text-faint">(optional)</span>
            </label>
            <input
              id="s-pv"
              type="number"
              min={0}
              value={data.pv_capacity_kwp}
              onChange={(e) => update({ pv_capacity_kwp: e.target.value })}
              placeholder="e.g. 120"
              className={`${inputCls} max-w-[180px]`}
            />
            <p className="mt-1 text-[11px] text-text-faint">
              On the nameplate / inverter — drives self-consumption &amp; ROI. Leave blank if unsure; add it later.
            </p>
          </div>
        )}
      </div>

      {/* Operating profile — with free-text "Other". */}
      <div className="mt-5 border-t border-border-subtle pt-5">
        <p className="mb-3 text-sm font-medium text-text-primary">
          Operating profile{" "}
          <span className="font-normal text-text-faint">(sharpens KPIs &amp; advice)</span>
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label htmlFor="s-heat" className={labelCls}>
              Heating
            </label>
            <select
              id="s-heat"
              value={data.heating_system}
              onChange={(e) => update({ heating_system: e.target.value })}
              className={inputCls}
            >
              <option value="">Select…</option>
              {HEATING_SYSTEMS.map((h) => (
                <option key={h.value} value={h.value}>
                  {h.label}
                </option>
              ))}
            </select>
            {data.heating_system === "other" && (
              <input
                type="text"
                maxLength={40}
                value={data.heating_other}
                onChange={(e) => update({ heating_other: e.target.value })}
                placeholder="Specify the heating system…"
                className={`${inputCls} mt-2`}
              />
            )}
          </div>
          <div>
            <label htmlFor="s-cool" className={labelCls}>
              Cooling
            </label>
            <select
              id="s-cool"
              value={data.cooling_system}
              onChange={(e) => update({ cooling_system: e.target.value })}
              className={inputCls}
            >
              <option value="">Select…</option>
              {COOLING_SYSTEMS.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
            {data.cooling_system === "other" && (
              <input
                type="text"
                maxLength={40}
                value={data.cooling_other}
                onChange={(e) => update({ cooling_other: e.target.value })}
                placeholder="Specify the cooling system…"
                className={`${inputCls} mt-2`}
              />
            )}
          </div>
          <div>
            <label htmlFor="s-occ" className={labelCls}>
              Occupancy
            </label>
            <select
              id="s-occ"
              value={data.occupancy_pattern}
              onChange={(e) => update({ occupancy_pattern: e.target.value })}
              className={inputCls}
            >
              <option value="">Select…</option>
              {OCCUPANCY_PATTERNS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* How will data arrive — method picker. */}
      <div className="mt-5 border-t border-border-subtle pt-5">
        <p className="mb-1 text-sm font-medium text-text-primary">How will this building&rsquo;s data arrive?</p>
        <p className="mb-3 text-xs text-text-muted">
          You can change this anytime — it just shapes the next step we guide you through.
        </p>
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {DATA_METHODS.map((m) => {
            const active = data.data_method === m.value
            return (
              <button
                key={m.value}
                type="button"
                onClick={() => update({ data_method: m.value })}
                aria-pressed={active}
                className={cn(
                  "rounded-lg border px-3 py-2.5 text-left transition-colors",
                  active
                    ? "border-brand-emerald/50 bg-brand-emerald/5"
                    : "border-border-subtle bg-white/[0.02] hover:border-border-faint"
                )}
              >
                <div className="text-sm font-medium text-text-primary">{m.label}</div>
                <div className="mt-0.5 text-xs text-text-muted">{m.desc}</div>
              </button>
            )
          })}
        </div>

        {data.data_method === "live" && (
          <div className="mt-3">
            <label htmlFor="s-source" className={labelCls}>
              Primary source / protocol
            </label>
            <select
              id="s-source"
              value={data.data_source}
              onChange={(e) => update({ data_source: e.target.value })}
              className={`${inputCls} max-w-xs`}
            >
              <option value="">Select…</option>
              {DATA_SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        )}
        {data.data_method === "upload" && (
          <p className="mt-3 rounded-md border border-border-subtle bg-white/[0.02] px-3 py-2 text-xs text-text-muted">
            After setup you&rsquo;ll be able to upload a consumption CSV or utility bills from the
            building page — we build your baseline from them.
          </p>
        )}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          type="button"
          onClick={onBack}
          className="text-sm text-text-muted hover:text-text-primary transition-colors"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={onNext}
          className="bg-brand-emerald hover:bg-brand-deep text-white font-medium px-6 py-2.5 rounded-md transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
        >
          Review →
        </button>
      </div>
    </div>
  )
}

function ChipMulti({
  options,
  selected,
  onToggle,
}: {
  options: readonly { value: string; label: string }[]
  selected: string[]
  onToggle: (value: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((o) => {
        const on = selected.includes(o.value)
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onToggle(o.value)}
            aria-pressed={on}
            className={cn(
              "rounded-md border px-2.5 py-1 text-xs transition-colors",
              on
                ? "border-brand-emerald/50 bg-brand-emerald/10 text-brand-emerald"
                : "border-border-subtle bg-white/[0.02] text-text-muted hover:border-border-faint"
            )}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

function SystemToggle({
  icon,
  label,
  desc,
  enabled,
  onToggle,
}: {
  icon: React.ReactNode
  label: string
  desc: string
  enabled: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={enabled}
      className={cn(
        "flex items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors",
        enabled
          ? "border-brand-emerald/40 bg-brand-emerald/5"
          : "border-border-subtle bg-white/[0.02] hover:border-border-faint"
      )}
    >
      <span className={cn("shrink-0 transition-colors", enabled ? "text-brand-emerald" : "text-text-muted")}>
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-text-primary">{label}</div>
        <div className="text-xs text-text-muted">{desc}</div>
      </div>
      <span
        className={cn(
          "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors",
          enabled ? "bg-brand-emerald" : "bg-border-subtle"
        )}
      >
        <span
          className={cn(
            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
            enabled ? "translate-x-4" : "translate-x-0.5"
          )}
        />
      </span>
    </button>
  )
}
