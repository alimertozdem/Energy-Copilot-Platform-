/**
 * Building AI advisor — deterministic insight engine (Layer 1).
 *
 * Pure functions over data the building view already fetches (no LLM, no new
 * backend). Each insight follows the consultant-grade shape from the
 * energy-insight-generator skill: a titled issue tied to ACTUAL building
 * behaviour, why it matters, an estimated RANGE (never fake precision), a
 * confidence level and the data assumption behind it — plus a deep-link to the
 * page that acts on it.
 *
 * Energy-logic guardrails (CLAUDE.md): realistic engineering logic only, no
 * invented fields, ranges over exact values, assumptions stated. The EUI
 * benchmark bands below are INDICATIVE public-benchmark ranges, surfaced as
 * such — the energy domain reviewer can refine them in one place.
 */
import type { ActionItem } from "@/lib/api/actions"
import type { AlertItem } from "@/lib/api/alerts"
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"
import type { ResidentialBuildingResponse } from "@/lib/api/residentialManager"
import type { EngineEstimate } from "@/lib/api/estimation"

export type InsightSeverity = "action" | "watch" | "info" | "good"
export type Confidence = "high" | "medium" | "low"

export type Insight = {
  id: string
  severity: InsightSeverity
  title: string
  detail: string
  metric?: string
  range?: string
  confidence: Confidence
  assumption?: string
  recommendation?: string
  href?: string
  cta?: string
}

/**
 * Declared building profile (Postgres), captured at onboarding. Lets the advisor
 * give EPC + heating advice even BEFORE live Fabric data is connected, and acts
 * as the EPC fallback when the Fabric KPI row hasn't been rated yet.
 */
export type DeclaredProfile = {
  epc_class: string | null
  heating_system: string | null
}

// Indicative typical EUI bands (kWh/m²·yr) by building type. These are public
// benchmark ranges (ENERGY STAR / CIBSE TM46 / EU typical), NOT site-specific
// targets — shown as "indicative" wherever used. One place to refine.
const EUI_BANDS: { match: RegExp; low: number; high: number; label: string }[] = [
  { match: /hospital|health|clinic|care/, low: 250, high: 450, label: "healthcare" },
  { match: /hotel|hospitality|lodg/, low: 200, high: 350, label: "hotel" },
  { match: /retail|mall|shop|store|supermarket/, low: 150, high: 300, label: "retail" },
  { match: /school|education|university|campus|lab/, low: 100, high: 220, label: "education / lab" },
  { match: /logistic|warehouse|distribution|storage/, low: 40, high: 120, label: "logistics" },
  { match: /residential|apartment|wohn|multi.?family/, low: 100, high: 180, label: "residential" },
  { match: /office|commercial|mixed/, low: 100, high: 200, label: "office" },
]
const EUI_DEFAULT = { low: 100, high: 250, label: "mixed commercial" }

// Indicative grid prices (€/kWh) — mirrors the anomaly-cost logic in CLAUDE.md.
const PRICE_BY_COUNTRY: Record<string, number> = { DE: 0.20, AT: 0.21, FR: 0.19, NL: 0.20, TR: 0.14 }
function gridPrice(country: string | null | undefined): number {
  if (!country) return 0.18
  return PRICE_BY_COUNTRY[country.toUpperCase()] ?? 0.18
}

function eur(n: number): string {
  if (n >= 10000) return "€" + new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(n)
  return "€" + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}

function isDatacenter(type: string): boolean {
  return /data\s*cent|datacenter|data_center|server\s*farm/.test(type)
}

// ----- individual rules -------------------------------------------------

