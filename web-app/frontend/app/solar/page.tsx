/**
 * /solar — dedicated solar detail page (Solar initiative C).
 *
 * Server component, auth-guarded. Renders generation/self-consumption charts
 * + summary from gold solar columns (via /solar/detail). Portfolio-wide by
 * default; a building slicer (?building_id) scopes it to one building.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { BuildingSlicer } from "@/components/BuildingSlicer"
import { FetchErrorNotice } from "@/components/FetchErrorNotice"
import { SolarMotif } from "@/components/motifs/SolarMotif"
import { authOptions } from "@/lib/auth/options"
import { fetchBuildings } from "@/lib/api/buildings"
import { fetchSolarDetail } from "@/lib/api/solar"
import { SolarDetail } from "@/components/solar/SolarDetail"

const SOLAR_ACCENT = "#F59E0B"

type PageProps = {
  searchParams: Promise<{ building_id?: string }>
}

export default async function SolarPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  const { building_id } = await searchParams
  const scoped = typeof building_id === "string" && building_id.length > 0

  const [result, buildingsResult] = await Promise.all([
    fetchSolarDetail(session.accessToken, scoped ? building_id : null),
    fetchBuildings(session.accessToken),
  ])

  // Only buildings with a Fabric id carry solar series; offer those in the slicer.
  const slicerBuildings = buildingsResult.ok
    ? buildingsResult.data.buildings
        .filter((b) => b.fabric_building_id)
        .map((b) => ({ id: b.fabric_building_id as string, name: b.name }))
    : []

  return (
    <AppChrome
      breadcrumb={[{ label: "Solar" }]}
      pageTitle="Solar"
      subtitle="On-site generation, self-consumption & performance"
      accentColor={SOLAR_ACCENT}
    >
      <SolarMotif />

      <div className="relative z-10 px-6 py-8 max-w-7xl mx-auto">
        {slicerBuildings.length > 0 && (
          <div className="mb-4 flex justify-end">
            <BuildingSlicer
              buildings={slicerBuildings}
              value={scoped ? building_id! : null}
            />
          </div>
        )}
        {!result.ok ? (
          <FetchErrorNotice error={result.error} label="solar data" />
        ) : (
          <SolarDetail data={result.data} />
        )}
      </div>
    </AppChrome>
  )
}
