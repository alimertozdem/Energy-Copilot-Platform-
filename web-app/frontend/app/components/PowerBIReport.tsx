"use client"

/**
 * PowerBIReport -- embeds the workspace report inside its parent container.
 *
 * Sizing model: 100% of the parent. Callers (page-level layouts) decide the
 * outer dimensions -- e.g. /buildings/[id] wraps this in a `h-[calc(...)]`
 * element so the embed fills the area below AppChrome.
 *
 * Filtering:
 *   * If `buildingId` is passed, applies a basic filter on
 *     silver_building_master.building_id, so every page of the embedded
 *     report shows that building only. Without the prop, the report renders
 *     in its default unfiltered state.
 *
 * Page-change event:
 *   * `onPageChanged(pageName)` fires whenever the user navigates between
 *     the report's 9 tabs. Used by the surrounding shell to update the
 *     app-level chrome (title, accent color).
 *
 * Slicer state hygiene:
 *   * persistentFiltersEnabled: false  -> embed never carries over the
 *     last user's slicer selections from a previous session. Prevents the
 *     "Building Name slicer remembers B009 while you're viewing B003" bug.
 */
import { useEffect, useRef, useState } from "react"
import { PowerBIEmbed } from "powerbi-client-react"
import { models, type Report } from "powerbi-client"
import { RefreshCw } from "lucide-react"

/**
 * Power BI's SDK often throws/returns a PLAIN object (not an Error), so
 * `String(e)` yields the useless "[object Object]". Pull a readable message
 * from the usual fields, falling back to JSON.
 */
function describePbiError(e: unknown): string {
  if (e instanceof Error) return e.message
  if (e && typeof e === "object") {
    const o = e as Record<string, unknown>
    const parts = [o.message, o.detailedMessage, o.errorCode].filter(
      (v): v is string => typeof v === "string" && v.length > 0
    )
    if (parts.length) return parts.join(" — ")
    try {
      return JSON.stringify(e)
    } catch {
      return "unknown Power BI error"
    }
  }
  return String(e)
}

type EmbedConfig = {
  embed_token: string
  embed_url: string
  report_id: string
  expiration: string
}

type PowerBIReportProps = {
  /**
   * Fabric building_ids to scope the embed to (e.g. ["B003"] or
   * ["B001","B003","B005"] for compare view). When empty/undefined,
   * the report renders unfiltered (whole portfolio).
   */
  buildingIds?: string[]
  /** Fires when the active report page changes. Receives the page's display name. */
  onPageChanged?: (pageName: string) => void
  /**
   * When true, fetch the embed token from /demo/embed/token (public, no auth)
   * instead of /embed/token (the private endpoint). The demo token carries
   * RLS effectiveIdentity = "demo@energylens.eu" so the dataset enforces the
   * B001-B006 allowlist even if the frontend filter is tampered with.
   */
  useDemo?: boolean
  /**
   * When set, navigate the embed to the PBI page whose displayName matches
   * and keep it there. Used by the per-page report routes
   * (/buildings/[id]/reports/[page]). When undefined, the report opens on its
   * default page and the user navigates freely between all tabs.
   */
  pageName?: string
  /** Fallback page navigation by tab index when displayName does not match. */
  pageIndex?: number
  /**
   * Hide Power BI's own page-navigation tab bar. The per-page routes drive
   * navigation from the app's ReportNav instead, so the embed shows a single
   * page with no PBI tabs.
   */
  hidePageNav?: boolean
}

/**
 * Backend's gold/silver table where building_id lives. Confirmed in
 * semantic-model/scripts/page5_v55c_new_names.cs.
 */
const BUILDING_TABLE = "silver_building_master"
const BUILDING_COLUMN = "building_id"

