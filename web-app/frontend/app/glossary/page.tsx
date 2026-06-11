/**
 * /glossary — public reference page listing every domain term, grouped by
 * category. Standalone (no auth guard, no AppChrome) so it's linkable from the
 * authed top bar, the public /demo, and the landing page alike. Reads the same
 * source-of-truth content module the InfoTip tooltips use (lib/glossary).
 *
 * Design: shares the landing's premium language — bg-radial-emerald-glow +
 * dot-grid + top pulse glow, LogoCard header, Space Grotesk (font-display)
 * heading, ping-dot pill, el-fade-up entrance, hover-lift term cards.
 */
import Link from "next/link"
import type { Metadata } from "next"

import { LogoCard } from "@/app/components/LogoCard"
import {
  GLOSSARY,
  GLOSSARY_CATEGORY_ORDER,
  CONFIDENCE_NOTE,
  type GlossaryCategory,
} from "@/lib/glossary"

export const metadata: Metadata = {
  title: "Glossary",
  description:
    "Plain-language definitions of the energy and sustainability terms used across EnergyLens — EUI, EPC, performance ratio, CRREM and more.",
}

const CATEGORY_BLURB: Record<GlossaryCategory, string> = {
  Portfolio: "Building performance & monitoring",
  Solar: "On-site generation metrics",
  Financial: "Investment & returns",
  Strategy: "Decarbonization & climate risk",
  Compliance: "Regulatory standards & disclosure",
}

export default function GlossaryPage() {
  const entries = Object.values(GLOSSARY)

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden bg-bg-base bg-radial-emerald-glow text-text-primary">
      <div className="pointer-events-none fixed inset-0 bg-dot-grid opacity-25" aria-hidden />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[420px] animate-pulse"
        aria-hidden
        style={{ background: "radial-gradient(55% 80% at 50% -5%, rgba(29,158,117,0.18), transparent 70%)" }}
      />

      <header className="relative z-10 border-b border-border-subtle bg-bg-elevated/60 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
          <LogoCard iconSize={44} />
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/demo" className="text-text-muted hover:text-text-primary transition-colors">
              Demo
            </Link>
            <Link href="/pricing" className="hidden sm:inline text-text-muted hover:text-text-primary transition-colors">
              Pricing
            </Link>
            <Link
              href="/portfolio"
              className="inline-flex items-center rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-sm font-medium text-brand-emerald hover:bg-brand-emerald/10 transition-colors"
            >
              Open app →
            </Link>
          </nav>
        </div>
      </header>

      <main id="main-content" className="relative z-10 flex-1 max-w-5xl w-full mx-auto px-6 py-12">
        <div className="el-fade-up max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-emerald/40 bg-brand-emerald/10 px-3 py-1 text-xs font-medium text-brand-emerald">
            <span className="relative inline-flex h-1.5 w-1.5">
              <span className="absolute inset-0 animate-ping rounded-full bg-brand-emerald opacity-60" />
              <span className="relative h-1.5 w-1.5 rounded-full bg-brand-emerald" />
            </span>
            Reference
          </span>
          <h1 className="font-display mt-5 text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
            Glossary
          </h1>
          <p className="mt-4 text-text-muted max-w-prose sm:text-lg">
            Plain-language definitions of the energy and sustainability terms used
            across EnergyLens. Numeric guides are rules of thumb — real targets
            vary by building type and climate.
          </p>
        </div>

        <div className="mt-12 space-y-10">
          {GLOSSARY_CATEGORY_ORDER.map((cat) => {
            const items = entries.filter((e) => e.category === cat)
            if (items.length === 0) return null
            return (
              <section key={cat}>
                <div className="flex items-baseline gap-2 mb-4">
                  <h2 className="text-xs uppercase tracking-[0.14em] text-brand-emerald font-semibold">
                    {cat}
                  </h2>
                  <span className="text-xs text-text-faint">
                    {CATEGORY_BLURB[cat]}
                  </span>
                </div>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {items.map((e) => (
                    <div
                      key={e.label}
                      className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5 transition-all hover:-translate-y-1 hover:border-brand-emerald/50"
                    >
                      <dt className="text-sm font-semibold text-text-primary">
                        {e.label}
                      </dt>
                      <dd className="mt-1.5 text-sm text-text-muted leading-relaxed">
                        {e.full}
                      </dd>
                      {e.method && (
                        <div className="mt-3 border-t border-border-subtle/60 pt-3">
                          <p className="text-[10px] font-semibold uppercase tracking-wide text-brand-emerald/80">
                            How it&rsquo;s calculated
                          </p>
                          <p className="mt-1 text-sm text-text-muted">{e.method}</p>
                          {e.assumptions && e.assumptions.length > 0 && (
                            <ul className="mt-1.5 space-y-0.5">
                              {e.assumptions.map((a) => (
                                <li key={a} className="text-xs text-text-faint">&bull; {a}</li>
                              ))}
                            </ul>
                          )}
                          {e.confidence && (
                            <p className="mt-2 text-xs italic text-text-faint">
                              {CONFIDENCE_NOTE[e.confidence]}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </dl>
              </section>
            )
          })}
        </div>
      </main>

      <footer className="relative z-10 border-t border-border-subtle/60 px-6 py-6">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-text-faint">
          <span>EnergyLens · Smart energy for smart buildings</span>
          <Link href="/demo" className="hover:text-brand-emerald transition-colors">Live demo</Link>
          <Link href="/pricing" className="hover:text-brand-emerald transition-colors">Pricing</Link>
        </div>
      </footer>
    </div>
  )
}
