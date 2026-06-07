/**
 * /pilot — public "request a pilot" page (no auth).
 *
 * A visitor (including someone who wants to pilot their own building) submits
 * interest; it lands in the founder's /admin pilot queue. Standalone brand
 * chrome like /demo — not the authenticated AppChrome.
 */
import type { Metadata } from "next"
import Link from "next/link"

import { LogoCard } from "@/app/components/LogoCard"
import { PilotForm } from "@/components/pilot/PilotForm"

export const metadata: Metadata = {
  title: "Request a pilot · EnergyLens",
  description:
    "Run an EnergyLens pilot on your own buildings — energy intelligence, fault detection and EU-compliance, no new hardware.",
}

export default async function PilotPage({
  searchParams,
}: {
  searchParams: Promise<{ source?: string }>
}) {
  const { source } = await searchParams

  return (
    <main className="relative min-h-screen overflow-hidden bg-bg-base bg-radial-emerald-glow">
      <div className="pointer-events-none fixed inset-0 bg-dot-grid opacity-25" aria-hidden />

      <header className="relative z-10 mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
        <Link href="/">
          <LogoCard iconSize={40} />
        </Link>
        <Link href="/demo" className="text-sm text-text-muted transition-colors hover:text-text-primary">
          Live demo
        </Link>
      </header>

      <section className="relative z-10 mx-auto max-w-2xl px-6 py-10">
        <h1 className="font-display text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
          Pilot EnergyLens on your buildings
        </h1>
        <p className="mt-3 text-base leading-relaxed text-text-muted">
          Start from a single utility bill — no new hardware. We&rsquo;ll set up your
          portfolio KPIs, fault detection, decarbonisation plan and EU-compliance view,
          and walk it with you. Tell us a little and we&rsquo;ll be in touch.
        </p>

        <div className="mt-8">
          <PilotForm source={source} />
        </div>
      </section>
    </main>
  )
}
