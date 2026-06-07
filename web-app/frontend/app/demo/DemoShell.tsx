"use client"

/**
 * DemoShell -- client root for the public /demo page.
 *
 * Layout:
 *   * Top bar:      LogoCard + "Demo Mode" badge + "Sign Up Free" CTA
 *   * Left rail:    SAMPLE BUILDINGS heading + 6 building cards
 *   * Center pane:  PowerBIReport embed (16:9 aspect-locked, accent glow)
 *   * Right rail:   atlas-style motif column (sustainability cues)
 *   * Bottom band:  sticky CTA banner ("Add your own buildings → Sign up")
 *
 * State:
 *   * selectedId — which building card is highlighted and used as the embed
 *     filter. Defaults to the first card in the list (B001 in our ASC sort).
 *
 * Why a sticky bottom CTA?
 *   The /demo page is the funnel entry for EXIST / BSBI pilot / EU funding
 *   pitches. Visitors should never have to scroll back up to find the signup
 *   path — the bottom banner stays in view through every embed click.
 *
 * Why a hardcoded buildingIds in the filter (not the selectedId alone)?
 *   PowerBIReport in demo mode already sweeps buildingIds through its own
 *   allowlist (DEMO_FABRIC_IDS). The selectedId we pass is single-element so
 *   the embed zooms to one building; if a user strips the filter via dev
 *   tools they only see the public sample portfolio anyway.
 */
import { useState } from "react"
import Link from "next/link"
import dynamic from "next/dynamic"
import { ArrowRight, Sparkles } from "lucide-react"

import { LogoCard } from "@/app/components/LogoCard"
import type { DemoBuilding } from "@/lib/api/demo"

import { DemoBuildingCard } from "./DemoBuildingCard"

// Same dynamic-import pattern as /buildings/[id]/ReportClient: powerbi-client
// touches `self` at module load, so it must stay out of the server bundle.
const PowerBIReport = dynamic(
  () => import("@/app/components/PowerBIReport"),
  {
    ssr: false,
    loading: () => (
      <div className="p-8 text-text-muted text-sm">
        Loading Power BI report…
      </div>
    ),
  }
)

// Soft accent driving the embed frame + side-rail glow. Emerald keeps the
// demo visually distinct from /buildings/[id], which retints per active page.
const DEMO_ACCENT = "#10b981"

type DemoShellProps = {
  buildings: DemoBuilding[]
  loadError: string | null
}

