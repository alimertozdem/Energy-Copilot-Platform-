/**
 * reportKit — shared building blocks for the print/PDF reports.
 *
 * The /actions and /alerts report documents render their own body (tables +
 * summary cards) and plug into <ReportFrame>, which owns the light page
 * wrapper, the print stylesheet (@page A4 landscape + print-color-adjust), the
 * no-print toolbar (Back link + PrintButton), the branded navy header band and
 * the footer. Everything is inline-styled (light, print-safe) and independent
 * of the app's dark Tailwind theme.
 *
 * (The Day 39 /portfolio report predates this kit and keeps its own inline
 * implementation; it can be migrated here later for one source of truth.)
 */
import type { CSSProperties, ReactNode } from "react"

import Link from "next/link"

import { PrintButton } from "./PrintButton"

// ---- light, print-friendly palette ----
export const INK = "#1e293b"
export const MUTED = "#64748b"
export const FAINT = "#94a3b8"
export const LINE = "#e2e8f0"
export const EMERALD = "#1D9E75"
export const DEEP = "#0F6E56"
export const NAVY = "#0A1628"
export const GOOD = "#0F6E56"
export const BAD = "#b45309"
export const DANGER = "#b91c1c"

// ---- formatters (mirror on-screen conventions) ----
const intFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 })

export function fmtInt(v: number | null): string {
  return v === null ? "—" : intFmt.format(v)
}

export function fmtCompact(value: number | null, digits = 1): string {
  if (value === null) return "—"
  if (Math.abs(value) >= 10_000) {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: digits,
    }).format(value)
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value)
}

export function fmtMoney(value: number | null): string {
  return value === null ? "—" : "€" + fmtCompact(value)
}

export function fmtNum(value: number | null): string {
  if (value === null) return "—"
  const abs = Math.abs(value)
  if (abs >= 10_000) {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: 1,
    }).format(value)
  }
  if (abs >= 100) {
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value)
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value)
}

/** ISO -> "YYYY-MM-DD HH:mm" (deterministic, no locale). */
export function fmtDateTime(iso: string | null): string {
  if (!iso) return "—"
  const [d, t] = iso.split("T")
  if (!t) return d
  return `${d} ${t.slice(0, 5)}`
}

// Payback display guard. A payback beyond ~40 years exceeds any equipment service
// life, so it is not a real financial payback — the measure is compliance / CO₂-
// driven. Show a dash rather than a misleading "999 yr".
export const MAX_PLAUSIBLE_PAYBACK_YEARS = 40
export function fmtPayback(years: number | null | undefined): string {
  if (years == null || years < 0 || years >= MAX_PLAUSIBLE_PAYBACK_YEARS) return "—"
  return `${years.toFixed(1)} yr`
}

// ---- table cell styles ----
const TH_BASE: CSSProperties = {
  padding: "8px 10px",
  fontSize: 10,
  letterSpacing: 0.6,
  textTransform: "uppercase",
  color: MUTED,
  fontWeight: 600,
  borderBottom: `2px solid ${LINE}`,
}
export function thStyle(align: "left" | "right" | "center" = "left"): CSSProperties {
  return { ...TH_BASE, textAlign: align }
}
const TD_BASE: CSSProperties = {
  padding: "7px 10px",
  fontVariantNumeric: "tabular-nums",
  borderBottom: `1px solid ${LINE}`,
  verticalAlign: "top",
}
export const tdL: CSSProperties = { ...TD_BASE, textAlign: "left" }
export const tdR: CSSProperties = { ...TD_BASE, textAlign: "right", whiteSpace: "nowrap" }
export const tdC: CSSProperties = { ...TD_BASE, textAlign: "center" }

// ---- small UI ----
export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        margin: "20px 0 9px",
        breakAfter: "avoid",
      }}
    >
      <span
        aria-hidden
        style={{ width: 4, height: 14, borderRadius: 2, backgroundColor: EMERALD, flexShrink: 0 }}
      />
      <span
        style={{
          fontSize: 12,
          fontWeight: 700,
          color: INK,
          textTransform: "uppercase",
          letterSpacing: 0.8,
        }}
      >
        {children}
      </span>
    </div>
  )
}

export function Notice({ error, label }: { error: string; label: string }) {
  const fabric = error === "fabric_unavailable"
  return (
    <div
      style={{
        padding: "10px 12px",
        borderRadius: 6,
        fontSize: 12,
        border: `1px solid ${fabric ? "#fcd34d" : "#fca5a5"}`,
        backgroundColor: fabric ? "#fffbeb" : "#fef2f2",
        color: fabric ? "#92400e" : "#991b1b",
      }}
    >
      {fabric
        ? `Live ${label} data is temporarily unavailable — please retry shortly.`
        : `Couldn't load ${label}.`}
    </div>
  )
}

