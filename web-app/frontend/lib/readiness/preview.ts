/**
 * Client-side Data Score preview for the onboarding wizard.
 *
 * The building does not exist yet during onboarding, so we cannot call
 * GET /buildings/{id}/readiness. This module MIRRORS the backend engine
 * (app/services/building_readiness.py) exactly — same signal weights, same
 * report dependencies, same scoring maths — so the live score the user sees
 * while filling the form matches what the server computes once the building is
 * saved. Keep the two in sync: if you change a weight or a report dependency on
 * the backend, change it here too.
 *
 * Consumption is treated as "not yet on file" during onboarding (months = 0):
 * the biggest unlock — uploading 12 months of energy use — therefore shows up
 * as the top "next action", which is exactly the motivating loop we want.
 */
import type {
  BuildingReadiness,
  ReadinessAction,
  ReadinessReport,
  ReadinessSignal,
} from "@/lib/api/readiness"
import type { OnboardingData } from "@/app/onboarding/types"

type Attrs = Record<string, unknown>

function has(a: Attrs, ...keys: string[]): boolean {
  return keys.every((k) => {
    const v = a[k]
    return v !== null && v !== undefined && v !== ""
  })
}

type Sig = {
  key: string
  label: string
  points: number
  present: (a: Attrs, months: number) => boolean
  applicable?: (a: Attrs) => boolean
  help: string
}

// Mirror of SIGNALS in building_readiness.py
const SIGNALS: Sig[] = [
  { key: "consumption", label: "12 months of energy use", points: 30, present: (_a, m) => m >= 1, help: "Upload a utility bill or monthly meter export." },
  { key: "area", label: "Floor area", points: 8, present: (a) => has(a, "area"), help: "Gross / conditioned m² — drives every intensity figure." },
  { key: "building_type", label: "Building type", points: 4, present: (a) => has(a, "building_type"), help: "" },
  { key: "construction_year", label: "Year built", points: 3, present: (a) => has(a, "construction_year"), help: "" },
  { key: "country", label: "Country", points: 3, present: (a) => has(a, "country"), help: "Sets the grid CO₂ factor and which national rules apply." },
  { key: "heating", label: "Heating system & fuel", points: 12, present: (a) => has(a, "heating_system"), help: "Unlocks Scope 1, the CO₂ cost split and the GEG §71 heating check." },
  { key: "u_values", label: "Envelope U-values", points: 15, present: (a) => has(a, "wall_u_value", "roof_u_value", "window_u_value"), help: "Wall / roof / window U-values unlock the GEG conformity check." },
  { key: "epc_class", label: "Energy certificate (EPC)", points: 6, present: (a) => has(a, "epc_class"), help: "Makes the EPC exact (otherwise it is estimated from your EUI)." },
  { key: "insulation_year", label: "Insulation year", points: 4, present: (a) => has(a, "insulation_year"), help: "" },
  { key: "occupants", label: "Typical occupants", points: 5, present: (a) => has(a, "typical_occupants"), help: "" },
  { key: "pv", label: "Solar PV details", points: 7, present: (a) => has(a, "pv_capacity"), applicable: (a) => Boolean(a["has_pv"]) || has(a, "pv_capacity"), help: "Capacity (kWp) + roof — unlocks the solar KPIs." },
]
const SIGNAL_BY_KEY: Record<string, Sig> = Object.fromEntries(SIGNALS.map((s) => [s.key, s]))

type Rep = {
  key: string
  label: string
  required: string[]
  improving?: string[]
  applicable?: (a: Attrs) => boolean
  note?: string
}

