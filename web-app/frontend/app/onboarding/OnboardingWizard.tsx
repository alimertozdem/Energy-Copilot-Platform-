"use client"

/**
 * OnboardingWizard -- multi-step state machine for the mandatory first-building
 * flow. Owns step index, shared form data, and submit state. Each step
 * component receives `data` + `update` and drives `onNext`/`onBack`.
 *
 *   0 Welcome - 1 Building - 2 Systems - 3 Review - 4 Done
 */
import { useState } from "react"
import Link from "next/link"

import { LogoCard } from "@/app/components/LogoCard"
import { cn } from "@/lib/utils"
import { BuildingBasicsStep } from "@/components/onboarding/BuildingBasicsStep"
import { SystemsStep } from "@/components/onboarding/SystemsStep"
import { EnvelopeStep } from "@/components/onboarding/EnvelopeStep"
import { ReviewStep } from "@/components/onboarding/ReviewStep"
import { DoneStep } from "@/components/onboarding/DoneStep"
import { WizardScorePreview } from "@/components/onboarding/WizardScorePreview"
import { previewReadiness } from "@/lib/readiness/preview"
import {
  createBuilding,
  type BuildingCreateRequest,
  type BuildingModuleInput,
} from "@/lib/api/buildings"

import { type OnboardingData, INITIAL_DATA, STEPS } from "./types"

function toNumber(s: string): number | null {
  const n = parseFloat(s)
  return Number.isFinite(n) ? n : null
}

function toIntOrNull(s: string): number | null {
  const n = parseInt(s, 10)
  return Number.isFinite(n) ? n : null
}

// On-site fossil combustion (drives Scope 1 + the CO₂ cost split). Unknown when
// no heating is chosen or it's free-text "other".
function gasFlag(d: OnboardingData): boolean | null {
  const h = d.heating_system
  if (!h || h === "other") return null
  return h === "gas_boiler" || h === "oil"
}

