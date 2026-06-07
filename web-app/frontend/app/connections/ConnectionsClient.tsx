"use client"

/**
 * ConnectionsClient — building selector + device/point CRUD for /connections.
 *
 * Pick a building, add devices (protocol + connection params, optionally seeded
 * from a built-in template), then map each device's points to a normalized
 * sensor_type + zone. All mutations go through the manage-gated backend; the
 * device list refreshes from the server response (no optimistic guessing).
 *
 * Honest by design: there is no "test connection" button — on-prem devices sit
 * behind the customer's firewall, so a device stays "pending" until an edge
 * agent / poller (which runs on-site) reports in.
 */
import { useCallback, useEffect, useMemo, useState } from "react"
import { Cpu, Plus, RefreshCw, Trash2 } from "lucide-react"

import type { Building } from "@/lib/api/buildings"
import {
  PROTOCOLS,
  PROTOCOL_FIELDS,
  addPoint,
  createDevice,
  deleteDevice,
  deletePoint,
  fetchDeviceTemplates,
  fetchDevices,
  updatePoint,
  type Device,
  type DeviceCreateInput,
  type DeviceProtocol,
  type DeviceTemplateCatalog,
  type Result,
  type SensorTypeOption,
} from "@/lib/api/connections"

import { AgentPanel } from "./AgentPanel"

const inputCls =
  "w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent"

const STATUS_STYLE: Record<string, string> = {
  pending: "border-amber-400/30 text-amber-300 bg-amber-400/5",
  active: "border-brand-emerald/30 text-brand-emerald bg-brand-emerald/5",
  error: "border-red-400/30 text-red-300 bg-red-400/5",
  disabled: "border-border-subtle text-text-faint",
}

function protoLabel(p: string): string {
  return PROTOCOLS.find((x) => x.value === p)?.label ?? p
}

export function ConnectionsClient({ buildings }: { buildings: Building[] }) {
  const own = useMemo(() => buildings.filter((b) => !b.is_sample_org), [buildings])
  const [buildingId, setBuildingId] = useState(own[0]?.id ?? "")
  const [catalog, setCatalog] = useState<DeviceTemplateCatalog | null>(null)
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAdd, setShowAdd] = useState(false)

  useEffect(() => {
    fetchDeviceTemplates().then((r) => {
      if (r.ok) setCatalog(r.data)
    })
  }, [])

  const reload = useCallback(async () => {
    if (!buildingId) {
      setDevices([])
      return
    }
    setLoading(true)
    setError(null)
    const r = await fetchDevices(buildingId)
    setLoading(false)
    if (r.ok) setDevices(r.data.devices)
    else setError(r.error)
  }, [buildingId])

  useEffect(() => {
    void reload()
  }, [reload])

  const replaceDevice = (d: Device) =>
    setDevices((prev) => prev.map((x) => (x.id === d.id ? d : x)))

  if (own.length === 0) {
    return (
      <div className="rounded-lg border border-border-subtle bg-bg-elevated/30 p-8 text-center">
        <div className="text-sm text-text-primary mb-1">No buildings to configure</div>
        <div className="text-xs text-text-muted">
          Add a building first, then connect its devices here.
        </div>
      </div>
    )
  }

  const sensorTypes: SensorTypeOption[] = catalog?.sensor_types ?? []

  return (
    <div className="space-y-6">
      {/* Toolbar: building selector + refresh + add */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-[240px]">
          <label htmlFor="cx-building" className="mb-1.5 block text-sm text-text-muted">
            Building
          </label>
          <select
            id="cx-building"
            value={buildingId}
            onChange={(e) => {
              setBuildingId(e.target.value)
              setShowAdd(false)
            }}
            className={inputCls}
          >
            {own.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
                {b.fabric_building_id ? ` (${b.fabric_building_id})` : " (pending)"}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void reload()}
            className="inline-flex items-center gap-1.5 rounded-md border border-border-subtle px-3 py-1.5 text-sm text-text-muted transition-colors hover:border-brand-emerald/60 hover:text-brand-emerald"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            onClick={() => setShowAdd((s) => !s)}
            className="inline-flex items-center gap-1.5 rounded-md bg-brand-emerald px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-brand-deep"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add device</span>
          </button>
        </div>
      </div>

      <p className="text-xs leading-relaxed text-text-faint">
        Devices start <span className="text-amber-300">pending</span>. An on-site edge agent or
        poller activates them once it reports in — the backend never reaches devices behind your
        firewall directly, so there is no live connection test here.
      </p>

      {showAdd && catalog && (
        <AddDeviceForm
          catalog={catalog}
          onCancel={() => setShowAdd(false)}
          onCreate={async (input) => {
            const r = await createDevice(buildingId, input)
            if (r.ok) {
              setDevices((p) => [...p, r.data])
              setShowAdd(false)
            }
            return r
          }}
        />
      )}

      {error && (
        <div className="rounded-lg border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-text-muted">Loading devices…</div>
      ) : devices.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border-subtle bg-bg-elevated/20 p-8 text-center">
          <Cpu className="mx-auto mb-2 h-6 w-6 text-text-faint" aria-hidden />
          <div className="text-sm text-text-primary mb-1">No devices yet</div>
          <div className="text-xs text-text-muted">
            Add a meter, controller or gateway to start mapping its data points.
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {devices.map((d) => (
            <DeviceCard
              key={d.id}
              buildingId={buildingId}
              device={d}
              sensorTypes={sensorTypes}
              onChange={replaceDevice}
              onRemove={(id) => setDevices((p) => p.filter((x) => x.id !== id))}
            />
          ))}
        </div>
      )}

      <AgentPanel buildingId={buildingId} />
    </div>
  )
}

