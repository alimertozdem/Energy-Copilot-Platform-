/**
 * HeroBand — page header banded across the viewport.
 *
 * Sits between AppChrome's top bar and the page content. Drives the visual
 * weight of the page identity: prominent title, pulsing accent dot,
 * page-coloured gradient background, and a thin bottom accent line that
 * connects the band to whatever follows it.
 *
 * Designed for `/buildings/[id]`, where the title changes with every PBI
 * tab click — the accent color and gradient transition smoothly to signal
 * the shift, while the building meta (subtitle) stays put.
 *
 * Sizing tuned to be present but not crowd the embed below: ~72px total.
 */

type HeroBandProps = {
  /** Title text (e.g. "Sustainability Compliance"). */
  title: string
  /** Optional smaller meta line below (e.g. building meta). */
  subtitle?: string
  /** Hex accent (e.g. "#1D9E75"). Drives gradient + dot color. */
  accentColor: string
}

export function HeroBand({ title, subtitle, accentColor }: HeroBandProps) {
  return (
    <div className="relative w-full overflow-hidden border-b border-border-subtle/40 z-10">
      {/* Background gradient — strong on the left, fades right. */}
      <div
        className="absolute inset-0 transition-all duration-700"
        aria-hidden
        style={{
          background: `linear-gradient(105deg, ${accentColor}22 0%, ${accentColor}0A 28%, transparent 65%)`,
        }}
      />

      {/* Decorative diagonal stripe — subtle texture catching the light. */}
      <div
        className="absolute inset-y-0 left-0 w-1/2 transition-opacity duration-700"
        aria-hidden
        style={{
          background: `repeating-linear-gradient(115deg, transparent 0 14px, ${accentColor}08 14px 15px)`,
        }}
      />

      {/* Bottom accent line — soft horizontal gradient seam. */}
      <div
        className="absolute bottom-0 left-0 right-0 h-px transition-all duration-700"
        aria-hidden
        style={{
          background: `linear-gradient(90deg, ${accentColor}99 0%, ${accentColor}55 25%, ${accentColor}1A 60%, transparent 100%)`,
        }}
      />

      <div className="relative px-6 py-3.5 max-w-7xl mx-auto">
        <div className="flex items-center gap-2.5">
          {/* Pulsing accent dot */}
          <span
            className="relative inline-flex shrink-0 w-2.5 h-2.5"
            aria-hidden
          >
            <span
              className="absolute inset-0 rounded-full opacity-60 animate-ping"
              style={{ backgroundColor: accentColor }}
            />
            <span
              className="relative w-2.5 h-2.5 rounded-full"
              style={{
                backgroundColor: accentColor,
                boxShadow: `0 0 10px ${accentColor}99`,
              }}
            />
          </span>

          <h1 className="text-xl md:text-2xl font-semibold text-text-primary tracking-tight transition-colors duration-500">
            {title}
          </h1>
        </div>

        {subtitle && (
          <p className="text-xs text-text-muted mt-1 ml-5 truncate">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  )
}
