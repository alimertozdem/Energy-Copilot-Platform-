/**
 * DataPendingBanner -- shown on /buildings and /portfolio when the user's own
 * buildings exist but none are connected to Fabric data yet
 * (fabric_building_id is NULL right after onboarding). Without it, those pages
 * look broken (empty cards / zero KPIs) for a freshly-onboarded customer.
 *
 * Honest copy: no spinner (the connection isn't auto-progressing). The status
 * row uses state markers, and a CTA steers the user to the live demo so they can
 * preview the dashboards while their own data is being connected.
 */
import Link from "next/link"
import { ArrowRight, CheckCircle2, Circle, Clock, Eye } from "lucide-react"

export function DataPendingBanner() {
  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Clock className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" aria-hidden />
          <div>
            <div className="text-sm font-medium text-text-primary">
              Connecting your energy data
            </div>
            <p className="mt-0.5 max-w-xl text-xs text-text-muted">
              Your buildings are set up. Reports and KPIs stay empty until a data source is
              connected — once ingestion is live, metrics populate here automatically.
            </p>
          </div>
        </div>
        <Link
          href="/demo"
          className="inline-flex shrink-0 items-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
        >
          <Eye className="h-4 w-4" aria-hidden />
          Preview with the live demo
          <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
      </div>

      {/* Honest status — state markers, not an auto-progressing spinner */}
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 pl-7 text-[11px]">
        <span className="inline-flex items-center gap-1.5 text-brand-emerald">
          <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> Building added
        </span>
        <span className="inline-flex items-center gap-1.5 text-amber-300">
          <Clock className="h-3.5 w-3.5" aria-hidden /> Connecting data source
        </span>
        <span className="inline-flex items-center gap-1.5 text-text-faint">
          <Circle className="h-3.5 w-3.5" aria-hidden /> KPIs go live
        </span>
      </div>
    </div>
  )
}
