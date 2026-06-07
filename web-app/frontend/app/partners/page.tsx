/**
 * /partners -- consultant (partner) relationship management.
 *
 * Server component: getServerSession -> token -> fetchPartnerLinks -> PartnersShell,
 * wrapped in AppChrome (top bar + nav). Visible to any authenticated org; lists links
 * touching the caller's org (as partner and/or client). The invite form is partner-only
 * -- enforced by the backend (403 for non-partner orgs), surfaced inline.
 */
import { getServerSession } from "next-auth"
import { redirect } from "next/navigation"

import { AppChrome } from "@/components/AppChrome"
import { PartnersShell } from "@/components/partners/PartnersShell"
import { fetchPartnerLinks } from "@/lib/api/partners"
import { authOptions } from "@/lib/auth/options"

const PARTNERS_ACCENT = "#1D9E75"

export default async function PartnersPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchPartnerLinks(session.accessToken)
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
      <PartnersShell
        links={result.ok ? result.data.links : null}
        error={result.ok ? null : result.error}
      />
    </AppChrome>
  )
}
