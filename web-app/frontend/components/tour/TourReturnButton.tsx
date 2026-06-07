"use client"

/**
 * TourReturnButton — a floating "← Back to tour" affordance.
 *
 * When the guided tour launches a live page (it sets sessionStorage
 * `el_tour_from=1` and remembers its step), this button appears on the live page
 * so the visitor can hop straight back into the tour where they left off. Mounted
 * once in AppChrome (which wraps every "Open live" target). Hidden otherwise.
 */
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"

export function TourReturnButton() {
  const pathname = usePathname()
  const [show, setShow] = useState(false)

  useEffect(() => {
    try {
      const active = sessionStorage.getItem("el_tour_from") === "1"
      setShow(active && !(pathname ?? "").startsWith("/tour"))
    } catch {
      setShow(false)
    }
  }, [pathname])

  if (!show) return null

  return (
    <Link
      href="/tour"
      className="fixed bottom-5 left-5 z-50 inline-flex items-center gap-2 rounded-full border border-brand-emerald/50 bg-bg-elevated/90 px-4 py-2 text-sm font-medium text-brand-emerald shadow-[0_8px_24px_rgba(0,0,0,0.4)] backdrop-blur transition-colors hover:bg-brand-emerald/10"
    >
      <ArrowLeft size={15} /> Back to tour
    </Link>
  )
}
