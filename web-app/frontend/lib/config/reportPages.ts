/**
 * reportPages.ts -- manifest of the 9 embedded Power BI report pages.
 *
 * Single source of truth for:
 *   * the /buildings/[fabric_building_id]/reports/[page] deep-link routes
 *   * the ReportNav left sub-nav
 *   * route-level module gating (which pages are locked for a building)
 *
 * Each page maps to:
 *   * slug           : URL segment -> /buildings/B003/reports/<slug>
 *   * pbiDisplayName : the PBI page.displayName we navigate to via setActive()
 *                      -- MUST match the keys in lib/config/pageAccents.ts and
 *                      the tab display names configured in Power BI Desktop.
 *   * title          : human label for breadcrumb / nav / document title
 *   * requiredModule : which BuildingModule must be enabled to view this page.
 *                      'meters' is always-on (Pages 1-7). 'iot' gates Page 8,
 *                      'battery' gates Page 9. Mirrors building_modules in the
 *                      backend (app/db/models/building.py).
 *   * accent         : page accent hex, kept in sync with pageAccents.ts so the
 *                      nav highlight matches the embed chrome.
 *   * iconKey        : lucide icon name, resolved by ReportNav. Kept as a string
 *                      (not a component import) so this module stays free of
 *                      React/client imports and is safe to import from server
 *                      components for slug validation + title lookup.
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
}

/**
 * Ordered to match the PBI report's own tab order (Pages 1-9). The first
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
  },
  {
    slug: "building-detail",
    pbiDisplayName: "02_building_detail",
    title: "Building Detail",
    requiredModule: "meters",
    accent: "#06B6D4",
    iconKey: "Building2",
  },
  {
    slug: "anomalies",
    pbiDisplayName: "03_anomalies_alerts",
    title: "Anomalies & Alerts",
    requiredModule: "meters",
    accent: "#F97316",
    iconKey: "TriangleAlert",
  },
  {
    slug: "forecast",
    pbiDisplayName: "04_forecast_recommendations",
    title: "Forecast & Recommendations",
    requiredModule: "meters",
    accent: "#EAB308",
    iconKey: "TrendingUp",
  },
  {
    slug: "occupancy",
    pbiDisplayName: "05_occupancy_analysis",
    title: "Occupancy Analysis",
    requiredModule: "meters",
    accent: "#EAB308",
    iconKey: "Users",
  },
  {
    slug: "sustainability",
    pbiDisplayName: "06_sustainability_compliance",
    title: "Sustainability Compliance",
    requiredModule: "meters",
    accent: "#06B6D4",
    iconKey: "Leaf",
  },
  {
    slug: "hvac",
    pbiDisplayName: "07_HVAC",
    title: "HVAC Analysis",
    requiredModule: "meters",
    accent: "#5DCAA5",
    iconKey: "Wind",
  },
  {
    slug: "iot",
    pbiDisplayName: "08_IoT",
    title: "IoT Monitoring",
    requiredModule: "iot",
    accent: "#3B82F6",
    iconKey: "Radio",
  },
  {
    slug: "battery",
    pbiDisplayName: "09_Battery_Strategy",
    title: "Battery Strategy",
    requiredModule: "battery",
    accent: "#1D9E75",
    iconKey: "BatteryCharging",
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
 * 'meters' (Pages 1-7) is always available. 'iot' (Page 8) and 'battery'
 * (Page 9) only unlock once the customer connects the relevant system --
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