export function OnboardingWizard({ userName }: { userName: string | null }) {
  const [step, setStep] = useState(0)
  const [data, setData] = useState<OnboardingData>(INITIAL_DATA)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedName, setSavedName] = useState("")
  const [savedId, setSavedId] = useState("")

  function update(patch: Partial<OnboardingData>) {
    setData((d) => ({ ...d, ...patch }))
  }

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1))
  const back = () => setStep((s) => Math.max(s - 1, 0))

  // Live Data Score mirror (consumption not yet uploaded → months = 0).
  const preview = previewReadiness(data)

  async function submit() {
    setSubmitting(true)
    setError(null)

    // The data method + protocol/sensor config are stored as JSON on the
    // relevant module notes (no schema change) — the edge / Fabric side reads
    // this to configure ingestion for the building.
    const metersNotes = JSON.stringify({
      data_method: data.data_method || null,
      data_source: data.data_source || null,
      ...(data.building_type === "Residential" && data.residential_units
        ? { residential_units: toNumber(data.residential_units) }
        : {}),
    })
    const modules: BuildingModuleInput[] = [
      { module_key: "meters", enabled: true, notes: metersNotes },
    ]
    if (data.has_iot) {
      modules.push({
        module_key: "iot",
        enabled: true,
        notes: JSON.stringify({
          protocols: data.iot_protocols,
          sensor_types: data.iot_sensor_types,
          zones: toNumber(data.iot_zones),
        }),
      })
    }
    if (data.has_battery) modules.push({ module_key: "battery", enabled: true })
    if (data.has_solar) modules.push({ module_key: "solar", enabled: true })

    // "Other" heating/cooling sends the free-text value the user typed.
    const heatingValue =
      data.heating_system === "other"
        ? data.heating_other.trim() || "other"
        : data.heating_system || null
    const coolingValue =
      data.cooling_system === "other"
        ? data.cooling_other.trim() || "other"
        : data.cooling_system || null

    const year = parseInt(data.construction_year, 10)
    const payload: BuildingCreateRequest = {
      name: data.name.trim(),
      building_type: data.building_type || null,
      city: data.city.trim() || null,
      country_code: data.country_code.trim() || null,
      floor_area_m2: toNumber(data.floor_area_m2),
      construction_year: Number.isFinite(year) ? year : null,
      epc_class: data.epc_class || null,
      heating_system: heatingValue,
      cooling_system: coolingValue,
      occupancy_pattern: data.occupancy_pattern || null,
      floors_above_ground: toNumber(data.floors_above_ground),
      typical_occupants: toNumber(data.typical_occupants),
      pv_capacity_kwp: data.has_solar ? toNumber(data.pv_capacity_kwp) : null,
      wall_u_value: toNumber(data.wall_u_value),
      roof_u_value: toNumber(data.roof_u_value),
      window_u_value: toNumber(data.window_u_value),
      insulation_year: toIntOrNull(data.insulation_year),
      has_gas_heating: gasFlag(data),
      modules,
    }

    const result = await createBuilding(payload)
    setSubmitting(false)
    if (!result.ok) {
      setError(result.error)
      return
    }
    setSavedName(result.data.name)
    setSavedId(result.data.id)
    setStep(5)
  }

  function resetForAnother() {
    setData(INITIAL_DATA)
    setError(null)
    setSavedName("")
    setSavedId("")
    setStep(1)
  }

  return (
    <main id="main-content" className="relative min-h-screen overflow-hidden bg-bg-base bg-radial-emerald-glow flex items-center justify-center p-4">
      <div className="pointer-events-none fixed inset-0 bg-dot-grid opacity-25" aria-hidden />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[420px] animate-pulse"
        aria-hidden
        style={{ background: "radial-gradient(55% 80% at 50% -5%, rgba(29,158,117,0.18), transparent 70%)" }}
      />

      <div className="relative z-10 w-full max-w-2xl">
        <div className="mb-6 flex flex-col items-center text-center">
          <LogoCard iconSize={56} />
          <p className="mt-3 text-[11px] uppercase tracking-[0.18em] text-text-faint">Set up your building</p>
        </div>

        <div className="relative rounded-2xl border border-brand-emerald/20 bg-bg-elevated/70 p-8 shadow-[0_20px_60px_rgba(0,0,0,0.45)] backdrop-blur-sm">
          <div
            className="pointer-events-none absolute inset-x-0 top-0 h-px"
            style={{ background: "linear-gradient(90deg, transparent, rgba(29,158,117,0.6), transparent)" }}
            aria-hidden
          />
          <ProgressBar step={step} />
          {step > 0 && step < STEPS.length - 1 && (
            <WizardScorePreview preview={preview} />
          )}

          <div key={step} className="el-fade-up">
          {step === 0 && <WelcomeStep userName={userName} onNext={next} />}
          {step === 1 && (
            <BuildingBasicsStep
              data={data}
              update={update}
              onNext={next}
              onBack={back}
            />
          )}
          {step === 2 && (
            <SystemsStep
              data={data}
              update={update}
              onNext={next}
              onBack={back}
            />
          )}
          {step === 3 && (
            <EnvelopeStep
              data={data}
              update={update}
              onNext={next}
              onBack={back}
            />
          )}
          {step === 4 && (
            <ReviewStep
              data={data}
              onSubmit={submit}
              onBack={back}
              submitting={submitting}
              error={error}
            />
          )}
          {step === 5 && (
            <DoneStep
              buildingName={savedName}
              buildingId={savedId}
              dataMethod={data.data_method}
              onAddAnother={resetForAnother}
            />
          )}
          </div>
        </div>
      </div>
    </main>
  )
}

function ProgressBar({ step }: { step: number }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-1.5">
        {STEPS.map((label, i) => (
          <div
            key={label}
            className={cn(
              "h-1 flex-1 rounded-full transition-colors",
              i <= step ? "bg-brand-emerald" : "bg-border-subtle"
            )}
          />
        ))}
      </div>
      <p className="mt-2 text-xs text-text-faint">
        Step {Math.min(step + 1, STEPS.length)} of {STEPS.length} - {STEPS[step]}
      </p>
    </div>
  )
}

function WelcomeStep({
  userName,
  onNext,
}: {
  userName: string | null
  onNext: () => void
}) {
  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary mb-1 tracking-tight">
        Welcome{userName ? `, ${userName.split(" ")[0]}` : ""}
      </h1>
      <p className="text-text-muted text-sm mb-4">
        Let&apos;s add your first building. It takes about a minute — and
        no new hardware is required.
      </p>
      <p className="text-sm text-text-muted mb-6">
        We&apos;ll capture a few details (location, type, size) and which energy
        systems it has. Your KPIs, reports and advisor come alive from your
        first utility bill or meter export — no sensors needed. Connect live
        data later if you want real-time monitoring. Meanwhile, explore the
        sample portfolio to see exactly what you&apos;ll get.
      </p>
      <button
        type="button"
        onClick={onNext}
        className="bg-brand-emerald hover:bg-brand-deep text-white font-medium px-6 py-2.5 rounded-md transition-colors shadow-[0_0_24px_rgba(29,158,117,0.2)]"
      >
        Get started
      </button>
      <p className="mt-4 text-sm text-text-muted">
        Managing a portfolio?{" "}
        <Link href="/buildings/import" className="text-brand-emerald hover:underline">
          Import buildings from CSV
        </Link>
      </p>
    </div>
  )
}
