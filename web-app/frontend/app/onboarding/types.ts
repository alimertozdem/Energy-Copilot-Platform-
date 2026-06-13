/**
 * Shared onboarding wizard types + constants.
 *
 * Kept in its own module so the wizard and its step components can import
 * the shape without a circular dependency (wizard imports steps; steps
 * import the data shape).
 */

export type OnboardingData = {
  // Building basics
  name: string
  building_type: string
  city: string
  country_code: string
  floor_area_m2: string // kept as string for inputs; parsed on submit
  construction_year: string
  epc_class: string
  floors_above_ground: string
  typical_occupants: string
  // Envelope & efficiency (unlock the GEG check + sharpen retrofit advice)
  wall_u_value: string
  roof_u_value: string
  window_u_value: string
  insulation_year: string
  // Systems & data
  has_iot: boolean
  has_battery: boolean
  has_solar: boolean
  pv_capacity_kwp: string
  heating_system: string
  heating_other: string
  cooling_system: string
  cooling_other: string
  occupancy_pattern: string
  // IoT connection config (revealed when has_iot)
  iot_protocols: string[]
  iot_sensor_types: string[]
  iot_zones: string
  // Residential-only
  residential_units: string
  data_source: string // intent: Manual / Meter / BACnet / Modbus / MQTT / API
  data_method: string // how data arrives: live / upload / manual / later
}

export const INITIAL_DATA: OnboardingData = {
  name: "",
  building_type: "",
  city: "",
  country_code: "",
  floor_area_m2: "",
  construction_year: "",
  epc_class: "",
  floors_above_ground: "",
  typical_occupants: "",
  wall_u_value: "",
  roof_u_value: "",
  window_u_value: "",
  insulation_year: "",
  has_iot: false,
  has_battery: false,
  has_solar: false,
  pv_capacity_kwp: "",
  heating_system: "",
  heating_other: "",
  cooling_system: "",
  cooling_other: "",
  occupancy_pattern: "",
  iot_protocols: [],
  iot_sensor_types: [],
  iot_zones: "",
  residential_units: "",
  data_source: "",
  data_method: "",
}

export const STEPS = ["Welcome", "Building", "Systems", "Envelope", "Review", "Done"] as const

export const BUILDING_TYPES = [
  "Office",
  "Retail",
  "Hotel",
  "Healthcare",
  "Logistics",
  "Datacenter",
  "Residential",
  "Mixed",
] as const

// Data-source intent (Phase 2 IoT interoperability protocols + simple options).
export const DATA_SOURCES = [
  "Manual entry",
  "Energy meter",
  "BACnet",
  "Modbus TCP",
  "MQTT",
  "Vendor API",
] as const

// Energy-profile option lists (value sent to backend / label shown to user).
export const EPC_CLASSES = ["A", "B", "C", "D", "E", "F", "G"] as const

export const HEATING_SYSTEMS = [
  { value: "gas_boiler", label: "Gas boiler" },
  { value: "heat_pump", label: "Heat pump" },
  { value: "district_heating", label: "District heating" },
  { value: "electric", label: "Electric / direct" },
  { value: "oil", label: "Oil" },
  { value: "biomass", label: "Biomass / pellets" },
  { value: "other", label: "Other" },
] as const

export const COOLING_SYSTEMS = [
  { value: "none", label: "None" },
  { value: "split_ac", label: "Split AC" },
  { value: "central_chiller", label: "Central chiller" },
  { value: "district_cooling", label: "District cooling" },
  { value: "other", label: "Other" },
] as const

export const OCCUPANCY_PATTERNS = [
  { value: "standard_hours", label: "Standard hours (≈9–5)" },
  { value: "extended_hours", label: "Extended hours" },
  { value: "always_on", label: "24/7" },
  { value: "seasonal", label: "Seasonal" },
] as const

// IoT connection config (revealed when the building has IoT sensors).
export const IOT_PROTOCOLS = [
  { value: "bacnet", label: "BACnet/IP" },
  { value: "modbus", label: "Modbus TCP" },
  { value: "mqtt", label: "MQTT" },
  { value: "rest_api", label: "REST API" },
  { value: "opc_ua", label: "OPC-UA" },
  { value: "unknown", label: "Not sure yet" },
] as const

export const IOT_SENSOR_TYPES = [
  { value: "temperature", label: "Temperature" },
  { value: "humidity", label: "Humidity" },
  { value: "co2", label: "CO₂" },
  { value: "power", label: "Power / energy" },
  { value: "occupancy", label: "Occupancy" },
  { value: "submeter", label: "Sub-meters" },
] as const

// How the building's data will reach EnergyLens. No-hardware options first —
// upload / manual need nothing but a bill; a live connection comes later.
export const DATA_METHODS = [
  {
    value: "upload",
    label: "Upload bills / CSV",
    desc: "No hardware — send historical consumption and we build your baseline.",
  },
  {
    value: "manual",
    label: "Manual entry",
    desc: "No hardware — type in monthly meter readings yourself.",
  },
  {
    value: "live",
    label: "Live connection",
    desc: "Stream from a BMS / gateway — BACnet, Modbus, MQTT or API.",
  },
  {
    value: "later",
    label: "Decide later",
    desc: "Set up the data connection once your workspace is ready.",
  },
] as const
