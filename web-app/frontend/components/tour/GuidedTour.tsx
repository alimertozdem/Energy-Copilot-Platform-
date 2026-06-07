"use client"

/**
 * GuidedTour — a full-screen, keyboard-navigable presentation spine for demos.
 *
 * Robust by design: it is self-contained narrative (NO Fabric / API calls), so it
 * never breaks mid-demo even if live data is unavailable. Each stop explains one
 * capability — what it shows, why it matters, key terms — and offers an
 * "Open live →" deep-link into the real page (new tab) when the presenter wants
 * to show real data. Drive it with ← / → (or the on-screen buttons); Esc exits.
 *
 * Copy follows the honesty layer: compliance/financial framings say "indicative"
 * / "decision-support", never overclaim.
 */
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Building2,
  Bot,
  Home,
  Layers,
  Leaf,
  ShieldCheck,
  Sun,
  TriangleAlert,
  Sparkles,
  X,
  Zap,
} from "lucide-react"
import Link from "next/link"
import { type ComponentType, useCallback, useEffect, useState } from "react"

type Stop = {
  eyebrow: string
  title: string
  what: string
  points: string[]
  terms?: string[]
  live?: { href: string; label: string }
  icon: ComponentType<{ size?: number; className?: string }>
  accent: string
}

const STOPS: Stop[] = [
  {
    eyebrow: "EnergyLens",
    title: "Energy intelligence for smart, sustainable buildings",
    what:
      "EnergyLens turns the data buildings already produce into portfolio KPIs, fault detection, decarbonisation planning and EU-compliance insight — no new hardware required.",
    points: [
      "Built on Microsoft Fabric (medallion: Bronze → Silver → Gold), EU-hosted.",
      "Hardware-optional: start from a meter CSV or a utility bill; connect sensors later.",
      "Sold to portfolios — property managers, housing companies, energy consultants.",
    ],
    terms: ["Microsoft Fabric", "Medallion", "Portfolio-first"],
    icon: Leaf,
    accent: "#1D9E75",
  },
  {
    eyebrow: "Stop 1 · Portfolio",
    title: "Portfolio intelligence",
    what:
      "One view across every building: energy use intensity (EUI) benchmarked against peers, plus cost and carbon.",
    points: [
      "EUI (kWh/m²·yr) ranks buildings so the worst performers surface first.",
      "Cost and CO₂ travel together — every kWh carries a € and a carbon number.",
      "Drill from the portfolio into any single building's overview.",
    ],
    terms: ["EUI", "Benchmark", "Scope 2 CO₂"],
    live: { href: "/portfolio", label: "Open Portfolio" },
    icon: Building2,
    accent: "#1D9E75",
  },
  {
    eyebrow: "Stop 2 · Decarbonisation",
    title: "Where every euro abates the most CO₂",
    what:
      "A marginal abatement cost curve (MACC) ranks measures by € per tonne of CO₂ avoided — the no-regret measures that pay for themselves sit on the left.",
    points: [
      "Answers the real question: what to invest in, in what order, for the best €/tCO₂.",
      "No-regret measures fund themselves; the curve shows the self-financing bundle.",
      "Indicative decision-support — undiscounted, with stated measure lifetimes.",
    ],
    terms: ["MACC", "€/tCO₂", "No-regret"],
    live: { href: "/decarbonisation", label: "Open Decarbonisation" },
    icon: BarChart3,
    accent: "#1D9E75",
  },
  {
    eyebrow: "Stop 3 · Alerts",
    title: "Fault detection with a price tag",
    what:
      "Automated anomaly detection flags equipment faults and waste, each quantified in €/day so operators triage by impact.",
    points: [
      "Physics-based rules (consumption spikes, night over-run, comfort breaches).",
      "Every alert carries an estimated cost so the biggest leaks get fixed first.",
      "Acknowledge / resolve workflow keeps the triage queue honest.",
    ],
    terms: ["Anomaly", "FDD", "€-quantified"],
    live: { href: "/alerts", label: "Open Alerts" },
    icon: TriangleAlert,
    accent: "#F97316",
  },
  {
    eyebrow: "Stop 4 · Actions",
    title: "Recommendations you can track",
    what:
      "Building-type-aware recommendations with savings, CapEx and payback — each with an editable status so improvement is tracked, not forgotten.",
    points: [
      "From decision support to decision tracking (open → in progress → done).",
      "Carries the same numbers the abatement curve uses — one source of truth.",
      "Status is shared across the org; sample buildings stay read-only.",
    ],
    terms: ["Payback", "CapEx", "Status overlay"],
    live: { href: "/actions", label: "Open Actions" },
    icon: Zap,
    accent: "#10b981",
  },
  {
    eyebrow: "Stop 5 · Compliance",
    title: "EU compliance, made legible",
    what:
      "A compliance hub that screens the portfolio against the regulations that increasingly drive building value.",
    points: [
      "MEPS renovation-risk radar, CRREM stranding pathways, EU Taxonomy screening.",
      "ESRS-E1-aligned reporting support for sustainability disclosure.",
      "Framed honestly as indicative screening — not a substitute for an auditor.",
    ],
    terms: ["EPBD MEPS", "CRREM", "EU Taxonomy", "ESRS-E1"],
    live: { href: "/compliance", label: "Open Compliance" },
    icon: ShieldCheck,
    accent: "#0D9488",
  },
  {
    eyebrow: "Stop 6 · Solar & battery",
    title: "Renewables and storage ROI",
    what:
      "On-site solar performance plus battery dispatch simulation with dynamic pricing and payback.",
    points: [
      "Specific yield (kWh/kWp) and self-consumption vs. your real load.",
      "Battery dispatch ROI uses regional prices, framed as a rigorous estimate.",
      "EU Battery Regulation 2023/1542-aware scenarios.",
    ],
    terms: ["Specific yield", "Self-consumption", "Dispatch ROI"],
    live: { href: "/solar", label: "Open Solar" },
    icon: Sun,
    accent: "#EAB308",
  },
  {
    eyebrow: "Stop 7 · Residential",
    title: "Down to the individual flat",
    what:
      "For residential portfolios, the same engine reaches the unit level — and gives each resident a private view of their own consumption.",
    points: [
      "Manager dashboard: per-unit EUI, EPC mix and UVI status across a building.",
      "Resident view: own usage + anonymous building benchmark via a magic link.",
      "Automates the German HKVO monthly consumption information (UVI) duty.",
    ],
    terms: ["Unit-level", "HKVO / UVI", "Magic-link"],
    live: { href: "/residential", label: "Open Residential" },
    icon: Home,
    accent: "#A855F7",
  },
  {
    eyebrow: "Stop 8 · Onboarding",
    title: "Self-serve onboarding & Fabric bridging",
    what:
      "A new building goes live without a consultant: upload a bill for baseline analytics, then bridge into the full Fabric experience — automatically.",
    points: [
      "Tier-1 baseline (EUI, cost, carbon, advisor) from a single CSV — no Fabric needed.",
      "An armed one-click 'bridge' provisions the building in Fabric and unlocks exactly the pages its data earns.",
      "Productised onboarding is a core USP — the platform sells and onboards itself.",
    ],
    terms: ["Tier-1 baseline", "Self-serve bridge", "Data-tier-aware"],
    icon: Layers,
    accent: "#5DCAA5",
  },
  {
    eyebrow: "Stop 9 · Copilot",
    title: "Ask the building anything",
    what:
      "An AI copilot answers questions over the building's own data — KPIs, anomalies, recommendations — in plain language.",
    points: [
      "Grounded in the same gold tables, so answers cite real numbers.",
      "Turns a dashboard into a conversation for non-technical owners.",
      "Tool-use architecture: the model calls real data functions, not guesses.",
    ],
    terms: ["LLM tool-use", "Grounded", "Plain language"],
    live: { href: "/copilot", label: "Open Copilot" },
    icon: Bot,
    accent: "#7B5BD6",
  },
  {
    eyebrow: "Architecture",
    title: "How it's built — and why it's defensible",
    what:
      "A clean medallion data platform on Microsoft Fabric, protocol-interoperable at the edge, with a multi-tenant web app on top.",
    points: [
      "Bronze → Silver → Gold separates raw ingestion, cleaning and business logic.",
      "Edge interoperability: BACnet, Modbus, MQTT, REST — vendor-neutral.",
      "Innovation & moat: data-tier-aware self-serve bridging, energy-correct logic, EU-compliance depth.",
    ],
    terms: ["Medallion", "Interoperability", "Multi-tenant RLS"],
    icon: Layers,
    accent: "#1D9E75",
  },
  {
    eyebrow: "That's EnergyLens",
    title: "Buildings that pay for their own decarbonisation",
    what:
      "Energy intelligence that turns the data your buildings already produce into savings, compliance, and a clear path to net zero — in one place.",
    points: [
      "Start free from a single utility bill — no new hardware.",
      "Portfolio KPIs, fault detection, decarbonisation planning and EU-compliance together.",
      "Explore the live demo, or create a free account to begin.",
    ],
    terms: ["No hardware", "EU-hosted", "Microsoft Fabric"],
    live: { href: "/demo", label: "Explore the live demo" },
    icon: Sparkles,
    accent: "#1D9E75",
  },
]