// --- add device form -------------------------------------------------------

function AddDeviceForm({
  catalog,
  onCancel,
  onCreate,
}: {
  catalog: DeviceTemplateCatalog
  onCancel: () => void
  onCreate: (input: DeviceCreateInput) => Promise<Result<Device>>
}) {
  const [name, setName] = useState("")
  const [nameTouched, setNameTouched] = useState(false)
  const [protocol, setProtocol] = useState<DeviceProtocol>("modbus")
  const [templateKey, setTemplateKey] = useState("")
  const [config, setConfig] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const templates = catalog.templates.filter((t) => t.protocol === protocol)
  const fields = PROTOCOL_FIELDS[protocol]
  const chosen = catalog.templates.find((t) => t.key === templateKey) || null

  function changeProtocol(p: DeviceProtocol) {
    setProtocol(p)
    setTemplateKey("")
    setConfig({})
  }

  function applyTemplate(key: string) {
    setTemplateKey(key)
    const t = catalog.templates.find((x) => x.key === key)
    if (t) {
      const cfg: Record<string, string> = {}
      Object.entries(t.default_config).forEach(([k, v]) => {
        cfg[k] = v == null ? "" : String(v)
      })
      setConfig(cfg)
      // Auto-fill the name from the template only while the user hasn't typed
      // their own — so switching templates updates the name instead of keeping a
      // stale one, but never clobbers a name the user entered.
      if (!nameTouched) setName(t.label)
    }
  }

  async function submit() {
    if (!name.trim()) {
      setErr("Give the device a name.")
      return
    }
    setBusy(true)
    setErr(null)
    const connection_config: Record<string, unknown> = {}
    Object.entries(config).forEach(([k, v]) => {
      if (v !== "") connection_config[k] = v
    })
    const r = await onCreate({
      name: name.trim(),
      protocol,
      template_key: templateKey || null,
      connection_config,
    })
    setBusy(false)
    if (!r.ok) setErr(r.error)
  }

  return (
    <div className="rounded-xl border border-brand-emerald/30 bg-brand-emerald/[0.04] p-4">
      <div className="mb-3 text-sm font-semibold text-text-primary">Add a device</div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs text-text-muted">Name</label>
          <input
            className={inputCls}
            value={name}
            onChange={(e) => {
              setName(e.target.value)
              setNameTouched(true)
            }}
            placeholder="Main meter"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-text-muted">Protocol</label>
          <select className={inputCls} value={protocol} onChange={(e) => changeProtocol(e.target.value as DeviceProtocol)}>
            {PROTOCOLS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className="mb-1 block text-xs text-text-muted">
            Template <span className="text-text-faint">(optional — seeds the point map)</span>
          </label>
          <select className={inputCls} value={templateKey} onChange={(e) => applyTemplate(e.target.value)}>
            <option value="">No template — I&rsquo;ll map points manually</option>
            {templates.map((t) => (
              <option key={t.key} value={t.key}>{t.label}</option>
            ))}
          </select>
          {chosen && (
            <p className="mt-1 text-[11px] text-text-faint">
              {chosen.description} · seeds {chosen.points.length} point
              {chosen.points.length === 1 ? "" : "s"} (verify against the device manual).
            </p>
          )}
        </div>
        {fields.map((f) => (
          <div key={f.key}>
            <label className="mb-1 block text-xs text-text-muted">{f.label}</label>
            <input
              className={inputCls}
              value={config[f.key] ?? ""}
              placeholder={f.placeholder}
              onChange={(e) => setConfig((c) => ({ ...c, [f.key]: e.target.value }))}
            />
          </div>
        ))}
      </div>

      {err && <div className="mt-3 text-xs text-red-300">{err}</div>}

      <div className="mt-4 flex items-center justify-end gap-2">
        <button type="button" onClick={onCancel} className="px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text-primary">
          Cancel
        </button>
        <button
          type="button"
          onClick={() => void submit()}
          disabled={busy}
          className="rounded-md bg-brand-emerald px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-brand-deep disabled:opacity-50"
        >
          {busy ? "Adding…" : "Add device"}
        </button>
      </div>
    </div>
  )
}

// --- device card -----------------------------------------------------------

function DeviceCard({
  buildingId,
  device,
  sensorTypes,
  onChange,
  onRemove,
}: {
  buildingId: string
  device: Device
  sensorTypes: SensorTypeOption[]
  onChange: (d: Device) => void
  onRemove: (id: string) => void
}) {
  const [busy, setBusy] = useState(false)
  const cfg = device.connection_config ?? {}
  const cfgSummary = Object.entries(cfg)
    .filter(([, v]) => v !== "" && v != null)
    .map(([k, v]) => `${k}: ${String(v)}`)
    .join(" · ")

  async function removeDevice() {
    if (!confirm(`Delete device "${device.name}" and its ${device.points.length} point(s)?`)) return
    setBusy(true)
    const r = await deleteDevice(buildingId, device.id)
    setBusy(false)
    if (r.ok) onRemove(device.id)
  }

  async function addNewPoint(input: { point_ref: string; sensor_type: string; zone: string; unit: string }) {
    const r = await addPoint(buildingId, device.id, {
      point_ref: input.point_ref,
      sensor_type: input.sensor_type,
      zone: input.zone || null,
      unit: input.unit || null,
    })
    if (r.ok) onChange(r.data)
    return r
  }

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-semibold text-text-primary">{device.name}</h3>
            <span className="rounded border border-border-subtle px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-text-muted">
              {protoLabel(device.protocol)}
            </span>
            <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${STATUS_STYLE[device.status] ?? STATUS_STYLE.disabled}`}>
              {device.status}
            </span>
          </div>
          {cfgSummary && <div className="mt-1 truncate text-[11px] text-text-faint">{cfgSummary}</div>}
        </div>
        <button
          type="button"
          onClick={() => void removeDevice()}
          disabled={busy}
          aria-label="Delete device"
          className="shrink-0 rounded-md border border-border-subtle p-1.5 text-text-faint transition-colors hover:border-red-400/40 hover:text-red-300 disabled:opacity-50"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Points */}
      <div className="mt-3 border-t border-border-subtle/40 pt-3">
        <div className="mb-2 text-[11px] uppercase tracking-wide text-text-faint">
          Data points ({device.points.length})
        </div>
        {device.points.length > 0 && (
          <div className="space-y-1.5">
            {device.points.map((p) => (
              <PointRow
                key={p.id}
                buildingId={buildingId}
                deviceId={device.id}
                point={p}
                sensorTypes={sensorTypes}
                onChange={onChange}
              />
            ))}
          </div>
        )}
        <AddPointForm sensorTypes={sensorTypes} onAdd={addNewPoint} />
      </div>
    </div>
  )
}

// --- one editable point row ------------------------------------------------

function PointRow({
  buildingId,
  deviceId,
  point,
  sensorTypes,
  onChange,
}: {
  buildingId: string
  deviceId: string
  point: Device["points"][number]
  sensorTypes: SensorTypeOption[]
  onChange: (d: Device) => void
}) {
  const [zone, setZone] = useState(point.zone ?? "")

  async function patch(fields: { sensor_type?: string; zone?: string | null; enabled?: boolean }) {
    const r = await updatePoint(buildingId, deviceId, point.id, fields)
    if (r.ok) onChange(r.data)
  }

  async function remove() {
    const r = await deletePoint(buildingId, deviceId, point.id)
    if (r.ok) onChange(r.data)
  }

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border border-border-subtle/60 bg-white/[0.02] px-2.5 py-1.5 text-xs">
      <code className="shrink-0 rounded bg-white/5 px-1.5 py-0.5 text-[11px] text-text-primary">{point.point_ref}</code>
      <span className="text-text-faint">→</span>
      <select
        value={point.sensor_type}
        onChange={(e) => void patch({ sensor_type: e.target.value })}
        className="bg-bg-input border border-border-faint text-text-primary rounded px-1.5 py-1 text-[11px] focus:outline-none focus:ring-1 focus:ring-brand-emerald"
        aria-label="Sensor type"
      >
        {sensorTypes.every((s) => s.value !== point.sensor_type) && (
          <option value={point.sensor_type}>{point.sensor_type}</option>
        )}
        {sensorTypes.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>
      <input
        value={zone}
        onChange={(e) => setZone(e.target.value)}
        onBlur={() => {
          const next = zone.trim() || null
          if (next !== (point.zone ?? null)) void patch({ zone: next })
        }}
        placeholder="zone"
        aria-label="Zone"
        className="w-24 bg-bg-input border border-border-faint text-text-primary rounded px-1.5 py-1 text-[11px] focus:outline-none focus:ring-1 focus:ring-brand-emerald"
      />
      {point.unit && <span className="text-text-faint">{point.unit}</span>}
      <label className="ml-auto flex items-center gap-1 text-text-muted">
        <input
          type="checkbox"
          checked={point.enabled}
          onChange={(e) => void patch({ enabled: e.target.checked })}
          className="accent-brand-emerald"
        />
        on
      </label>
      <button
        type="button"
        onClick={() => void remove()}
        aria-label="Delete point"
        className="rounded p-1 text-text-faint transition-colors hover:text-red-300"
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  )
}

// --- add point inline form -------------------------------------------------

function AddPointForm({
  sensorTypes,
  onAdd,
}: {
  sensorTypes: SensorTypeOption[]
  onAdd: (input: { point_ref: string; sensor_type: string; zone: string; unit: string }) => Promise<Result<Device>>
}) {
  const [ref, setRef] = useState("")
  const [sensorType, setSensorType] = useState(sensorTypes[0]?.value ?? "")
  const [zone, setZone] = useState("")
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const unit = sensorTypes.find((s) => s.value === sensorType)?.unit ?? ""

  async function add() {
    if (!ref.trim()) {
      setErr("Enter the point reference (register / object / topic).")
      return
    }
    if (!sensorType) {
      setErr("Pick a sensor type.")
      return
    }
    setBusy(true)
    setErr(null)
    const r = await onAdd({ point_ref: ref.trim(), sensor_type: sensorType, zone, unit })
    setBusy(false)
    if (r.ok) {
      setRef("")
      setZone("")
    } else {
      setErr(r.error)
    }
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <input
        value={ref}
        onChange={(e) => setRef(e.target.value)}
        placeholder="point ref (e.g. 3060 / AI:1 / temperature)"
        aria-label="Point reference"
        className="w-56 bg-bg-input border border-border-faint text-text-primary rounded px-2 py-1 text-[11px] focus:outline-none focus:ring-1 focus:ring-brand-emerald"
      />
      <select
        value={sensorType}
        onChange={(e) => setSensorType(e.target.value)}
        aria-label="Sensor type"
        className="bg-bg-input border border-border-faint text-text-primary rounded px-1.5 py-1 text-[11px] focus:outline-none focus:ring-1 focus:ring-brand-emerald"
      >
        {sensorTypes.map((s) => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
      </select>
      <input
        value={zone}
        onChange={(e) => setZone(e.target.value)}
        placeholder="zone (optional)"
        aria-label="Zone"
        className="w-24 bg-bg-input border border-border-faint text-text-primary rounded px-2 py-1 text-[11px] focus:outline-none focus:ring-1 focus:ring-brand-emerald"
      />
      <button
        type="button"
        onClick={() => void add()}
        disabled={busy}
        className="inline-flex items-center gap-1 rounded border border-brand-emerald/40 px-2 py-1 text-[11px] text-brand-emerald transition-colors hover:bg-brand-emerald/10 disabled:opacity-50"
      >
        <Plus className="h-3 w-3" />
        {busy ? "Adding…" : "Add point"}
      </button>
      {err && <span className="text-[11px] text-red-300">{err}</span>}
    </div>
  )
}
