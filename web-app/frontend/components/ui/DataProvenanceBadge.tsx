/**
 * DataProvenanceBadge — ONE consistent "where is this number from?" badge.
 *
 * Replaces the scattered ad-hoc indicators (solar's "Live telemetry", HVAC's
 * "From your data", the baseline card's "Estimated", etc.) with a single canonical
 * vocabulary + styling so the user always reads provenance the same way:
 *
 *   measured  — your real data (uploaded bills / live telemetry)
 *   estimated — model / archetype based (no metered data yet)
 *   sample    — demo placeholder (sample org)
 *   simulated — test feed, not a real device
 *   mixed     — a combination
 *
 * Pairs with the confidence legend (components/DataBasisNote = method confidence)
 * and the glossary; this badge is the per-figure DATA SOURCE, not method tier.
 */
import { cn } from "@/lib/utils"

export type DataBasis = "measured" | "estimated" | "sample" | "simulated" | "mixed" | "unknown"

const CFG: Record<DataBasis, { label: string; dot: string; cls: string }> = {
  measured: { label: "Measured", dot: "bg-brand-emerald", cls: "border-brand-emerald/30 bg-brand-emerald/5 text-brand-emerald" },
  estimated: { label: "Estimated", dot: "bg-amber-400", cls: "border-amber-400/30 bg-amber-400/5 text-amber-300" },
  sample: { label: "Sample", dot: "bg-slate-400", cls: "border-border-subtle bg-white/[0.03] text-text-muted" },
  simulated: { label: "Simulated", dot: "bg-sky-400", cls: "border-sky-400/30 bg-sky-400/5 text-sky-300" },
  mixed: { label: "Mixed", dot: "bg-amber-400", cls: "border-amber-400/30 bg-amber-400/5 text-amber-300" },
  unknown: { label: "Unknown", dot: "bg-slate-500", cls: "border-border-subtle bg-white/[0.02] text-text-faint" },
}

/** Standard "how to sharpen this" prompt for non-measured bases (null when measured). */
export function sharpenHint(basis: DataBasis): string | null {
  switch (basis) {
    case "estimated":
      return "Estimated from typical values — add a bill or live data to replace it with measured figures."
    case "sample":
      return "Sample data — add your own building to see real figures."
    case "simulated":
      return "Simulated test feed — connect a real device for live readings."
    default:
      return null
  }
}

export function DataProvenanceBadge({
  basis,
  detail,
  className,
}: {
  basis: DataBasis
  /** Optional suffix, e.g. "3 buildings" or "0.11 €/kWh". */
  detail?: string
  className?: string
}) {
  const c = CFG[basis] ?? CFG.unknown
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
        c.cls,
        className
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", c.dot)} aria-hidden />
      {c.label}
      {detail ? <span className="font-normal normal-case opacity-80">· {detail}</span> : null}
    </span>
  )
}
