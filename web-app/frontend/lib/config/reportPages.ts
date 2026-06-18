/**
 * reportPages.ts -- manifest of the 10 embedded Power BI report pages.
 *
 * Single source of truth for:
 *   * the /buildings/[fabric_building_id]/reports/[page] deep-link routes
 *   * the ReportNav left sub-nav
 *   * route-level module gating (which pages are locked for a building)
 *   * the ReportCompanion "how to read this" guidance (summary/reads/watch/act)
 *
 * Each page maps to:
 *   * slug           : URL segment -> /buildings/B003/reports/<slug>
 *   * pbiDisplayName : the PBI page.displayName we navigate to via setActive()
 *                      -- MUST match the keys in lib/config/pageAccents.ts and
 *                      the tab display names configured in Power BI Desktop.
 *   * title          : human label for breadcrumb / nav / document title
 *   * requiredModule : which BuildingModule must be enabled to view this page.
 *                      'meters' is always-on (Pages 1-7). 'iot' gates Page 8,
 *                      'battery' gates Page 9, 'solar' gates Page 10. Mirrors building_modules in the
 *                      backend (app/db/models/building.py).
 *   * accent         : page accent hex, kept in sync with pageAccents.ts so the
 *                      nav highlight matches the embed chrome.
 *   * iconKey        : lucide icon name, resolved by ReportNav. Kept as a string
 *                      (not a component import) so this module stays free of
 *                      React/client imports and is safe to import from server
 *                      components for slug validation + title lookup.
 *   * summary/reads/watch/act : ReportCompanion content (plain-language guide).
 *
 * Energy thresholds quoted in `reads` are screening-grade and were product-owner
 * approved (2026-06-18): EUI = GEG Anlage 10 bands (residential basis, approximate
 * for commercial); base-load <30/30-50/>50%; payback <3/3-7/>7 yr; spike >120%
 * baseline; DE grid 0.363 location / 0.725 residual; MEPS EPC G 2030 / F 2033;
 * HVAC heating ΔT 10-20 K / cooling 5-7 K, COP/JAZ ~3.0 floor; CO2 800/1500 ppm;
 * comfort 20-24 C; PV PR 0.75-0.85 (>1 = data error), DE yield 900-1050 kWh/kWp.
 *
 * Pure data on purpose -- no React / lucide imports here.
 */
import type { Building, ModuleKey } from "@/lib/api/buildings"

export type ReportPageMeta = {
  slug: string
  pbiDisplayName: string
  title: string
  requiredModule: ModuleKey
  accent: string
  iconKey: string
  /** Plain-language: what this page shows (report companion). */
  summary: string
  /** The single thing to look at first on this page (report companion). */
  watch: string
  /** Per-visual guide: each key chart on the page -> what it tells you. */
  reads: { v: string; m: string }[]
  /** Where the page leads -- a deep link. {id} -> building.fabric_building_id. */
  act?: { label: string; href: string }
}

/**
 * Ordered to match the PBI report's own tab order (Pages 1-10). The first
 * entry is the default landing page for a building's report section.
 */
