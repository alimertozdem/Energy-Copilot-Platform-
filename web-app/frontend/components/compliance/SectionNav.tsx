"use client"

import * as React from "react"

export type NavSection = { id: string; label: string }

/**
 * SectionNav — sticky in-page navigator for the /compliance sections.
 *
 * Renders a row of pills; clicking smooth-scrolls to the matching <section id>.
 * An IntersectionObserver highlights the section currently in view (scrollspy).
 * Client component (needs scroll APIs). The page passes only the sections that
 * actually rendered, so a pill never points at a missing anchor.
 */
export function SectionNav({ sections }: { sections: NavSection[] }) {
  const [active, setActive] = React.useState<string | null>(
    sections[0]?.id ?? null
  )

  React.useEffect(() => {
    const els = sections
      .map((s) => document.getElementById(s.id))
      .filter((el): el is HTMLElement => el != null)
    if (els.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        const top = visible[0]
        if (top) setActive(top.target.id)
      },
      { rootMargin: "-96px 0px -55% 0px", threshold: 0 }
    )
    els.forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [sections])

  if (sections.length <= 1) return null

  function handleClick(e: React.MouseEvent<HTMLAnchorElement>, id: string) {
    e.preventDefault()
    const el = document.getElementById(id)
    if (!el) return
    el.scrollIntoView({ behavior: "smooth", block: "start" })
    setActive(id)
    history.replaceState(null, "", `#${id}`)
  }

  return (
    <nav
      aria-label="Compliance sections"
      className="sticky top-0 z-30 py-2.5 bg-bg-elevated/85 backdrop-blur-md rounded-b-xl"
    >
      <div className="flex gap-2 overflow-x-auto">
        {sections.map((s) => {
          const isActive = s.id === active
          return (
            <a
              key={s.id}
              href={`#${s.id}`}
              onClick={(e) => handleClick(e, s.id)}
              aria-current={isActive ? "true" : undefined}
              className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-emerald/15 text-brand-emerald border border-brand-emerald/40"
                  : "border border-border-subtle text-text-muted hover:text-text-primary hover:bg-white/5"
              }`}
            >
              {s.label}
            </a>
          )
        })}
      </div>
    </nav>
  )
}
