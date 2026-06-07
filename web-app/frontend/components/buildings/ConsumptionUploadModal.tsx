"use client"

/**
 * ConsumptionUploadModal — upload a building's monthly consumption (CSV / PDF bill).
 *
 * Self-contained: pick a building, drop a CSV or a digital PDF bill, preview the
 * parsed months, then POST. Addresses buildings by their Postgres UUID, so it
 * works for buildings still pending a Fabric bridge (the common case right after
 * onboarding). CSV is parsed in the browser; a PDF bill is sent to the backend
 * for best-effort extraction (digital PDFs only) and the rows are shown for
 * review before saving — nothing is stored until you upload.
 */
import { useState } from "react"
import { CheckCircle2, FileSpreadsheet, Upload, X } from "lucide-react"

import type { Building } from "@/lib/api/buildings"
import {
  type ConsumptionRow,
  type ConsumptionSummary,
  parseBillPdf,
  parseConsumptionCsv,
  uploadConsumption,
} from "@/lib/api/consumption"

function fmt(n: number): string {
  return Math.round(n).toLocaleString("en-US")
}

/** Read a File as base64 (without the data: URL prefix). */
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const s = String(reader.result)
      resolve(s.slice(s.indexOf(",") + 1))
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

export function ConsumptionUploadModal({
  buildings,
  onClose,
  onUploaded,
}: {
  buildings: Building[]
  onClose: () => void
  /** Called after a successful upload (e.g. to refresh the page's server data). */
  onUploaded?: () => void
}) {
  const own = buildings.filter((b) => !b.is_sample_org)
  const [buildingId, setBuildingId] = useState(own[0]?.id ?? "")
  const [rows, setRows] = useState<ConsumptionRow[]>([])
  const [parseErrors, setParseErrors] = useState<string[]>([])
  const [fileName, setFileName] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [source, setSource] = useState("csv")
  const [summary, setSummary] = useState<ConsumptionSummary | null>(null)

  async function onFile(file: File) {
    setError(null)
    setSummary(null)
    setNotice(null)
    setFileName(file.name)
    setRows([])
    setParseErrors([])

    const isPdf = /\.pdf$/i.test(file.name) || file.type === "application/pdf"
    if (isPdf) {
      if (!buildingId) {
        setError("Pick a building first.")
        return
      }
      setParsing(true)
      try {
        const b64 = await fileToBase64(file)
        const res = await parseBillPdf(buildingId, b64)
        if (!res.ok) {
          setError(res.error)
          return
        }
        setRows(res.data.rows)
        setSource("bill")
        setNotice(res.data.warnings[0] ?? null)
      } finally {
        setParsing(false)
      }
      return
    }

    const text = await file.text()
    const parsed = parseConsumptionCsv(text)
    setRows(parsed.rows)
    setParseErrors(parsed.errors)
    setSource("csv")
  }

  async function handleUpload() {
    if (!buildingId || rows.length === 0) return
    setUploading(true)
    setError(null)
    const res = await uploadConsumption(buildingId, rows, source)
    setUploading(false)
    if (!res.ok) {
      setError(res.error)
      return
    }
    setSummary(res.data)
    // Refresh the page's server data so baseline KPIs + bridge readiness update
    // behind the still-open success card (Next preserves this modal's state).
    onUploaded?.()
  }

  const totalKwh = rows.reduce((s, r) => s + r.energy_kwh, 0)
  const inputCls =
    "w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent"

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div className="relative z-10 w-full max-w-lg rounded-2xl border border-border-subtle bg-bg-elevated p-6 shadow-[0_20px_60px_rgba(0,0,0,0.5)]">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 text-text-faint transition-colors hover:text-text-primary"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-brand-emerald/15 ring-1 ring-brand-emerald/30">
            <Upload className="h-4 w-4 text-brand-emerald" aria-hidden />
          </span>
          <h2 className="font-display text-lg font-semibold text-text-primary">Upload consumption data</h2>
        </div>

        {summary ? (
          <div className="mt-5">
            <div className="flex items-start gap-2.5 rounded-xl border border-brand-emerald/30 bg-brand-emerald/5 p-4">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand-emerald" aria-hidden />
              <div className="text-sm text-text-primary">
                Imported <span className="font-semibold">{summary.months}</span> month
                {summary.months === 1 ? "" : "s"} · {fmt(summary.total_kwh)} kWh
                {summary.period_start && (
                  <div className="mt-1 text-xs text-text-muted">
                    {summary.period_start} → {summary.period_end}
                    {summary.avg_monthly_kwh != null && ` · ~${fmt(summary.avg_monthly_kwh)} kWh/mo avg`}
                  </div>
                )}
              </div>
            </div>
            <p className="mt-3 text-xs text-text-faint">
              Saved as this building&rsquo;s baseline. Baseline KPIs (EUI, energy, carbon, cost) light
              up the dashboard + advisor for this building.
            </p>
            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={onClose}
                className="rounded-md bg-brand-emerald px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <>
            <p className="mt-2 text-xs text-text-muted">
              A CSV with monthly rows (date/period, kWh, optional cost) — or a digital PDF utility
              bill, which we read on a best-effort basis. Review the rows before saving.
            </p>

            <div className="mt-4 space-y-3">
              {own.length === 1 ? (
                // Scoped to a single building (e.g. opened from a building's
                // detail page) — show it statically instead of a 1-option select.
                <div>
                  <label className="mb-1.5 block text-sm text-text-muted">Building</label>
                  <div className={`${inputCls} flex items-center justify-between`}>
                    <span className="text-text-primary">{own[0].name}</span>
                    <span className="text-xs text-text-faint">
                      {own[0].fabric_building_id ? own[0].fabric_building_id : "pending"}
                    </span>
                  </div>
                </div>
              ) : (
                <div>
                  <label htmlFor="cu-building" className="mb-1.5 block text-sm text-text-muted">
                    Building
                  </label>
                  <select
                    id="cu-building"
                    value={buildingId}
                    onChange={(e) => setBuildingId(e.target.value)}
                    className={inputCls}
                  >
                    {own.length === 0 && <option value="">No buildings</option>}
                    {own.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name}
                        {b.fabric_building_id ? ` (${b.fabric_building_id})` : " (pending)"}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-sm text-text-muted">CSV or PDF file</label>
                <label
                  htmlFor="cu-file"
                  className="flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-border-faint bg-white/[0.02] px-4 py-5 text-sm text-text-muted transition-colors hover:border-brand-emerald/50"
                >
                  <FileSpreadsheet className="h-5 w-5 shrink-0 text-brand-emerald" aria-hidden />
                  <span>{fileName ? fileName : "Choose a .csv or .pdf file…"}</span>
                </label>
                <input
                  id="cu-file"
                  type="file"
                  accept=".csv,.txt,.pdf,text/csv,application/pdf"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    if (f) void onFile(f)
                  }}
                />
              </div>

              {parsing && (
                <div className="rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2 text-xs text-text-muted">
                  Reading the PDF…
                </div>
              )}

              {fileName && !parsing && (
                <div className="rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2 text-xs">
                  {rows.length > 0 ? (
                    <>
                      <span className="text-text-primary">
                        {rows.length} month{rows.length === 1 ? "" : "s"} · {fmt(totalKwh)} kWh ready
                      </span>
                      {parseErrors.length > 0 && (
                        <span className="ml-1.5 text-text-faint">
                          ({parseErrors.length} row{parseErrors.length === 1 ? "" : "s"} skipped)
                        </span>
                      )}
                    </>
                  ) : (
                    // Surface the concrete reason (e.g. which columns were detected)
                    // instead of a generic warning, so the user can fix the file.
                    <span className="text-amber-300">
                      {parseErrors[0] ?? "No readable rows — check the file."}
                    </span>
                  )}
                </div>
              )}

              {notice && (
                <div className="rounded-lg border border-amber-400/30 bg-amber-400/5 px-3 py-2 text-xs text-amber-200">
                  {notice}
                </div>
              )}

              {error && (
                <div className="rounded-lg border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200">
                  {error}
                </div>
              )}
            </div>

            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-text-muted transition-colors hover:text-text-primary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleUpload}
                disabled={!buildingId || rows.length === 0 || uploading || parsing}
                className="rounded-md bg-brand-emerald px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep disabled:opacity-50"
              >
                {uploading ? "Uploading…" : `Upload ${rows.length || ""} ${rows.length === 1 ? "month" : "months"}`.trim()}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
