"use client"

/**
 * Report toolbar actions (screen-only — carries `.no-print`).
 *
 *  • Download PDF — primary. Calls /api/reports/pdf, which renders THIS report
 *    server-side with headless Chromium and streams back a true, vector,
 *    text-selectable A4 PDF (identical to screen). One click, no print dialog.
 *  • Print — fallback. Native print / "Save as PDF" if the server render ever
 *    fails (cold start, capacity paused, etc.).
 */
import { Download, Loader2, Printer } from "lucide-react"
import { useState } from "react"

export function PrintButton({ downloadName }: { downloadName?: string }) {
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)

  async function downloadPdf() {
    setBusy(true)
    setFailed(false)
    try {
      const path = window.location.pathname + window.location.search
      const cleanName =
        (downloadName || "EnergyLens-Report").replace(/[^a-zA-Z0-9 _.-]/g, "").trim() ||
        "EnergyLens-Report"
      const filename = cleanName.toLowerCase().endsWith(".pdf") ? cleanName : `${cleanName}.pdf`
      const res = await fetch(
        `/api/reports/pdf?path=${encodeURIComponent(path)}&filename=${encodeURIComponent(filename)}`,
      )
      if (!res.ok) throw new Error(`pdf ${res.status}`)
      const blob = await res.blob()
      const objectUrl = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = objectUrl
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(objectUrl)
    } catch {
      setFailed(true)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="no-print inline-flex items-center gap-2">
      {failed && (
        <span className="text-xs font-medium text-amber-700">
          PDF render failed — use Print
        </span>
      )}
      <button
        type="button"
        onClick={downloadPdf}
        disabled={busy}
        className="inline-flex items-center gap-2 rounded-md bg-brand-emerald px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep disabled:cursor-not-allowed disabled:opacity-60"
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
        ) : (
          <Download className="h-4 w-4" aria-hidden />
        )}
        {busy ? "Preparing PDF…" : "Download PDF"}
      </button>
      <button
        type="button"
        onClick={() => window.print()}
        className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
      >
        <Printer className="h-4 w-4" aria-hidden />
        Print
      </button>
    </div>
  )
}
