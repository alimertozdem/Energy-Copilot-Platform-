/**
 * GlassCard — the /compliance "glass" surface (design language 2026-06-16).
 *
 * A translucent, backdrop-blurred panel that sits above the global
 * EnergyParticles field so page motion shows through the chrome without
 * hurting readability. One reusable surface for every compliance section,
 * stat tile and table so the page reads as a single system, not ten ad-hoc
 * boxes. Server-component safe (no hooks).
 *
 * Tokens: border-white/10 hairline, inset white ring (top highlight), soft
 * drop shadow, optional accent top-edge gradient driven by `accent`.
 */
import * as React from "react"

import { cn } from "@/lib/utils"

/** Shared glass surface classes — use directly where a wrapper isn't wanted. */
export const glassClass =
  "relative overflow-hidden rounded-2xl border border-white/10 " +
  "bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.015))] " +
  "backdrop-blur-xl ring-1 ring-inset ring-white/[0.04] " +
  "shadow-[0_10px_30px_-14px_rgba(0,0,0,0.6)]"

type GlassCardProps = React.HTMLAttributes<HTMLDivElement> & {
  /** Accent hex for the top-edge gradient + hover tint (e.g. the page accent). */
  accent?: string
  /** Adds hover affordance (border/bg lift). Use for clickable cards. */
  interactive?: boolean
}

export function GlassCard({
  accent,
  interactive,
  className,
  children,
  style,
  ...rest
}: GlassCardProps) {
  return (
    <div
      className={cn(
        glassClass,
        interactive &&
          "transition-colors duration-200 hover:border-white/20 hover:bg-white/[0.06]",
        className
      )}
      style={
        accent
          ? ({ ...style, "--gc-accent": accent } as React.CSSProperties)
          : style
      }
      {...rest}
    >
      {accent && (
        <span
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px opacity-70"
          style={{
            background:
              "linear-gradient(90deg, transparent, var(--gc-accent), transparent)",
          }}
        />
      )}
      {children}
    </div>
  )
}
