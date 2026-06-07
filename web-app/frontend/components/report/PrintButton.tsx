"use client"

/**
 * PrintButton — opens the browser's native print / "Save as PDF" dialog.
 *
 * Client component (needs window). Carries `.no-print` so the button itself
 * never shows up in the exported PDF.
 */
import { Printer } from "lucide-react"

export function PrintButton() {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="no-print inline-flex items-center gap-2 rounded-md bg-brand-emerald px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep"
    >
      <Printer className="h-4 w-4" aria-hidden />
      Print / Save as PDF
    </button>
  )
}
