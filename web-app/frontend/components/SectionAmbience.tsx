/**
 * SectionAmbience — living, section-tinted energy backdrop (design language, 2026-06-15 v2).
 *
 * Each section passes its accentColor (portfolio emerald, compliance teal, solar amber,
 * copilot purple…). Renders a strong top wash + slow-drifting auroras in that accent, so
 * the screen visibly "transforms" per section — the green-energy / sustainability mood Mert
 * wants. Behind ALL content (pointer-events-none, aria-hidden); cards keep their own bg so
 * text stays readable. CSS-only (el-aurora) → auto-damped by prefers-reduced-motion.
 *
 * NOTE: only shows on the React app shell — NOT inside embedded Power BI report iframes.
 */

export function SectionAmbience({ color }: { color?: string }) {
  const accent = color ?? "#1D9E75"
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {/* strong accent wash down from the header — the section's mood */}
      <div
        className="absolute inset-x-0 top-0 h-[30rem] transition-all duration-700"
        style={{
          background: `radial-gradient(120% 72% at 50% -12%, ${accent}52 0%, ${accent}26 34%, transparent 66%)`,
        }}
      />
      {/* drifting energy auroras (clearly visible, still behind content) */}
      <div
        className="el-aurora"
        style={{
          top: "-6%",
          left: "50%",
          width: 640,
          height: 640,
          background: `radial-gradient(circle, ${accent}82, transparent 70%)`,
        }}
      />
      <div
        className="el-aurora"
        style={{
          bottom: "-12%",
          left: "-8%",
          width: 520,
          height: 520,
          background: `radial-gradient(circle, ${accent}5e, transparent 70%)`,
          animationDelay: "-7s",
          animationDuration: "24s",
        }}
      />
      <div
        className="el-aurora"
        style={{
          top: "28%",
          right: "-6%",
          width: 440,
          height: 440,
          background: `radial-gradient(circle, ${accent}4c, transparent 70%)`,
          animationDelay: "-13s",
          animationDuration: "30s",
        }}
      />
    </div>
  )
}
