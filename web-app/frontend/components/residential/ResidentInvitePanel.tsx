"use client"

/**
 * ResidentInvitePanel — manager mints a resident magic-link for one unit.
 *
 * Posts to /api/residential/invites (BFF → backend, B2B-auth + can_manage gate).
 * On success it shows the copy-link the manager hands to the tenant — the same
 * single-use magic-link the resident opens at /residence/enter. No email is sent
 * (copy-link model, like the org-invite flow); resident accounts stay free.
 */
import { useState, type FormEvent } from "react"

export function ResidentInvitePanel({
  fabricBuildingId,
  units,
}: {
  fabricBuildingId: string
  units: string[]
}) {
  const [unit, setUnit] = useState(units[0] ?? "")
  const [email, setEmail] = useState("")
  const [busy, setBusy] = useState(false)
  const [link, setLink] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setLink(null)
    setCopied(false)
    try {
      const res = await fetch("/api/residential/invites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fabric_building_id: fabricBuildingId,
          fabric_unit_id: unit.trim(),
          email: email.trim(),
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (res.ok && data.token) {
        setLink(`${window.location.origin}/residence/enter?token=${data.token}`)
      } else {
        setError(data.detail || "Could not create the invite link.")
      }
    } catch {
      setError("Something went wrong. Please try again.")
    } finally {
      setBusy(false)
    }
  }

  async function copy() {
    if (!link) return
    try {
      await navigator.clipboard.writeText(link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard blocked — the link stays selectable in the field
    }
  }

  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
        Invite a resident
      </p>
      <p className="mt-1 text-xs text-text-muted">
        Generates a private magic-link for one unit. Share it with the tenant — it signs
        them in to their own home-energy view, no account needed. Resident access is free.
      </p>

      <form onSubmit={submit} className="mt-3 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] text-text-faint">Unit ID</span>
          <input
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            list="residence-units"
            placeholder="B011-U0101"
            required
            className="w-40 rounded-md border border-border-subtle bg-bg-base px-3 py-1.5 text-sm text-text-primary outline-none focus:border-brand-emerald"
          />
          <datalist id="residence-units">
            {units.map((u) => (
              <option key={u} value={u} />
            ))}
          </datalist>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] text-text-faint">Resident email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="tenant@example.com"
            required
            className="w-60 rounded-md border border-border-subtle bg-bg-base px-3 py-1.5 text-sm text-text-primary outline-none focus:border-brand-emerald"
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-brand-emerald px-4 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-brand-emerald/90 disabled:opacity-60"
        >
          {busy ? "Generating…" : "Generate invite link"}
        </button>
      </form>

      {error && <p className="mt-3 text-xs text-red-300">{error}</p>}

      {link && (
        <div className="mt-3 rounded-md border border-brand-emerald/30 bg-brand-emerald/5 p-3">
          <p className="text-[11px] text-text-muted">
            Magic-link (single use, valid 14 days) — copy and send to the resident:
          </p>
          <div className="mt-1.5 flex items-center gap-2">
            <input
              readOnly
              value={link}
              onFocus={(e) => e.target.select()}
              className="flex-1 rounded border border-border-subtle bg-bg-base px-2 py-1.5 text-xs text-text-primary"
            />
            <button
              type="button"
              onClick={copy}
              className="shrink-0 rounded-md border border-brand-emerald/40 px-3 py-1.5 text-xs font-medium text-brand-emerald hover:bg-brand-emerald/10"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