function euiInsight(kpis: PortfolioBuildingRow): Insight | null {
  const eui = kpis.eui_kwh_m2_yr
  if (eui == null || eui <= 0) return null
  const type = (kpis.building_type || "").toLowerCase()

  if (isDatacenter(type)) {
    return {
      id: "eui-dc",
      severity: "info",
      title: "EUI per m² isn’t the right yardstick here",
      detail:
        "For a datacenter, IT load dwarfs floor-area intensity, so kWh/m² says little. Track PUE (facility ÷ IT energy) instead.",
      metric: `${Math.round(eui)} kWh/m²·yr`,
      confidence: "high",
      assumption: "Datacenter inferred from building type.",
    }
  }

  const band = EUI_BANDS.find((b) => b.match.test(type)) ?? EUI_DEFAULT
  const rangeLabel = `${band.low}–${band.high} kWh/m²·yr (indicative, ${band.label})`

  if (eui < band.low) {
    return {
      id: "eui",
      severity: "good",
      title: "Energy intensity below the typical range",
      detail: `At ${Math.round(eui)} kWh/m²·yr this building sits under the typical band for ${band.label} — efficient on a per-area basis.`,
      metric: `${Math.round(eui)} kWh/m²·yr`,
      range: rangeLabel,
      confidence: "low",
      assumption: "EUI is an annualized run-rate, not weather-corrected; benchmark band is indicative.",
    }
  }

  if (eui <= band.high) {
    return {
      id: "eui",
      severity: "info",
      title: "Energy intensity is within the typical range",
      detail: `${Math.round(eui)} kWh/m²·yr falls inside the typical band for ${band.label}. Anomaly and recommendation insights below show where to push further.`,
      metric: `${Math.round(eui)} kWh/m²·yr`,
      range: rangeLabel,
      confidence: "low",
      assumption: "EUI is an annualized run-rate, not weather-corrected; benchmark band is indicative.",
    }
  }

  // Above the typical band — quantify an indicative saving toward the top of range.
  const area = kpis.floor_area_m2 ?? 0
  const excessKwh = Math.max(0, eui - band.high) * area
  const price = gridPrice(kpis.country)
  const full = excessKwh * price
  const lo = full * 0.4
  const hi = full * 0.8
  const pctOver = Math.round(((eui - band.high) / band.high) * 100)
  const hasMoney = area > 0 && full >= 500

  return {
    id: "eui",
    severity: eui > band.high * 1.25 ? "action" : "watch",
    title: `Energy intensity ~${pctOver}% above the typical range`,
    detail:
      `At ${Math.round(eui)} kWh/m²·yr this building runs above the typical band for ${band.label}.` +
      (hasMoney ? " Closing part of that gap is where the money is." : " Worth a closer look at HVAC scheduling and controls."),
    metric: `${Math.round(eui)} kWh/m²·yr`,
    range: hasMoney ? `${eur(lo)}–${eur(hi)}/yr indicative` : rangeLabel,
    confidence: "low",
    recommendation:
      "Start with HVAC scheduling and setpoint review, then controls and envelope — these usually recover the first 10–20% of the gap.",
    assumption:
      `Indicative only: gap to the top of the ${band.low}–${band.high} kWh/m²·yr band × ${Math.round(area).toLocaleString("en-US")} m² × €${price.toFixed(2)}/kWh, capturing 40–80%. EUI is a run-rate, not weather-corrected.`,
  }
}

function estimatedEuiInsight(est: EngineEstimate | null): Insight | null {
  if (!est || est.eui_point == null) return null
  const type = (est.building_type || "").toLowerCase()
  const band = EUI_BANDS.find((b) => b.match.test(type)) ?? EUI_DEFAULT
  const eui = Math.round(est.eui_point)
  const range =
    est.eui_low != null && est.eui_high != null
      ? `${Math.round(est.eui_low)}\u2013${Math.round(est.eui_high)} kWh/m\u00b2\u00b7yr (estimated)`
      : undefined
  // An estimate never claims "high" confidence.
  const conf: Confidence = est.confidence === "high" ? "medium" : "low"
  const verdict = eui > band.high ? "above" : eui < band.low ? "below" : "within"
  const tail =
    verdict === "above"
      ? ` That\u2019s above the typical ${band.low}\u2013${band.high} band for ${band.label}, so it\u2019s a likely efficiency / retrofit candidate.`
      : verdict === "below"
        ? ` That\u2019s below the typical ${band.low}\u2013${band.high} band for ${band.label}.`
        : ` That\u2019s inside the typical ${band.low}\u2013${band.high} band for ${band.label}.`
  return {
    id: "eui-est",
    severity: verdict === "above" ? "watch" : "info",
    title: `Estimated energy intensity ~${eui} kWh/m\u00b2\u00b7yr`,
    detail:
      `No bills uploaded yet \u2014 estimated at ~${eui} kWh/m\u00b2\u00b7yr from this building\u2019s type, age and climate.` +
      tail +
      " Upload a bill to replace this estimate with measured numbers.",
    metric: `~${eui} kWh/m\u00b2\u00b7yr (est.)`,
    range,
    confidence: conf,
    assumption: `Screening estimate (not measured): ${est.method || "archetype"}. Sharpens to actual once \u226512 months of bills exist.`,
  }
}