/**
 * Demo-mode allowlist (defence-in-depth).
 *
 * Why hardcoded in the frontend, not just enforced by the backend?
 *   The backend /demo/embed/token endpoint already refuses non-demo building
 *   IDs. But the issued embed token itself is not RLS-bound (DirectLake
 *   doesn't support effectiveIdentity), so a tampered embedConfig.filters
 *   could in principle widen visibility past the 6 demo buildings. By also
 *   sweeping buildingIds against this list before passing them to PBI, the
 *   official frontend path stays restricted even under noisy callers.
 *
 *   Determined adversaries with dev-tools can still strip the filter
 *   entirely; the V1 risk acceptance is that demo data is public sample
 *   data, so exfiltration impact is nil. (See app/services/demo_data.py.)
 */
const DEMO_FABRIC_IDS: ReadonlySet<string> = new Set([
  "B001",
  "B002",
  "B003",
  "B004",
  "B005",
  "B006",
])

function makeBuildingFilter(buildingIds: string[]): models.IBasicFilter {
  return {
    $schema: "http://powerbi.com/product/schema#basic",
    target: {
      table: BUILDING_TABLE,
      column: BUILDING_COLUMN,
    },
    operator: "In",
    values: buildingIds,
    filterType: models.FilterType.Basic,
    // Allow multi-select when comparing buildings.
    requireSingleSelection: buildingIds.length === 1,
  }
}

/**
 * Clear any *building* slicer on the report's active page. The .pbix ships saved
 * slicer selections (e.g. "Frankfurt") that AND-conflict with our report-level
 * building filter (building_id IN [...]) -> empty intersection -> blank page.
 * Clearing the building slicer lets the report-level filter scope cleanly.
 * Best-effort: any failure leaves the report as-is (no regression).
 */
async function clearBuildingSlicers(report: Report): Promise<void> {
  try {
    const page = await report.getActivePage()
    if (!page) return
    const visuals = await page.getVisuals()
    await Promise.all(
      visuals
        .filter((v) => v.type === "slicer")
        .map(async (v) => {
          try {
            const state = await v.getSlicerState()
            const targets = (state?.targets ?? []) as Array<{
              column?: string
              hierarchy?: string
            }>
            const isBuilding = targets.some((t) =>
              (t?.column ?? t?.hierarchy ?? "").toLowerCase().includes("building")
            )
            if (isBuilding && state?.filters && state.filters.length > 0) {
              await v.setSlicerState({ filters: [] })
            }
          } catch {
            /* per-slicer best-effort */
          }
        })
    )
  } catch {
    /* page/visuals not ready -- skip */
  }
}

