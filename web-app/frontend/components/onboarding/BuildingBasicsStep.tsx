"use client"

/**
 * Step 2 — building basics. Name is required; everything else optional.
 * Uses the login/signup raw-input styling so it matches the onboarding shell.
 */
import { type OnboardingData, BUILDING_TYPES, EPC_CLASSES, COUNTRIES } from "@/app/onboarding/types"

const inputCls =
  "w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent transition-all"
const labelCls = "block text-sm text-text-muted mb-1.5"

export function BuildingBasicsStep({
  data,
  update,
  onNext,
  onBack,
}: {
  data: OnboardingData
  update: (patch: Partial<OnboardingData>) => void
  onNext: () => void
  onBack: () => void
}) {
  const canContinue = data.name.trim().length > 0

  return (
    <div>
      <h2 className="font-display text-2xl font-bold text-text-primary mb-1 tracking-tight">
        Building details
      </h2>
      <p className="text-text-muted text-sm mb-6">
        Just the basics — you can refine these later.
      </p>

      <div className="flex flex-col gap-4">
        <div>
          <label htmlFor="b-name" className={labelCls}>
            Building name <span className="text-brand-emerald">*</span>
          </label>
          <input
            id="b-name"
            type="text"
            required
            autoFocus
            maxLength={255}
            value={data.name}
            onChange={(e) => update({ name: e.target.value })}
            placeholder="e.g. Berlin HQ"
            className={inputCls}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="b-type" className={labelCls}>
              Type
            </label>
            <select
              id="b-type"
              value={data.building_type}
              onChange={(e) => update({ building_type: e.target.value })}
              className={inputCls}
            >
              <option value="">Select type…</option>
              {BUILDING_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="b-area" className={labelCls}>
              Floor area (m²)
            </label>
            <input
              id="b-area"
              type="number"
              min={0}
              value={data.floor_area_m2}
              onChange={(e) => update({ floor_area_m2: e.target.value })}
              placeholder="e.g. 4200"
              className={inputCls}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="b-city" className={labelCls}>
              City
            </label>
            <input
              id="b-city"
              type="text"
              maxLength={100}
              value={data.city}
              onChange={(e) => update({ city: e.target.value })}
              placeholder="e.g. Berlin"
              className={inputCls}
            />
          </div>
          <div>
            <label htmlFor="b-country" className={labelCls}>
              Country
            </label>
            <select
              id="b-country"
              value={data.country_code}
              onChange={(e) => update({ country_code: e.target.value })}
              className={inputCls}
            >
              <option value="">Select country…</option>
              {COUNTRIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="b-year" className={labelCls}>
              Construction year
            </label>
            <input
              id="b-year"
              type="number"
              min={1800}
              max={2100}
              value={data.construction_year}
              onChange={(e) => update({ construction_year: e.target.value })}
              placeholder="e.g. 1998"
              className={inputCls}
            />
          </div>
          <div>
            <label htmlFor="b-epc" className={labelCls}>
              EPC class <span className="text-text-faint">(if known)</span>
            </label>
            <select
              id="b-epc"
              value={data.epc_class}
              onChange={(e) => update({ epc_class: e.target.value })}
              className={inputCls}
            >
              <option value="">Unknown</option>
              {EPC_CLASSES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="b-floors" className={labelCls}>
              Floors above ground
            </label>
            <input
              id="b-floors"
              type="number"
              min={0}
              value={data.floors_above_ground}
              onChange={(e) => update({ floors_above_ground: e.target.value })}
              placeholder="e.g. 6"
              className={inputCls}
            />
          </div>
          <div>
            <label htmlFor="b-occ" className={labelCls}>
              Typical occupants
            </label>
            <input
              id="b-occ"
              type="number"
              min={0}
              value={data.typical_occupants}
              onChange={(e) => update({ typical_occupants: e.target.value })}
              placeholder="e.g. 250"
              className={inputCls}
            />
          </div>
        </div>

        {data.building_type === "Residential" && (
          <div className="w-1/2 pr-1.5">
            <label htmlFor="b-units" className={labelCls}>
              Residential units
            </label>
            <input
              id="b-units"
              type="number"
              min={0}
              value={data.residential_units}
              onChange={(e) => update({ residential_units: e.target.value })}
              placeholder="e.g. 42"
              className={inputCls}
            />
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          type="button"
          onClick={onBack}
          className="text-sm text-text-muted hover:text-text-primary transition-colors"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={!canContinue}
          className="bg-brand-emerald hover:bg-brand-deep disabled:bg-brand-deep disabled:opacity-50 text-white font-medium px-6 py-2.5 rounded-md transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
        >
          Continue →
        </button>
      </div>
    </div>
  )
}