export function DemoShell({ buildings, loadError }: DemoShellProps) {
  const [selectedId, setSelectedId] = useState<string | null>(
    buildings.length > 0 ? buildings[0].fabric_building_id : null
  )

  const selected = buildings.find((b) => b.fabric_building_id === selectedId)

  return (
    <div className="relative min-h-screen flex flex-col bg-bg-base bg-radial-emerald-glow overflow-hidden">
      {/* Ambient dot-grid texture, same as authed AppChrome + landing */}
      <div
        className="absolute inset-0 bg-dot-grid opacity-25 pointer-events-none"
        aria-hidden
      />
      {/* Soft top-of-page emerald glow tuned for demo accent */}
      <div
        className="absolute inset-0 pointer-events-none"
        aria-hidden
        style={{
          background: `radial-gradient(circle at 50% 0%, ${DEMO_ACCENT}1A 0%, transparent 45%)`,
        }}
      />

      {/* =================== TOP BAR =================== */}
      <header className="relative z-10 border-b border-border-subtle bg-bg-elevated/60 backdrop-blur-sm">
        <div className="px-6 py-3 flex items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <LogoCard iconSize={44} />
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                         text-[10px] font-semibold uppercase tracking-wider
                         text-brand-emerald border border-brand-emerald/40
                         bg-brand-emerald/10"
            >
              <span className="relative inline-flex w-1.5 h-1.5">
                <span className="absolute inset-0 rounded-full bg-brand-emerald opacity-60 animate-ping" />
                <span className="relative w-1.5 h-1.5 rounded-full bg-brand-emerald" />
              </span>
              Live Demo
            </span>
            <span className="hidden md:inline text-xs text-text-muted">
              Read-only · 6 sample buildings · No signup required
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/pricing"
              className="text-sm text-text-muted hover:text-text-primary transition-colors hidden sm:inline"
            >
              Pricing
            </Link>
            <Link
              href="/login"
              className="text-sm text-text-muted hover:text-text-primary transition-colors hidden sm:inline"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-md
                         bg-brand-emerald text-bg-base text-sm font-semibold
                         shadow-[0_0_18px_rgba(16,185,129,0.35)]
                         hover:bg-brand-emerald/90 transition-colors"
            >
              <span>Sign Up Free</span>
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </header>

      {/* =================== VALUE STRIP =================== */}
      <div className="el-fade-up relative z-10 border-b border-border-subtle bg-bg-elevated/30">
        <div className="px-6 py-3 flex items-center gap-x-5 gap-y-2 flex-wrap">
          <p className="text-text-primary">
            <span className="font-display text-base font-semibold tracking-tight">Commercial-building energy intelligence</span>
            <span className="text-sm text-text-muted">
              {" "}— explore live analytics across six sample EU buildings.
            </span>
          </p>
          <div className="flex items-center gap-2 flex-wrap">
            {[
              "Portfolio KPIs & EUI",
              "Anomaly alerts",
              "Battery & solar ROI",
              "AI copilot",
              "Microsoft Fabric · EU-hosted",
            ].map((f) => (
              <span
                key={f}
                className="inline-flex items-center gap-1.5 rounded-full border border-border-subtle bg-white/[0.03] px-2.5 py-1 text-[11px] text-text-muted"
              >
                <span className="w-1 h-1 rounded-full bg-brand-emerald" aria-hidden />
                {f}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* =================== MAIN AREA =================== */}
      <main id="main-content" className="relative z-10 flex-1 flex min-h-0">
        {/* -------- LEFT RAIL: building cards -------- */}
        <aside className="w-[280px] shrink-0 border-r border-border-subtle bg-bg-elevated/30 p-4 overflow-y-auto">
          <h2 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-3">
            Sample Buildings
          </h2>

          {loadError && (
            <div className="mb-3 p-2 rounded border border-red-400/40 bg-red-400/5 text-[11px] text-red-300">
              Couldn&rsquo;t load buildings: {loadError}
            </div>
          )}
          {buildings.length === 0 && !loadError && (
            <div className="p-2 rounded border border-border-subtle text-[11px] text-text-muted">
              No demo buildings available right now. Please try again shortly.
            </div>
          )}

          <div className="flex flex-col gap-2">
            {buildings.map((b) => (
              <DemoBuildingCard
                key={b.fabric_building_id}
                building={b}
                selected={b.fabric_building_id === selectedId}
                onSelect={setSelectedId}
              />
            ))}
          </div>

          {/* Persistent rail CTA */}
          <div className="mt-6 p-3 rounded-lg border border-brand-emerald/30 bg-brand-emerald/5">
            <div className="flex items-start gap-2">
              <Sparkles
                size={14}
                className="text-brand-emerald shrink-0 mt-0.5"
              />
              <div className="min-w-0">
                <p className="text-xs text-text-primary font-semibold">
                  Like what you see?
                </p>
                <p className="text-[11px] text-text-muted mt-1 leading-snug">
                  Connect your own buildings — free during the pilot.
                </p>
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-1 mt-2 text-[11px] font-semibold text-brand-emerald hover:text-brand-emerald/80"
                >
                  Sign up free
                  <ArrowRight size={11} />
                </Link>
              </div>
            </div>
          </div>
        </aside>

        {/* -------- CENTER: embed pane -------- */}
        <section className="flex-1 min-w-0 flex flex-col items-center justify-center p-4 pb-20">
          {/* Currently-viewed building meta strip */}
          {selected && (
            <div className="w-full max-w-[1280px] mb-3 flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wider text-text-faint">
                  Now viewing
                </span>
                <span className="text-sm font-semibold text-text-primary">
                  {selected.name}
                </span>
              </div>
              <span className="text-text-faint">·</span>
              <span className="text-xs text-text-muted">
                {selected.country} · {selected.city} · {selected.building_type}
              </span>
              {selected.epc_class && (
                <>
                  <span className="text-text-faint">·</span>
                  <span className="text-xs text-text-muted">
                    EPC {selected.epc_class}
                  </span>
                </>
              )}
            </div>
          )}

          {selectedId ? (
            <div
              className="relative aspect-video w-full max-w-[1280px] max-h-full rounded-xl
                         overflow-hidden bg-bg-base"
              style={{
                border: `1px solid ${DEMO_ACCENT}55`,
                boxShadow: `0 0 28px ${DEMO_ACCENT}1A, 0 8px 28px rgba(0,0,0,0.3)`,
              }}
            >
              {/* Decorative corner brackets — same accent treatment as
                  /buildings/[id] for visual continuity with authed pages. */}
              {(["top-left", "top-right", "bottom-left", "bottom-right"] as const).map(
                (corner) => {
                  const cls: Record<typeof corner, string> = {
                    "top-left": "top-1.5 left-1.5 border-l border-t rounded-tl",
                    "top-right": "top-1.5 right-1.5 border-r border-t rounded-tr",
                    "bottom-left":
                      "bottom-1.5 left-1.5 border-l border-b rounded-bl",
                    "bottom-right":
                      "bottom-1.5 right-1.5 border-r border-b rounded-br",
                  }
                  return (
                    <div
                      key={corner}
                      className={`absolute w-4 h-4 pointer-events-none z-10 ${cls[corner]}`}
                      style={{ borderColor: `${DEMO_ACCENT}CC` }}
                      aria-hidden
                    />
                  )
                }
              )}
              <PowerBIReport useDemo={true} buildingIds={[selectedId]} />
            </div>
          ) : (
            <div className="text-text-muted text-sm">
              Select a building from the left to view its energy report.
            </div>
          )}
        </section>
      </main>

      {/* =================== STICKY BOTTOM CTA BANNER =================== */}
      <div className="absolute bottom-0 left-[280px] right-0 z-20 pointer-events-none px-4 pb-4">
        <div
          className="pointer-events-auto mx-auto max-w-[1280px] rounded-lg
                     border border-brand-emerald/40
                     bg-gradient-to-r from-brand-emerald/15 via-brand-emerald/10 to-brand-emerald/15
                     backdrop-blur-sm shadow-[0_8px_28px_rgba(0,0,0,0.4)]
                     px-5 py-3 flex items-center justify-between gap-4 flex-wrap"
        >
          <div className="flex items-center gap-3 min-w-0">
            <span
              className="hidden sm:inline-flex items-center justify-center
                         w-9 h-9 rounded-full bg-brand-emerald/20
                         border border-brand-emerald/40"
            >
              <Sparkles size={16} className="text-brand-emerald" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-text-primary leading-tight">
                Add your own commercial buildings.
              </p>
              <p className="text-xs text-text-muted mt-0.5">
                Free during pilot · BACnet / Modbus / MQTT supported · EU
                hosted
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/login"
              className="text-xs text-text-muted hover:text-text-primary transition-colors px-2 py-1"
            >
              I already have an account
            </Link>
            <Link
              href="/signup"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md
                         bg-brand-emerald text-bg-base text-sm font-semibold
                         shadow-[0_0_18px_rgba(16,185,129,0.35)]
                         hover:bg-brand-emerald/90 transition-colors"
            >
              Sign Up Free
              <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
