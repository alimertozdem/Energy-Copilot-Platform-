"use client"

/**
 * SubscriptionCard — current plan + self-serve Stripe billing.
 *
 * Admins can upgrade/switch via Stripe Checkout or open the Customer Portal
 * (manage/cancel); non-admins see a read-only plan with a note. Enterprise is
 * "contact sales". The org's tier/status are synced from Stripe by the backend
 * webhook, so this card reflects DB state and just kicks off hosted flows.
 */
import { useState } from "react"
import { Loader2, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { openPortal, startCheckout, type BillingTier } from "@/lib/api/billing"
import { type OrganizationProfile } from "@/lib/api/settings"
import { cn } from "@/lib/utils"

const TIER_ORDER = ["free", "basic", "monitor", "enterprise"] as const

const TIER_META: Record<string, { label: string; blurb: string }> = {
  free: {
    label: "Free",
    blurb: "Core dashboards for a single workspace.",
  },
  basic: {
    label: "Basic",
    blurb: "Portfolio analytics across multiple buildings.",
  },
  monitor: {
    label: "Monitor",
    blurb: "Adds live IoT monitoring and battery simulation modules.",
  },
  enterprise: {
    label: "Enterprise",
    blurb: "Full platform with priority support and custom SLAs.",
  },
}

const SELF_SERVE: BillingTier[] = ["basic", "monitor"]

const STATUS_META: Record<string, { label: string; cls: string }> = {
  active: {
    label: "Active",
    cls: "bg-brand-emerald/10 text-brand-emerald border-brand-emerald/30",
  },
  past_due: {
    label: "Past due",
    cls: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  },
  canceled: {
    label: "Canceled",
    cls: "bg-accent-red/10 text-accent-red border-accent-red/30",
  },
}

export function SubscriptionCard({
  org,
  canManage,
}: {
  org: OrganizationProfile
  canManage: boolean
}) {
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const currentTier = org.subscription_tier
  const status =
    STATUS_META[org.subscription_status] ?? {
      label: org.subscription_status,
      cls: "bg-white/5 text-text-muted border-border-subtle",
    }

  async function go(action: "portal" | BillingTier) {
    setError(null)
    setBusy(action)
    const result = action === "portal" ? await openPortal() : await startCheckout(action)
    if (result.ok) {
      window.location.href = result.url
      return // navigating to Stripe; keep the buttons disabled
    }
    setError(result.error)
    setBusy(null)
  }

  return (
    <section className="rounded-xl border border-border-subtle bg-bg-elevated/60 p-5">
      <header className="flex items-center gap-2 mb-4">
        <Sparkles className="w-4 h-4 text-brand-emerald" />
        <h2 className="text-sm font-semibold text-text-primary">Subscription</h2>
      </header>

      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl font-semibold text-text-primary">
          {TIER_META[currentTier]?.label ?? currentTier}
        </span>
        <span
          className={cn(
            "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium",
            status.cls
          )}
        >
          {status.label}
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
        {TIER_ORDER.map((t) => {
          const meta = TIER_META[t]
          const isCurrent = t === currentTier
          return (
            <div
              key={t}
              className={cn(
                "rounded-lg border p-3 transition-colors",
                isCurrent
                  ? "border-brand-emerald/40 bg-brand-emerald/5"
                  : "border-border-subtle bg-white/[0.02]"
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-text-primary">{meta.label}</span>
                {isCurrent && (
                  <span className="text-[10px] uppercase tracking-wider text-brand-emerald">
                    Current
                  </span>
                )}
              </div>
              <p className="text-xs text-text-muted mt-1">{meta.blurb}</p>
            </div>
          )
        })}
      </div>

      {error && (
        <div className="mb-3 rounded-md border border-accent-red/30 bg-accent-red/5 px-3 py-2 text-xs text-accent-red">
          {error}
        </div>
      )}

      {canManage ? (
        <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border-subtle">
          {SELF_SERVE.filter((t) => t !== currentTier).map((t) => (
            <Button key={t} size="sm" onClick={() => go(t)} disabled={busy !== null}>
              {busy === t && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {currentTier === "free"
                ? `Upgrade to ${TIER_META[t].label}`
                : `Switch to ${TIER_META[t].label}`}
            </Button>
          ))}
          {currentTier !== "free" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => go("portal")}
              disabled={busy !== null}
            >
              {busy === "portal" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Manage billing
            </Button>
          )}
          <Button asChild variant="ghost" size="sm" className="ml-auto">
            <a href="mailto:alimert@energylens.eu?subject=EnergyLens%20Enterprise%20plan">
              Enterprise? Contact sales
            </a>
          </Button>
        </div>
      ) : (
        <p className="pt-3 border-t border-border-subtle text-xs text-text-faint">
          Ask an organization admin to change the plan.
        </p>
      )}
    </section>
  )
}