// Mirror of REPORTS in building_readiness.py
const REPORTS: Rep[] = [
  { key: "energy", label: "Energy KPIs & EUI", required: ["consumption", "area"] },
  { key: "ghg", label: "GHG Inventory (Scope 1/2/3)", required: ["consumption", "area"], improving: ["heating", "country"], note: "Scope 1 needs the heating fuel; Scope 3 is always estimated." },
  { key: "esrs", label: "ESRS E-1 (Climate)", required: ["consumption", "area"] },
  { key: "vsme", label: "VSME report", required: ["consumption", "area"] },
  { key: "gresb", label: "GRESB readiness", required: ["consumption", "area"] },
  { key: "crrem", label: "CRREM stranding", required: ["consumption", "area", "country"] },
  { key: "epc", label: "EPC pre-assessment", required: ["consumption", "area"], improving: ["epc_class"], note: "Estimated from your EUI; add the EPC class to make it exact." },
  { key: "geg", label: "GEG conformity", required: ["u_values", "heating"], improving: ["insulation_year", "country"] },
  { key: "co2_cost", label: "CO₂ Cost Split", required: ["heating", "area"], improving: ["consumption"] },
  { key: "enefg", label: "EnEfG plan", required: ["consumption"] },
  { key: "recommendations", label: "Retrofit recommendations", required: ["consumption", "area"], improving: ["heating", "u_values", "construction_year"] },
  { key: "solar", label: "Solar KPIs", required: ["pv"], applicable: (a) => Boolean(a["has_pv"]) },
]

/** Map the in-progress onboarding form to the engine's attrs dict. */
export function attrsFromOnboarding(d: OnboardingData): Attrs {
  return {
    area: d.floor_area_m2,
    building_type: d.building_type,
    construction_year: d.construction_year,
    country: d.country_code,
    heating_system: d.heating_system,
    epc_class: d.epc_class,
    typical_occupants: d.typical_occupants,
    pv_capacity: d.has_solar ? d.pv_capacity_kwp : "",
    has_pv: d.has_solar,
    wall_u_value: d.wall_u_value,
    roof_u_value: d.roof_u_value,
    window_u_value: d.window_u_value,
    insulation_year: d.insulation_year,
  }
}

export function previewReadiness(d: OnboardingData, consumptionMonths = 0): BuildingReadiness {
  const a = attrsFromOnboarding(d)

  const applicable: Record<string, boolean> = {}
  const present: Record<string, boolean> = {}
  for (const s of SIGNALS) {
    applicable[s.key] = s.applicable ? s.applicable(a) : true
    present[s.key] = applicable[s.key] && s.present(a, consumptionMonths)
  }

  const earned = SIGNALS.filter((s) => present[s.key]).reduce((t, s) => t + s.points, 0)
  const possible = SIGNALS.filter((s) => applicable[s.key]).reduce((t, s) => t + s.points, 0) || 1
  const score = Math.round((earned / possible) * 100)

  const signals: ReadinessSignal[] = SIGNALS.map((s) => ({
    key: s.key, label: s.label, points: s.points,
    present: present[s.key], applicable: applicable[s.key], help: s.help,
  }))

  const reports: ReadinessReport[] = REPORTS.map((r) => {
    if (r.applicable && !r.applicable(a)) {
      return { key: r.key, label: r.label, status: "not_applicable", missing: [], note: "" }
    }
    const missReq = r.required.filter((k) => !present[k])
    const missImp = (r.improving ?? []).filter((k) => !present[k])
    let status: ReadinessReport["status"]
    if (missReq.length) status = "locked"
    else if (missImp.length || r.note) status = "partial"
    else status = "ready"
    const missKeys = missReq.length ? missReq : missImp
    return {
      key: r.key, label: r.label, status,
      missing: missKeys.map((k) => SIGNAL_BY_KEY[k]?.label).filter((x): x is string => Boolean(x)),
      note: status === "partial" ? r.note ?? "" : "",
    }
  })

  const next_actions: ReadinessAction[] = [...SIGNALS]
    .sort((x, y) => y.points - x.points)
    .filter((s) => applicable[s.key] && !present[s.key])
    .map((s) => {
      const unlocks = REPORTS.filter(
        (r) =>
          (!r.applicable || r.applicable(a)) &&
          r.required.includes(s.key) &&
          r.required.every((k) => present[k] || k === s.key)
      ).map((r) => r.label)
      return { key: s.key, label: s.label, points: s.points, help: s.help, unlocks }
    })

  return { data_score: score, points_earned: earned, points_possible: possible, signals, reports, next_actions }
}
