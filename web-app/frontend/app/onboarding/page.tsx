/**
 * /onboarding — mandatory first-building wizard.
 *
 * Server component. Auth-guarded. If the user already has at least one OWN
 * (non-sample) building, they've onboarded → send them to /buildings. This is
 * the reverse of the guard on /buildings + /portfolio (0 own → /onboarding),
 * so the two never bounce a user in a loop.
 *
 * Standalone branded shell (not AppChrome): the user isn't "inside" the app
 * until they finish, so the authenticated nav would be misleading.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { authOptions } from "@/lib/auth/options"
import { countOwnBuildings, fetchBuildings } from "@/lib/api/buildings"

import { OnboardingWizard } from "./OnboardingWizard"

export default async function OnboardingPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  // Already onboarded? Skip the wizard.
  const result = await fetchBuildings(session.accessToken)
  if (result.ok && countOwnBuildings(result.data.buildings) > 0) {
    redirect("/buildings")
  }

  return <OnboardingWizard userName={session.user?.name ?? null} />
}