export function Chip({ label, color }: { label: string; color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        border: `1px solid ${color}`,
        borderRadius: 999,
        color,
        fontWeight: 600,
        fontSize: 10,
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </span>
  )
}

export function StatCard({
  label,
  value,
  color = INK,
  hint,
}: {
  label: string
  value: number | string
  color?: string
  hint?: string
}) {
  return (
    <div
      style={{
        flex: 1,
        minWidth: 0,
        backgroundColor: "#ffffff",
        border: `1px solid ${LINE}`,
        borderTop: `3px solid ${EMERALD}`,
        borderRadius: 8,
        padding: "12px 14px",
        breakInside: "avoid",
      }}
    >
      <div
        style={{
          fontSize: 10,
          letterSpacing: 1.2,
          textTransform: "uppercase",
          color: MUTED,
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color, fontVariantNumeric: "tabular-nums" }}>
        {value}
      </div>
      {hint && <div style={{ marginTop: 4, fontSize: 10, color: FAINT }}>{hint}</div>}
    </div>
  )
}

// ---- print frame ----
const PRINT_CSS = `
  @page { size: A4 landscape; margin: 10mm; }
  html, body { -webkit-print-color-adjust: exact; print-color-adjust: exact; background: #f8fafc; }
  .report-surface table { border-collapse: collapse; }
  .report-surface thead { display: table-header-group; }
  .report-surface tr { break-inside: avoid; page-break-inside: avoid; }
  @media print {
    .no-print { display: none !important; }
    .report-surface { box-shadow: none !important; border-radius: 0 !important; margin: 0 !important; padding: 0 !important; }
  }
`

export function ReportFrame({
  backHref,
  backLabel = "Back",
  title,
  generatedAt,
  metaLine,
  footerCenter,
  children,
}: {
  backHref: string
  backLabel?: string
  title: string
  generatedAt: string
  metaLine?: string
  footerCenter?: string
  children: ReactNode
}) {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f8fafc" }}>
      <style dangerouslySetInnerHTML={{ __html: PRINT_CSS }} />

      <div
        className="no-print"
        style={{
          maxWidth: 1120,
          margin: "0 auto",
          padding: "16px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Link href={backHref} style={{ fontSize: 13, color: "#475569", textDecoration: "none" }}>
          ← {backLabel}
        </Link>
        <PrintButton />
      </div>

      <div
        className="report-surface"
        style={{
          maxWidth: 1120,
          margin: "0 auto 48px",
          backgroundColor: "#ffffff",
          borderRadius: 12,
          boxShadow: "0 1px 3px rgba(15,23,42,0.12)",
          padding: "28px 32px",
          color: INK,
          fontSize: 13,
          lineHeight: 1.5,
          fontFamily:
            "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            backgroundColor: NAVY,
            color: "#ffffff",
            borderRadius: 10,
            padding: "20px 24px",
            marginBottom: 8,
          }}
        >
          <div>
            <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: -0.5 }}>
              <span style={{ color: "#ffffff" }}>Energy</span>
              <span style={{ color: "#5DCAA5" }}>Lens</span>
            </div>
            <div style={{ fontSize: 12, color: "#9FB3C8", marginTop: 2 }}>
              Smart energy for smart buildings
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 16, fontWeight: 600 }}>{title}</div>
            <div style={{ fontSize: 11, color: "#9FB3C8", marginTop: 4 }}>
              Generated {generatedAt}
            </div>
            {metaLine && (
              <div style={{ fontSize: 11, color: "#9FB3C8", marginTop: 2 }}>{metaLine}</div>
            )}
          </div>
        </div>

        <div
          aria-hidden
          style={{ height: 3, backgroundColor: EMERALD, borderRadius: 999, margin: "0 2px 16px" }}
        />

        {children}

        <div
          style={{
            marginTop: 18,
            paddingTop: 10,
            borderTop: `1px solid ${LINE}`,
            display: "flex",
            justifyContent: "space-between",
            fontSize: 10,
            color: FAINT,
          }}
        >
          <span>energylens.eu · Confidential</span>
          <span>{footerCenter ?? ""}</span>
          <span>Generated {generatedAt}</span>
        </div>
      </div>
    </div>
  )
}
