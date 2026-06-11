/**
 * /pricing — public plans page.
 *
 * Server component, no auth (a public marketing surface like /demo). Mirrors
 * the tier model used by billing (free / basic / monitor / enterprise). CTAs
 * route to /signup — a visitor creates an account, then upgrades self-serve in
 * Settings -> Subscription (Stripe Checkout). Enterprise is "contact sales".
 *
 * NOTE: prices below follow docs/strategy/pricing-model-v2.md (the authoritative
 * spec). The live price lives in Stripe; per-building automation is v1.1 (see doc).
 *
 * Design: shares the landing's premium language — bg-radial-emerald-glow +
 * dot-grid + top pulse glow, Space Grotesk (font-display) headings, ping-dot
 * pill, el-fade-up entrance, hover-lift cards, glow-shadow CTAs, trust strip.
 */
import type { Metadata } from "next"
import Link from "next/link"
import { Check } from "lucide-react"

import { LogoCard } from "@/app/components/LogoCard"
import { cn } from "@/lib/utils"

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "EnergyLens plans — from a free single-workspace tier to live IoT monitoring, battery & solar simulation, and an AI energy copilot. Built on Microsoft Fabric, EU-hosted.",
  alternates: { canonical: "/pricing" },
  openGraph: {
    type: "website",
    url: "/pricing",
    title: "EnergyLens — Pricing",
    description:
      "Start free, upgrade as your portfolio grows. Live IoT monitoring, battery & solar ROI, and an AI energy copilot on Microsoft Fabric.",
  },
}

type Plan = {
  id: string
  name: string
  price: string
  cadence?: string
  annual?: string
  blurb: string
  features: string[]
  cta: { label: string; href: string }
  featured?: boolean
}

const PLANS: Plan[] = [
  {
    id: "free",
    name: "Free",
    price: "€0",
    cadence: "forever",
    blurb: "Core dashboards for a single workspace.",
    features: [
      "1 building / workspace",
      "Portfolio KPIs & EUI benchmarking",
      "PDF report export",
      "Community support",
    ],
    cta: { label: "Get started", href: "/signup" },
  },
  {
    id: "basic",
    name: "Basic",
    price: "€99",
    cadence: "/mo",
    annual: "or €1,010/yr — save 15%",
    blurb: "Portfolio analytics across multiple buildings.",
    features: [
      "3 buildings included, then €35 each / mo",
      "Anomaly detection & alerts",
      "Recommendations tracking",
      "Email support",
    ],
    cta: { label: "Start with Basic", href: "/signup" },
  },
  {
    id: "monitor",
    name: "Monitor",
    price: "€299",
    cadence: "/mo",
    annual: "or €3,050/yr — save 15%",
    blurb: "Live operations + investment decision support.",
    features: [
      "5 buildings included, then €60 each / mo",
      "Everything in Basic",
      "Live IoT monitoring (BACnet / Modbus / MQTT)",
      "Battery & solar ROI simulation",
      "AI energy copilot",
    ],
    cta: { label: "Start with Monitor", href: "/signup" },
    featured: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    blurb: "Full platform, priority support, custom SLAs.",
    features: [
      "Unlimited buildings",
      "SSO & custom data isolation",
      "Priority support + SLA",
      "Onboarding & integrations",
    ],
    cta: {
      label: "Contact sales",
      href: "mailto:alimert@energylens.eu?subject=EnergyLens%20Enterprise%20plan",
    },
  },
]

const RESIDENTIAL_PLANS: Plan[] = [
  {
    id: "residential",
    name: "Residential",
    price: "€49",
    cadence: "/building/mo + €3/unit",
    blurb: "Per-unit heating insight + the monthly tenant statement.",
    features: [
      "Per-unit heating & hot-water EUI + EPC band",
      "HKVO common-area split (70/30)",
      "Monthly consumption statements (UVI / EED)",
      "Resident accounts included free",
    ],
    cta: { label: "Start with Residential", href: "/signup" },
  },
  {
    id: "residential-enterprise",
    name: "Residential Enterprise",
    price: "Custom",
    blurb: "For large Wohnungsunternehmen — volume pricing + SEPA / invoice.",
    features: [
      "Volume per-unit pricing",
      "SEPA / invoice billing",
      "Bulk resident onboarding",
      "Onboarding & integrations",
    ],
    cta: {
      label: "Contact sales",
      href: "mailto:alimert@energylens.eu?subject=EnergyLens%20Residential%20plan",
    },
  },
]

const TRUST = [
  { label: "Microsoft Fabric", dot: "bg-brand-emerald" },
  { label: "EU-hosted", dot: "bg-accent-cyan" },
  { label: "Stripe billing", dot: "bg-accent-purple" },
  { label: "Cancel anytime", dot: "bg-accent-yellow" },
]

