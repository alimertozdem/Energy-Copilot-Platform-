"use client"

/**
 * ImportClient — CSV portfolio import: choose/paste → preview + fix → commit.
 *
 * Parsing happens in the browser (lib/api/buildingsBulk) so the user sees exactly
 * what will be created before anything is written. Rows without a name are
 * auto-excluded; soft issues (unknown type, bad country code) are surfaced inline
 * and the offending value is blanked rather than rejected. Commit goes through
 * the /api/buildings/bulk proxy; the result lists per-row outcomes.
 */
import { useMemo, useRef, useState } from "react"
import Link from "next/link"
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  Loader2,
  Upload,
} from "lucide-react"

import {
  type BulkBuildingRow,
  type BulkImportResponse,
  type ParseResult,
  importBuildings,
  parseBuildingsCsv,
  templateCsv,
} from "@/lib/api/buildingsBulk"

const MAX_ROWS = 200

export function ImportClient() {
  const [parsed, setParsed] = useState<ParseResult | null>(null)
  const [excluded, setExcluded] = useState<Set<number>>(new Set())
  const [fileName, setFileName] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<BulkImportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  function ingest(text: string, name: string) {
    setParsed(parseBuildingsCsv(text))
    setExcluded(new Set())
    setResult(null)
    setError(null)
    setFileName(name)
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    ingest(await file.text(), file.name)
  }

  function downloadTemplate() {
    const blob = new Blob([templateCsv()], { type: "text/csv;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "energylens-buildings-template.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  const valid = useMemo(
    () => (parsed?.rows ?? []).filter((r) => r.valid),
    [parsed]
  )
  const included = useMemo(
    () => valid.filter((r) => !excluded.has(r.line)),
    [valid, excluded]
  )
  const skipped = (parsed?.rows.length ?? 0) - valid.length
  const overCap = included.length > MAX_ROWS

  function toggle(line: number) {
    setExcluded((prev) => {
      const next = new Set(prev)
      if (next.has(line)) next.delete(line)
      else next.add(line)
      return next
    })
  }

  async function onImport() {
    if (included.length === 0) return
    setSubmitting(true)
    setError(null)
    const payload: BulkBuildingRow[] = included.slice(0, MAX_ROWS).map((r) => ({
      name: r.name,
      building_type: r.building_type,
      city: r.city,
      country_code: r.country_code,
      floor_area_m2: r.floor_area_m2,
      construction_year: r.construction_year,
      epc_class: r.epc_class,
      heating_system: r.heating_system,
    }))
    const res = await importBuildings(payload)
    setSubmitting(false)
    if (!res.ok) {
      setError(res.error)
      return
    }
    setResult(res.data)
  }

  // --- result view ---------------------------------------------------------
  if (result) {
    const failedRows = result.results.filter((r) => !r.ok)
    return (
      <div className="space-y-5">
        <div className="rounded-xl border border-brand-emerald/30 bg-brand-emerald/[0.05] p-5">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="h-6 w-6 text-brand-emerald" aria-hidden />
            <div>
              <div className="text-sm font-semibold text-text-primary">
                {result.created} building{result.created === 1 ? "" : "s"} imported
                {result.failed > 0 ? `, ${result.failed} failed` : ""}
              </div>
              <div className="text-xs text-text-muted">
                Each building starts with no data — add a baseline or connect a live source next.
              </div>
            </div>
          </div>
        </div>

        {failedRows.length > 0 && (
          <div className="rounded-lg border border-amber-400/30 bg-amber-400/5 p-4">
            <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-amber-200">
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden /> Rows that didn’t import
            </div>
            <ul className="space-y-1 text-xs text-text-muted">
              {failedRows.map((r) => (
                <li key={r.index}>
                  <span className="text-text-primary">{r.name || `Row ${r.index + 1}`}</span> — {r.error}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap gap-2.5">
          <Link
            href="/buildings"
            className="inline-flex items-center gap-2 rounded-md bg-brand-emerald px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-deep"
          >
            View buildings <ArrowRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
          <button
            type="button"
            onClick={() => {
              setParsed(null)
              setResult(null)
              setFileName("")
              if (fileRef.current) fileRef.current.value = ""
            }}
            className="rounded-md border border-border-subtle px-5 py-2.5 text-sm text-text-muted transition-colors hover:border-brand-emerald/60 hover:text-brand-emerald"
          >
            Import another file
          </button>
        </div>
      </div>
    )
  }

  // --- intake + preview ----------------------------------------------------
  return (
    <div className="space-y-5">
      <p className="text-sm text-text-muted">
        Managing a portfolio? Upload a CSV to create many buildings at once. The
        only required column is <code className="text-text-primary">name</code>;
        everything else (type, city, country, area, year, EPC, heating) is optional
        and sharpens each building’s Data Score.
      </p>

      <div className="flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="inline-flex items-center gap-2 rounded-md bg-brand-emerald px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep"
        >
          <Upload className="h-4 w-4" aria-hidden /> Choose CSV file
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".csv,.txt,text/csv"
          onChange={onFile}
          className="hidden"
        />
        <button
          type="button"
          onClick={downloadTemplate}
          className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-4 py-2 text-sm text-text-muted transition-colors hover:border-brand-emerald/60 hover:text-brand-emerald"
        >
          <Download className="h-4 w-4" aria-hidden /> Download template
        </button>
        {fileName && <span className="text-xs text-text-faint">{fileName}</span>}
      </div>

      {parsed?.headerError && (
        <div className="rounded-lg border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200">
          {parsed.headerError}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      {parsed && !parsed.headerError && parsed.rows.length > 0 && (
        <>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
            <span className="text-brand-emerald">{included.length} to import</span>
            {skipped > 0 && <span className="text-amber-300">{skipped} skipped (no name)</span>}
            {valid.length - included.length > 0 && (
              <span className="text-text-faint">{valid.length - included.length} excluded</span>
            )}
            {overCap && (
              <span className="text-amber-300">
                only the first {MAX_ROWS} will import — split the file for more
              </span>
            )}
          </div>

          <div className="overflow-x-auto rounded-lg border border-border-subtle">
            <table className="w-full text-xs">
              <thead className="text-left text-text-faint">
                <tr className="border-b border-border-subtle">
                  <th className="px-2 py-2 font-medium"> </th>
                  <th className="px-2 py-2 font-medium">Name</th>
                  <th className="px-2 py-2 font-medium">Type</th>
                  <th className="px-2 py-2 font-medium">City</th>
                  <th className="px-2 py-2 font-medium">Country</th>
                  <th className="px-2 py-2 font-medium">Area m²</th>
                  <th className="px-2 py-2 font-medium">Year</th>
                  <th className="px-2 py-2 font-medium">EPC</th>
                  <th className="px-2 py-2 font-medium">Notes</th>
                </tr>
              </thead>
              <tbody>
                {parsed.rows.map((r) => {
                  const isIncluded = r.valid && !excluded.has(r.line)
                  return (
                    <tr
                      key={r.line}
                      className={`border-b border-border-subtle/50 ${
                        r.valid ? "" : "opacity-50"
                      }`}
                    >
                      <td className="px-2 py-1.5">
                        <input
                          type="checkbox"
                          checked={isIncluded}
                          disabled={!r.valid}
                          onChange={() => toggle(r.line)}
                          aria-label={`Include ${r.name || "row " + r.line}`}
                          className="accent-brand-emerald"
                        />
                      </td>
                      <td className="px-2 py-1.5 text-text-primary">{r.name || "—"}</td>
                      <td className="px-2 py-1.5 text-text-muted">{r.building_type ?? ""}</td>
                      <td className="px-2 py-1.5 text-text-muted">{r.city ?? ""}</td>
                      <td className="px-2 py-1.5 text-text-muted">{r.country_code ?? ""}</td>
                      <td className="px-2 py-1.5 text-text-muted">{r.floor_area_m2 ?? ""}</td>
                      <td className="px-2 py-1.5 text-text-muted">{r.construction_year ?? ""}</td>
                      <td className="px-2 py-1.5 text-text-muted">{r.epc_class ?? ""}</td>
                      <td className="px-2 py-1.5 text-text-faint">
                        {r.issues.length > 0 ? r.issues.join("; ") : ""}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <button
            type="button"
            onClick={onImport}
            disabled={submitting || included.length === 0}
            className="inline-flex items-center gap-2 rounded-md bg-brand-emerald px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-deep disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> Importing…
              </>
            ) : (
              <>
                Import {Math.min(included.length, MAX_ROWS)} building
                {Math.min(included.length, MAX_ROWS) === 1 ? "" : "s"}
                <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </>
            )}
          </button>
        </>
      )}

      {!parsed && (
        <div className="rounded-lg border border-dashed border-border-subtle bg-bg-elevated/20 p-8 text-center">
          <FileSpreadsheet className="mx-auto mb-2 h-6 w-6 text-text-faint" aria-hidden />
          <div className="mb-1 text-sm text-text-primary">No file chosen yet</div>
          <div className="text-xs text-text-muted">
            Choose a CSV (or download the template to see the expected columns).
          </div>
        </div>
      )}
    </div>
  )
}
