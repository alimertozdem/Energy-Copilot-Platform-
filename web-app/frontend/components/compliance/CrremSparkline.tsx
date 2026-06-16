/**
 * CrremSparkline — inline per-building CRREM pathway chart (design B, 2026-06-16).
 *
 * Draws the descending 1.5C target pathway for the building's type, the
 * building's (held-flat) carbon intensity as a horizontal line, and a marker at
 * the stranding point (where the flat line first exceeds the pathway). Pure SVG,
 * no chart lib. Indicative — pathway anchors are illustrative (see lib/crrem).
 * Server component.
 */
import {
  PATHWAY_END_YEAR,
  PATHWAY_START_YEAR,
  pathwayPoints,
  pathwayStart,
  type StrandingStatus,
} from "@/lib/crrem"

const W = 132
const H = 38
const PAD_L = 3
const PAD_R = 5
const PAD_T = 5
const PAD_B = 5

type Props = {
  buildingType: string
  intensity: number | null
  strandingYear: number | null
  status: StrandingStatus
  className?: string
}

const STROKE: Record<StrandingStatus, string> = {
  stranded_now: "#FCA5A5", // red-300
  stranding: "#FCD34D", // amber-300
  on_track: "#6EE7B7", // emerald-300
  unknown: "#475569", // slate-600
}

export function CrremSparkline({
  buildingType,
  intensity,
  strandingYear,
  status,
  className,
}: Props) {
  const pts = pathwayPoints(buildingType, 5)
  const start = pathwayStart(buildingType)
  const yMax = Math.max(start, intensity ?? 0) * 1.12 || 1

  const mapX = (year: number) =>
    PAD_L +
    ((year - PATHWAY_START_YEAR) / (PATHWAY_END_YEAR - PATHWAY_START_YEAR)) *
      (W - PAD_L - PAD_R)
  const mapY = (val: number) =>
    PAD_T + (1 - val / yMax) * (H - PAD_T - PAD_B)

  const pathwayD = pts
    .map((p, i) => `${i === 0 ? "M" : "L"} ${mapX(p.year).toFixed(1)} ${mapY(p.value).toFixed(1)}`)
    .join(" ")

  const color = STROKE[status]

  if (intensity == null) {
    return (
      <svg viewBox={`0 0 ${W} ${H}`} className={className} aria-hidden fill="none">
        <line
          x1={PAD_L}
          y1={H / 2}
          x2={W - PAD_R}
          y2={H / 2}
          stroke="#475569"
          strokeWidth="1"
          strokeDasharray="3 3"
          opacity="0.6"
        />
      </svg>
    )
  }

  const yFlat = mapY(intensity)
  const showMarker = status === "stranded_now" || status === "stranding"
  const markerYear = strandingYear ?? PATHWAY_START_YEAR
  const markerX = mapX(markerYear)

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className={className}
      role="img"
      aria-label={`CRREM pathway, status ${status.replace(/_/g, " ")}`}
      fill="none"
    >
      {/* target pathway (descending, dashed) */}
      <path
        d={pathwayD}
        stroke="#5DCAA5"
        strokeWidth="1.1"
        strokeDasharray="4 3"
        strokeLinecap="round"
        opacity="0.5"
      />
      {/* building intensity, held flat */}
      <line
        x1={PAD_L}
        y1={yFlat}
        x2={W - PAD_R}
        y2={yFlat}
        stroke={color}
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      {/* stranding marker */}
      {showMarker && (
        <g>
          {/* breathing halo (CSS el-breathe — auto-damped under reduced-motion) */}
          <circle cx={markerX} cy={yFlat} r="5.5" fill={color} opacity="0.22" className="el-breathe" />
          <circle cx={markerX} cy={yFlat} r="3.2" fill={color} />
        </g>
      )}
    </svg>
  )
}
