"use client"

import { signIn } from "next-auth/react"
import Link from "next/link"
import {
  ArrowRight,
  Building2,
  Eye,
  Leaf,
  Mail,
  ShieldCheck,
  Sun,
  TriangleAlert,
} from "lucide-react"

import { Logo } from "@/components/Logo"

const FEATURES = [
  { icon: Building2, color: "#1D9E75", title: "Portfolio intelligence", body: "EUI benchmarking with cost and carbon across every building." },
  { icon: TriangleAlert, color: "#F97316", title: "Fault detection", body: "Automated anomaly detection with €-quantified alerts." },
  { icon: Sun, color: "#EAB308", title: "Battery & solar ROI", body: "Dispatch simulation, dynamic pricing and payback." },
  { icon: ShieldCheck, color: "#A855F7", title: "Compliance & financing", body: "CRREM, MEPS and EU Taxonomy plus subsidy capture." },
]

const THEMES = ["Smart buildings", "Sustainability", "Renewable energy", "Energy management"]

const TRUST = [
  { label: "Microsoft Fabric", dot: "bg-brand-emerald" },
  { label: "BACnet / Modbus / MQTT", dot: "bg-accent-cyan" },
  { label: "EU Regulation 2023/1542", dot: "bg-accent-yellow" },
  { label: "CRREM Pathways", dot: "bg-accent-purple" },
]

