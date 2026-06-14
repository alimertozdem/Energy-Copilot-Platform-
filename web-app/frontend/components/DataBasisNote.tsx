/**
 * DataBasisNote — a visible "how to read these figures" trust strip (design audit P1-4, 2026-06-15).
 *
 * The app already has a strong honesty layer in lib/glossary.ts: every calculated
 * figure carries a method, assumptions, a measured/indicative/screening confidence,
 * and a sourceRef — but it only shows inside hover tooltips. This surfaces the same
 * confidence legend (reusing CONFIDENCE_NOTE, no new copy) in plain sight, where the
 * skeptical personas (auditor / consultant / investor) see the numbers. Reusable on
 * any data surface; links to /glossary for full methodology + sources.
 */
import Link from "next/link"
import { Info } from "lucide-react"

import { CONFIDENCE_NOTE } from "@/lib/glossary"

const TIERS: { key: keyof typeof CONFIDENCE_NOTE; label: string; dot: string }[] = [
  { key: "measured", label: "Measured", dot: "bg-brand-emerald" },
  { key: "indicative", label: "Indicative", dot: "bg-amber-400" },
  { key: "screening", label: "Screening", dot: "bg-purple-400" },
]

export function DataBasisNote() {
  return (
    <section
      aria-label="How to read these figures"
      className="rounded-xl border border-border-faint bg-bg-elevated/30 p-4"
    >
      <div className="flex items-start gap-2">
        <Info size={15} className="mt-0.5 shrink-0 text-text-muted" aria-hidden />
        <div className="min-w-0">
          <h3 className="text-xs font-semibold text-text-primary">How to read these figures</h3>
          <ul className="mt-1.5 space-y-1 text-[11px]">
            {TIERS.map((t) => (
              <li key={t.key} className="flex items-start gap-1.5 text-text-muted">
                <span className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${t.dot}`} aria-hidden />
                <span>
                  <span className="font-medium text-text-primary">{t.label}</span> — {CONFIDENCE_NOTE[t.key]}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[11px] text-text-faint">
            Every calculated figure carries its method, assumptions and source.{" "}
            <Link href="/glossary" className="text-brand-emerald hover:text-brand-mint">
              Methodology &amp; data sources →
            </Link>
          </p>
        </div>
      </div>
    </section>
  )
}
