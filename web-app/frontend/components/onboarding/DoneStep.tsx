"use client"

/**
 * Step 5 — success + what-happens-next.
 *
 * The building's metadata is saved, but its energy-data connection is pending
 * (fabric_building_id stays NULL until ingestion is live). The fastest value —
 * with NO hardware — is to upload a utility bill / meter CSV, which produces a
 * baseline (EUI, cost, carbon) + advisor immediately. So the primary next step
 * steers to the building's own page (where upload lives), not to empty
 * dashboards. The honest 3-step status reflects this hardware-free path.
 */
import Link from "next/link"
import { ArrowRight, CheckCircle2, Circle, Clock, FileUp } from "lucide-react"

function Step({
  state,
  label,
  sub,
}: {
  state: "done" | "active" | "todo"
  label: string
  sub: string
}) {
  const Icon = state === "done" ? CheckCircle2 : state === "active" ? Clock : Circle
  const iconColor =
    state === "done" ? "text-brand-emerald" : state === "active" ? "text-amber-300" : "text-text-faint"
  const labelColor = state === "todo" ? "text-text-muted" : "text-text-primary"
  return (
    <div className="flex items-start gap-2.5">
      <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${iconColor}`} aria-hidden />
      <div>
        <div className={`text-sm font-medium ${labelColor}`}>{label}</div>
        <div className="text-[11px] text-text-faint">{sub}</div>
      </div>
    </div>
  )
}

export function DoneStep({
  buildingName,
  buildingId,
  onAddAnother,
}: {
  buildingName: string
  buildingId?: string
  onAddAnother: () => void
}) {
  // Deep-link to the building's own page (where the no-hardware baseline upload
  // lives). Fall back to the buildings list if we somehow lack the id.
  const buildingHref = buildingId
    ? `/buildings/by-id/${encodeURIComponent(buildingId)}`
    : "/buildings"

  return (
    <div className="text-center">
      <div className="flex justify-center mb-4">
        <CheckCircle2 className="w-12 h-12 text-brand-emerald" />
      </div>
      <h2 className="text-xl font-bold text-text-primary mb-1 tracking-tight">
        {buildingName || "Your building"} is set up
      </h2>
      <p className="text-text-muted text-sm mb-5 max-w-sm mx-auto">
        No hardware needed to start: upload a utility bill or a meter CSV and your
        baseline KPIs (energy intensity, cost, carbon) + advisor appear right away.
        Connect live data later for real-time monitoring.
      </p>

      {/* What happens next — honest, hardware-free first step */}
      <div className="mx-auto mb-6 max-w-xs space-y-2.5 text-left">
        <Step state="done" label="Building added" sub="Details & systems saved" />
        <Step state="active" label="Add a baseline" sub="Upload a bill / CSV — no hardware" />
        <Step state="todo" label="KPIs go live" sub="Baseline analytics + advisor populate" />
      </div>

      <div className="mx-auto flex max-w-xs flex-col gap-2.5">
        <Link
          href={buildingHref}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-brand-emerald px-6 py-2.5 font-medium text-white shadow-[0_0_24px_rgba(29,158,117,0.2)] transition-colors hover:bg-brand-deep"
        >
          <FileUp className="h-4 w-4" aria-hidden />
          Add your baseline data
          <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
        <Link
          href="/demo"
          className="rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-6 py-2.5 font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
        >
          Preview with the live demo
        </Link>
        <button
          type="button"
          onClick={onAddAnother}
          className="rounded-md border border-border-subtle px-6 py-2.5 font-medium text-text-primary transition-colors hover:border-brand-emerald hover:text-brand-emerald"
        >
          Add another building
        </button>
      </div>
    </div>
  )
}
