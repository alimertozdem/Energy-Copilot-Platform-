/**
 * Devices & Connections (Tier-2/3) — browser client helpers.
 *
 * All calls go through the /api/buildings/{uuid}/devices... proxies (which
 * forward the session token). building_id is the Postgres UUID, so this works
 * for buildings still pending a Fabric bridge. Types stay in lockstep with
 * backend app/schemas/connection.py.
 */
export type DeviceProtocol = "bacnet" | "modbus" | "mqtt" | "rest_api" | "opc_ua"
export type DeviceStatus = "pending" | "active" | "error" | "disabled"

export type SensorPoint = {
  id: string
  device_id: string
  point_ref: string
  sensor_type: string
  zone: string | null
  unit: string | null
  scale: number
  enabled: boolean
}

export type Device = {
  id: string
  building_id: string
  name: string
  protocol: string
  connection_config: Record<string, unknown> | null
  status: string
  template_key: string | null
  last_seen_at: string | null
  points: SensorPoint[]
}

export type SensorTypeOption = { value: string; label: string; unit: string | null }

export type TemplatePoint = {
  point_ref: string
  sensor_type: string
  unit: string | null
  scale: number
  label: string | null
}

export type DeviceTemplate = {
  key: string
  label: string
  protocol: DeviceProtocol
  description: string | null
  default_config: Record<string, unknown>
  points: TemplatePoint[]
}

export type DeviceTemplateCatalog = {
  templates: DeviceTemplate[]
  sensor_types: SensorTypeOption[]
}

export type SensorPointInput = {
  point_ref: string
  sensor_type: string
  zone?: string | null
  unit?: string | null
  scale?: number
  enabled?: boolean
}

export type DeviceCreateInput = {
  name: string
  protocol: DeviceProtocol
  connection_config?: Record<string, unknown> | null
  template_key?: string | null
  points?: SensorPointInput[]
}

export type DeviceUpdateInput = {
  name?: string
  connection_config?: Record<string, unknown> | null
  status?: DeviceStatus
}

export type SensorPointUpdateInput = Partial<SensorPointInput>

export type Result<T> = { ok: true; data: T } | { ok: false; error: string }

/** Protocol options for the device-add form (label + connection-field hints). */
export const PROTOCOLS: { value: DeviceProtocol; label: string }[] = [
  { value: "modbus", label: "Modbus TCP" },
  { value: "bacnet", label: "BACnet/IP" },
  { value: "mqtt", label: "MQTT" },
  { value: "rest_api", label: "REST API" },
  { value: "opc_ua", label: "OPC-UA" },
]

/** The connection_config keys each protocol expects (drives the dynamic form). */
export const PROTOCOL_FIELDS: Record<DeviceProtocol, { key: string; label: string; placeholder?: string }[]> = {
  modbus: [
    { key: "host", label: "Host / IP", placeholder: "192.168.1.50" },
    { key: "port", label: "Port", placeholder: "502" },
    { key: "unit_id", label: "Unit ID", placeholder: "1" },
  ],
  bacnet: [
    { key: "host", label: "Host / IP", placeholder: "192.168.1.60" },
    { key: "device_instance", label: "Device instance", placeholder: "1001" },
    { key: "port", label: "Port", placeholder: "47808" },
  ],
  mqtt: [
    { key: "broker", label: "Broker host", placeholder: "mqtt.example.com" },
    { key: "port", label: "Port", placeholder: "1883" },
    { key: "base_topic", label: "Base topic", placeholder: "building/+/climate" },
  ],
  rest_api: [
    { key: "endpoint", label: "Endpoint URL", placeholder: "https://api.example.com/readings" },
    { key: "auth_header", label: "Auth header", placeholder: "Bearer ..." },
  ],
  opc_ua: [
    { key: "endpoint", label: "Endpoint URL", placeholder: "opc.tcp://192.168.1.70:4840" },
  ],
}

async function jreq<T>(
  url: string,
  method: "GET" | "POST" | "PATCH" | "DELETE",
  body?: unknown
): Promise<Result<T>> {
  try {
    const res = await fetch(url, {
      method,
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
    if (res.status === 204) {
      return { ok: true, data: null as T }
    }
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const detail =
        data && typeof data === "object" && "detail" in data
          ? String((data as { detail: unknown }).detail)
          : `Request failed (${res.status})`
      return { ok: false, error: detail }
    }
    return { ok: true, data: data as T }
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
}

const base = (buildingId: string) =>
  `/api/buildings/${encodeURIComponent(buildingId)}/devices`

export function fetchDeviceTemplates(): Promise<Result<DeviceTemplateCatalog>> {
  return jreq<DeviceTemplateCatalog>("/api/device-templates", "GET")
}

export function fetchDevices(buildingId: string): Promise<Result<{ devices: Device[] }>> {
  return jreq<{ devices: Device[] }>(base(buildingId), "GET")
}

export function createDevice(
  buildingId: string,
  input: DeviceCreateInput
): Promise<Result<Device>> {
  return jreq<Device>(base(buildingId), "POST", input)
}

export function updateDevice(
  buildingId: string,
  deviceId: string,
  input: DeviceUpdateInput
): Promise<Result<Device>> {
  return jreq<Device>(`${base(buildingId)}/${encodeURIComponent(deviceId)}`, "PATCH", input)
}

export function deleteDevice(buildingId: string, deviceId: string): Promise<Result<null>> {
  return jreq<null>(`${base(buildingId)}/${encodeURIComponent(deviceId)}`, "DELETE")
}

export function addPoint(
  buildingId: string,
  deviceId: string,
  input: SensorPointInput
): Promise<Result<Device>> {
  return jreq<Device>(`${base(buildingId)}/${encodeURIComponent(deviceId)}/points`, "POST", input)
}

export function updatePoint(
  buildingId: string,
  deviceId: string,
  pointId: string,
  input: SensorPointUpdateInput
): Promise<Result<Device>> {
  return jreq<Device>(
    `${base(buildingId)}/${encodeURIComponent(deviceId)}/points/${encodeURIComponent(pointId)}`,
    "PATCH",
    input
  )
}

export function deletePoint(
  buildingId: string,
  deviceId: string,
  pointId: string
): Promise<Result<Device>> {
  return jreq<Device>(
    `${base(buildingId)}/${encodeURIComponent(deviceId)}/points/${encodeURIComponent(pointId)}`,
    "DELETE"
  )
}

// --- pipeline verification (test telemetry + recent landed readings) -------

export type TestTelemetryResult = { accepted: number; building_id: string }

export type RecentReading = {
  sensor_type: string
  reading_value: number | null
  reading_unit: string | null
  sensor_location: string | null
  source_protocol: string | null
  received_at: string
  simulated: boolean
}

/** Push a few simulated readings through the live ingest path (no hardware). */
export function sendTestTelemetry(
  buildingId: string
): Promise<Result<TestTelemetryResult>> {
  return jreq<TestTelemetryResult>(
    `/api/buildings/${encodeURIComponent(buildingId)}/test-telemetry`,
    "POST"
  )
}

/** Most recent landed readings for a building (real + simulated, tagged). */
export function fetchRecentReadings(
  buildingId: string,
  limit = 20
): Promise<Result<{ readings: RecentReading[] }>> {
  return jreq<{ readings: RecentReading[] }>(
    `/api/buildings/${encodeURIComponent(buildingId)}/recent-readings?limit=${limit}`,
    "GET"
  )
}
