/**
 * DataMatrixMotif — regular dot grid with scattered brighter "active" nodes,
 * meant to evoke sensor data, telemetry, anomaly heatmaps.
 *
 * Used on Anomalies (03), Occupancy (05), and IoT (08) pages where the
 * concept is discrete observations across a field.
 *
 * Anchored to the upper-right, balancing other motifs at lower corners.
 */
import { cn } from "@/lib/utils"

type DataMatrixMotifProps = {
  className?: string
  opacity?: number
}

// Pre-computed scattered "active" cells in the grid (col, row) pairs.
// Hand-picked to look organic, not random.
const ACTIVE_CELLS: ReadonlyArray<[number, number]> = [
  [2, 3],
  [5, 2],
  [8, 4],
  [11, 1],
  [3, 7],
  [7, 6],
  [10, 8],
  [4, 10],
  [9, 11],
  [12, 7],
]

// Grid dimensions
const COLS = 14
const ROWS = 12
const CELL = 22

export function DataMatrixMotif({
  className,
  opacity = 0.2,
}: DataMatrixMotifProps) {
  const width = COLS * CELL
  const height = ROWS * CELL

  // Build dot grid
  const baseDots: React.ReactElement[] = []
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      baseDots.push(
        <circle
          key={`${c}-${r}`}
          cx={c * CELL + CELL / 2}
          cy={r * CELL + CELL / 2}
          r="1"
          fill="#5DCAA5"
          opacity="0.5"
        />
      )
    }
  }

  return (
    <div
      className={cn(
        "fixed top-24 right-0 pointer-events-none select-none z-0",
        className
      )}
      style={{ opacity, filter: "grayscale(1) brightness(1.7)", transform: "scale(1.2)", transformOrigin: "top right" }}
      aria-hidden
    >
      <svg
        width={width}
        height={height + 20}
        viewBox={`0 0 ${width} ${height + 20}`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
      >
        {/* Base dot grid */}
        {baseDots}

        {/* Connecting lines between a few active cells */}
        <g stroke="#5DCAA5" strokeWidth="0.4" opacity="0.4">
          <line
            x1={ACTIVE_CELLS[0][0] * CELL + CELL / 2}
            y1={ACTIVE_CELLS[0][1] * CELL + CELL / 2}
            x2={ACTIVE_CELLS[1][0] * CELL + CELL / 2}
            y2={ACTIVE_CELLS[1][1] * CELL + CELL / 2}
          />
          <line
            x1={ACTIVE_CELLS[2][0] * CELL + CELL / 2}
            y1={ACTIVE_CELLS[2][1] * CELL + CELL / 2}
            x2={ACTIVE_CELLS[3][0] * CELL + CELL / 2}
            y2={ACTIVE_CELLS[3][1] * CELL + CELL / 2}
          />
          <line
            x1={ACTIVE_CELLS[4][0] * CELL + CELL / 2}
            y1={ACTIVE_CELLS[4][1] * CELL + CELL / 2}
            x2={ACTIVE_CELLS[5][0] * CELL + CELL / 2}
            y2={ACTIVE_CELLS[5][1] * CELL + CELL / 2}
          />
        </g>

        {/* Active nodes — brighter, larger, glow-tinted */}
        {ACTIVE_CELLS.map(([c, r], i) => (
          <g key={`active-${i}`} className="el-twinkle" style={{ animationDelay: `${i * 0.32}s` }}>
            <circle
              cx={c * CELL + CELL / 2}
              cy={r * CELL + CELL / 2}
              r="3"
              stroke="#C0DD97"
              strokeWidth="0.8"
              fill="none"
            />
            <circle
              cx={c * CELL + CELL / 2}
              cy={r * CELL + CELL / 2}
              r="1.4"
              fill="#C0DD97"
            />
          </g>
        ))}

        {/* Annotation */}
        <g
          fill="#5DCAA5"
          fontFamily="Inter, system-ui, sans-serif"
          fontSize="6"
          letterSpacing="0.15em"
        >
          <text x={width - 130} y={height + 14}>
            MATRIX · OBSERVATIONAL
          </text>
        </g>
      </svg>
    </div>
  )
}
