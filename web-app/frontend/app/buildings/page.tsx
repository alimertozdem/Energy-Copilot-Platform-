/**
 * /buildings -- grid card list of buildings visible to the authenticated user.
 *
 * Server component. Auth-guarded. Also enforces mandatory onboarding: a user
 * with zero own (non-sample) buildings is redirected to /onboarding.
 *
 * Visibility (enforced by backend): user's org buildings + sample org buildings.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { CitySkylineMotif } from "@/components/CitySkylineMotif"
import { DataPendingBanner } from "@/components/DataPendingBanner"
import { SampleDataToggle } from "@/components/SampleDataToggle"
import { SustainabilityMotif } from "@/components/SustainabilityMotif"
import {
  countOwnBuildings,
  fetchBuildings,
  ownBuildingsAllPending,
} from "@/lib/api/buildings"
import { authOptions } from "@/lib/auth/options"
import { fetchSampleDataState } from "@/lib/api/sampleData"

import { BuildingsListClient } from "./BuildingsListClient"

export default async function BuildingsPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchBuildings(session.accessToken)

  // Mandatory onboarding: zero own (non-sample) buildings -> finish the wizard
  // first. /onboarding sends them back here once done, so the two never loop.
  if (result.ok && countOwnBuildings(result.data.buildings) === 0) {
    redirect("/onboarding")
  }

  const sampleState = await fetchSampleDataState(session.accessToken)
  const sampleEnabled = sampleState.ok ? sampleState.data.enabled : true

  return (
    <AppChrome
      breadcrumb={[{ label: "Buildings" }]}
      pageTitle="Buildings"
      subtitle={
        result.ok
          ? `${result.data.total} ${result.data.total === 1 ? "building" : "buildings"} in your portfolio`
          : "Could not load buildings"
      }
    >
      <SustainabilityMotif />
      <CitySkylineMotif />

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto">
        <div className="mb-4 flex items-center justify-between gap-3">
          <p className="text-xs text-text-faint">
            Sample buildings carry full demo data — useful for previewing the reports.
          </p>
          <SampleDataToggle initialEnabled={sampleEnabled} />
        </div>
        {!result.ok ? (
          <div className="rounded-lg border border-accent-red/30 bg-accent-red/5 p-6 text-text-primary">
            <div className="text-sm font-medium mb-1">
              Failed to load buildings
            </div>
            <div className="text-xs text-text-muted">{result.error}</div>
          </div>
        ) : result.data.buildings.length === 0 ? (
          <div className="rounded-lg border border-border-subtle bg-bg-elevated/30 p-8 text-center">
            <div className="text-sm text-text-primary mb-1">No buildings yet</div>
            <div className="text-xs text-text-muted">
              Your portfolio is empty. Buildings will appear here once added.
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {ownBuildingsAllPending(result.data.buildings) && (
              <DataPendingBanner />
            )}
            <BuildingsListClient buildings={result.data.buildings} />
          </div>
        )}
      </div>
    </AppChrome>
  )
}
