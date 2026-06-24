"use client"

/**
 * AddBuildingModal — lightweight "add a single building" form for the /buildings
 * page, so a logged-in user can grow their portfolio without re-running the full
 * onboarding wizard (and without needing a CSV for one building).
 *
 * Only `name` is required; every other field is optional and simply sharpens the
 * building's screening estimate / Data Score. Submits through the proven
 * createBuilding() → /api/buildings proxy (same path onboarding uses), then
 * refreshes the list so the new card appears. For many buildings at once, the
 * footer links to the CSV import flow.
 */
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2, Plus, X } from "lucide-react"
import Link from "next/link"

import { createBuilding, type BuildingCreateRequest } from "@/lib/api/buildings"
import { COUNTRIES } from "@/app/onboarding/types"

const BUILDING_TYPES = [
  "Office",
  "Retail",
  "Logistics",
  "Hotel",
  "Healthcare",
  "Education",
  "Residential",
  "Mixed-use",
  "Other",
]
const EPC_CLASSES = ["A+", "A", "B", "C", "D", "E", "F", "G", "H"]
const HEATING = [
  { v: "gas_boiler", l: "Gas boiler" },
  { v: "oil", l: "Oil" },
  { v: "district_heating", l: "District heating" },
  { v: "heat_pump", l: "Heat pump" },
  { v: "electric", l: "Direct electric" },
  { v: "biomass", l: "Biomass" },
]

export function AddBuildingModal({ onClose }: { onClose: () => void }) {
  const router = useRouter()
  const [name, setName] = useState("")
  const [type, setType] = useState("")
  const [city, setCity] = useState("")
  const [country, setCountry] = useState("")
  const [area, setArea] = useState("")
  const [year, setYear] = useState("")
  const [epc, setEpc] = useState("")
  const [heating, setHeating] = useState("")
  const [units, setUnits] = useState("")
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const num = (s: string): number | null => {
    const n = Number(s)
    return s.trim() !== "" && Number.isFinite(n) ? n : null
  }

  async function save() {
    if (!name.trim()) {
      setErr("Building name is required.")
      return
    }
    setSaving(true)
    setErr(null)
    const payload: BuildingCreateRequest = {
      name: name.trim(),
      building_type: type || null,
      city: city.trim() || null,
      country_code: country.trim().toUpperCase() || null,
      floor_area_m2: num(area),
      construction_year: num(year),
      epc_class: epc || null,
      heating_system: heating || null,
      residential_units: num(units),
    }
    const res = await createBuilding(payload)
    if (!res.ok) {
      setErr(res.error || "Couldn’t create the building — please try again.")
      setSaving(false)
      return
    }
    router.refresh()
    onClose()
  }

  const field =
    "mt-1 w-full rounded-md border border-border-subtle bg-white/5 px-2.5 py-1.5 text-sm text-text-primary placeholder:text-text-faint focus:border-brand-emerald/60 focus:outline-none"
  const lbl = "block text-xs font-medium text-text-muted"

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Add building"
    >
      <div
        className="w-full max-w-lg rounded-2xl border border-border-subtle bg-bg-elevated p-5 shadow-[0_16px_48px_rgba(0,0,0,0.5)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-text-primary">Add a building</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-text-faint transition-colors hover:text-text-primary"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className={lbl}>
              Building name <span className="text-brand-emerald">*</span>
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Hamburg Office Tower"
              className={field}
              autoFocus
            />
          </div>

          <div>
            <label className={lbl}>Type</label>
            <select value={type} onChange={(e) => setType(e.target.value)} className={field}>
              <option value="">—</option>
              {BUILDING_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={lbl}>City</label>
            <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Hamburg" className={field} />
          </div>

          <div>
            <label className={lbl}>Country</label>
            <select value={country} onChange={(e) => setCountry(e.target.value)} className={field}>
              <option value="">—</option>
              {COUNTRIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={lbl}>Floor area (m²)</label>
            <input
              type="number"
              inputMode="numeric"
              value={area}
              onChange={(e) => setArea(e.target.value)}
              placeholder="12000"
              className={field}
            />
          </div>

          <div>
            <label className={lbl}>Year built</label>
            <input
              type="number"
              inputMode="numeric"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="1995"
              className={field}
            />
          </div>
          <div>
            <label className={lbl}>EPC class</label>
            <select value={epc} onChange={(e) => setEpc(e.target.value)} className={field}>
              <option value="">—</option>
              {EPC_CLASSES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className={lbl}>Heating</label>
            <select value={heating} onChange={(e) => setHeating(e.target.value)} className={field}>
              <option value="">—</option>
              {HEATING.map((h) => (
                <option key={h.v} value={h.v}>
                  {h.l}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={lbl}>Residential units</label>
            <input
              type="number"
              inputMode="numeric"
              value={units}
              onChange={(e) => setUnits(e.target.value)}
              placeholder="optional"
              className={field}
            />
          </div>
        </div>

        <p className="mt-3 text-[11px] leading-relaxed text-text-faint">
          Only the name is required. Every other field sharpens the building’s screening
          estimate — you can fill them in later or upload a bill for measured numbers.
        </p>

        {err && (
          <div className="mt-3 rounded-md border border-red-400/30 bg-red-400/5 px-3 py-2 text-xs text-red-200">
            {err}
          </div>
        )}

        <div className="mt-4 flex items-center justify-between gap-3">
          <Link
            href="/buildings/import"
            className="text-xs text-text-muted underline-offset-2 transition-colors hover:text-brand-emerald hover:underline"
          >
            Adding many? Import a CSV
          </Link>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-border-subtle px-4 py-2 text-sm text-text-muted transition-colors hover:text-text-primary"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={save}
              disabled={saving || !name.trim()}
              className="inline-flex items-center gap-1.5 rounded-md bg-brand-emerald px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> Adding…
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" aria-hidden /> Add building
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