const ALERT_SEV_RANK: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }

function prettyAnomaly(t: string | null | undefined): string {
  if (!t) return "an anomaly"
  return t
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\bpr\b/g, "PR")
    .replace(/\bco2\b/g, "CO₂")
    .replace(/^\w/, (c) => c.toUpperCase())
}

function alertsInsight(
  kpis: PortfolioBuildingRow,
  topAlerts: AlertItem[] = []
): Insight | null {
  const n = kpis.open_anomalies
  if (n == null || n <= 0) return null

  // Name the building's most-severe open anomaly so the advice is concrete,
  // not just a count (mirrors how recsInsight names the top measure).
  const top = [...topAlerts].sort(
    (a, b) =>
      (ALERT_SEV_RANK[(a.severity || "").toLowerCase()] ?? 9) -
      (ALERT_SEV_RANK[(b.severity || "").toLowerCase()] ?? 9)
  )[0]
  const topLabel = top ? prettyAnomaly(top.anomaly_type) : null

  return {
    id: "alerts",
    severity: n >= 3 ? "action" : "watch",
    title: `${n} open alert${n === 1 ? "" : "s"} (high + critical)`,
    detail: topLabel
      ? `Top issue: ${topLabel}${top?.severity ? ` (${top.severity})` : ""}. Unresolved anomalies are live, costed waste — clear the most severe first.`
      : "Unresolved anomalies usually mean wasted energy, comfort drift or an equipment fault. Triage the queue to stop the bleed.",
    metric: `${n} open`,
    confidence: "high",
    recommendation: topLabel
      ? `Start with “${topLabel}” — the highest-severity open anomaly — then work down the queue.`
      : "Open the queue and clear critical/high first — each unresolved anomaly is live, costed waste.",
    href: `/alerts?building_id=${encodeURIComponent(kpis.fabric_building_id)}`,
    cta: "Open alerts",
  }
}

function recsInsight(kpis: PortfolioBuildingRow, topActions: ActionItem[]): Insight | null {
  const n = kpis.open_recommendations
  if (n == null || n <= 0) return null

  const top = [...topActions]
    .filter((a) => a.annual_saving_eur != null)
    .sort((x, y) => (y.annual_saving_eur ?? 0) - (x.annual_saving_eur ?? 0))[0]

  const detail = top
    ? `Biggest opportunity: ${top.title ?? top.action_type ?? "a measure"}` +
      (top.annual_saving_eur != null
        ? ` (~${eur(top.annual_saving_eur)}/yr` +
          (top.payback_years != null ? `, ~${top.payback_years.toFixed(0)} yr payback)` : ")")
        : "") +
      "."
    : "Open the list to see each measure quantified by saving and payback."

  return {
    id: "recs",
    severity: "action",
    title: `${n} savings opportunit${n === 1 ? "y" : "ies"} to review`,
    detail,
    metric: `${n} open`,
    confidence: top ? "medium" : "low",
    assumption: top ? "Saving and payback are model estimates from the recommendation engine." : undefined,
    recommendation: top
      ? "Action the top measure first — it has the best saving-to-payback ratio."
      : "Open the list and start with the highest saving-to-payback measure.",
    href: `/actions?building_id=${encodeURIComponent(kpis.fabric_building_id)}`,
    cta: "Review recommendations",
  }
}

