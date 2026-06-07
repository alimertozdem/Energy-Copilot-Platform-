/**
 * CitySkylineMotif -- abstract architectural silhouette, watermark sibling
 * to SustainabilityMotif.
 *
 * Placed in the lower-right corner (mirror of SustainabilityMotif at lower-left)
 * to create compositional balance. Same hairline philosophy, same opacity
 * register -- the two motifs are siblings in the same drawing series.
 *
 * Building shapes are deliberately abstract: an anonymous skyline that fits
 * any city. We do not depict any specific landmark.
 */
import { cn } from "@/lib/utils"

type CitySkylineMotifProps = {
  className?: string
  opacity?: number
}

export function CitySkylineMotif({
  className,
  opacity = 0.08,
}: CitySkylineMotifProps) {
  return (
    <div
      className={cn(
        "fixed bottom-0 right-0 pointer-events-none select-none z-0",
        className
      )}
      style={{ opacity }}
      aria-hidden
    >
      <svg
        width="520"
        height="280"
        viewBox="0 0 520 280"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
      >
        {/* ── Ground line ───────────────────────────────────────────── */}
        <line
          x1="0"
          y1="260"
          x2="520"
          y2="260"
          stroke="#5DCAA5"
          strokeWidth="0.75"
        />

        {/* ── Buildings (back to front, far -> near) ────────────────── */}
        {/* Tower 1 — slim high-rise */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <rect x="40" y="120" width="34" height="140" />
          {/* window grid */}
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="40" y1="140" x2="74" y2="140" />
            <line x1="40" y1="160" x2="74" y2="160" />
            <line x1="40" y1="180" x2="74" y2="180" />
            <line x1="40" y1="200" x2="74" y2="200" />
            <line x1="40" y1="220" x2="74" y2="220" />
            <line x1="40" y1="240" x2="74" y2="240" />
            <line x1="57" y1="120" x2="57" y2="260" />
          </g>
        </g>

        {/* Tower 2 — mid-rise with stepped top */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <path d="M 90 260 L 90 170 L 110 170 L 110 158 L 140 158 L 140 260 Z" />
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="90" y1="190" x2="140" y2="190" />
            <line x1="90" y1="210" x2="140" y2="210" />
            <line x1="90" y1="230" x2="140" y2="230" />
            <line x1="115" y1="170" x2="115" y2="260" />
          </g>
        </g>

        {/* Tower 3 — tallest, sleek diagonal-cut top */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <path d="M 160 260 L 160 100 L 195 90 L 195 260 Z" />
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="160" y1="120" x2="195" y2="120" />
            <line x1="160" y1="140" x2="195" y2="140" />
            <line x1="160" y1="160" x2="195" y2="160" />
            <line x1="160" y1="180" x2="195" y2="180" />
            <line x1="160" y1="200" x2="195" y2="200" />
            <line x1="160" y1="220" x2="195" y2="220" />
            <line x1="160" y1="240" x2="195" y2="240" />
            <line x1="177" y1="100" x2="177" y2="260" />
          </g>
          {/* antenna tip */}
          <line x1="195" y1="90" x2="195" y2="72" stroke="#5DCAA5" strokeWidth="0.6" />
          <circle cx="195" cy="70" r="1.5" fill="#C0DD97" stroke="none" />
        </g>

        {/* Tower 4 — short office block */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <rect x="215" y="195" width="48" height="65" />
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="215" y1="210" x2="263" y2="210" />
            <line x1="215" y1="225" x2="263" y2="225" />
            <line x1="215" y1="240" x2="263" y2="240" />
            <line x1="231" y1="195" x2="231" y2="260" />
            <line x1="247" y1="195" x2="247" y2="260" />
          </g>
        </g>

        {/* Tower 5 — rounded-top high-rise (Gherkin-esque) */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <path d="M 280 260 L 280 145 Q 280 115 305 110 Q 330 115 330 145 L 330 260 Z" />
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="280" y1="160" x2="330" y2="160" />
            <line x1="280" y1="180" x2="330" y2="180" />
            <line x1="280" y1="200" x2="330" y2="200" />
            <line x1="280" y1="220" x2="330" y2="220" />
            <line x1="280" y1="240" x2="330" y2="240" />
            <line x1="305" y1="110" x2="305" y2="260" />
          </g>
        </g>

        {/* Tower 6 — mid-rise modern slab */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <rect x="350" y="155" width="42" height="105" />
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="350" y1="175" x2="392" y2="175" />
            <line x1="350" y1="195" x2="392" y2="195" />
            <line x1="350" y1="215" x2="392" y2="215" />
            <line x1="350" y1="235" x2="392" y2="235" />
            <line x1="371" y1="155" x2="371" y2="260" />
          </g>
        </g>

        {/* Tower 7 — short stepped pyramid (Burj-vari setback) */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <path d="M 412 260 L 412 200 L 425 200 L 425 180 L 442 180 L 442 200 L 455 200 L 455 260 Z" />
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="412" y1="220" x2="455" y2="220" />
            <line x1="412" y1="240" x2="455" y2="240" />
            <line x1="433" y1="180" x2="433" y2="260" />
          </g>
        </g>

        {/* Tower 8 — slim sliver (right edge) */}
        <g stroke="#0F6E56" strokeWidth="1" fill="none">
          <rect x="475" y="175" width="22" height="85" />
          <g stroke="#5DCAA5" strokeWidth="0.4">
            <line x1="475" y1="195" x2="497" y2="195" />
            <line x1="475" y1="215" x2="497" y2="215" />
            <line x1="475" y1="235" x2="497" y2="235" />
          </g>
        </g>

        {/* ── Quiet annotation -- specimen card cue ─────────────────── */}
        <g
          fill="#5DCAA5"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="6"
          letterSpacing="0.15em"
        >
          <text x="40" y="276">PORTFOLIO · ABSTRACT</text>
        </g>
      </svg>
    </div>
  )
}
