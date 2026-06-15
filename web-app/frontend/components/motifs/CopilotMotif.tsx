/**
 * CopilotMotif — a small neural constellation: nodes linked into a network with a
 * bright reasoning core. Page-identity backdrop for the Copilot page — the user
 * should feel "this is the AI assistant" at a glance.
 *
 * Greyscaled + scaled at the wrapper. Nodes twinkle (staggered); the core breathes.
 */
import { cn } from "@/lib/utils"

type CopilotMotifProps = {
  className?: string
  opacity?: number
}

// node coords + a twinkle delay each, hand-placed to look like a reasoning graph
const NODES: ReadonlyArray<[number, number, number]> = [
  [60, 70, 0],
  [150, 40, 0.5],
  [120, 150, 1.1],
  [210, 110, 0.3],
  [300, 60, 0.8],
  [280, 170, 1.4],
  [360, 120, 0.6],
]

const EDGES: ReadonlyArray<[number, number]> = [
  [0, 1],
  [0, 2],
  [1, 3],
  [2, 3],
  [3, 4],
  [3, 5],
  [4, 6],
  [5, 6],
]

export function CopilotMotif({ className, opacity = 0.2 }: CopilotMotifProps) {
  return (
    <div
      className={cn(
        "fixed top-28 right-0 pointer-events-none select-none z-0",
        className
      )}
      style={{
        opacity,
        filter: "grayscale(1) brightness(1.7)",
        transform: "scale(1.3)",
        transformOrigin: "top right",
      }}
      aria-hidden
    >
      <svg width="420" height="240" viewBox="0 0 420 240" xmlns="http://www.w3.org/2000/svg" fill="none">
        {/* ── Edges ─────────────────────────────────────────────────── */}
        <g stroke="#5DCAA5" strokeWidth="0.5" opacity="0.55">
          {EDGES.map(([a, b], i) => (
            <line key={i} x1={NODES[a][0]} y1={NODES[a][1]} x2={NODES[b][0]} y2={NODES[b][1]} />
          ))}
        </g>

        {/* ── Nodes (twinkling) ─────────────────────────────────────── */}
        {NODES.map(([x, y, d], i) => (
          <g key={i} className="el-twinkle" style={{ animationDelay: `${d}s` }}>
            <circle cx={x} cy={y} r="4.5" stroke="#5DCAA5" strokeWidth="0.7" fill="none" />
            <circle cx={x} cy={y} r="1.6" fill="#C0DD97" />
          </g>
        ))}

        {/* ── Reasoning core — central larger node with a 4-point spark ── */}
        <g className="el-breathe">
          <circle cx="210" cy="110" r="13" stroke="#C0DD97" strokeWidth="0.8" fill="none" />
          <g stroke="#C0DD97" strokeWidth="1" strokeLinecap="round">
            <line x1="210" y1="99" x2="210" y2="121" />
            <line x1="199" y1="110" x2="221" y2="110" />
          </g>
        </g>

        {/* ── Annotation ────────────────────────────────────────────── */}
        <g fill="#5DCAA5" fontFamily="Inter, system-ui, sans-serif" fontSize="6" letterSpacing="0.15em">
          <text x="60" y="220">AI · COPILOT · REASONING</text>
        </g>
      </svg>
    </div>
  )
}