export const REPORT_PAGES: ReportPageMeta[] = [
  {
    slug: "portfolio-overview",
    pbiDisplayName: "01_portfolio_overview",
    title: "Portfolio Overview",
    requiredModule: "meters",
    accent: "#1D9E75",
    iconKey: "LayoutGrid",
    summary: "Your whole portfolio at a glance — total energy, cost and CO₂, and how buildings rank against each other.",
    watch: "The worst-ranked buildings — that is where most of the savings sit.",
    reads: [
      { v: "EUI benchmark by building", m: "Energy per m²·yr vs the portfolio median. Bars to the right are your least efficient — and your biggest savings." },
      { v: "Consumption trend (current vs PY)", m: "Year-over-year direction. Rising while floor area is flat means creeping waste." },
      { v: "Cost & CO₂ totals", m: "The portfolio's exposure. CO₂ drives CRREM/EPC risk even where the bill still looks fine." },
      { v: "Building summary table", m: "Per-building EUI, cost and class — triage where to spend attention first." },
    ],
    act: { label: "See portfolio compliance", href: "/compliance" },
  },
  {
    slug: "building-detail",
    pbiDisplayName: "02_building_detail",
    title: "Building Detail",
    requiredModule: "meters",
    accent: "#06B6D4",
    iconKey: "Building2",
    summary: "This building's energy, cost and carbon over time, plus the core efficiency metrics that say whether it's run well.",
    watch: "Actual demand vs the baseline line — the gap above baseline is avoidable spend.",
    reads: [
      { v: "EUI gauge", m: "Energy per m²·yr vs typical bands — the headline 'is this efficient?' number. Fair/Poor = retrofit candidate (commercial bands are approximate)." },
      { v: "Consumption vs outdoor temperature", m: "How weather-driven the building is. Steep slope = heating/cooling dominates (envelope + HVAC levers); flat = plug/process loads." },
      { v: "Daily load profile (24h)", m: "When you peak. A high overnight floor is always-on base load you can often trim with scheduling." },
      { v: "Base load ratio", m: "Share used when effectively empty. Indicative: <30% lean · 30–50% typical · >50% investigate (higher for refrigerated/logistics)." },
      { v: "HDD / CDD vs consumption", m: "Sensitivity to heating- vs cooling-degree-days. Tight cluster = predictable; points above the trend = possible anomalies." },
    ],
    act: { label: "See recommended measures", href: "/buildings/{id}/reports/forecast" },
  },
  {
    slug: "anomalies",
    pbiDisplayName: "03_anomalies_alerts",
    title: "Anomalies & Alerts",
    requiredModule: "meters",
    accent: "#F97316",
    iconKey: "TriangleAlert",
    summary: "Detected irregularities — spikes, drifts and faults that usually mean wasted energy.",
    watch: "Critical and high anomalies first; each unresolved one is live, costed waste.",
    reads: [
      { v: "Anomaly list by severity", m: "Critical/high first — each is live, costed waste until it's cleared." },
      { v: "Spike vs baseline", m: "Demand above ~120% of baseline flags an event worth a look — a control fault or manual override." },
      { v: "Drift over time", m: "A slow upward creep means degrading equipment or loosened setpoints, not a one-off." },
      { v: "Estimated € impact", m: "Rough cost of each unresolved anomaly — use it to prioritise; treat as 'Est.'." },
    ],
    act: { label: "Open the alerts queue", href: "/alerts" },
  },
  {
    slug: "forecast",
    pbiDisplayName: "04_forecast_recommendations",
    title: "Forecast & Recommendations",
    requiredModule: "meters",
    accent: "#EAB308",
    iconKey: "TrendingUp",
    summary: "Where energy and cost are heading, plus the recommended measures to bend the curve.",
    watch: "The measures ranked by saving vs payback — start at the top.",
    reads: [
      { v: "Consumption / cost forecast", m: "Where you're heading on current behaviour — the 'do nothing' line to beat." },
      { v: "Measures ranked by saving vs payback", m: "Start at the top. Indicative payback: <3 yr quick win · 3–7 yr standard · >7 yr strategic." },
      { v: "Saving potential per measure", m: "Estimated annual €/kWh/CO₂ — screening-grade; confirm with an audit before capex." },
    ],
    act: { label: "Cost it with subsidies (Financing)", href: "/financing" },
  },
  {
    slug: "occupancy",
    pbiDisplayName: "05_occupancy_analysis",
    title: "Occupancy Analysis",
    requiredModule: "meters",
    accent: "#EAB308",
    iconKey: "Users",
    summary: "How occupancy drives energy use — base (empty) load vs occupied load.",
    watch: "High load when the building is empty — a scheduling / controls opportunity.",
    reads: [
      { v: "Base (empty) vs occupied load", m: "What runs when nobody's in. A high empty load (>~50% of peak) is the cheapest fix — scheduling, not capex." },
      { v: "Load vs occupancy hours", m: "If consumption doesn't fall after hours, timers/controls are the lever." },
      { v: "Weekday / weekend pattern", m: "Weekend use near weekday levels = always-on equipment left running." },
    ],
    act: { label: "Check HVAC scheduling", href: "/buildings/{id}/reports/hvac" },
  },
  {
    slug: "sustainability",
    pbiDisplayName: "06_sustainability_compliance",
    title: "Sustainability Compliance",
    requiredModule: "meters",
    accent: "#06B6D4",
    iconKey: "Leaf",
    summary: "This building's carbon footprint and where it stands against the EU compliance lines.",
    watch: "The Scope 1/2 split and the EPC / MEPS position.",
    reads: [
      { v: "Scope 1 / 2 split", m: "Scope 1 = on-site combustion (gas/oil), Scope 2 = purchased electricity. The split says whether to electrify or green the supply." },
      { v: "Carbon intensity (kgCO₂/m²·yr)", m: "Against the CRREM decarbonisation line — the year you cross it is the building's 'stranding' year." },
      { v: "EPC / MEPS position", m: "EPC F/G/H = EU renovation watch (worst 15% / EPC G by 2030, EPC F by 2033)." },
      { v: "Grid factor used", m: "DE location-based ~0.363 vs residual-mix ~0.725 kgCO₂/kWh — the choice moves Scope 2 a lot." },
    ],
    act: { label: "Full compliance view", href: "/compliance" },
  },
  {
    slug: "hvac",
    pbiDisplayName: "07_HVAC",
    title: "HVAC Analysis",
    requiredModule: "meters",
    accent: "#5DCAA5",
    iconKey: "Wind",
    summary: "Heating, cooling and ventilation performance — usually the single biggest consumer.",
    watch: "Supply–return ΔT and runtime vs occupancy — over-conditioning is common.",
    reads: [
      { v: "Supply–return ΔT", m: "Heating design ~10–20 K, cooling ~5–7 K. A collapsed ΔT = low-ΔT syndrome (over-pumping, poor heat transfer)." },
      { v: "Runtime vs occupancy", m: "Conditioning outside occupied hours is the most common, cheapest waste to cut." },
      { v: "Heat pump COP / JAZ", m: "~3.0 is a floor; 3.5–4.5 air-source / 4–5 ground-source is healthy. Low in the cold = sizing or defrost issue." },
      { v: "Setpoint deviation", m: "Each °C of over-conditioning ≈ 2–5 kW extra here — small setpoint changes pay back fast." },
    ],
    act: { label: "Cost a HVAC retrofit", href: "/financing" },
  },
  {
    slug: "iot",
    pbiDisplayName: "08_IoT",
    title: "IoT Monitoring",
    requiredModule: "iot",
    accent: "#3B82F6",
    iconKey: "Radio",
    summary: "Live sensor readings — real-time power, comfort and air quality.",
    watch: "Zones outside the comfort band, and any sensors that have gone quiet.",
    reads: [
      { v: "Live power (building + HVAC)", m: "Real-time kW vs baseline — green/amber/red. A sustained red is money leaking right now." },
      { v: "CO₂ by zone", m: "<800 ppm good · 800–1500 fair · >1500 poor (under-ventilation or over-occupancy)." },
      { v: "Comfort band", m: "~20–24 °C occupied. Zones outside this = comfort complaints and usually over-conditioning." },
      { v: "Sensor uptime", m: "A sensor gone quiet is a blind spot — reconnect before trusting that zone's numbers." },
    ],
    act: { label: "Open the alerts queue", href: "/alerts" },
  },
  {
    slug: "battery",
    pbiDisplayName: "09_Battery_Strategy",
    title: "Battery Strategy",
    requiredModule: "battery",
    accent: "#1D9E75",
    iconKey: "BatteryCharging",
    summary: "Battery dispatch economics — charge/discharge against tariff and solar.",
    watch: "Payback and self-consumption — the sizing has to match the load profile.",
    reads: [
      { v: "Charge/discharge vs tariff", m: "Charges off-peak / on solar surplus, discharges at peak. Hugging the price curve = good dispatch." },
      { v: "Self-consumption", m: "Share of solar kept on-site. Most battery value comes from raising this, not arbitrage alone." },
      { v: "State-of-charge trend", m: "Healthy cycling between bounds; flat or idle = oversized or mis-scheduled." },
      { v: "Payback", m: "Tariff- and self-consumption-dependent — treat the figure as indicative, not a quote." },
    ],
    act: { label: "See solar performance", href: "/buildings/{id}/reports/solar" },
  },
  {
    slug: "solar",
    pbiDisplayName: "10_Solar",
    title: "Solar Performance",
    requiredModule: "solar",
    accent: "#F59E0B",
    iconKey: "Sun",
    summary: "On-site PV generation, self-consumption and export.",
    watch: "Performance ratio and self-consumption — a low PR points to a fault.",
    reads: [
      { v: "Performance ratio (PR)", m: "Healthy 0.75–0.85. <0.70 = a fault (shading, soiling, inverter). >1.0 = a sensor/data error, not real output." },
      { v: "Self-consumption vs export", m: "On-site use is worth more than export — lots of export hints a battery or load-shift could pay." },
      { v: "Specific yield (kWh/kWp·yr)", m: "DE ~900–1,050 typical. Well below = orientation, shading or underperformance." },
      { v: "Generation vs irradiance", m: "Output should track sunlight; a gap on bright days is a problem to chase." },
    ],
    act: { label: "Check battery fit", href: "/buildings/{id}/reports/battery" },
  },
]

export const REPORT_PAGES_BY_SLUG: Record<string, ReportPageMeta> =
  Object.fromEntries(REPORT_PAGES.map((p) => [p.slug, p]))

/** Resolve a page by its URL slug. Returns undefined for unknown slugs. */
export function getReportPage(slug: string): ReportPageMeta | undefined {
  return REPORT_PAGES_BY_SLUG[slug]
}

/** The default report page a building's /reports section lands on. */
export const DEFAULT_REPORT_SLUG = REPORT_PAGES[0].slug

/**
 * A page is locked when its required module is not 'meters' and the building
 * does not have that module enabled.
 *
 * 'meters' (Pages 1-7) is always available. 'iot' (Page 8), 'battery' (Page 9) and 'solar'
 * (Page 10) only unlock once the customer connects the relevant system --
 * recorded as an enabled BuildingModule (onboarding wizard / admin). This is
 * the web-app "module layer" of the 3-layer access model; Power BI RLS does
 * not enforce page visibility.
 */
export function isPageLocked(
  building: Pick<Building, "modules">,
  page: ReportPageMeta
): boolean {
  if (page.requiredModule === "meters") return false
  return !building.modules.some(
    (m) => m.module_key === page.requiredModule && m.enabled
  )
}
