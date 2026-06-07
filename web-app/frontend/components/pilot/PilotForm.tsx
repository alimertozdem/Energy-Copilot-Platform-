"use client"

/**
 * PilotForm — public "request a pilot" form. Posts to /api/pilot-requests (no
 * auth). On success shows a thank-you state. `source` tags where the lead came
 * from (landing / demo / tour / pricing).
 */
import { CheckCircle2, Loader2 } from "lucide-react"
import { useState } from "react"

import { submitPilotRequest } from "@/lib/api/pilot"

const inputCls =
  "w-full rounded-md border border-border-faint bg-bg-input px-3 py-2 text-sm text-text-primary placeholder:text-text-faint focus:border-transparent focus:outline-none focus:ring-2 focus:ring-brand-emerald"
const labelCls = "mb-1.5 block text-sm text-text-muted"

export function PilotForm({ source }: { source?: string }) {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [organization, setOrganization] = useState("")
  const [country, setCountry] = useState("")
  const [buildings, setBuildings] = useState("")
  const [message, setMessage] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!name.trim() || !email.trim()) {
      setError("Name and email are required.")
      return
    }
    setBusy(true)
    const bc = parseInt(buildings, 10)
    const res = await submitPilotRequest({
      name: name.trim(),
      email: email.trim(),
      organization: organization.trim() || null,
      country_code: country.trim().toUpperCase() || null,
      building_count: Number.isFinite(bc) ? bc : null,
      message: message.trim() || null,
      source: source || "pilot_page",
    })
    setBusy(false)
    if (!res.ok) {
      setError(res.error)
      return
    }
    setDone(true)
  }

  if (done) {
    return (
      <div className="rounded-2xl border border-brand-emerald/30 bg-bg-elevated/60 p-8 text-center">
        <CheckCircle2 className="mx-auto h-12 w-12 text-brand-emerald" />
        <h2 className="mt-4 text-xl font-semibold text-text-primary">Thanks — request received</h2>
        <p className="mx-auto mt-2 max-w-sm text-sm text-text-muted">
          We&rsquo;ll be in touch about running an EnergyLens pilot. You can also explore the
          live demo meanwhile.
        </p>
        <a
          href="/demo"
          className="mt-5 inline-flex items-center justify-center rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-5 py-2.5 text-sm font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
        >
          Explore the live demo
        </a>
      </div>
    )
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-2xl border border-border-subtle bg-bg-elevated/60 p-6 backdrop-blur-sm"
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="p-name" className={labelCls}>Name *</label>
          <input id="p-name" value={name} onChange={(e) => setName(e.target.value)} className={inputCls} placeholder="Your name" />
        </div>
        <div>
          <label htmlFor="p-email" className={labelCls}>Work email *</label>
          <input id="p-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} placeholder="you@company.com" />
        </div>
        <div>
          <label htmlFor="p-org" className={labelCls}>Organization</label>
          <input id="p-org" value={organization} onChange={(e) => setOrganization(e.target.value)} className={inputCls} placeholder="Company / housing portfolio" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="p-country" className={labelCls}>Country</label>
            <input id="p-country" maxLength={2} value={country} onChange={(e) => setCountry(e.target.value)} className={inputCls} placeholder="DE" />
          </div>
          <div>
            <label htmlFor="p-buildings" className={labelCls}>Buildings</label>
            <input id="p-buildings" type="number" min={0} value={buildings} onChange={(e) => setBuildings(e.target.value)} className={inputCls} placeholder="e.g. 8" />
          </div>
        </div>
      </div>
      <div className="mt-4">
        <label htmlFor="p-msg" className={labelCls}>What would you like to pilot?</label>
        <textarea id="p-msg" rows={3} value={message} onChange={(e) => setMessage(e.target.value)} className={inputCls} placeholder="Optional — your portfolio, goals, or a building you'd like to start with." />
      </div>

      {error && <p className="mt-3 text-sm text-accent-red">{error}</p>}

      <button
        type="submit"
        disabled={busy}
        className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-emerald px-6 py-3 text-sm font-semibold text-bg-base shadow-[0_0_24px_rgba(16,185,129,0.3)] transition-colors hover:bg-brand-emerald/90 disabled:opacity-50 sm:w-auto"
      >
        {busy && <Loader2 className="h-4 w-4 animate-spin" />}
        Request a pilot
      </button>
      <p className="mt-3 text-[11px] text-text-faint">
        We only use your details to contact you about a pilot.
      </p>
    </form>
  )
}
