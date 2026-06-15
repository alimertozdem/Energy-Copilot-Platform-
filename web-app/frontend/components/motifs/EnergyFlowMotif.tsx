/**
 * EnergyFlowMotif — flow lines streaming from upper-left to lower-right,
 * meant to evoke energy/data passing through a system.
 *
 * Used on Forecast (04) and Battery Strategy (09) pages where the concept
 * is temporal movement / dispatch / projection.
 *
 * Hairline philosophy preserved: same opacity register as siblings, all
 * lines no fills, brand palette only.
 */
import { cn } from "@/lib/utils"

type EnergyFlowMotifProps = {
  className?: string
  opacity?: number
}

export function EnergyFlowMotif({
  className,
  opacity = 0.2,
}: EnergyFlowMotifProps) {
  return (
    <div
      className={cn(
        "fixed top-32 left-0 pointer-events-none select-none z-0",
        className
      )}
      style={{ opacity, filter: "grayscale(1) brightness(1.7)", transform: "scale(1.2)", transformOrigin: "top left" }}
      aria-hidden
    >
      <svg
        width="520"
        height="380"
        viewBox="0 0 520 380"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
      >
        {/* Cascading flow lines — 8 bezier streams */}
        <g className="el-flow" strokeDasharray="5 9" stroke="#5DCAA5" strokeLinecap="round" fill="none">
          <path d="M -20 40 C 120 50, 200 90, 320 80 S 480 60, 540 100" strokeWidth="0.75" opacity="0.9" />
          <path d="M -20 70 C 100 90, 220 110, 320 110 S 480 100, 540 130" strokeWidth="0.6" opacity="0.7" />
          <path d="M -20 110 C 140 130, 240 150, 320 150 S 460 140, 540 170" strokeWidth="0.5" opacity="0.6" />
          <path d="M -20 150 C 120 170, 220 200, 320 200 S 480 180, 540 220" strokeWidth="0.75" opacity="0.85" />
          <path d="M -20 200 C 100 220, 240 240, 320 250 S 460 230, 540 270" strokeWidth="0.5" opacity="0.5" />
          <path d="M -20 250 C 140 270, 220 300, 320 300 S 480 280, 540 320" strokeWidth="0.6" opacity="0.7" />
          <path d="M -20 300 C 120 320, 240 340, 320 340 S 460 320, 540 350" strokeWidth="0.5" opacity="0.55" />
          <path d="M -20 340 C 100 350, 200 360, 320 365 S 480 355, 540 375" strokeWidth="0.4" opacity="0.45" />
        </g>

        {/* Data nodes — sparse glow points along the streams */}
        <g className="el-breathe" fill="#C0DD97">
          <circle cx="80" cy="55" r="1.8" opacity="0.9" />
          <circle cx="320" cy="80" r="1.4" opacity="0.7" />
          <circle cx="180" cy="150" r="1.5" opacity="0.8" />
          <circle cx="400" cy="200" r="2" opacity="1" />
          <circle cx="240" cy="270" r="1.3" opacity="0.6" />
          <circle cx="120" cy="320" r="1.4" opacity="0.7" />
        </g>

        {/* Annotation */}
        <g
          fill="#5DCAA5"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="6"
          letterSpacing="0.15em"
        >
          <text x="-20" y="370">FLOW · TEMPORAL</text>
        </g>
      </svg>
    </div>
  )
}