function epcInsight(epcRaw: string | null): Insight | null {
  const epc = (epcRaw || "").toUpperCase()
  if (!epc) return null

  if (epc === "F" || epc === "G") {
    return {
      id: "epc",
      severity: "action",
      title: `EPC ${epc} — renovation risk`,
      detail:
        "Under the EU EPBD, the worst-performing bands face minimum-performance phase-outs this decade. Plan upgrades before the deadline bites.",
      metric: `EPC ${epc}`,
      confidence: "medium",
      recommendation:
        "Commission a renovation roadmap (iSFP) and check BAFA / KfW eligibility before the MEPS deadline.",
      assumption: "EPBD MEPS timing is indicative — national transposition varies.",
      href: "/compliance",
      cta: "See compliance",
    }
  }
  if (epc === "E") {
    return {
      id: "epc",
      severity: "watch",
      title: "EPC E — watch the MEPS line",
      detail:
        "Band E sits just above the first EPBD minimum-performance thresholds. A step up to D/C de-risks the renovation timeline.",
      metric: "EPC E",
      confidence: "medium",
      assumption: "EPBD MEPS timing is indicative.",
      href: "/compliance",
      cta: "See compliance",
    }
  }
  if (epc === "A" || epc === "B") {
    return {
      id: "epc",
      severity: "good",
      title: `EPC ${epc} — strong rating`,
      detail: "Compliance headroom is healthy; focus shifts from band risk to operational savings.",
      metric: `EPC ${epc}`,
      confidence: "high",
    }
  }
  return null
}

function heatingSystemInsight(p: DeclaredProfile): Insight | null {
  const h = p.heating_system
  if (!h) return null
  if (h === "gas_boiler" || h === "oil") {
    return {
      id: "heating",
      severity: "watch",
      title: h === "oil" ? "Oil heating — high-carbon" : "Gas heating — fossil-based",
      detail:
        "Fossil heating is usually the single biggest carbon source on site and faces tightening regulation this decade.",
      confidence: "medium",
      recommendation:
        "A heat-pump retrofit is the biggest carbon lever — check KfW 458 (up to 70%) eligibility.",
      assumption: "From the declared heating system; the actual saving depends on the building's heat demand.",
      href: "/financing",
      cta: "See subsidies",
    }
  }
  if (h === "electric") {
    return {
      id: "heating",
      severity: "watch",
      title: "Direct electric heating — costly",
      detail:
        "Resistive electric heating turns one unit of electricity into one unit of heat; a heat pump delivers three to four.",
      confidence: "medium",
      recommendation:
        "Model a heat-pump retrofit — it typically cuts heating energy 3–4× and qualifies for KfW 458.",
      assumption: "From the declared heating system.",
      href: "/financing",
      cta: "See subsidies",
    }
  }
  if (h === "heat_pump") {
    return {
      id: "heating",
      severity: "good",
      title: "Heat pump installed",
      detail: "Efficient, low-carbon heating is already in place — focus shifts to controls and envelope.",
      confidence: "high",
    }
  }
  if (h === "district_heating") {
    return {
      id: "heating",
      severity: "info",
      title: "District heating",
      detail:
        "Carbon depends on the network's generation mix — track the supplier's emission factor for accurate reporting.",
      confidence: "medium",
    }
  }
  if (h === "biomass") {
    return {
      id: "heating",
      severity: "info",
      title: "Biomass heating",
      detail: "Low operational carbon, but verify sustainable sourcing and local air-quality rules.",
      confidence: "low",
    }
  }
  return null
}

function assetInsights(kpis: PortfolioBuildingRow): Insight[] {
  const out: Insight[] = []
  const type = (kpis.building_type || "").toLowerCase()

  if (kpis.has_pv) {
    out.push({
      id: "pv",
      severity: "good",
      title: "On-site solar is active",
      detail: "Keep an eye on generation, self-consumption and export so the array keeps pulling its weight.",
      confidence: "high",
      href: "/solar",
      cta: "Open solar",
    })
  } else if (!isDatacenter(type)) {
    out.push({
      id: "pv",
      severity: "info",
      title: "No on-site solar yet",
      detail: "A rooftop PV assessment can show whether on-site generation would cut grid draw and carbon here.",
      confidence: "low",
      recommendation: "Commission a rooftop PV feasibility study (roof area, orientation, shading).",
      assumption: "Indicative — depends on roof area, orientation and shading (not yet assessed).",
      href: "/solar",
      cta: "Explore solar",
    })
  }

  if (kpis.has_pv && !kpis.has_battery) {
    out.push({
      id: "battery",
      severity: "info",
      title: "Solar without storage",
      detail: "A battery could shift midday export into evening self-use and shave peak demand.",
      confidence: "low",
      assumption: "Indicative — sizing depends on the load profile and tariff.",
      href: "/solar",
      cta: "Battery scenarios",
    })
  }

  if (!kpis.has_iot) {
    out.push({
      id: "iot",
      severity: "info",
      title: "No live IoT monitoring",
      detail: "Sub-metering (BACnet / Modbus / MQTT) sharpens fault detection and unlocks real-time alerts for this building.",
      confidence: "medium",
    })
  }

  return out
}

