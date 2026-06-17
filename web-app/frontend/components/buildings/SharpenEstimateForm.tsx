/**
 * SharpenEstimateForm — the data flywheel. Shown under the estimate card for a
 * data-poor building, it nudges the user to supply the highest-leverage MISSING
 * inputs (year built, EPC class, heating, floor area). Saving PATCHes the
 * building and refreshes the page so the estimate re-runs sharper.
 *
 * Only the inputs that are actually missing are shown — so it shrinks to nothing
 * once the building is fully described (then the next step is uploading a bill).
 */
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

type Current = {
  construction_year: number | null
  epc_class: string | null
  heating_system: string | null
  floor_area_m2: number | null
}

const EPC_CLASSES = ["A+", "A", "B", "C", "D", "E", "F", "G", "H"]
const HEATING = [
  { v: "gas_boiler", l: "Gas" },
  { v: "oil", l: "Oil" },
  { v: "district_heating", l: "District heating" },
  { v: "heat_pump", l: "Heat pump" },
  { v: "electric", l: "Direct electric" },
]

export function SharpenEstimateForm({
  buildingId,
  current,
  canManage,
}: {
  buildingId: string
  current: Current
  canManage: boolean
}) {
  const router = useRouter()
  const [year, setYear] = useState("")
  const [epc, setEpc] = useState("")
  const [heating, setHeating] = useState("")
  const [area, setArea] = useState("")
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  if (!canManage) return null

  const showYear = !current.construction_year
  const showEpc = !current.epc_class
  const showHeating = !current.heating_system
  const showArea = !current.floor_area_m2
  if (!showYear && !showEpc && !showHeating && !showArea) return null

  async function save() {
    const payload: Record<string, unknown> = {}
    if (showYear && year) payload.construction_year = Number(year)
    if (showEpc && epc) payload.epc_class = epc
    if (showHeating && heating) payload.heating_system = heating
    if (showArea && area) payload.floor_area_m2 = Number(area)
    if (Object.keys(payload).length === 0) return

    setSaving(true)
    setErr(null)
    try {
      const res = await fetch(`/api/buildings/${encodeURIComponent(buildingId)}/profile`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        setErr("Couldn’t save — please try again.")
        setSaving(false)
        return
      }
      router.refresh()
    } catch {
      setErr("Couldn’t save — please try again.")
      setSaving(false)
    }
  }

  const field = "mt-0.5 rounded border border-white/15 bg-white/5 px-2 py-1 text-xs text-text-primary"
  const lbl = "flex flex-col text-[11px] text-text-muted"

  return (
    <div className="mt-2 rounded-xl border border-white/10 bg-white/[0.02] p-3">
      <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-text-faint">
        Sharpen this estimate
      </div>
      <div className="flex flex-wrap items-end gap-2">
        {showYear && (
          <label className={lbl}>
            Year built
            <input
              type="number"
              inputMode="numeric"
              placeholder="e.g. 1985"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className={`${field} w-24`}
            />
          </label>
        )}
        {showEpc && (
          <label className={lbl}>
            EPC class
            <select value={epc} onChange={(e) => setEpc(e.target.value)} className={`${field} w-20`}>
              <option value="">—</option>
              {EPC_CLASSES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        )}
        {showHeating && (
          <label className={lbl}>
            Heating
            <select value={heating} onChange={(e) => setHeating(e.target.value)} className={`${field} w-32`}>
              <option value="">—</option>
              {HEATING.map((h) => (
                <option key={h.v} value={h.v}>
                  {h.l}
                </option>
              ))}
            </select>
          </label>
        )}
        {showArea && (
          <label className={lbl}>
            Floor area (m²)
            <input
              type="number"
              inputMode="numeric"
              placeholder="m²"
              value={area}
              onChange={(e) => setArea(e.target.value)}
              className={`${field} w-24`}
            />
          </label>
        )}
        <button
          onClick={save}
          disabled={saving}
          className="rounded-md border border-emerald-400/40 bg-emerald-400/10 px-3 py-1.5 text-xs font-medium text-emerald-300 transition-colors hover:bg-emerald-400/20 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Sharpen"}
        </button>
      </div>
      <p className="mt-1.5 text-[11px] text-text-faint">
        Each input narrows the range; a bill replaces the estimate with measured numbers.
      </p>
      {err && <p className="mt-1 text-[11px] text-red-300">{err}</p>}
    </div>
  )
}
