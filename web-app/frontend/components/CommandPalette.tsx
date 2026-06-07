"use client"

/**
 * CommandPalette — global Cmd/Ctrl+K quick-jump.
 *
 * Bypasses the (necessarily compact) top nav: type to filter every destination,
 * arrow-keys to move, Enter to go. Mounted once in AppChrome so it's available on
 * every authenticated page. Portaled to <body> so it overlays everything.
 *
 * V1 = static page destinations (zero fetch → robust). Buildings could be added
 * later by loading /api/buildings.
 */
import { Search } from "lucide-react"
import { useRouter } from "next/navigation"
import { useCallback, useEffect, useMemo, useState } from "react"
import { createPortal } from "react-dom"

type Dest = { label: string; href: string; group: string; keywords?: string }

const DESTINATIONS: Dest[] = [
  { label: "Portfolio", href: "/portfolio", group: "Overview", keywords: "home dashboard kpi eui" },
  { label: "Buildings", href: "/buildings", group: "Overview", keywords: "assets list" },
  { label: "Decarbonisation", href: "/decarbonisation", group: "Insights", keywords: "macc co2 abatement carbon invest" },
  { label: "Actions", href: "/actions", group: "Insights", keywords: "recommendations measures payback" },
  { label: "Alerts", href: "/alerts", group: "Insights", keywords: "anomalies faults monitoring" },
  { label: "Solar", href: "/solar", group: "Insights", keywords: "pv generation yield" },
  { label: "Compliance", href: "/compliance", group: "Compliance", keywords: "meps crrem taxonomy esrs eu" },
  { label: "Financing", href: "/financing", group: "Compliance", keywords: "subsidy kfw bafa grant" },
  { label: "Residential", href: "/residential", group: "Segments", keywords: "units uvi hkvo tenants" },
  { label: "Partners", href: "/partners", group: "Segments", keywords: "consultant clients" },
  { label: "Connections", href: "/connections", group: "Setup", keywords: "devices sensors edge" },
  { label: "Copilot", href: "/copilot", group: "Tools", keywords: "ai assistant chat ask" },
  { label: "Glossary", href: "/glossary", group: "Tools", keywords: "terms definitions help" },
  { label: "Guided tour", href: "/tour", group: "Tools", keywords: "walkthrough demo intro" },
  { label: "Settings", href: "/settings", group: "Account", keywords: "billing org members profile" },
  { label: "Admin", href: "/admin", group: "Account", keywords: "platform founder queue" },
]

export function CommandPalette() {
  const router = useRouter()
  const [mounted, setMounted] = useState(false)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [active, setActive] = useState(0)

  useEffect(() => setMounted(true), [])

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setOpen((o) => !o)
      } else if (e.key === "Escape") {
        setOpen(false)
      }
    }
    function onOpenEvent() {
      setOpen(true)
    }
    window.addEventListener("keydown", onKey)
    window.addEventListener("el:open-command", onOpenEvent)
    return () => {
      window.removeEventListener("keydown", onKey)
      window.removeEventListener("el:open-command", onOpenEvent)
    }
  }, [])

  useEffect(() => {
    if (open) {
      setQuery("")
      setActive(0)
    }
  }, [open])

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return DESTINATIONS
    return DESTINATIONS.filter(
      (d) =>
        d.label.toLowerCase().includes(q) ||
        d.group.toLowerCase().includes(q) ||
        (d.keywords ?? "").includes(q)
    )
  }, [query])

  const go = useCallback(
    (href: string) => {
      setOpen(false)
      router.push(href)
    },
    [router]
  )

  function onInputKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setActive((a) => Math.min(a + 1, results.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActive((a) => Math.max(a - 1, 0))
    } else if (e.key === "Enter") {
      e.preventDefault()
      const hit = results[active]
      if (hit) go(hit.href)
    }
  }

  if (!mounted || !open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-[70] flex items-start justify-center pt-[12vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setOpen(false)} aria-hidden />
      <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-border-subtle bg-bg-elevated shadow-[0_20px_60px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-2.5 border-b border-border-subtle px-4 py-3">
          <Search size={16} className="shrink-0 text-text-faint" aria-hidden />
          {/* eslint-disable-next-line jsx-a11y/no-autofocus */}
          <input
            autoFocus
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setActive(0)
            }}
            onKeyDown={onInputKey}
            placeholder="Jump to… (type a page)"
            className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-faint outline-none"
          />
          <kbd className="rounded border border-border-subtle px-1.5 py-0.5 text-[10px] text-text-faint">esc</kbd>
        </div>
        <ul className="max-h-80 overflow-y-auto py-1">
          {results.length === 0 ? (
            <li className="px-4 py-6 text-center text-sm text-text-muted">No matches.</li>
          ) : (
            results.map((d, i) => (
              <li key={d.href}>
                <button
                  type="button"
                  onMouseEnter={() => setActive(i)}
                  onClick={() => go(d.href)}
                  className={`flex w-full items-center justify-between px-4 py-2 text-left text-sm transition-colors ${
                    i === active ? "bg-brand-emerald/10 text-text-primary" : "text-text-muted"
                  }`}
                >
                  <span>{d.label}</span>
                  <span className="text-[11px] text-text-faint">{d.group}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>,
    document.body
  )
}
