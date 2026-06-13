"use client"

/**
 * Step 4 — building envelope & efficiency.
 *
 * Optional, but high-value: the wall / roof / window U-values are what unlock the
 * German GEG §10/§71 conformity check, and together with the insulation year they
 * sharpen the retrofit recommendations. Everything here can be left blank and
 * added later — the live Data Score strip shows exactly how many points each
 * field is worth. Typical-range hints keep the numbers honest.
 */
import { type OnboardingData } from "@/app/onboarding/types"

const inputCls =
  "w-full bg-bg-input border border-border-faint text-text-primary rounded-md px-3 py-2 text-sm placeholder:text-text-faint focus:outline-none focus:ring-2 focus:ring-brand-emerald focus:border-transparent transition-all"
const labelCls = "block text-sm text-text-muted mb-1.5"

// W/m²K — modern (insulated) → old (uninsulated). Shown as honest guidance only.
const U_FIELDS = [
  { key: "wall_u_value" as const, label: "Wall U-value", placeholder: "e.g. 0.28", range: "0.15 (new) – 1.4 (old, solid)" },
  { key: "roof_u_value" as const, label: "Roof U-value", placeholder: "e.g. 0.20", range: "0.12 (new) – 1.0 (old)" },
  { key: "window_u_value" as const, label: "Window U-value", placeholder: "e.g. 1.10", range: "0.8 (triple) – 5.8 (single)" },
]

export function EnvelopeStep({
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
  return (
    <div>
      <h2 className="font-display text-2xl font-bold text-text-primary mb-1 tracking-tight">
        Envelope &amp; efficiency
      </h2>
      <p className="text-text-muted text-sm mb-4">
        Optional — but these are the highest-value fields. If you have an energy
        certificate (Energieausweis) or a retrofit report, the numbers are on it.
      </p>

      <div className="mb-5 rounded-lg border border-brand-emerald/25 bg-brand-emerald/[0.06] px-3.5 py-2.5">
        <p className="text-xs text-text-muted">
          <span className="font-medium text-brand-emerald">Unlocks:</span> the U-values
          (+15 pts) turn on the <span className="text-text-primary">GEG conformity check</span>,
          and with the insulation year they sharpen the{" "}
          <span className="text-text-primary">retrofit recommendations</span>. Leave blank to
          skip — you can add them anytime.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        <div>
          <p className="mb-2 text-sm font-medium text-text-primary">
            Envelope U-values{" "}
            <span className="font-normal text-text-faint">(W/m²K)</span>
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {U_FIELDS.map((f) => (
              <div key={f.key}>
                <label htmlFor={`e-${f.key}`} className={labelCls}>
                  {f.label}
                </label>
                <input
                  id={`e-${f.key}`}
                  type="number"
                  min={0}
                  step="0.01"
                  value={data[f.key]}
                  onChange={(e) => update({ [f.key]: e.target.value })}
                  placeholder={f.placeholder}
                  className={inputCls}
                />
                <p className="mt-1 text-[11px] text-text-faint" title={`Typical range: ${f.range} W/m²K`}>
                  Typical {f.range}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="w-1/2 pr-1.5">
          <label htmlFor="e-insulation" className={labelCls}>
            Last insulation / refurbishment year{" "}
            <span className="text-text-faint">(if any)</span>
          </label>
          <input
            id="e-insulation"
            type="number"
            min={1800}
            max={2100}
            value={data.insulation_year}
            onChange={(e) => update({ insulation_year: e.target.value })}
            placeholder="e.g. 2014"
            className={inputCls}
          />
          <p className="mt-1 text-[11px] text-text-faint">
            When the building was last insulated — leave blank if never / unknown.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          type="button"
          onClick={onBack}
          className="text-sm text-text-muted hover:text-text-primary transition-colors"
        >
          ← Back
        </button>
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={onNext}
            className="text-sm text-text-muted hover:text-text-primary transition-colors"
          >
            Skip for now
          </button>
          <button
            type="button"
            onClick={onNext}
            className="bg-brand-emerald hover:bg-brand-deep text-white font-medium px-6 py-2.5 rounded-md transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
          >
            Review →
          </button>
        </div>
      </div>
    </div>
  )
}