// ----- residential rules (per-building rollup) -------------------------
// Multi-family stock is metered for heating + hot water, not whole-building
// electricity, so it gets its own insight set: a heating-intensity verdict, the
// EED / Heizkostenverordnung monthly-statement (UVI) coverage gap, and EPC-band
// concentration. The shared alerts + recommendation insights still apply.

const RES_HEATING_BAND = { low: 100, high: 180 } // kWh/m²·yr, indicative MF heating+DHW

function heatingEuiInsight(r: ResidentialBuildingResponse): Insight | null {
  const eui = r.rollup.building_avg_eui_kwh_m2_yr
  if (eui == null || eui <= 0) return null
  const range = `${RES_HEATING_BAND.low}–${RES_HEATING_BAND.high} kWh/m²·yr (indicative, residential heating + hot water)`

  if (eui > RES_HEATING_BAND.high) {
    const pct = Math.round(((eui - RES_HEATING_BAND.high) / RES_HEATING_BAND.high) * 100)
    return {
      id: "res-eui",
      severity: eui > RES_HEATING_BAND.high * 1.25 ? "action" : "watch",
      title: `Heating intensity ~${pct}% above typical`,
      detail:
        `Building-average heating + hot-water intensity is ${Math.round(eui)} kWh/m²·yr — above the typical multi-family band. Envelope and heating-control upgrades are the usual levers.`,
      metric: `${Math.round(eui)} kWh/m²·yr`,
      range,
      confidence: "low",
      recommendation:
        "Prioritise envelope upgrades (insulation, glazing) and heating controls; model a gas vs heat-pump retrofit.",
      assumption:
        "Indicative band; heating EUI is not weather-corrected. Savings depend on the heating system (gas vs heat pump), so not estimated here.",
      href: "/compliance",
      cta: "Renovation pathways",
    }
  }
  if (eui < RES_HEATING_BAND.low) {
    return {
      id: "res-eui",
      severity: "good",
      title: "Heating intensity below typical",
      detail: `At ${Math.round(eui)} kWh/m²·yr this building heats efficiently for multi-family stock.`,
      metric: `${Math.round(eui)} kWh/m²·yr`,
      range,
      confidence: "low",
      assumption: "Indicative band; not weather-corrected.",
    }
  }
  return {
    id: "res-eui",
    severity: "info",
    title: "Heating intensity within typical range",
    detail: `${Math.round(eui)} kWh/m²·yr sits inside the typical multi-family band.`,
    metric: `${Math.round(eui)} kWh/m²·yr`,
    range,
    confidence: "low",
    assumption: "Indicative band; not weather-corrected.",
  }
}

function uviInsight(r: ResidentialBuildingResponse): Insight | null {
  const total = r.rollup.units_with_data
  const covered = r.rollup.uvi.units_covered
  if (total <= 0) return null
  const gap = total - covered
  if (gap <= 0) {
    return {
      id: "uvi",
      severity: "good",
      title: "Monthly consumption info complete",
      detail: `All ${total} units have monthly statements (UVI) — the EED / Heizkostenverordnung obligation is met.`,
      metric: `${covered}/${total}`,
      confidence: "high",
    }
  }
  return {
    id: "uvi",
    severity: "watch",
    title: `${gap} unit${gap === 1 ? "" : "s"} missing monthly statements`,
    detail:
      `UVI covers ${covered} of ${total} units. The EED / Heizkostenverordnung requires monthly consumption information for occupants — close the gap to stay compliant.`,
    metric: `${covered}/${total}`,
    confidence: "medium",
    recommendation: "Onboard the missing units to monthly statements to meet the EED / HKVO obligation.",
    assumption: "Coverage from the latest UVI period.",
    href: `/buildings/${encodeURIComponent(r.fabric_building_id)}/residential`,
    cta: "Residential units",
  }
}