export default function PricingPage() {
  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden bg-bg-base bg-radial-emerald-glow">
      <div className="pointer-events-none fixed inset-0 bg-dot-grid opacity-25" aria-hidden />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[420px] animate-pulse"
        aria-hidden
        style={{ background: "radial-gradient(55% 80% at 50% -5%, rgba(29,158,117,0.18), transparent 70%)" }}
      />

      <header className="relative z-10 border-b border-border-subtle bg-bg-elevated/60 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
          <LogoCard iconSize={44} />
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/demo" className="text-text-muted hover:text-text-primary transition-colors">
              Demo
            </Link>
            <Link
              href="/login"
              className="hidden sm:inline text-text-muted hover:text-text-primary transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center rounded-md bg-brand-emerald px-3.5 py-2 text-sm font-semibold text-bg-base shadow-[0_0_18px_rgba(16,185,129,0.35)] hover:bg-brand-emerald/90 transition-colors"
            >
              Sign Up Free
            </Link>
          </nav>
        </div>
      </header>

      <main id="main-content" className="relative z-10 flex-1 w-full max-w-6xl mx-auto px-6 py-12">
        <div className="el-fade-up text-center mb-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-emerald/40 bg-brand-emerald/10 px-3 py-1 text-xs font-medium text-brand-emerald">
            <span className="relative inline-flex h-1.5 w-1.5">
              <span className="absolute inset-0 animate-ping rounded-full bg-brand-emerald opacity-60" />
              <span className="relative h-1.5 w-1.5 rounded-full bg-brand-emerald" />
            </span>
            Transparent pricing · no hidden fees
          </span>
          <h1 className="font-display mt-5 text-3xl sm:text-5xl font-bold tracking-tight text-text-primary">
            Plans &amp; pricing
          </h1>
          <p className="mt-4 max-w-2xl mx-auto text-text-muted sm:text-lg">
            Start free, upgrade as your portfolio grows. Pay monthly or annually
            (save 15%); larger portfolios scale per building. Every plan runs on
            Microsoft Fabric and is EU-hosted.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-stretch">
          {PLANS.map((p) => (
            <div
              key={p.id}
              className={cn(
                "relative flex flex-col rounded-xl border p-6 transition-all hover:-translate-y-1",
                p.featured
                  ? "border-brand-emerald/50 bg-brand-emerald/[0.06] shadow-[0_0_30px_rgba(29,158,117,0.15)] hover:shadow-[0_0_40px_rgba(29,158,117,0.25)]"
                  : "border-border-subtle bg-bg-elevated/40 hover:border-brand-emerald/50"
              )}
            >
              {p.featured && (
                <span className="absolute -top-2.5 left-6 rounded-full bg-brand-emerald px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-bg-base">
                  Most popular
                </span>
              )}
              <h2 className="text-lg font-semibold text-text-primary">{p.name}</h2>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="font-display text-3xl font-bold text-text-primary">{p.price}</span>
                {p.cadence && <span className="text-sm text-text-muted">{p.cadence}</span>}
              </div>
              {p.annual && <p className="mt-1 text-xs text-brand-emerald">{p.annual}</p>}
              <p className="mt-2 text-sm text-text-muted">{p.blurb}</p>

              <ul className="mt-4 flex-1 space-y-2">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-text-primary/90">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-brand-emerald" aria-hidden />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={p.cta.href}
                className={cn(
                  "mt-6 inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition-all hover:-translate-y-0.5",
                  p.featured
                    ? "bg-brand-emerald text-bg-base shadow-[0_0_24px_rgba(16,185,129,0.4)] hover:bg-brand-emerald/90"
                    : "border border-brand-emerald/40 text-brand-emerald hover:bg-brand-emerald/10"
                )}
              >
                {p.cta.label}
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-14 mb-8 text-center">
          <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-text-primary">
            For residential portfolios
          </h2>
          <p className="mt-3 max-w-2xl mx-auto text-text-muted">
            For Hausverwaltungen &amp; Wohnungsunternehmen. Priced per building plus a
            per-unit band &mdash; and resident accounts are always included free.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-stretch max-w-3xl mx-auto">
          {RESIDENTIAL_PLANS.map((p) => (
            <div
              key={p.id}
              className="relative flex flex-col rounded-xl border border-border-subtle bg-bg-elevated/40 p-6 transition-all hover:-translate-y-1 hover:border-brand-emerald/50"
            >
              <h3 className="text-lg font-semibold text-text-primary">{p.name}</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="font-display text-3xl font-bold text-text-primary">{p.price}</span>
                {p.cadence && <span className="text-sm text-text-muted">{p.cadence}</span>}
              </div>
              <p className="mt-2 text-sm text-text-muted">{p.blurb}</p>

              <ul className="mt-4 flex-1 space-y-2">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-text-primary/90">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-brand-emerald" aria-hidden />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={p.cta.href}
                className="mt-6 inline-flex items-center justify-center rounded-md border border-brand-emerald/40 px-4 py-2 text-sm font-semibold text-brand-emerald transition-all hover:-translate-y-0.5 hover:bg-brand-emerald/10"
              >
                {p.cta.label}
              </Link>
            </div>
          ))}
        </div>

        <p className="mt-4 max-w-2xl mx-auto text-center text-xs text-text-faint">
          Aligned with EED / Heizkostenverordnung monthly consumption information (UVI).
          Final per-building and per-unit amounts are set before launch.
        </p>

        <p className="mt-8 text-center text-xs text-text-faint">
          Prices exclude VAT. Upgrade, downgrade, or cancel anytime from Settings →
          Subscription. Enterprise terms are tailored to your portfolio.
        </p>
      </main>

      <footer className="relative z-10 border-t border-border-subtle/60 px-6 py-6">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-text-faint">
          {TRUST.map((t) => (
            <span key={t.label} className="flex items-center gap-1.5">
              <span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} /> {t.label}
            </span>
          ))}
        </div>
      </footer>
    </div>
  )
}
