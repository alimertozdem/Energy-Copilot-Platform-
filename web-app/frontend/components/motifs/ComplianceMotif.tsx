/**
 * ComplianceMotif — a CRREM "stranding" diagram: a descending regulatory target
 * pathway, a building's emission line crossing it (the stranding point), and a
 * compliance shield. Page-identity backdrop for the Compliance page — the user
 * should feel "this is about EU rules / stranding risk" at a glance.
 *
 * Greyscaled + scaled at the wrapper to read as a visible-but-quiet backdrop.
 * The stranding node breathes.
 */
import { cn } from "@/lib/utils"

type ComplianceMotifProps = {
  className?: string
  opacity?: number
}

export function ComplianceMotif({ className, opacity = 0.2 }: ComplianceMotifProps) {
  return (
    <div
      className={cn(
        "fixed bottom-0 left-0 pointer-events-none select-none z-0",
        className
      )}
      style={{
        opacity,
        filter: "grayscale(1) brightness(1.7)",
        transform: "scale(1.3)",
        transformOrigin: "bottom left",
      }}
      aria-hidden
    >
      <svg width="440" height="290" viewBox="0 0 440 290" xmlns="http://www.w3.org/2000/svg" fill="none">
        {/* ── Axes ──────────────────────────────────────────────────── */}
        <line x1="40" y1="40" x2="40" y2="230" stroke="#5DCAA5" strokeWidth="0.75" opacity="0.7" />
        <line x1="40" y1="230" x2="400" y2="230" stroke="#5DCAA5" strokeWidth="0.75" opacity="0.7" />

        {/* ── CRREM target pathway — descending dashed steps ───────────── */}
        <path
          d="M 40 110 L 110 110 L 110 130 L 180 130 L 180 152 L 250 152 L 250 176 L 320 176 L 320 200 L 400 200"
          stroke="#5DCAA5"
          strokeWidth="1.1"
          strokeDasharray="4 4"
          strokeLinecap="round"
        />

        {/* ── Building emission line — starts compliant, drifts above (strands) ── */}
        <path
          d="M 40 150 C 120 140, 170 120, 230 118 S 340 130, 400 138"
          stroke="#C0DD97"
          strokeWidth="1.25"
          strokeLinecap="round"
        />

        {/* ── Stranding point — where emission crosses above the target ── */}
        <g className="el-breathe">
          <circle cx="247" cy="150" r="9" stroke="#C0DD97" strokeWidth="0.8" fill="none" />
          <circle cx="247" cy="150" r="2.4" fill="#C0DD97" />
        </g>

        {/* ── Compliance shield + check (upper-right) ───────────────────── */}
        <g stroke="#5DCAA5" strokeWidth="1.1" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d="M 360 40 L 392 50 L 392 78 Q 392 96 376 106 Q 360 96 360 78 Z" />
          <path d="M 369 72 L 375 79 L 387 63" strokeWidth="1.25" />
        </g>

        {/* ── Annotation ────────────────────────────────────────────── */}
        <g fill="#5DCAA5" fontFamily="Inter, system-ui, sans-serif" fontSize="6" letterSpacing="0.15em">
          <text x="40" y="252">CRREM · STRANDING · gCO₂ m⁻²</text>
        </g>
      </svg>
    </div>
  )
}