function epcMixInsight(r: ResidentialBuildingResponse): Insight | null {
  const dist = r.rollup.epc_distribution || {}
  const total = Object.values(dist).reduce((s, n) => s + (n || 0), 0)
  if (total <= 0) return null
  const low = (dist.E || 0) + (dist.F || 0) + (dist.G || 0)
  if (low <= 0) {
    return {
      id: "res-epc",
      severity: "good",
      title: "No units in the worst EPC bands",
      detail: "No units sit in E–G — the building is clear of the near-term EPBD minimum-performance line.",
      confidence: "high",
    }
  }
  return {
    id: "res-epc",
    severity: low >= Math.ceil(total / 2) ? "action" : "watch",
    title: `${low} unit${low === 1 ? "" : "s"} at EPC E–G`,
    detail:
      `${low} of ${total} units fall in the worst-performing bands, which face EPBD minimum-performance phase-outs this decade. Prioritise these for renovation.`,
    metric: `${low}/${total} E–G`,
    confidence: "medium",
    recommendation: "Sequence the E–G units to the front of the renovation plan.",
    assumption: "EPBD MEPS timing is indicative — national transposition varies.",
    href: `/buildings/${encodeURIComponent(r.fabric_building_id)}/residential`,
    cta: "See units",
  }
}

// ----- public entry point ----------------------------------------------

const RANK: Record<InsightSeverity, number> = { action: 0, watch: 1, info: 2, good: 3 }

export function buildAdvisorInsights(input: {
  kpis: PortfolioBuildingRow | null
  topActions: ActionItem[]
  isResidential: boolean
  residential?: ResidentialBuildingResponse | null
  profile?: DeclaredProfile | null
  estimate?: EngineEstimate | null
  topAlerts?: AlertItem[]
}): Insight[] {
  const { kpis, topActions, isResidential, residential, profile, estimate } = input
  const topAlerts = input.topAlerts ?? []

  const raw: (Insight | null)[] = []

  if (isResidential && residential) {
    // Multi-family set: heating intensity, UVI compliance gap, EPC concentration,
    // plus the shared alerts + recommendations from the commercial KPI row.
    raw.push(heatingEuiInsight(residential))
    raw.push(uviInsight(residential))
    raw.push(epcMixInsight(residential))
    if (kpis) {
      raw.push(alertsInsight(kpis, topAlerts))
      raw.push(recsInsight(kpis, topActions))
    }
  } else if (kpis) {
    // Live Fabric data: full commercial set. EPC prefers the Fabric rating but
    // falls back to the declared profile; heating advice comes from the profile
    // (the Fabric KPI row doesn't carry the heating system).
    raw.push(euiInsight(kpis) ?? estimatedEuiInsight(estimate ?? null))
    raw.push(alertsInsight(kpis, topAlerts))
    raw.push(recsInsight(kpis, topActions))
    raw.push(epcInsight(kpis.epc_class ?? profile?.epc_class ?? null))
    raw.push(...assetInsights(kpis))
    if (profile) raw.push(heatingSystemInsight(profile))
  } else if (profile) {
    // Pre-Fabric-connection: advise from the declared profile alone so the panel
    // is useful from day one (EPC band + heating system).
    raw.push(epcInsight(profile.epc_class))
    raw.push(heatingSystemInsight(profile))
  }

  return raw
    .filter((x): x is Insight => x !== null)
    .sort((a, b) => RANK[a.severity] - RANK[b.severity])
    .slice(0, 6)
}

// ----- portfolio-level ranking -----------------------------------------

const SEV_WEIGHT: Record<InsightSeverity, number> = { action: 3, watch: 2, info: 0.3, good: 0 }

export type RankedBuilding = {
  building: PortfolioBuildingRow
  insights: Insight[]
  score: number
  top: Insight | null
  needsAttention: boolean
}

/**
 * Run the advisor across every building and rank by urgency (most critical
 * first). Per-building residential rollups aren't available at portfolio scope,
 * so insights use the commercial KPI row — the type-aware EUI bands still apply,
 * and the per-building page carries the full residential set.
 */
export function rankBuildingsByUrgency(buildings: PortfolioBuildingRow[]): RankedBuilding[] {
  return buildings
    .map((building) => {
      const insights = buildAdvisorInsights({ kpis: building, topActions: [], isResidential: false })
      const score = insights.reduce((s, i) => s + SEV_WEIGHT[i.severity], 0)
      const top = insights[0] ?? null
      const needsAttention = insights.some((i) => i.severity === "action" || i.severity === "watch")
      return { building, insights, score, top, needsAttention }
    })
    .sort((a, b) => b.score - a.score)
}
