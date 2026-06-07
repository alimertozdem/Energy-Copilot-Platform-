/**
 * SidePanel -- decorative ESG / smart-energy column anchored beside the embed.
 *
 * Rendered as a flex item inside BuildingReportShell / CompareReportShell:
 *
 *   <div className="flex">
 *     <SidePanel side="left"  ... />
 *     <div className="flex-1">...embed...</div>
 *     <SidePanel side="right" ... />
 *   </div>
 *
 * Each panel is a multi-layer composition:
 *   * solid emerald gradient base (no white showing through)
 *   * pulsing top dot + accent glow
 *   * stacked thematic glyphs (wind / solar / leaf on left;
 *     pulse / circular / battery on right)
 *   * rotated ESG message stack
 *   * pulse-waveform bottom band
 *
 * All decoration is in the active accent colour so the panel "tunes" along
 * with the embed when the user switches PBI tabs.
 */
import { cn } from "@/lib/utils"

type SidePanelProps = {
  side: "left" | "right"
  accentColor: string
}

const LEFT_MESSAGES = [
  "RENEWABLE · FIRST",
  "ZERO CARBON 2030",
  "SMART · GRID",
]

const RIGHT_MESSAGES = [
  "NET ZERO 2050",
  "ESG · COMPLIANCE",
  "CIRCULAR · ECONOMY",
]

export function SidePanel({ side, accentColor }: SidePanelProps) {
  const isLeft = side === "left"
  const messages = isLeft ? LEFT_MESSAGES : RIGHT_MESSAGES

  return (
    <aside
      className={cn(
        "relative w-20 shrink-0 hidden md:flex flex-col items-center justify-between",
        "py-5 overflow-hidden pointer-events-none select-none"
      )}
      aria-hidden
    >
      {/* Base layer: solid emerald gradient so no white shows through. */}
      <div
        className="absolute inset-0 transition-all duration-500"
        style={{
          background: `linear-gradient(${isLeft ? "180deg" : "180deg"},
            ${accentColor}1F 0%,
            ${accentColor}10 30%,
            ${accentColor}08 60%,
            ${accentColor}1A 100%)`,
        }}
      />

      {/* Dot-grid overlay -- subtle texture */}
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage: `radial-gradient(circle, ${accentColor}30 1px, transparent 1px)`,
          backgroundSize: "12px 12px",
        }}
      />

      {/* Inner edge accent line -- separates panel from embed */}
      <div
        className={cn(
          "absolute top-0 bottom-0 w-px transition-colors duration-500",
          isLeft ? "right-0" : "left-0"
        )}
        style={{
          background: `linear-gradient(180deg, transparent 0%, ${accentColor}88 50%, transparent 100%)`,
        }}
      />

      {/* TOP — thematic SVG cluster (different per side) */}
      <div className="relative flex flex-col items-center gap-3">
        {/* Pulsing apex dot */}
        <span className="relative inline-flex w-2 h-2">
          <span
            className="absolute inset-0 rounded-full animate-ping opacity-60"
            style={{ backgroundColor: accentColor }}
          />
          <span
            className="relative w-2 h-2 rounded-full"
            style={{
              backgroundColor: accentColor,
              boxShadow: `0 0 12px ${accentColor}`,
            }}
          />
        </span>
        {isLeft ? <WindTurbineGlyph color={accentColor} /> : <CircularGlyph color={accentColor} />}
        {isLeft ? <SolarPanelGlyph color={accentColor} /> : <BatteryGlyph color={accentColor} />}
      </div>

      {/* MIDDLE — rotated message stack */}
      <div className="relative flex flex-col items-center gap-12 px-1">
        {messages.map((msg) => (
          <div
            key={msg}
            className="font-semibold text-[9.5px] tracking-[0.35em] whitespace-nowrap transition-colors duration-500"
            style={{
              color: accentColor,
              writingMode: "vertical-rl",
              transform: isLeft ? "rotate(180deg)" : "rotate(0deg)",
              textShadow: `0 0 10px ${accentColor}88`,
            }}
          >
            {msg}
          </div>
        ))}
      </div>

      {/* BOTTOM — leaf / pulse glyph + base dot */}
      <div className="relative flex flex-col items-center gap-3">
        {isLeft ? <LeafClusterGlyph color={accentColor} /> : <PulseWaveGlyph color={accentColor} />}
        <span
          className="block w-1.5 h-1.5 rounded-full"
          style={{
            backgroundColor: accentColor,
            boxShadow: `0 0 8px ${accentColor}`,
          }}
        />
      </div>
    </aside>
  )
}

/* ── Decorative glyphs — hairline SVG, stroke only ─────────────────────── */

