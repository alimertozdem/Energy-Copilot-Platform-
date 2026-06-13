/**
 * /compliance/vsme-editor — write the VSME Basic Module qualitative narrative.
 *
 * Server component, auth-guarded. Loads the org's saved narrative (shared with ESRS,
 * keyed by datapoint_key; VSME uses B1, B2, B4–B11) and hands it to the reusable
 * NarrativeEditor. B3 (energy & GHG) is auto-filled in the report, not edited here.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { NarrativeEditor } from "@/components/compliance/NarrativeEditor"
import { fetchEsrsNarrativeServer, narrativeMap } from "@/lib/api/esrsNarrative"
import { authOptions } from "@/lib/auth/options"
import { VSME_ALL_NARRATIVE } from "@/lib/vsme/vsmeDisclosures"

export const dynamic = "force-dynamic"

export default async function VsmeEditorPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }
  const res = await fetchEsrsNarrativeServer(session.accessToken)
  const saved = res.ok ? narrativeMap(res.data.items) : {}
  const loadError = res.ok ? null : res.error
  return (
    <NarrativeEditor
      disclosures={VSME_ALL_NARRATIVE}
      saved={saved}
      loadError={loadError}
      heading="VSME — narrative editor"
      intro="Write the VSME narrative disclosures — Basic Module (B1, B2, B4–B11) and, for the Comprehensive level, C1–C9. B3 (energy & GHG) is auto-filled in the report from your metered data; the Comprehensive C3/C4 also draw on it. Each box starts from a guided draft that prompts for the figures to provide — edit it, then save. Saved text appears in the report."
      asksLabel="VSME asks"
      reportHref="/compliance/vsme-report"
      reportLabel="Open VSME report →"
    />
  )
}