export default function PowerBIReport({
  buildingIds,
  onPageChanged,
  useDemo = false,
  pageName,
  pageIndex,
  hidePageNav = false,
}: PowerBIReportProps) {
  const [embedConfig, setEmbedConfig] = useState<EmbedConfig | null>(null)
  const [error, setError] = useState<string | null>(null)
  // Hold the embedded Report instance so we can call PBI APIs imperatively
  // (e.g. getActivePage() on first render -- PBI does NOT fire pageChanged
  // for the initial page; we have to read it ourselves).
  const reportRef = useRef<Report | null>(null)
  // Always-current page target so the (memoised) PBI "rendered" handler never
  // navigates to a STALE page -- the "click page 3 -> flips to another page"
  // glitch. The imperative effect below already reads the latest via deps.
  const pageNameRef = useRef(pageName)
  pageNameRef.current = pageName
  const pageIndexRef = useRef(pageIndex)
  pageIndexRef.current = pageIndex

  // Stable key for the building set. Depending on the raw `buildingIds` array
  // would re-run the token fetch (and thus FULLY re-embed the report → flicker)
  // on every parent re-render that passes a new array reference — which is what
  // happens when navigating between report pages. Keying on the content keeps
  // the embed mounted across page nav; only a real building-set change re-embeds.
  const buildingIdsKey = (buildingIds ?? []).join(",")

  useEffect(() => {
    // Demo mode uses the public, RLS-restricted /demo/embed/token endpoint.
    // It returns the same EmbedConfig shape, so the rest of this component
    // stays unchanged.
    const tokenUrl = useDemo
      ? "/api/demo/embed-token"
      : "/api/embed-token"

    const body =
      useDemo && buildingIds && buildingIds.length === 1
        ? JSON.stringify({ building_id: buildingIds[0] })
        : useDemo
        ? JSON.stringify({})
        : undefined

    fetch(tokenUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    })
      .then((res) => {
        if (!res.ok) throw new Error(`Backend error: ${res.status}`)
        return res.json()
      })
      .then((data: EmbedConfig) => setEmbedConfig(data))
      .catch((err) => setError(err.message))
    // buildingIdsKey (content) instead of buildingIds (reference) — see above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useDemo, buildingIdsKey])

  // Imperative page navigation. When the embed stays mounted across the
  // per-page report routes (the /reports layout persists it), a change to
  // pageName won't re-fire "rendered" -- so we drive setActive() directly off
  // reportRef. No-op until the report is embedded (getEmbeddedComponent sets
  // the ref) and when pageName is unset. The initial landing is handled by the
  // "rendered" handler below; this covers subsequent in-place nav.
  useEffect(() => {
    const report = reportRef.current
    if (!report || !pageName) return
    let cancelled = false
    void (async () => {
      try {
        const pages = await report.getPages()
        const target =
          pages.find((p) => p.displayName === pageName) ??
          (pageIndex != null ? pages[pageIndex] : undefined)
        if (!cancelled && target && !target.isActive) {
          await target.setActive()
        }
        if (!cancelled) await clearBuildingSlicers(report)
      } catch (e) {
        // Best-effort page nav — not fatal (the report still renders). warn,
        // not error, so it doesn't trip the dev error overlay.
        console.warn("[PowerBIReport] setActive skipped:", describePbiError(e))
      }
    })()
    return () => {
      cancelled = true
    }
  }, [pageName, embedConfig])

  if (error) {
    return (
      <div className="p-8 text-accent-red">
        <h3 className="font-semibold mb-1">Report failed to load</h3>
        <p className="text-sm text-text-muted">{error}</p>
      </div>
    )
  }

  if (!embedConfig) {
    return (
      <div className="p-8 text-text-muted text-sm">
        Loading Power BI report…
      </div>
    )
  }

  // In demo mode, sweep buildingIds through the hardcoded allowlist (see
  // DEMO_FABRIC_IDS above). Non-demo IDs silently dropped.
  const effectiveBuildingIds =
    useDemo && buildingIds
      ? buildingIds.filter((id) => DEMO_FABRIC_IDS.has(id))
      : buildingIds

  const filters =
    effectiveBuildingIds && effectiveBuildingIds.length > 0
      ? [makeBuildingFilter(effectiveBuildingIds)]
      : []

  return (
    <div className="relative w-full h-full">
      <PowerBIEmbed
        embedConfig={{
          type: "report",
          id: embedConfig.report_id,
          embedUrl: embedConfig.embed_url,
          accessToken: embedConfig.embed_token,
          tokenType: models.TokenType.Embed,
          // Force English PBI chrome (slicer "All", filter pane, dates) regardless
          // of the viewer's / SP's Turkish locale. Report-DESIGN text (measure
          // strings like "Boş"/"Hedef") is baked in the .pbix -> Desktop only.
          localeSettings: { language: "en-US", formatLocale: "en-US" },
          filters,
          settings: {
            panes: {
              filters: { expanded: false, visible: true },
              // Hidden on the per-page report routes -- the app's ReportNav
              // drives navigation there. Visible on the full-report views
              // (/buildings/[id], compare) where PBI's own tabs are wanted.
              pageNavigation: { visible: !hidePageNav },
            },
            // Default keeps the report's own page-background designs visible.
            // (The white edge-strips were the <html> canvas, fixed in globals.css,
            // not the PBI gutter — so no need for Transparent here.)
            background: models.BackgroundType.Default,
            layoutType: models.LayoutType.Custom,
            customLayout: {
              // FitToPage = no scroll, ever. Aspect ratio preserved. The
              // wrapper is aspect-locked to 16:9 so the PBI canvas fills
              // the box exactly; any remaining viewport space is owned by
              // the parent layout and painted with the page accent gradient.
              displayOption: models.DisplayOption.FitToPage,
            },
            // Never resurrect the previous viewer's slicer/filter state --
            // critical for our embed-time building filter to win cleanly.
            persistentFiltersEnabled: false,
            bookmarksPaneEnabled: false,
          },
        }}
        eventHandlers={
          new Map<string, (event?: { detail?: unknown }) => void>([
            ["loaded", () => console.log("[PowerBIReport] loaded")],
            [
              "rendered",
              async () => {
                // page.name is an internal GUID (e.g. "b9246889dce..."),
                // page.displayName is the tab name we set in Desktop
                // ("01_portfolio_overview"). We match + forward displayName.
                //
                // Never console.log the page/event object whole -- its
                // cross-origin Window references throw SecurityError in
                // Next.js's dev logger. Log only string fields.
                const report = reportRef.current
                if (!report) return
                try {
                  // If a specific page was requested, land on it before
                  // reporting state. Covers the initial embed; later in-place
                  // pageName changes are handled by the imperative effect.
                  const wantName = pageNameRef.current
                  const wantIndex = pageIndexRef.current
                  if (wantName) {
                    const pages = await report.getPages()
                    const target =
                      pages.find((p) => p.displayName === wantName) ??
                      (wantIndex != null ? pages[wantIndex] : undefined)
                    if (target && !target.isActive) {
                      await target.setActive()
                    }
                  }
                  if (onPageChanged) {
                    const page = await report.getActivePage()
                    const displayName = page?.displayName
                    if (displayName) onPageChanged(displayName)
                  }
                  await clearBuildingSlicers(report)
                } catch (e) {
                  // Landing on a specific page is a best-effort enhancement; if
                  // the report's pages aren't ready / renamed, the report still
                  // renders fine. warn (not error) keeps the dev overlay calm.
                  console.warn(
                    "[PowerBIReport] render-nav skipped:",
                    describePbiError(e)
                  )
                }
              },
            ],
            [
              "pageChanged",
              (event) => {
                const detail = event?.detail as
                  | { newPage?: { name?: string; displayName?: string } }
                  | undefined
                const displayName = detail?.newPage?.displayName
                if (displayName && onPageChanged) {
                  console.log("[PowerBIReport] page changed:", displayName)
                  onPageChanged(displayName)
                }
              },
            ],
            [
              "error",
              (event) => {
                // Same cross-origin caveat -- derive a readable string, never log
                // the raw event (its Window refs throw SecurityError in dev).
                console.error(
                  "[PowerBIReport] embed error:",
                  describePbiError(event?.detail)
                )
              },
            ],
          ])
        }
        cssClassName="report-style-class"
        getEmbeddedComponent={(embeddedReport) => {
          reportRef.current = embeddedReport as Report
          // Kept for backwards-compat with any console debugging.
          ;(window as unknown as { report: Report }).report =
            embeddedReport as Report
        }}
      />
      <button
        type="button"
        onClick={() => { void reportRef.current?.reload() }}
        title="Refresh — load the latest published report"
        aria-label="Refresh report"
        className="absolute top-2 right-2 z-20 inline-flex h-8 w-8 items-center justify-center rounded-md border border-border-subtle bg-bg-base/70 text-text-muted backdrop-blur-sm transition-colors hover:border-brand-emerald hover:text-brand-emerald"
      >
        <RefreshCw className="h-4 w-4" aria-hidden />
      </button>
    </div>
  )
}
