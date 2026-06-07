/**
 * /residence — the resident (tenant) view. PUBLIC route, lightweight React,
 * NO Power BI embed.
 *
 * Identity (separate from NextAuth): the resident session cookie `el_resident`
 * (set by the magic-link flow: /residence/enter -> /api/residence/session). For
 * dev/testing the ?resident= query param still works when the backend has
 * RESIDENT_DEV_MODE=1 (the P4-1 override). The cookie wins when both are present.
 *
 * A resident sees ONLY their own unit + an anonymized building benchmark — the
 * scope is enforced server-side in resolve_resident_scope (tenancy window).
 */
import type { Metadata } from "next"
import { cookies } from "next/headers"

import { fetchResidenceSummary } from "@/lib/api/residence"

import { ResidenceShell } from "./ResidenceShell"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "My Home Energy",
  description:
    "Your apartment's monthly energy use, efficiency rating, and shared-area share.",
  robots: { index: false, follow: false },
}

export default async function ResidencePage({
  searchParams,
}: {
  searchParams: Promise<{ resident?: string }>
}) {
  const { resident } = await searchParams
  const devResidentId = resident?.trim() || null

  const cookieStore = await cookies()
  const token = cookieStore.get("el_resident")?.value || null

  const hasIdentity = Boolean(token || devResidentId)
  if (!hasIdentity) {
    return <ResidenceShell summary={null} loadError={null} hasIdentity={false} residentId={null} />
  }

  const result = await fetchResidenceSummary({ token, devResidentId })
  return (
    <ResidenceShell
      summary={result.ok ? result.data : null}
      loadError={result.ok ? null : result.error}
      hasIdentity
      residentId={token ? null : devResidentId}
    />
  )
}
