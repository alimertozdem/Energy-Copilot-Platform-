/**
 * /solar — dedicated solar detail page (Solar initiative C).
 *
 * Server component, auth-guarded. Renders generation/self-consumption charts
 * + summary from gold_kpi_daily solar columns (via /solar/detail). No PBI embed.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { SolarMotif } from "@/components/motifs/SolarMotif"
import { authOptions } from "@/lib/auth/options"
import { fetchSolarDetail } from "@/lib/api/solar"
import { SolarDetail } from "@/components/solar/SolarDetail"

const SOLAR_ACCENT = "#F59E0B"

export default async function SolarPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const result = await fetchSolarDetail(session.accessToken)

  return (
    <AppChrome
      breadcrumb={[{ label: "Solar" }]}
      pageTitle="Solar"
      subtitle="On-site generation, self-consumption & performance"
      accentColor={SOLAR_ACCENT}
    >
      <SolarMotif />

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto">
        {!result.ok ? (
          <FetchErrorNotice error={result.error} label="solar data" />
        ) : (
          <SolarDetail data={result.data} />
        )}
      </div>
    </AppChrome>
  )
}
