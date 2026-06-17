/**
 * /financing — portfolio subsidy-capture (Financing bridge V1, lean).
 *
 * Server component, auth-guarded. Maps the recommendation catalog (/actions) to
 * indicative KfW/BAFA subsidies and a downloadable application pack. Stateless —
 * no new backend, reuses fetchActions. Support, not advice (see FinancingView).
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { FinancingView } from "@/components/financing/FinancingView"
import { fetchFinancingSummary } from "@/lib/api/financing"
import { authOptions } from "@/lib/auth/options"

export const dynamic = "force-dynamic"

const ACCENT = "#534AB7"

export default async function FinancingPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchFinancingSummary(session.accessToken)

  return (
    <AppChrome
      breadcrumb={[{ label: "Financing" }]}
      pageTitle="Financing & subsidies"
      subtitle="Indicative subsidy capture across your portfolio"
      accentColor={ACCENT}
    >
      <div className="relative z-10 mx-auto max-w-7xl px-6 py-8">
        {!result.ok ? (
          <FetchErrorNotice error={result.error} label="recommendations" />
        ) : (
          <FinancingView summary={result.data} />
        )}
      </div>
    </AppChrome>
  )
}
