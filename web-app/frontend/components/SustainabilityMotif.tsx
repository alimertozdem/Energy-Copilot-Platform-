/**
 * SustainabilityMotif — *Quiet Photosynthesis* watermark.
 *
 * A botanical-engineering specimen: a vertical stem with wind rotor, solar
 * disc + rays, root network, and pulse-wave horizon. Hairline strokes in the
 * Emerald palette, no fills.
 *
 * Used as a low-opacity decorative anchor in the lower-left corner of
 * authenticated pages (AppChrome <main> area). Pointer-events disabled —
 * pure visual signature, never interactive.
 *
 * Philosophy: docs/design/sustainability-motif-philosophy.md
 */
import { cn } from "@/lib/utils"

type SustainabilityMotifProps = {
  /** Position/sizing override. Defaults to absolute bottom-left. */
  className?: string
  /** Overall transparency (default 0.10). Lower for noisy backgrounds. */
  opacity?: number
}

export function SustainabilityMotif({
  className,
  opacity = 0.1,
}: SustainabilityMotifProps) {
  return (
    <div
      className={cn(
        // `fixed` so the motif acts as a page-level watermark -- always
        // anchored to the viewport corner, never scrolls off with content.
        // Layouts that want it scoped to <main> can override via className.
        "fixed bottom-0 left-0 pointer-events-none select-none z-0",
        className
      )}
      style={{ opacity }}
      aria-hidden
    >
      <svg
        width="420"
        height="280"
        viewBox="0 0 420 280"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
      >
        {/* ── Wind rotor (apex) ─────────────────────────────────────── */}
        <g stroke="#5DCAA5" strokeWidth="1.25" strokeLinecap="round">
          {/* Blade 1 — 12 o'clock, slight S-curve twist */}
          <path d="M 70 47 Q 68 32 72 20 Q 73 18 71 15" />
          {/* Blade 2 — 4 o'clock (120°) */}
          <path d="M 73 51 Q 88 56 96 66 Q 98 67 100 67" />
          {/* Blade 3 — 8 o'clock (240°) */}
          <path d="M 67 51 Q 52 56 44 66 Q 42 67 40 67" />
        </g>
        {/* Hub */}
        <circle cx="70" cy="50" r="2.5" stroke="#1D9E75" strokeWidth="1" />

        {/* ── Vertical stem ─────────────────────────────────────────── */}
        <line
          x1="70"
          y1="55"
          x2="70"
          y2="240"
          stroke="#0F6E56"
          strokeWidth="1.5"
          strokeLinecap="round"
        />

        {/* ── Solar disc — outer + inner concentric ─────────────────── */}
        <circle cx="70" cy="135" r="15" stroke="#5DCAA5" strokeWidth="1" />
        <circle
          cx="70"
          cy="135"
          r="8"
          stroke="#5DCAA5"
          strokeWidth="0.5"
          opacity="0.6"
        />

        {/* ── Solar rays — 10 equal angular steps (skipping stem overlap) ── */}
        <g stroke="#5DCAA5" strokeWidth="0.75" strokeLinecap="round">
          {/*   0° */} <line x1="88" y1="135" x2="96" y2="135" />
          {/*  30° */} <line x1="85.6" y1="144" x2="92.5" y2="148" />
          {/*  60° */} <line x1="79" y1="150.6" x2="83" y2="157.5" />
          {/* 120° */} <line x1="61" y1="150.6" x2="57" y2="157.5" />
          {/* 150° */} <line x1="54.4" y1="144" x2="47.5" y2="148" />
          {/* 180° */} <line x1="52" y1="135" x2="44" y2="135" />
          {/* 210° */} <line x1="54.4" y1="126" x2="47.5" y2="122" />
          {/* 240° */} <line x1="61" y1="119.4" x2="57" y2="112.5" />
          {/* 300° */} <line x1="79" y1="119.4" x2="83" y2="112.5" />
          {/* 330° */} <line x1="85.6" y1="126" x2="92.5" y2="122" />
        </g>

        {/* ── Glow node at solar center ─────────────────────────────── */}
        <circle cx="70" cy="135" r="1.5" fill="#C0DD97" />

        {/* ── Root network — phyllotaxic branching ──────────────────── */}
        <g stroke="#0F6E56" strokeWidth="1" strokeLinecap="round">
          <line x1="70" y1="240" x2="70" y2="252" />
          <path d="M 70 240 Q 70 248 60 256" />
          <path d="M 70 240 Q 70 248 80 256" />
          <path d="M 70 245 Q 60 250 48 258" />
          <path d="M 70 245 Q 80 250 92 258" />
        </g>

        {/* ── Pulse wave horizon — Emerald Pulse restated ───────────── */}
        <path
          d="M 20 265 q 17.5 -3 35 0 t 35 0 t 35 0 t 35 0 t 35 0 t 35 0 t 35 0 t 35 0 t 35 0 t 35 0 t 35 0"
          stroke="#5DCAA5"
          strokeWidth="0.75"
          strokeLinecap="round"
        />

        {/* ── Glow node at stem-pulse intersection ──────────────────── */}
        <circle cx="70" cy="265" r="1.5" fill="#C0DD97" />

        {/* ── Scientific annotations (specimen card cues) ───────────── */}
        <g
          fill="#5DCAA5"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="6"
          letterSpacing="0.15em"
        >
          <text x="100" y="137">kW · m⁻²</text>
          <text x="370" y="270">EL · 001</text>
        </g>
      </svg>
    </div>
  )
}
