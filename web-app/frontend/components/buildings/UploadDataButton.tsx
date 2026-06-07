"use client"

/**
 * UploadDataButton — a small client wrapper that opens the ConsumptionUploadModal.
 *
 * Drop it onto any building's detail page (server component) and pass that one
 * building: `<UploadDataButton buildings={[building]} />`. With a single owned
 * building the modal auto-scopes to it (no building picker), so uploading a
 * baseline happens right where the user is looking — on the building, not on the
 * portfolio-wide list.
 */
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Upload } from "lucide-react"

import type { Building } from "@/lib/api/buildings"
import { ConsumptionUploadModal } from "@/components/buildings/ConsumptionUploadModal"

export function UploadDataButton({
  buildings,
  label = "Upload data",
  variant = "outline",
}: {
  buildings: Building[]
  label?: string
  /** "solid" for a primary CTA (empty state); "outline" for a toolbar button. */
  variant?: "outline" | "solid"
}) {
  const [open, setOpen] = useState(false)
  const router = useRouter()

  const cls =
    variant === "solid"
      ? "inline-flex items-center gap-1.5 rounded-md bg-brand-emerald px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-deep"
      : "inline-flex items-center gap-1.5 rounded-md border border-border-subtle px-3 py-1.5 text-sm text-text-muted transition-colors hover:border-brand-emerald/60 hover:text-brand-emerald"

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className={cls}>
        <Upload className="h-3.5 w-3.5" />
        <span>{label}</span>
      </button>
      {open && (
        <ConsumptionUploadModal
          buildings={buildings}
          onClose={() => setOpen(false)}
          onUploaded={() => router.refresh()}
        />
      )}
    </>
  )
}
