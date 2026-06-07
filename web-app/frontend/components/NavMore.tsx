"use client"

/**
 * NavMore — a small "More ⋯" overflow dropdown for the primary nav.
 *
 * Holds the lower-traffic destinations (Connections, Financing, Partners) so the
 * top bar stays uncrowded. Routes are unchanged — this is purely a presentation
 * declutter. Closes on outside-click or after picking an item.
 */
import { MoreHorizontal } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useRef, useState } from "react"

import { cn } from "@/lib/utils"

const MORE_ITEMS: { href: string; label: string }[] = [
  { href: "/connections", label: "Connections" },
  { href: "/financing", label: "Financing" },
  { href: "/partners", label: "Partners" },
]

export function NavMore() {
  const pathname = usePathname() ?? ""
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const activeHere = MORE_ITEMS.some((i) => pathname.startsWith(i.href))

  useEffect(() => {
    if (!open) return
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onDoc)
    return () => document.removeEventListener("mousedown", onDoc)
  }, [open])

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className={cn(
          "inline-flex items-center gap-1 px-3 py-1.5 rounded-md text-sm transition-colors",
          activeHere
            ? "bg-brand-emerald/10 text-brand-emerald"
            : "text-text-muted hover:text-text-primary hover:bg-white/5"
        )}
      >
        More <MoreHorizontal size={15} aria-hidden />
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-1 w-44 rounded-md border border-border-subtle bg-bg-elevated py-1 shadow-[0_8px_24px_rgba(0,0,0,0.4)] z-50"
        >
          {MORE_ITEMS.map((i) => (
            <Link
              key={i.href}
              href={i.href}
              role="menuitem"
              onClick={() => setOpen(false)}
              aria-current={pathname.startsWith(i.href) ? "page" : undefined}
              className={cn(
                "block px-3 py-2 text-sm transition-colors",
                pathname.startsWith(i.href)
                  ? "text-brand-emerald"
                  : "text-text-muted hover:text-text-primary hover:bg-white/5"
              )}
            >
              {i.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
