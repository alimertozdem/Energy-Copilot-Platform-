"use client"

/**
 * EsrsEditorClient — thin wrapper that renders the shared NarrativeEditor with the
 * ESRS E-1 disclosure list. The editor UI + save logic live in NarrativeEditor; the
 * VSME editor uses the same component with the VSME disclosure list.
 */
import { NarrativeEditor } from "@/components/compliance/NarrativeEditor"
import { E1_NARRATIVE } from "@/lib/esrs/e1Disclosures"

export function EsrsEditorClient({
  saved,
  loadError,
}: {
  saved: Record<string, string>
  loadError: string | null
}) {
  return (
    <NarrativeEditor
      disclosures={E1_NARRATIVE}
      saved={saved}
      loadError={loadError}
      heading="ESRS E-1 — narrative editor"
      intro="Write the qualitative disclosures (E1-1…E1-4, E1-7…E1-9). The quantitative datapoints (E1-5 energy, E1-6 GHG) are auto-filled in the report from your metered data. Each box starts from a guided draft — edit it to reflect your company, then save. Saved text appears in the report."
      asksLabel="ESRS asks"
      reportHref="/compliance/esrs-report"
      reportLabel="Open ESRS E-1 report →"
    />
  )
}
