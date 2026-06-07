"use client"

/**
 * OrgProfileCard — view + (admin-only) edit of the organization profile.
 *
 * Read-only for managers/viewers; admins get an inline edit form for name,
 * billing email, and country code. Save goes through updateOrganization and
 * lifts the fresh profile up via onUpdated so the rest of the page stays in
 * sync (e.g. the subscription card reads the same org object).
 */
import { useState } from "react"
import { Building2, Check, Loader2, Pencil, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import {
  type OrganizationProfile,
  updateOrganization,
} from "@/lib/api/settings"

type OrgProfileCardProps = {
  org: OrganizationProfile
  canManage: boolean
  onUpdated: (org: OrganizationProfile) => void
}

export function OrgProfileCard({
  org,
  canManage,
  onUpdated,
}: OrgProfileCardProps) {
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(org.name)
  const [billingEmail, setBillingEmail] = useState(org.billing_email ?? "")
  const [country, setCountry] = useState(org.country_code ?? "")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function startEdit() {
    setName(org.name)
    setBillingEmail(org.billing_email ?? "")
    setCountry(org.country_code ?? "")
    setError(null)
    setEditing(true)
  }

  function cancel() {
    setError(null)
    setEditing(false)
  }

  async function save() {
    setSaving(true)
    setError(null)
    const result = await updateOrganization({
      name: name.trim() || org.name,
      billing_email: billingEmail.trim() || null,
      country_code: country.trim() ? country.trim().toUpperCase() : null,
    })
    setSaving(false)
    if (!result.ok) {
      setError(result.error)
      return
    }
    onUpdated(result.data)
    setEditing(false)
  }

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-5">
      <header className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Building2 className="w-4 h-4 text-brand-emerald" />
          <h2 className="text-sm font-semibold text-text-primary">
            Organization
          </h2>
        </div>
        {canManage && !editing && (
          <Button variant="outline" size="sm" onClick={startEdit}>
            <Pencil className="w-3.5 h-3.5" />
            Edit
          </Button>
        )}
      </header>

      {editing ? (
        <div className="space-y-4">
          <Field label="Name">
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={255}
              placeholder="Organization name"
            />
          </Field>
          <Field label="Billing email">
            <Input
              type="email"
              value={billingEmail}
              onChange={(e) => setBillingEmail(e.target.value)}
              placeholder="billing@company.com"
            />
          </Field>
          <Field label="Country" hint="ISO-2, e.g. DE">
            <Input
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              maxLength={2}
              placeholder="DE"
              className="w-24 uppercase"
            />
          </Field>

          {error && <p className="text-xs text-accent-red">{error}</p>}

          <div className="flex items-center gap-2 pt-1">
            <Button size="sm" onClick={save} disabled={saving}>
              {saving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Check className="w-3.5 h-3.5" />
              )}
              Save changes
            </Button>
            <Button variant="ghost" size="sm" onClick={cancel} disabled={saving}>
              <X className="w-3.5 h-3.5" />
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
          <Row label="Name" value={org.name} />
          <Row label="Workspace ID" value={org.slug} mono />
          <Row label="Billing email" value={org.billing_email || "—"} />
          <Row label="Country" value={org.country_code || "—"} />
        </dl>
      )}
    </section>
  )
}

function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-text-muted">
        {label}
        {hint && (
          <span className="text-text-faint font-normal"> · {hint}</span>
        )}
      </Label>
      {children}
    </div>
  )
}

function Row({
  label,
  value,
  mono,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div>
      <dt className="text-xs text-text-muted">{label}</dt>
      <dd
        className={cn(
          "mt-0.5 text-sm text-text-primary",
          mono && "font-mono text-xs"
        )}
      >
        {value}
      </dd>
    </div>
  )
}
