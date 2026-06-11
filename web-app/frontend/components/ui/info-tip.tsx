"use client"

import * as React from "react"
import { Tooltip as TooltipPrimitive } from "radix-ui"
import { Info } from "lucide-react"

import { cn } from "@/lib/utils"
import { GLOSSARY, CONFIDENCE_NOTE, type TermKey } from "@/lib/glossary"

/**
 * InfoTip — a small accessible "i" trigger that reveals a glossary term's
 * definition AND (when present) how the figure is calculated, on hover OR
 * keyboard focus.
 *
 * Built on radix Tooltip, so it ships with focus management, Escape-to-close
 * and aria-describedby wiring for free. Each instance carries its own
 * Provider, so callers never need to mount one at the app root.
 *
 * Safe to drop inside a sortable <th> or a row <Link>: the trigger stops
 * click/pointer propagation so it won't toggle a column sort or follow a link.
 */
export function InfoTip({
  term,
  label,
  className,
}: {
  term: TermKey
  /** Override the aria label / heading; defaults to the glossary label. */
  label?: string
  className?: string
}) {
  const entry = GLOSSARY[term]
  if (!entry) return null
  const heading = label ?? entry.label

  return (
    <TooltipPrimitive.Provider delayDuration={120} skipDelayDuration={300}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          <button
            type="button"
            aria-label={`What is ${heading}?`}
            onClick={(e) => e.stopPropagation()}
            onPointerDown={(e) => e.stopPropagation()}
            className={cn(
              "inline-flex items-center justify-center align-middle cursor-help",
              "text-white/35 hover:text-white/70 focus-visible:text-white/80",
              "transition-colors",
              className
            )}
          >
            <Info className="w-3 h-3" aria-hidden />
          </button>
        </TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side="top"
            align="center"
            sideOffset={6}
            collisionPadding={8}
            className={cn(
              "z-50 max-w-[320px] rounded-lg border border-white/15 bg-zinc-900/95",
              "px-3 py-2 text-xs leading-relaxed text-white/90 shadow-xl backdrop-blur-md"
            )}
          >
            <span className="block font-semibold text-white mb-0.5">
              {entry.label}
            </span>
            {entry.short}
            {entry.method && (
              <span className="mt-2 block border-t border-white/10 pt-2">
                <span className="block text-[10px] font-semibold uppercase tracking-wide text-white/45">
                  How it&rsquo;s calculated
                </span>
                <span className="mt-0.5 block text-white/90">{entry.method}</span>
                {entry.assumptions && entry.assumptions.length > 0 && (
                  <span className="mt-1 block">
                    {entry.assumptions.map((a) => (
                      <span key={a} className="block text-[11px] text-white/60">
                        • {a}
                      </span>
                    ))}
                  </span>
                )}
                {entry.confidence && (
                  <span className="mt-1.5 block text-[11px] italic text-white/55">
                    {CONFIDENCE_NOTE[entry.confidence]}
                  </span>
                )}
              </span>
            )}
            <TooltipPrimitive.Arrow className="fill-zinc-900" width={11} height={6} />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  )
}

/**
 * TermLabel — a label followed by its InfoTip. Handy for table headers:
 *
 *   header: () => <TermLabel term="eui">EUI</TermLabel>
 */
export function TermLabel({
  term,
  children,
  className,
}: {
  term: TermKey
  children: React.ReactNode
  className?: string
}) {
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      {children}
      <InfoTip term={term} />
    </span>
  )
}
