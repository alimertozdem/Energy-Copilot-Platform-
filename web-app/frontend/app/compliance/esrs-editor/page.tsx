/**
 * /compliance/esrs-editor — write the ESRS E-1 qualitative narrative.
 *
 * Server component, auth-guarded. Loads the org's saved narrative (falling back to
 * boilerplate in the client) and hands it to the editor. The quantitative datapoints
 * (E1-5/E1-6) are auto-filled in the report and are not edited here.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { fetchEsrsNarrativeServer, narrativeMap } from "@/lib/api/esrsNarrative"
import { authOptions } from "@/lib/auth/options"

import { EsrsEditorClient } from "./EsrsEditorClient"

export const dynamic = "force-dynamic"

export default async function EsrsEditorPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }
  const res = await fetchEsrsNarrativeServer(session.accessToken)
  const saved = res.ok ? narrativeMap(res.data.items) : {}
  const loadError = res.ok ? null : res.error
  return <EsrsEditorClient saved={saved} loadError={loadError} />
}
