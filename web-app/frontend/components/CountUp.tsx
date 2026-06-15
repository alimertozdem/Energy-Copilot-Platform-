"use client"

/**
 * CountUp — animates a number from 0 to its value on mount (design language: "alive").
 * Cubic ease-out, ~1.2s. Mirrors the dashboard's fmt(): integers for >=1000, else 1 decimal.
 * Respects prefers-reduced-motion (jumps straight to the value).
 */

import { useEffect, useRef, useState } from "react"

function format(n: number): string {
  return Math.abs(n) >= 1000
    ? Math.round(n).toLocaleString("en-US")
    : n.toLocaleString("en-US", { maximumFractionDigits: 1 })
}

export function CountUp({ value, durationMs = 1200 }: { value: number; durationMs?: number }) {
  const [n, setN] = useState(value)
  const started = useRef(false)

  useEffect(() => {
    if (started.current) return
    started.current = true

    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    if (reduce) {
      setN(value)
      return
    }

    setN(0)
    const start = performance.now()
    let raf = 0
    const tick = (now: number) => {
      const p = Math.min((now - start) / durationMs, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setN(value * eased)
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, durationMs])

  return <span suppressHydrationWarning>{format(n)}</span>
}
