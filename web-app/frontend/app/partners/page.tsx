/**
 * /partners -- consultant (partner) relationship management + multi-client cockpit.
 *
 * Server component: getServerSession -> token -> fetchPartnerLinks + fetchPartnerOverview
 * -> PartnerOverview (cockpit, partner orgs only) + PartnersShell (lifecycle actions),
 * wrapped in AppChrome. The invite form is partner-only (enforced by the backend).
 */
import { getServerSession } from "next-auth"
import { redirect } from "next/navigation"

import { AppChrome } from "@/components/AppChrome"
import { PartnerOverview } from "@/components/partners/PartnerOverview"
import { PartnersShell } from "@/components/partners/PartnersShell"
import { fetchPartnerLinks, fetchPartnerOverview } from "@/lib/api/partners"
import { authOptions } from "@/lib/auth/options"

const PARTNERS_ACCENT = "#1D9E75"

export default async function PartnersPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const [result, overview] = await Promise.all([
    fetchPartnerLinks(session.accessToken),
    fetchPartnerOverview(session.accessToken),
  ])
  const count = result.ok ? result.data.links.length : 0

  return (
    <AppChrome
      breadcrumb={[{ label: "Partners" }]}
      pageTitle="Partners"
      subtitle={
        result.ok
          ? `${count} ${count === 1 ? "relationship" : "relationships"}`
          : "Consultant relationships"
      }
      accentColor={PARTNERS_ACCENT}
    >
      {overview.ok && overview.data.clients.length > 0 && (
        <div className="mx-auto max-w-4xl px-4 pt-8">
          <PartnerOverview overview={overview.data} />
        </div>
      )}
      <PartnersShell
        links={result.ok ? result.data.links : null}
        error={result.ok ? null : result.error}
      />
    </AppChrome>
  )
}
