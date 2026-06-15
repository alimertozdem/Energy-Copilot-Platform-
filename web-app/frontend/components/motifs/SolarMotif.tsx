/**
 * SolarMotif — a sun over a photovoltaic panel array. Page-identity backdrop for
 * the Solar page: the user should feel "this is about on-site solar" at a glance.
 *
 * Hairline / specimen philosophy like its siblings; greyscaled + scaled-up at the
 * wrapper so it reads as a visible-but-quiet backdrop. The sun's rays breathe.
 */
import { cn } from "@/lib/utils"

type SolarMotifProps = {
  className?: string
  opacity?: number
}

export function SolarMotif({ className, opacity = 0.2 }: SolarMotifProps) {
  return (
    <div
      className={cn(
        "fixed bottom-0 right-0 pointer-events-none select-none z-0",
        className
      )}
      style={{
        opacity,
        filter: "grayscale(1) brightness(1.7)",
        transform: "scale(1.35)",
        transformOrigin: "bottom right",
      }}
      aria-hidden
    >
      <svg width="460" height="300" viewBox="0 0 460 300" xmlns="http://www.w3.org/2000/svg" fill="none">
        {/* ── Sun disc + rays (breathing) ───────────────────────────── */}
        <circle cx="120" cy="80" r="26" stroke="#5DCAA5" strokeWidth="1.25" />
        <circle cx="120" cy="80" r="15" stroke="#5DCAA5" strokeWidth="0.6" opacity="0.6" />
        <g className="el-breathe" stroke="#C0DD97" strokeWidth="1" strokeLinecap="round">
          <line x1="120" y1="36" x2="120" y2="20" />
          <line x1="120" y1="140" x2="120" y2="124" />
          <line x1="76" y1="80" x2="60" y2="80" />
          <line x1="180" y1="80" x2="164" y2="80" />
          <line x1="89" y1="49" x2="78" y2="38" />
          <line x1="151" y1="49" x2="162" y2="38" />
          <line x1="89" y1="111" x2="78" y2="122" />
          <line x1="151" y1="111" x2="162" y2="122" />
        </g>

        {/* ── PV panel array (perspective rows of cells) ────────────── */}
        <g stroke="#5DCAA5" strokeWidth="1" fill="none">
          {/* back row */}
          <path d="M 250 150 L 430 150 L 410 178 L 230 178 Z" />
          {/* front row */}
          <path d="M 235 196 L 432 196 L 410 232 L 213 232 Z" />
          {/* cell divisions — back */}
          <g strokeWidth="0.45" opacity="0.8">
            <line x1="295" y1="150" x2="277" y2="178" />
            <line x1="340" y1="150" x2="324" y2="178" />
            <line x1="385" y1="150" x2="371" y2="178" />
            <line x1="240" y1="164" x2="420" y2="164" />
          </g>
          {/* cell divisions — front */}
          <g strokeWidth="0.45" opacity="0.8">
            <line x1="285" y1="196" x2="266" y2="232" />
            <line x1="335" y1="196" x2="318" y2="232" />
            <line x1="385" y1="196" x2="370" y2="232" />
            <line x1="224" y1="214" x2="421" y2="214" />
          </g>
        </g>
        {/* panel mounting legs */}
        <g stroke="#0F6E56" strokeWidth="1" strokeLinecap="round">
          <line x1="250" y1="178" x2="248" y2="196" />
          <line x1="410" y1="178" x2="411" y2="196" />
          <line x1="232" y1="232" x2="230" y2="248" />
          <line x1="410" y1="232" x2="412" y2="248" />
        </g>

        {/* ── Annotation ────────────────────────────────────────────── */}
        <g fill="#5DCAA5" fontFamily="Inter, system-ui, sans-serif" fontSize="6" letterSpacing="0.15em">
          <text x="213" y="262">PV · kWp · SELF-CONSUMPTION</text>
        </g>
      </svg>
    </div>
  )
}
