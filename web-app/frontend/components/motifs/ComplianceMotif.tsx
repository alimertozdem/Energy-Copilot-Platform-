/**
 * ComplianceMotif — bespoke CRREM "stranding" motif for the /compliance hero
 * (design language 2026-06-16). A descending regulatory target pathway, a
 * building's emission line drifting above it (the stranding point), and a
 * compliance shield — now rendered IN-PALETTE (mint / glow / emerald) and alive
 * (breathing node + drifting motes), consistent with the global EnergyParticles
 * field instead of the old greyscale backdrop.
 *
 * Self-contained, inline SVG. Sized by the parent (give it a width/height via
 * className). Decorative only (aria-hidden). Motion classes (el-breathe /
 * el-float) are auto-damped under prefers-reduced-motion via globals.css.
 */
import type { CSSProperties } from "react"

import { cn } from "@/lib/utils"

type ComplianceMotifProps = {
  className?: string
  /** Accent for the stranding node + shield (defaults to brand mint). */
  accent?: string
  opacity?: number
}

export function ComplianceMotif({
  className,
  accent = "#5DCAA5",
  opacity = 1,
}: ComplianceMotifProps) {
  return (
    <div
      className={cn("pointer-events-none select-none", className)}
      style={{ opacity, ["--cm-accent" as string]: accent } as CSSProperties}
      aria-hidden
    >
      <svg
        viewBox="0 0 360 200"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        className="h-full w-full"
      >
        {/* faint baseline axes */}
        <line x1="28" y1="24" x2="28" y2="168" stroke="#5DCAA5" strokeWidth="0.75" opacity="0.35" />
        <line x1="28" y1="168" x2="332" y2="168" stroke="#5DCAA5" strokeWidth="0.75" opacity="0.35" />

        {/* CRREM target pathway — descending dashed steps */}
        <path
          d="M 28 70 L 92 70 L 92 88 L 156 88 L 156 106 L 220 106 L 220 124 L 284 124 L 284 142 L 332 142"
          stroke="#5DCAA5"
          strokeWidth="1.4"
          strokeDasharray="5 5"
          strokeLinecap="round"
          opacity="0.6"
        />

        {/* building emission line — starts compliant, drifts above (strands) */}
        <path
          d="M 28 112 C 96 104, 150 92, 206 94 S 300 110, 332 116"
          stroke="var(--cm-accent)"
          strokeWidth="2"
          strokeLinecap="round"
          opacity="0.95"
        />

        {/* stranding point — where emission crosses above the target */}
        <g className="el-breathe">
          <circle cx="196" cy="98" r="13" stroke="var(--cm-accent)" strokeWidth="1" fill="none" opacity="0.55" />
          <circle cx="196" cy="98" r="7" stroke="var(--cm-accent)" strokeWidth="1.2" fill="none" />
          <circle cx="196" cy="98" r="3" fill="#C0DD97" />
        </g>

        {/* compliance shield + check (upper-right) */}
        <g
          stroke="var(--cm-accent)"
          strokeWidth="1.4"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.9"
        >
          <path d="M 290 28 L 320 37 L 320 62 Q 320 78 305 87 Q 290 78 290 62 Z" />
          <path d="M 298 57 L 304 63 L 314 49" strokeWidth="1.6" />
        </g>

        {/* drifting motes — particle language */}
        <g fill="#C0DD97">
          <circle className="el-float-slow" cx="120" cy="46" r="1.8" opacity="0.7" />
          <circle className="el-float" cx="244" cy="60" r="1.4" opacity="0.6" />
          <circle className="el-float-slow" cx="312" cy="104" r="1.6" opacity="0.5" />
          <circle className="el-float" cx="70" cy="138" r="1.3" opacity="0.55" />
        </g>

        {/* annotation */}
        <text
          x="28"
          y="188"
          fill="#5DCAA5"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="8"
          letterSpacing="0.18em"
          opacity="0.7"
        >
          CRREM · 1.5°C PATHWAY · gCO₂ m⁻²
        </text>
      </svg>
    </div>
  )
}
