"use client"

/**
 * LockedReportPreview -- shown in place of the embed when a report page's
 * required module is not enabled for the building.
 *
 * Pattern: lock badge + "connect X to unlock" + contact CTA. Mirrors the
 * SubscriptionCard upgrade CTA (mailto:alimert@energylens.eu). This component
 * never renders the locked data -- page visibility is a web-app concern (the
 * module layer of the 3-layer access model), not Power BI RLS.
 */
import { Lock } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { ReportPageMeta } from "@/lib/config/reportPages"

/** Friendly copy per gated module. Falls back to a generic message. */
const MODULE_COPY: Record<string, { system: string; blurb: string }> = {
  iot: {
    system: "live IoT sensors",
    blurb:
      "Real-time zone comfort, CO2 and sub-metered power need connected IoT sensors (BACnet / Modbus / MQTT).",
  },
  battery: {
    system: "a battery system",
    blurb:
      "Dispatch simulation, ROI and chemistry comparison need a battery system connected to this building.",
  },
}

type LockedReportPreviewProps = {
  page: ReportPageMeta
  buildingName: string
}

export function LockedReportPreview({
  page,
  buildingName,
}: LockedReportPreviewProps) {
  const copy = MODULE_COPY[page.requiredModule] ?? {
    system: "an additional module",
    blurb:
      "This report requires a module that is not enabled for this building.",
  }
  const subject = encodeURIComponent(
    `EnergyLens: enable ${page.title} for ${buildingName}`
  )

  return (
    <div className="flex h-full w-full items-center justify-center p-8">
      <div
        className="relative w-full max-w-md overflow-hidden rounded-2xl border bg-bg-elevated/70 p-8 text-center backdrop-blur-sm"
        style={{ borderColor: `${page.accent}40` }}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background: `radial-gradient(circle at 50% 0%, ${page.accent}1A, transparent 60%)`,
          }}
        />
        <div className="relative">
          <span
            className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full"
            style={{ backgroundColor: `${page.accent}1A`, color: page.accent }}
          >
            <Lock className="h-5 w-5" aria-hidden />
          </span>
          <h2 className="text-lg font-semibold text-text-primary">
            {page.title} is locked
          </h2>
          <p className="mt-1 text-sm text-text-muted">
            Connect {copy.system} to unlock this report for{" "}
            <span className="text-text-primary">{buildingName}</span>.
          </p>
          <p className="mt-3 text-xs leading-relaxed text-text-faint">
            {copy.blurb}
          </p>
          <Button asChild size="sm" className="mt-6">
            <a href={`mailto:alimert@energylens.eu?subject=${subject}`}>
              Contact us to enable
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}
