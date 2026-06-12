"use client"

/**
 * AlertDetailPanel — right slide-over with the full anomaly + remediation guide.
 *
 * Opened from an /alerts row (AlertsShell holds the selected alert). Turns a raw
 * anomaly into something actionable: what was detected, reading vs threshold,
 * triage, then plain-language guidance from lib/anomalyGuide (what it means,
 * likely causes, what to check, what to do if it persists) plus the pipeline's
 * own recommended action. Closes on backdrop click or Escape.
 */
import Link from "next/link"
import { useEffect, useState, type ReactNode } from "react"
import { createPortal } from "react-dom"

import { InfoTip } from "@/components/ui/info-tip"
import { anomalyGuide, estAnomalyCostEur } from "@/lib/anomalyGuide"
import type { AckStatus, AlertItem } from "@/lib/api/alerts"

import { AlertAckDropdown } from "./AlertAckDropdown"
import { SeverityBadge } from "./SeverityBadge"

function fmtNum(v: number | null): string {
  if (v === null) return "—"
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(v)
}

function fmtDetected(iso: string | null): string {
  if (!iso) return "—"
  const [d, t] = iso.split("T")
  return t ? `${d} ${t.slice(0, 5)}` : d
}

export function AlertDetailPanel({
  alert,
  pending,
  onClose,
  onAckChange,
}: {
  alert: AlertItem | null
  pending: boolean
  onClose: () => void
  onAckChange: (anomaly_id: string, next: AckStatus) => void
}) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  useEffect(() => {
    if (!alert) return
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [alert, onClose])

  if (!alert || !mounted) return null

  const guide = anomalyGuide(alert.anomaly_type)
  const aid = alert.anomaly_id
  const dev = alert.deviation_pct
  const estCost = estAnomalyCostEur(
    alert.anomaly_type,
    alert.metric_value,
    alert.threshold_value,
  )

  // Portal to <body> so the overlay escapes any transformed/blurred ancestor
  // (otherwise a `fixed` panel gets trapped below the sticky app header).
  return createPortal(
    <div
      className="fixed inset-0 z-[60] flex justify-end"
      role="dialog"
      aria-modal="true"
      aria-label="Alert details"
    >
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />

      <div className="relative h-full w-full max-w-md overflow-y-auto border-l border-white/10 bg-zinc-950 shadow-2xl">
        <div className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-white/10 bg-zinc-950/95 backdrop-blur-sm px-5 py-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <SeverityBadge severity={alert.severity} />
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border tracking-wider uppercase bg-white/5 text-white/70 border-white/15">
                {alert.anomaly_type ?? "—"}
              </span>
            </div>
            <h2 className="text-sm font-semibold text-white">{guide.category}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close details"
            className="shrink-0 rounded-md p-1 text-white/50 hover:text-white hover:bg-white/10 transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-5 py-5 space-y-6 text-sm">
          <div className="space-y-3">
            <Link
              href={`/buildings/${alert.fabric_building_id}`}
              className="inline-flex items-center gap-1 text-white hover:text-emerald-300 transition-colors font-medium"
            >
              {alert.building_name}
              <span className="text-white/40 text-xs">{alert.fabric_building_id}</span>
            </Link>
            <div className="grid grid-cols-2 gap-3">
              <Meta label="Detected" value={fmtDetected(alert.detected_at)} />
              <Meta label="State" value={alert.is_resolved ? "Resolved" : "Open"} />
              <Meta label="Reading" value={`${fmtNum(alert.metric_value)} vs ${fmtNum(alert.threshold_value)}`} />
              <Meta
                label="Deviation"
                value={dev === null ? "—" : `${dev > 0 ? "+" : ""}${dev.toFixed(0)}%`}
                tone={dev !== null && dev > 0 ? "bad" : "ok"}
              />
            </div>
            {estCost != null && (
              <div className="flex items-center justify-between rounded-lg border border-amber-400/20 bg-amber-400/5 px-3 py-2">
                <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.12em] text-amber-200/70">
                  Est. impact
                  <InfoTip term="anomaly_cost" />
                </span>
                <span className="text-sm font-semibold tabular-nums text-amber-200">
                  ~€{estCost.toLocaleString("en-US", { maximumFractionDigits: 0 })}
                </span>
              </div>
            )}
          </div>

          {alert.description && (
            <Section title="What was detected">
              <p className="text-white/80 leading-relaxed">{alert.description}</p>
            </Section>
          )}

          {aid != null && (
            <Section title="Triage">
              <div className="flex items-center gap-3">
                <AlertAckDropdown
                  ackStatus={alert.ack_status}
                  pending={pending}
                  onChange={(next) => onAckChange(aid, next)}
                />
                <span className="text-xs text-white/45">
                  Mark this alert as acknowledged or dismissed.
                </span>
              </div>
            </Section>
          )}

          <Section title="What this means">
            <p className="text-white/80 leading-relaxed">{guide.whatItMeans}</p>
          </Section>

          <Section title="Likely causes">
            <ul className="space-y-1.5">
              {guide.likelyCauses.map((c, i) => (
                <li key={i} className="flex gap-2 text-white/80">
                  <span className="text-white/30 mt-0.5">•</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </Section>

          <Section title="What to check">
            <ul className="space-y-1.5">
              {guide.whatToCheck.map((c, i) => (
                <li key={i} className="flex gap-2 text-white/80">
                  <span className="text-emerald-400/70 mt-0.5">✓</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </Section>

          {alert.recommended_action && (
            <Section title="Recommended action">
              <p className="text-white/80 leading-relaxed">{alert.recommended_action}</p>
            </Section>
          )}

          <Section title="If it persists">
            <p className="text-white/80 leading-relaxed">{guide.ifItPersists}</p>
          </Section>

          <p className="text-[11px] text-white/35 leading-relaxed border-t border-white/10 pt-4">
            General operational guidance, not a site-specific diagnosis. Confirm on
            site and follow local maintenance procedures.
          </p>
        </div>
      </div>
    </div>,
    document.body
  )
}

function Meta({
  label,
  value,
  tone,
}: {
  label: string
  value: string
  tone?: "ok" | "bad"
}) {
  const vc =
    tone === "bad"
      ? "text-red-300"
      : tone === "ok"
        ? "text-emerald-300"
        : "text-white/90"
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.12em] text-white/40">{label}</div>
      <div className={`text-sm font-medium tabular-nums mt-0.5 ${vc}`}>{value}</div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-[11px] uppercase tracking-[0.12em] text-white/45 font-medium">
        {title}
      </h3>
      {children}
    </div>
  )
}
