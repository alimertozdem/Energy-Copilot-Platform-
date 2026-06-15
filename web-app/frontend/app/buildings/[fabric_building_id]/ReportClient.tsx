"use client"

/**
 * Client wrapper for PowerBIReport.
 *
 * Why this file exists:
 *   * Next.js 16 forbids `dynamic({ ssr: false })` inside server components.
 *   * powerbi-client-react touches `self` at module-load time, so we MUST
 *     keep it out of the server bundle.
 *   * Solution: a tiny "use client" wrapper that owns the dynamic import.
 *     The server-rendered page.tsx renders <ReportClient/> normally; the
 *     dynamic({ ssr: false }) call happens entirely on the client.
 *
 * The `onPageChanged` callback is forwarded through to PowerBIReport so the
 * outer shell can react to PBI tab navigation (title + accent update).
 */
import dynamic from "next/dynamic"

const PowerBIReport = dynamic(
  () => import("@/app/components/PowerBIReport"),
  {
    ssr: false,
    loading: () => (
      <div className="p-8 text-text-muted text-sm">
        Loading Power BI report…
      </div>
    ),
  }
)

type ReportClientProps = {
  buildingIds?: string[]
  onPageChanged?: (pageName: string) => void
  /** Pin the embed to a single PBI page (by displayName). Used by /reports/[page]. */
  pageName?: string
  /** Fallback: navigate by tab order/index when displayName does not match. */
  pageIndex?: number
  /** Hide PBI's own tab bar (per-page routes drive nav from ReportNav). */
  hidePageNav?: boolean
}

export function ReportClient({
  buildingIds,
  onPageChanged,
  pageName,
  pageIndex,
  hidePageNav,
}: ReportClientProps) {
  return (
    <PowerBIReport
      buildingIds={buildingIds}
      onPageChanged={onPageChanged}
      pageName={pageName}
      pageIndex={pageIndex}
      hidePageNav={hidePageNav}
    />
  )
}