function HeroPreview() {
  const bars = [38, 62, 47, 80, 55, 70, 44]
  return (
    <div className="el-float relative mx-auto mt-12 w-full max-w-xl rounded-2xl border border-border-subtle bg-bg-elevated/60 p-5 backdrop-blur-sm shadow-[0_20px_60px_rgba(0,0,0,0.45)]">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Portfolio · last 30 days</span>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-emerald/15 px-2 py-0.5 text-[10px] font-medium text-brand-emerald">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-emerald" /> live
        </span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2">
        {[["EUI", "142", "kWh/m²·yr"], ["Energy", "1.2", "GWh"], ["CO₂ saved", "310", "t"]].map(([l, v, u]) => (
          <div key={l} className="rounded-lg bg-white/[0.03] px-3 py-2">
            <div className="text-[10px] text-text-faint">{l}</div>
            <div className="text-base font-semibold text-text-primary">{v} <span className="text-[10px] font-normal text-text-muted">{u}</span></div>
          </div>
        ))}
      </div>
      <svg viewBox="0 0 320 90" className="mt-3 w-full" role="img" aria-label="Energy trend preview">
        {[0, 1, 2, 3].map((g) => (
          <line key={g} x1="0" x2="320" y1={g * 28 + 4} y2={g * 28 + 4} stroke="rgba(148,163,184,0.12)" strokeWidth="1" />
        ))}
        {bars.map((h, i) => (
          <rect key={i} x={i * 46 + 8} y={88 - h} width="26" height={h} rx="3" fill="#1D9E75" opacity={0.85} />
        ))}
        <path d="M21 40 L67 28 L113 48 L159 18 L205 34 L251 22 L297 38" fill="none" stroke="#5DCAA5" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}

export default function Home() {
  return (
    <main id="main-content" className="relative flex min-h-screen flex-col overflow-hidden bg-bg-base bg-radial-emerald-glow">
      <div className="pointer-events-none fixed inset-0 bg-dot-grid opacity-25" aria-hidden />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-[460px] animate-pulse"
        aria-hidden
        style={{ background: "radial-gradient(55% 80% at 50% -5%, rgba(29,158,117,0.20), transparent 70%)" }}
      />

      {/* ===== Top bar ===== */}
      <header className="relative z-10">
        <div className="mx-auto flex max-w-6xl items-center justify-end gap-4 px-6 py-4 text-sm">
          <Link href="/tour" className="hidden text-text-muted transition-colors hover:text-text-primary sm:inline">Tour</Link>
          <Link href="/demo" className="hidden text-text-muted transition-colors hover:text-text-primary sm:inline">Demo</Link>
          <Link href="/pricing" className="hidden text-text-muted transition-colors hover:text-text-primary sm:inline">Pricing</Link>
          <Link href="/pilot?source=landing" className="hidden text-brand-emerald transition-colors hover:text-brand-mint sm:inline">Request a pilot</Link>
          <a href="#sign-in" className="text-text-muted transition-colors hover:text-text-primary">Sign in</a>
          <Link href="/signup" className="inline-flex items-center rounded-md bg-brand-emerald px-3.5 py-2 font-semibold text-bg-base shadow-[0_0_18px_rgba(16,185,129,0.35)] transition-colors hover:bg-brand-emerald/90">Sign up free</Link>
        </div>
      </header>

      {/* ===== Hero ===== */}
      <section className="el-fade-up relative z-10 mx-auto flex w-full max-w-5xl flex-1 flex-col items-center px-6 pt-10 pb-16 text-center sm:pt-16">
        <Logo size={54} className="mb-8" />

        <span className="inline-flex items-center gap-2 rounded-full border border-brand-emerald/40 bg-brand-emerald/10 px-3 py-1 text-xs font-medium text-brand-emerald">
          <span className="relative inline-flex h-1.5 w-1.5">
            <span className="absolute inset-0 animate-ping rounded-full bg-brand-emerald opacity-60" />
            <span className="relative h-1.5 w-1.5 rounded-full bg-brand-emerald" />
          </span>
          Built on Microsoft Fabric · EU-hosted
        </span>

        <h1 className="font-display mx-auto mt-6 max-w-3xl text-4xl font-bold leading-[1.05] tracking-tight text-text-primary sm:text-6xl">
          Energy intelligence for{" "}
          <span className="text-brand-emerald">smart, sustainable</span> buildings
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-text-muted sm:text-lg">
          EnergyLens turns the data your buildings already produce into portfolio KPIs,
          fault detection, battery &amp; solar ROI, and EU-compliance insight — no new
          hardware required.
        </p>

        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link href="/demo" className="group inline-flex w-full items-center justify-center gap-2 rounded-md bg-brand-emerald px-6 py-3.5 text-sm font-semibold text-bg-base shadow-[0_0_28px_rgba(16,185,129,0.4)] transition-all hover:-translate-y-0.5 hover:bg-brand-emerald/90 sm:w-auto">
            <Eye size={16} /> Explore the live demo
            <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link href="/signup" className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-6 py-3.5 text-sm font-semibold text-brand-emerald transition-all hover:-translate-y-0.5 hover:border-brand-emerald hover:bg-brand-emerald/10 sm:w-auto">
            Get started free
          </Link>
        </div>
        <p className="mt-3 text-xs text-text-faint">6 sample buildings · no signup required for the demo</p>

        <HeroPreview />
      </section>

      {/* ===== Features ===== */}
      <section className="relative z-10 mx-auto w-full max-w-6xl px-6 pb-12">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5 transition-all hover:-translate-y-1 hover:border-brand-emerald/50">
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-lg" style={{ background: `${f.color}1A`, border: `1px solid ${f.color}40` }}>
                <f.icon size={22} style={{ color: f.color }} aria-hidden />
              </span>
              <h3 className="mt-3 text-sm font-semibold text-text-primary">{f.title}</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-text-muted">{f.body}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {THEMES.map((t) => (
            <span key={t} className="inline-flex items-center gap-1.5 rounded-full border border-border-subtle bg-white/[0.03] px-3 py-1 text-xs text-text-muted">
              <Leaf size={12} className="text-brand-emerald" aria-hidden /> {t}
            </span>
          ))}
        </div>
      </section>

      {/* ===== Sign-in card (auth UNCHANGED) ===== */}
      <section id="sign-in" className="relative z-10 mx-auto w-full max-w-md px-6 pb-16">
        <div className="rounded-2xl border border-border-subtle bg-bg-elevated/50 p-6 backdrop-blur-sm">
          <h2 className="font-display text-center text-lg font-semibold text-text-primary">Sign in to your workspace</h2>
          <div className="mt-5 flex flex-col gap-3">
            <button onClick={() => signIn("azure-ad", { callbackUrl: "/dashboard" })} className="flex w-full items-center justify-center gap-3 rounded-md border border-white/10 bg-[#2F2F2F] px-5 py-3 font-medium text-white transition-colors hover:bg-[#1F1F1F]">
              <svg width="18" height="18" viewBox="0 0 23 23" xmlns="http://www.w3.org/2000/svg">
                <rect x="1" y="1" width="10" height="10" fill="#F25022" />
                <rect x="12" y="1" width="10" height="10" fill="#7FBA00" />
                <rect x="1" y="12" width="10" height="10" fill="#00A4EF" />
                <rect x="12" y="12" width="10" height="10" fill="#FFB900" />
              </svg>
              <span>Sign in with Microsoft</span>
            </button>
            <button onClick={() => signIn("google", { callbackUrl: "/dashboard" })} className="flex w-full items-center justify-center gap-3 rounded-md border border-white/10 bg-surface-light-bright px-5 py-3 font-medium text-text-on-light transition-colors hover:bg-surface-light">
              <svg width="18" height="18" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z" />
                <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z" />
                <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z" />
                <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z" />
              </svg>
              <span>Sign in with Google</span>
            </button>
            <Link href="/login" className="flex w-full items-center justify-center gap-3 rounded-md bg-brand-emerald px-5 py-3 font-medium text-white shadow-[0_0_24px_rgba(29,158,117,0.25)] transition-colors hover:bg-brand-deep">
              <Mail size={18} />
              <span>Sign in with Email</span>
            </Link>
          </div>
          <p className="mt-5 text-center text-sm text-text-muted">
            New here?{" "}
            <Link href="/signup" className="font-medium text-brand-mint transition-colors hover:text-brand-glow">Create account</Link>
          </p>
        </div>
      </section>

      {/* ===== Trust strip ===== */}
      <footer className="relative z-10 border-t border-border-subtle/60 px-6 py-6">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-text-faint">
          {TRUST.map((t) => (
            <span key={t.label} className="flex items-center gap-1.5">
              <span className={`h-1.5 w-1.5 rounded-full ${t.dot}`} /> {t.label}
            </span>
          ))}
        </div>
      </footer>
    </main>
  )
}
