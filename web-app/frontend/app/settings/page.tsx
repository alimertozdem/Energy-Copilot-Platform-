/**
 * /settings — organization management page.
 *
 * Server component. Auth-guarded (mirrors /portfolio, /actions).
 *
 * Scope (V1): shows the org carried in the session JWT (the user's current
 * org -- no org switcher yet). Backend enforces membership + admin gating;
 * this page just renders what GET /settings/organization returns. The activity
 * feed is admin-only on the backend (403 for non-admins -> empty section).
 *
 * ?billing=success|cancel arrives after a Stripe Checkout redirect -> a calm
 * confirmation banner (BillingNotice); the tier change itself lands via webhook.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { SustainabilityMotif } from "@/components/SustainabilityMotif"
import { BillingNotice } from "@/components/settings/BillingNotice"
import { authOptions } from "@/lib/auth/options"
import { fetchOrgSettings, fetchSettingsActivity } from "@/lib/api/settings"

import { SettingsShell } from "./SettingsShell"

// Section accent -- emerald, matching the brand's primary hue.
const SETTINGS_ACCENT = "#10b981"

type PageProps = {
  searchParams: Promise<{ billing?: string }>
}

export default async function SettingsPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { billing } = await searchParams

  const [result, activityResult] = await Promise.all([
    fetchOrgSettings(session.accessToken),
    fetchSettingsActivity(session.accessToken),
  ])

  return (
    <AppChrome
      breadcrumb={[{ label: "Settings" }]}
      pageTitle="Settings"
      subtitle={
        result.ok ? result.data.organization.name : "Organization & members"
      }
      accentColor={SETTINGS_ACCENT}
    >
      <SustainabilityMotif />

      <div className="relative z-10 px-6 py-8 max-w-5xl mx-auto">
        <BillingNotice status={billing} />

        {!result.ok ? (
          <div className="rounded-lg border border-accent-red/30 bg-accent-red/5 p-4 text-text-primary">
            <div className="text-sm font-medium mb-1">
              Failed to load settings
            </div>
            <div className="text-xs text-text-muted">{result.error}</div>
          </div>
        ) : (
          <SettingsShell
            initial={result.data}
            activity={activityResult.ok ? activityResult.data.events : []}
          />
        )}
      </div>
    </AppChrome>
  )
}
