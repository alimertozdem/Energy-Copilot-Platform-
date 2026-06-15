"use client"

/**
 * EnergyParticles — a living field of rising "energy motes" behind app content.
 *
 * Design language (2026-06-15, Mert: "animasyon dozu zayıf → daha güçlü + yaratıcı,
 * bütün sayfalara"). Accent-tinted glowing particles drift upward + sideways with
 * varied speed/size, like sparks of energy / photosynthetic motes. Rendered behind
 * content (z-0) inside AppChrome, so every authenticated page gets visible motion
 * without hurting readability (cards sit above with their own background).
 *
 * Self-contained: keyframes ship in an inline <style> (no globals.css dependency,
 * which the dev server doesn't always recompile). Deterministic particle layout
 * (seeded PRNG) so server and client markup match — no hydration drift. Fully
 * disabled under prefers-reduced-motion.
 */
import type { CSSProperties } from "react"

const COUNT = 14

// Seeded PRNG (mulberry32) → identical values on server + client (no hydration mismatch).
function mulberry32(a: number) {
  return function () {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const rand = mulberry32(20260615)
const PARTICLES = Array.from({ length: COUNT }, () => ({
  left: rand() * 100,
  bottom: rand() * 100,
  size: 2 + rand() * 6,
  dur: 9 + rand() * 12,
  delay: -rand() * 20,
  dx: (rand() * 2 - 1) * 60,
  op: 0.32 + rand() * 0.45,
}))

export function EnergyParticles({ color = "#1D9E75" }: { color?: string }) {
  return (
    <div
      className="el-field"
      aria-hidden
      style={{ "--el-accent": color } as CSSProperties}
    >
      <style>{`
        .el-field{position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:0}
        .el-field .p{position:absolute;border-radius:9999px;
          background:radial-gradient(circle, var(--el-accent,#1D9E75) 0%, transparent 68%);
          animation:el-rise var(--d,12s) linear infinite;animation-delay:var(--dl,0s);opacity:0}
        @keyframes el-rise{
          0%{transform:translate(0,0) scale(.6);opacity:0}
          12%{opacity:var(--op,.5)}
          50%{transform:translate(calc(var(--dx,0px) * .5),-48vh) scale(1)}
          86%{opacity:var(--op,.5)}
          100%{transform:translate(var(--dx,0px),-96vh) scale(.55);opacity:0}}
        @media (prefers-reduced-motion: reduce){.el-field .p{animation:none;opacity:.16}}
      `}</style>
      {PARTICLES.map((p, i) => (
        <span
          key={i}
          className="p"
          style={
            {
              left: `${p.left}%`,
              bottom: `${p.bottom}%`,
              width: p.size,
              height: p.size,
              "--d": `${p.dur}s`,
              "--dl": `${p.delay}s`,
              "--dx": `${p.dx}px`,
              "--op": p.op,
            } as CSSProperties
          }
        />
      ))}
    </div>
  )
}
