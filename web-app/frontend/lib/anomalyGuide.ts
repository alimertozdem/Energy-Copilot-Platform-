/**
 * anomalyGuide — plain-language remediation guidance per anomaly category.
 *
 * The /alerts detail panel turns a raw anomaly (type + description +
 * recommended_action) into something an operator can act on: what it means,
 * likely causes, what to check, and what to do if it persists.
 *
 * Matching is by substring on the (uppercased) anomaly_type, so it is robust to
 * the exact enum names emitted by the AFDD pipeline. Unknown types fall back to
 * a generic entry; the panel still shows the pipeline's own recommended action
 * alongside this guidance.
 *
 * This is GENERAL operational guidance (standard building-energy / fault-
 * detection practice), not a site-specific diagnosis — always confirm on site.
 */

export type AnomalyGuide = {
  category: string
  whatItMeans: string
  likelyCauses: string[]
  whatToCheck: string[]
  ifItPersists: string
}

const SOLAR: AnomalyGuide = {
  category: "Solar underperformance",
  whatItMeans:
    "The PV system is generating, but its performance ratio is below the healthy range, so it produces less than the irradiance and installed capacity would predict.",
  likelyCauses: [
    "Soiling, snow or new shading on the panels",
    "Inverter fault, clipping or an offline string",
    "Blown string fuse or a DC isolation issue",
    "MPPT mis-tracking or temperature derating",
    "Gradual module degradation",
  ],
  whatToCheck: [
    "Inverter status and fault log for error codes",
    "Per-string currents for a weak or offline string",
    "Panels for dirt, debris or recent shading",
    "That measured irradiance and the expected-yield baseline look sane",
  ],
  ifItPersists:
    "If the ratio stays low after cleaning and an inverter check, raise a maintenance ticket with the O&M provider and compare against string-level data. A persistent shortfall usually points to an inverter or string fault rather than weather.",
}

const HVAC: AnomalyGuide = {
  category: "HVAC / comfort deviation",
  whatItMeans:
    "Zone conditions or HVAC energy use are outside the expected band, so comfort or efficiency is drifting away from setpoint.",
  likelyCauses: [
    "A setpoint or schedule override left in place",
    "A stuck damper, valve or economizer",
    "Simultaneous heating and cooling",
    "A fouled coil or filter, or a failing sensor",
  ],
  whatToCheck: [
    "Current setpoints and schedule against occupancy",
    "Supply and return temperatures and the delta-T",
    "Damper and valve positions for stuck actuators",
    "Filter / coil condition and sensor calibration",
  ],
  ifItPersists:
    "If conditions stay out of band after clearing overrides and resetting schedules, inspect the actuators and sensors on site. Recurring simultaneous heating and cooling is a controls issue worth escalating to the BMS integrator.",
}

const AIR: AnomalyGuide = {
  category: "Air quality / CO2",
  whatItMeans:
    "Indoor CO2 (or another air-quality reading) is above its threshold, indicating under-ventilation relative to occupancy.",
  likelyCauses: [
    "Outdoor-air damper closed or economizer stuck",
    "Demand-controlled ventilation set too low",
    "Higher occupancy than the ventilation schedule assumes",
    "A drifting or failing CO2 sensor",
  ],
  whatToCheck: [
    "Outdoor-air damper position and the fresh-air rate",
    "Ventilation schedule against actual occupancy",
    "CO2 sensor calibration",
  ],
  ifItPersists:
    "If levels stay high after increasing fresh air, verify the sensor and inspect the air-handling unit. Sustained high CO2 is both a comfort and a compliance concern worth prioritising.",
}

const POWER: AnomalyGuide = {
  category: "Power / demand spike",
  whatItMeans:
    "Electrical demand has risen well above the building baseline, which can drive peak-demand charges and signals an abnormal load.",
  likelyCauses: [
    "Equipment running outside its schedule",
    "Several large loads starting at once",
    "A faulty or short-cycling system",
    "A metering or sub-metering error",
  ],
  whatToCheck: [
    "Which circuit or sub-meter carries the excess load",
    "Equipment schedules around the time of the spike",
    "Whether the spike lines up with occupancy or a known event",
  ],
  ifItPersists:
    "If spikes recur, stagger large-load start-ups and review the demand profile. Persistent peaks are worth addressing for both cost (peak charges) and equipment health.",
}

const CONSUMPTION: AnomalyGuide = {
  category: "Consumption deviation",
  whatItMeans:
    "Measured energy use deviates significantly from the building's expected baseline for these conditions.",
  likelyCauses: [
    "A recent schedule or override change",
    "Weather or occupancy not reflected in the baseline",
    "Degrading equipment efficiency",
    "A metering or data-quality issue",
  ],
  whatToCheck: [
    "Recent schedule, setpoint or tenant changes",
    "Whether weather or occupancy explains the shift",
    "Meter data continuity across the period",
  ],
  ifItPersists:
    "If the deviation continues without an obvious operational cause, compare against sub-meters to localise it and review the affected systems.",
}

const GENERIC: AnomalyGuide = {
  category: "Flagged anomaly",
  whatItMeans:
    "A reading deviates significantly from the building's expected baseline and has been flagged for review.",
  likelyCauses: [
    "Equipment running outside its schedule or setpoint",
    "A fault, drift or calibration issue in the affected system",
    "Weather or occupancy not captured by the baseline",
    "A metering or data-quality issue",
  ],
  whatToCheck: [
    "The affected system's status and any recent changes",
    "Whether the reading aligns with a known operational event",
    "Sensor calibration and meter continuity",
  ],
  ifItPersists:
    "If the anomaly recurs after the immediate checks, localise it with sub-metering and escalate to the responsible system owner.",
}

/** Map an anomaly_type string to its remediation guide (substring-matched). */
export function anomalyGuide(anomalyType: string | null): AnomalyGuide {
  const t = (anomalyType ?? "").toUpperCase()
  if (/SOLAR|PV|INVERTER|YIELD|PERFORMANCE_?RATIO/.test(t)) return SOLAR
  if (/HVAC|TEMP|COMFORT|SETPOINT|HEAT|COOL/.test(t)) return HVAC
  if (/CO2|VENT|AIR|HUMID/.test(t)) return AIR
  if (/POWER|SPIKE|DEMAND|PEAK|LOAD/.test(t)) return POWER
  if (/CONSUM|BASELINE|ENERGY|USAGE|KWH/.test(t)) return CONSUMPTION
  return GENERIC
}


// --- Anomaly cost (screening) -------------------------------------------------
// Indicative € impact, shown ONLY where the metric is an energy quantity.
// CONSUMPTION_SPIKE: metric=day kWh, threshold=baseline kWh -> excess kWh x price.
// Other types (EUI ratios, ppm, PR) are not directly cost-able -> null.
const ANOMALY_PRICE_EUR_KWH = 0.2 // DE default; see glossary `anomaly_cost`

export function estAnomalyCostEur(
  anomalyType: string | null,
  metricValue: number | null,
  thresholdValue: number | null,
): number | null {
  if (anomalyType !== "CONSUMPTION_SPIKE") return null
  if (metricValue == null || thresholdValue == null) return null
  const excessKwh = metricValue - thresholdValue
  if (!(excessKwh > 0)) return null
  return excessKwh * ANOMALY_PRICE_EUR_KWH
}
