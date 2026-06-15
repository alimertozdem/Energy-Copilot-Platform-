/**
 * ScopeRingsMotif — concentric rings with a spotlight pulse beam emerging
 * from the center; a direct echo of the EnergyLens brand mark's "lens DNA"
 * (rings + pulse spotlight).
 *
 * Used on Sustainability (06) and HVAC (07) pages where the concept is
 * focused inspection / scoped measurement / lens-like analysis.
 *
 * Anchored to the upper-left, just below the logo card so the eye walks
 * from logo -> rings -> content.
 */
import { cn } from "@/lib/utils"

type ScopeRingsMotifProps = {
  className?: string
  opacity?: number
}

export function ScopeRingsMotif({
  className,
  opacity = 0.2,
}: ScopeRingsMotifProps) {
  return (
    <div
      className={cn(
        "fixed top-28 left-72 pointer-events-none select-none z-0",
        className
      )}
      style={{ opacity, filter: "grayscale(1) brightness(1.7)", transform: "scale(1.25)", transformOrigin: "top left" }}
      aria-hidden
    >
      <svg
        width="320"
        height="320"
        viewBox="0 0 320 320"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
      >
        {/* Outer dashed scan ring */}
        <circle
          cx="160"
          cy="160"
          r="140"
          stroke="#5DCAA5"
          strokeWidth="0.5"
          strokeDasharray="3 4"
          opacity="0.6"
          className="el-scan"
          style={{ transformOrigin: "160px 160px", transformBox: "view-box" }}
        />

        {/* Concentric rings — gradually tightening */}
        <g stroke="#5DCAA5" fill="none">
          <circle cx="160" cy="160" r="115" strokeWidth="0.6" opacity="0.7" />
          <circle cx="160" cy="160" r="90" strokeWidth="0.75" opacity="0.85" />
          <circle cx="160" cy="160" r="65" strokeWidth="1" opacity="1" />
          <circle cx="160" cy="160" r="40" strokeWidth="0.75" opacity="0.85" />
          <circle cx="160" cy="160" r="18" strokeWidth="0.5" opacity="0.7" />
        </g>

        {/* Crosshair ticks — 4 cardinal short marks at the inner ring */}
        <g stroke="#5DCAA5" strokeWidth="0.75">
          <line x1="160" y1="40" x2="160" y2="55" />
          <line x1="160" y1="265" x2="160" y2="280" />
          <line x1="40" y1="160" x2="55" y2="160" />
          <line x1="265" y1="160" x2="280" y2="160" />
        </g>

        {/* Spotlight pulse beam — vertical column emerging upward */}
        <g className="el-breathe" opacity="0.5">
          <line
            x1="160"
            y1="160"
            x2="160"
            y2="20"
            stroke="#C0DD97"
            strokeWidth="0.5"
          />
          <line
            x1="156"
            y1="160"
            x2="156"
            y2="40"
            stroke="#C0DD97"
            strokeWidth="0.4"
            opacity="0.5"
          />
          <line
            x1="164"
            y1="160"
            x2="164"
            y2="40"
            stroke="#C0DD97"
            strokeWidth="0.4"
            opacity="0.5"
          />
        </g>

        {/* Center glow node */}
        <circle cx="160" cy="160" r="2" fill="#C0DD97" />

        {/* Annotation */}
        <g
          fill="#5DCAA5"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="6"
          letterSpacing="0.15em"
        >
          <text x="160" y="305" textAnchor="middle">
            SCOPE · FOCUSED
          </text>
        </g>
      </svg>
    </div>
  )
}
