/**
 * /demo -- public marketing page.
 *
 * Server component. No auth — anyone hitting this URL gets the page.
 * Loads the 6-building demo portfolio from /demo/buildings and hands it
 * to <DemoShell/> which owns the interactive UI + embed.
 *
 * Why a server component for the initial fetch?
 *   * Faster TTFB (no client-side waterfall before first paint).
 *   * BACKEND_URL stays a server-only env variable.
 *   * Search engines see real building names in the HTML, helping SEO for
 *     EnergyLens marketing pages.
 *
 * Error fallback:
 *   * If the backend is down we still render the shell with an empty list +
 *     a friendly notice. Better than a stack trace on a public URL.
 */
import type { Metadata } from "next"

import { fetchDemoBuildings } from "@/lib/api/demo"

import { DemoShell } from "./DemoShell"

export const dynamic = "force-dynamic" // never statically cache demo numbers

// Title flows through the root template -> "Live Demo · EnergyLens". The OG +
// Twitter image are inherited from the site-wide app/opengraph-image card.
export const metadata: Metadata = {
  title: "Live Demo",
  description:
    "Explore EnergyLens with six sample commercial buildings across Europe — portfolio KPIs, anomaly alerts, and battery/solar scenarios. No signup required.",
  alternates: { canonical: "/demo" },
  openGraph: {
    type: "website",
    url: "/demo",
    title: "EnergyLens — Live Demo",
    description:
      "Six sample commercial buildings across Europe. Explore portfolio KPIs, anomaly alerts, and battery/solar ROI — no signup required.",
  },
  twitter: {
    card: "summary_large_image",
    title: "EnergyLens — Live Demo",
    description:
      "Six sample commercial buildings. Explore the live dashboard — no signup required.",
  },
}

export default async function DemoPage() {
  const result = await fetchDemoBuildings()
  const buildings = result.ok ? result.data.buildings : []
  const loadError = result.ok ? null : result.error

  return <DemoShell buildings={buildings} loadError={loadError} />
}
