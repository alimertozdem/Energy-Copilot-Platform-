/**
 * /tour — guided product tour (public presentation spine for demos).
 *
 * Public + no auth guard so it works on any machine in front of an audience.
 * Self-contained narrative (no data fetch), so it never breaks mid-demo. The
 * "Open live →" links inside open the real pages (which require auth) in a new
 * tab when the presenter wants to show real data.
 */
import type { Metadata } from "next"

import { GuidedTour } from "@/components/tour/GuidedTour"

export const metadata: Metadata = {
  title: "Guided tour · EnergyLens",
  description: "A guided walkthrough of the EnergyLens energy-intelligence platform.",
  robots: { index: false, follow: false },
}

export default function TourPage() {
  return <GuidedTour />
}