export function GuidedTour() {
  const [i, setI] = useState(0)
  const n = STOPS.length

  const go = useCallback(
    (d: number) => setI((cur) => Math.min(Math.max(cur + d, 0), n - 1)),
    [n]
  )

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight" || e.key === "PageDown") go(1)
      else if (e.key === "ArrowLeft" || e.key === "PageUp") go(-1)
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [go])

  // Resume where we left off when returning from an "Open live" page, and clear
  // the "from tour" flag now that we're back in the tour.
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem("el_tour_step")
      if (saved !== null) {
        const k = parseInt(saved, 10)
        if (Number.isFinite(k) && k >= 0 && k < n) setI(k)
      }
      sessionStorage.removeItem("el_tour_from")
    } catch {
      /* sessionStorage unavailable — ignore */
    }
    // run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Persist the current step so a live-page round-trip can resume here.
  useEffect(() => {
    try {
      sessionStorage.setItem("el_tour_step", String(i))
    } catch {
      /* ignore */
    }
  }, [i])

  function leaveTour() {
    try {
      sessionStorage.removeItem("el_tour_from")
      sessionStorage.removeItem("el_tour_step")
    } catch {
      /* ignore */
    }
  }

  function openLive() {
    try {
      sessionStorage.setItem("el_tour_from", "1")
      sessionStorage.setItem("el_tour_step", String(i))
    } catch {
      /* ignore */
    }
  }

  const s = STOPS[i]
  const Icon = s.icon
  const isFirst = i === 0
  const isLast = i === n - 1

  return (
    <main
      className="relative flex min-h-screen flex-col overflow-hidden bg-bg-base"
      style={{
        background: `radial-gradient(60% 70% at 50% -5%, ${s.accent}22, transparent 70%), var(--color-bg-base, #0b1220)`,
      }}
    >
      <div className="pointer-events-none fixed inset-0 bg-dot-grid opacity-20" aria-hidden />

      {/* Top bar: progress + exit */}
      <header className="relative z-10 flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-1.5" aria-hidden>
          {STOPS.map((st, k) => (
            <button
              key={k}
              onClick={() => setI(k)}
              className="h-1.5 rounded-full transition-all"
              style={{
                width: k === i ? 28 : 10,
                background: k === i ? st.accent : "rgba(148,163,184,0.3)",
              }}
              aria-label={`Go to stop ${k + 1}`}
            />
          ))}
        </div>
        <Link
          href="/"
          onClick={leaveTour}
          className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs text-text-muted transition-colors hover:text-text-primary"
        >
          <X size={14} /> Exit tour
        </Link>
      </header>

      {/* Stage */}
      <section className="relative z-10 mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-6 py-8">
        <span
          className="inline-flex w-fit items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium"
          style={{ borderColor: `${s.accent}55`, background: `${s.accent}14`, color: s.accent }}
        >
          <Icon size={14} /> {s.eyebrow}
        </span>

        <h1 className="font-display mt-5 text-3xl font-bold leading-tight tracking-tight text-text-primary sm:text-5xl">
          {s.title}
        </h1>

        <p className="mt-5 max-w-2xl text-base leading-relaxed text-text-muted sm:text-lg">
          {s.what}
        </p>

        <ul className="mt-6 space-y-2.5">
          {s.points.map((p, k) => (
            <li key={k} className="flex gap-3 text-sm leading-relaxed text-text-primary/90">
              <span
                className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ background: s.accent }}
                aria-hidden
              />
              <span>{p}</span>
            </li>
          ))}
        </ul>

        {s.terms && (
          <div className="mt-6 flex flex-wrap gap-2">
            {s.terms.map((t) => (
              <span
                key={t}
                className="rounded-full border border-border-subtle bg-white/[0.03] px-3 py-1 text-xs text-text-muted"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {s.live && (
          <a
            href={s.live.href}
            onClick={openLive}
            className="mt-7 inline-flex w-fit items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium transition-all hover:-translate-y-0.5"
            style={{ borderColor: `${s.accent}55`, background: `${s.accent}12`, color: s.accent }}
          >
            <ArrowRight size={15} /> {s.live.label}
          </a>
        )}
      </section>

      {/* Footer controls */}
      <footer className="relative z-10 flex items-center justify-between px-6 py-5">
        <button
          onClick={() => go(-1)}
          disabled={isFirst}
          className="inline-flex items-center gap-2 rounded-md border border-border-subtle px-4 py-2 text-sm text-text-muted transition-colors hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ArrowLeft size={15} /> Back
        </button>

        <span className="text-xs text-text-faint">
          {i + 1} / {n} · use ← → keys
        </span>

        {isLast ? (
          <Link
            href="/portfolio"
            onClick={leaveTour}
            className="inline-flex items-center gap-2 rounded-md bg-brand-emerald px-4 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-brand-emerald/90"
          >
            Enter the app <ArrowRight size={15} />
          </Link>
        ) : (
          <button
            onClick={() => go(1)}
            className="inline-flex items-center gap-2 rounded-md bg-brand-emerald px-4 py-2 text-sm font-semibold text-bg-base transition-colors hover:bg-brand-emerald/90"
          >
            Next <ArrowRight size={15} />
          </button>
        )}
      </footer>
    </main>
  )
}
