/**
 * /buildings/import — portfolio bulk import (CSV).
 *
 * Server component, auth-guarded. For portfolio managers (Hausverwaltung) who
 * need to stand up 20–40 buildings at once instead of running the single-building
 * wizard each time. The client parses the CSV in the browser, previews + lets the
 * user fix rows, then commits via POST /buildings/bulk.
 */
import { redirect } from "next/navigation"
import { getServerSession } from "next-auth"

import { AppChrome } from "@/components/AppChrome"
import { authOptions } from "@/lib/auth/options"

import { ImportClient } from "./ImportClient"

export const metadata = { title: "Import buildings" }

export default async function BuildingsImportPage() {
  const session = await getServerSession(authOptions)
  if (!session?.accessToken) {
    redirect("/")
  }

  return (
    <AppChrome
      breadcrumb={[{ label: "Buildings", href: "/buildings" }, { label: "Import" }]}
      pageTitle="Import a portfolio"
      subtitle="Add many buildings at once from a CSV"
    >
      <div className="relative z-10 px-6 py-8 max-w-5xl mx-auto">
        <ImportClient />
      </div>
    </AppChrome>
  )
}