function WindTurbineGlyph({ color }: { color: string }) {
  return (
    <svg width="26" height="32" viewBox="0 0 26 32" fill="none" aria-hidden>
      {/* Mast */}
      <line x1="13" y1="14" x2="13" y2="30" stroke={color} strokeWidth="1" />
      {/* Hub */}
      <circle cx="13" cy="14" r="1.5" stroke={color} strokeWidth="1" />
      {/* 3 blades */}
      <path d="M 13 13 Q 11 4 14 1" stroke={color} strokeWidth="1" strokeLinecap="round" />
      <path d="M 14 15 Q 23 16 25 13" stroke={color} strokeWidth="1" strokeLinecap="round" />
      <path d="M 12 15 Q 3 16 1 19" stroke={color} strokeWidth="1" strokeLinecap="round" />
      {/* Base */}
      <line x1="10" y1="30" x2="16" y2="30" stroke={color} strokeWidth="1" />
    </svg>
  )
}

function SolarPanelGlyph({ color }: { color: string }) {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden>
      {/* Panel grid */}
      <path d="M 5 8 L 21 8 L 24 22 L 2 22 Z" stroke={color} strokeWidth="1" fill="none" />
      <line x1="3.5" y1="15" x2="22.5" y2="15" stroke={color} strokeWidth="0.6" opacity="0.7" />
      <line x1="9" y1="8" x2="6" y2="22" stroke={color} strokeWidth="0.6" opacity="0.7" />
      <line x1="13" y1="8" x2="13" y2="22" stroke={color} strokeWidth="0.6" opacity="0.7" />
      <line x1="17" y1="8" x2="20" y2="22" stroke={color} strokeWidth="0.6" opacity="0.7" />
      {/* Sun rays */}
      <circle cx="20" cy="4" r="1.5" stroke={color} strokeWidth="0.8" />
      <line x1="20" y1="0.5" x2="20" y2="1.5" stroke={color} strokeWidth="0.6" />
      <line x1="23" y1="2" x2="22.2" y2="2.8" stroke={color} strokeWidth="0.6" />
    </svg>
  )
}

function LeafClusterGlyph({ color }: { color: string }) {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
      {/* Stem */}
      <line x1="14" y1="6" x2="14" y2="26" stroke={color} strokeWidth="1" />
      {/* Three leaves */}
      <path
        d="M 14 10 Q 22 8 21 14 Q 18 14 14 12"
        stroke={color}
        strokeWidth="1"
        fill="none"
      />
      <path
        d="M 14 16 Q 6 14 7 20 Q 10 20 14 18"
        stroke={color}
        strokeWidth="1"
        fill="none"
      />
      <path
        d="M 14 22 Q 22 20 21 26 Q 18 26 14 24"
        stroke={color}
        strokeWidth="1"
        fill="none"
      />
    </svg>
  )
}

function CircularGlyph({ color }: { color: string }) {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
      {/* Circular-economy curved arrows */}
      <path
        d="M 14 4 A 10 10 0 0 1 24 14"
        stroke={color}
        strokeWidth="1"
        fill="none"
        strokeLinecap="round"
      />
      <path d="M 21 11 L 24 14 L 21 17" stroke={color} strokeWidth="1" strokeLinecap="round" />
      <path
        d="M 14 24 A 10 10 0 0 1 4 14"
        stroke={color}
        strokeWidth="1"
        fill="none"
        strokeLinecap="round"
      />
      <path d="M 7 17 L 4 14 L 7 11" stroke={color} strokeWidth="1" strokeLinecap="round" />
      {/* Center accent */}
      <circle cx="14" cy="14" r="1.5" fill={color} />
    </svg>
  )
}

function BatteryGlyph({ color }: { color: string }) {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden>
      {/* Battery body */}
      <rect x="4" y="6" width="18" height="14" rx="1.5" stroke={color} strokeWidth="1" fill="none" />
      {/* Battery cap */}
      <rect x="22" y="10" width="2" height="6" rx="0.5" stroke={color} strokeWidth="1" fill="none" />
      {/* Charge cells */}
      <rect x="6" y="8" width="3" height="10" fill={color} opacity="0.9" />
      <rect x="10" y="8" width="3" height="10" fill={color} opacity="0.7" />
      <rect x="14" y="8" width="3" height="10" fill={color} opacity="0.5" />
      <rect x="18" y="8" width="2" height="10" stroke={color} strokeWidth="0.6" opacity="0.4" />
    </svg>
  )
}

function PulseWaveGlyph({ color }: { color: string }) {
  return (
    <svg width="28" height="20" viewBox="0 0 28 20" fill="none" aria-hidden>
      <path
        d="M 0 10 L 5 10 L 7 3 L 11 17 L 15 3 L 17 10 L 22 10 L 24 6 L 28 10"
        stroke={color}
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  )
}
