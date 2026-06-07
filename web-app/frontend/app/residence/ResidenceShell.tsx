"use client"

/**
 * ResidenceShell — client root for the public /residence (resident) view.
 *
 * Lightweight, NO Power BI embed. A tenant sees ONLY their own unit plus an
 * anonymized building benchmark (the comparison is pre-aggregated into their own
 * Gold row server-side — neighbors' data is never fetched). Cards:
 *   1. Efficiency rating (EUI + EPC band)
 *   2. Compared to my building (anonymized vs-average)
 *   3. Shared areas (HKVO 70/30 allocation)
 *   4. My yearly use (annualized heating + hot water)
 * plus a monthly consumption (UVI) bar trend — the EED/HKVO monthly information.
 *
 * Copy is written for tenants (lay audience), not energy professionals.
 */
import { useState, type ReactNode } from "react"
import Link from "next/link"
import { Home, Info, Lightbulb } from "lucide-react"

import { LogoCard } from "@/app/components/LogoCard"
import type {
  ResidenceSummary,
  ResidenceUnit,
  ResidenceMonthlyPoint,
} from "@/lib/api/residence"

const ACCENT = "#10b981"
const MONTHS = [
  "",
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
const EPC_COLORS: Record<string, string> = {
  A: "#10b981", B: "#34d399", C: "#a3e635", D: "#fbbf24", E: "#f87171",
}

type Props = {
  summary: ResidenceSummary | null
  loadError: string | null
  hasIdentity: boolean
  residentId?: string | null
}

function fmt(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—"
  return n.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function vsBuildingLabel(pct: number | null): { text: string; tone: "good" | "bad" | "neutral" } {
  if (pct === null || pct === undefined) return { text: "No comparison available yet", tone: "neutral" }
  if (Math.abs(pct) < 0.5) return { text: "About the same as your building average", tone: "neutral" }
  if (pct < 0) return { text: `${fmt(Math.abs(pct), 0)}% below your building average`, tone: "good" }
  return { text: `${fmt(pct, 0)}% above your building average`, tone: "bad" }
}

type MonthAgg = {
  year: number
  month: number
  kwh: number
  cost: number | null
  buildingAvg: number | null
  hasData: boolean
}

function aggregateMonthly(points: ResidenceMonthlyPoint[]): MonthAgg[] {
  const map = new Map<string, MonthAgg>()
  for (const p of points) {
    const key = `${p.year}-${String(p.month).padStart(2, "0")}`
    const cur =
      map.get(key) ??
      { year: p.year, month: p.month, kwh: 0, cost: null, buildingAvg: null, hasData: false }
    if (p.kwh !== null && p.kwh !== undefined) {
      cur.kwh += p.kwh
      cur.hasData = true
    }
    if (p.cost_eur !== null && p.cost_eur !== undefined) {
      cur.cost = (cur.cost ?? 0) + p.cost_eur
    }
    if (p.building_avg_kwh !== null && p.building_avg_kwh !== undefined) {
      cur.buildingAvg = (cur.buildingAvg ?? 0) + p.building_avg_kwh
    }
    map.set(key, cur)
  }
  return [...map.values()].sort((a, b) => a.year - b.year || a.month - b.month)
}

// ---------------------------------------------------------------------------

function Card({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5">
      {children}
    </div>
  )
}

function CardLabel({ children }: { children: ReactNode }) {
  return (
    <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
      {children}
    </p>
  )
}

function RatingCard({ unit }: { unit: ResidenceUnit }) {
  const k = unit.kpi
  const band = k?.epc_band ?? null
  const color = band ? EPC_COLORS[band] ?? "#94a3b8" : "#94a3b8"
  const adjusted = k?.climate_adjustment_factor != null && Math.abs(k.climate_adjustment_factor - 1) > 0.001
  return (
    <Card>
      <CardLabel>Efficiency rating</CardLabel>
      <div className="mt-3 flex items-center gap-4">
        <div
          className="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl text-3xl font-bold text-bg-base"
          style={{ background: color }}
          aria-label={band ? `EPC band ${band}` : "EPC band not available"}
        >
          {band ?? "—"}
        </div>
        <div className="min-w-0">
          <p className="text-2xl font-semibold text-text-primary">
            {fmt(k?.eui_kwh_m2_yr, 0)}{" "}
            <span className="text-sm font-normal text-text-muted">kWh/m²·yr</span>
          </p>
          <p className="mt-0.5 text-xs text-text-muted">
            Heating + hot water, per m² of living space
            {adjusted ? " · climate-adjusted" : ""}
          </p>
        </div>
      </div>
    </Card>
  )
}

function VsBuildingCard({ unit }: { unit: ResidenceUnit }) {
  const k = unit.kpi
  const v = vsBuildingLabel(k?.vs_building_pct ?? null)
  const toneClass =
    v.tone === "good" ? "text-brand-emerald" : v.tone === "bad" ? "text-amber-400" : "text-text-primary"
  return (
    <Card>
      <CardLabel>Compared to my building</CardLabel>
      <p className={`mt-3 text-lg font-semibold ${toneClass}`}>{v.text}</p>
      <p className="mt-1 text-xs text-text-muted">
        Building average: {fmt(k?.building_avg_eui_kwh_m2_yr, 0)} kWh/m²·yr
      </p>
      <p className="mt-2 flex items-start gap-1.5 text-[11px] text-text-faint">
        <Info size={12} className="mt-0.5 shrink-0" aria-hidden />
        Anonymized — you only ever see the building average, never a neighbour&rsquo;s use.
      </p>
    </Card>
  )
}

function SharedAreasCard({ unit }: { unit: ResidenceUnit }) {
  const c = unit.common_area
  const sharePct = c?.allocation_share != null ? c.allocation_share * 100 : null
  return (
    <Card>
      <CardLabel>Shared areas</CardLabel>
      <p className="mt-3 text-2xl font-semibold text-text-primary">
        {fmt(c?.unit_allocated_kwh, 0)}{" "}
        <span className="text-sm font-normal text-text-muted">kWh</span>
      </p>
      <p className="mt-0.5 text-xs text-text-muted">
        Your share of shared heating &amp; hot water
        {sharePct != null ? ` (${fmt(sharePct, 1)}% of the building)` : ""}
      </p>
      <p className="mt-2 text-[11px] text-text-faint">
        Split per HKVO: {fmt((c?.cons_weight ?? 0.7) * 100, 0)}% by use,{" "}
        {fmt((c?.area_weight ?? 0.3) * 100, 0)}% by floor area.
      </p>
    </Card>
  )
}

function YearlyUseCard({ unit }: { unit: ResidenceUnit }) {
  const k = unit.kpi
  return (
    <Card>
      <CardLabel>My yearly use</CardLabel>
      <p className="mt-3 text-2xl font-semibold text-text-primary">
        {fmt(k?.heating_dhw_kwh_annual, 0)}{" "}
        <span className="text-sm font-normal text-text-muted">kWh/yr</span>
      </p>
      <p className="mt-0.5 text-xs text-text-muted">Heating + hot water, annualized</p>
      {k?.cov_days != null && (
        <p className="mt-2 text-[11px] text-text-faint">
          Estimated from {fmt(k.cov_days, 0)} days of readings.
        </p>
      )}
    </Card>
  )
}

function SavingsCard({ unit }: { unit: ResidenceUnit }) {
  const k = unit.kpi
  const pct = k?.vs_building_pct ?? null
  const band = k?.epc_band ?? null

  // Headline tone from the (anonymized) comparison to the building average.
  let headline: string
  let tone: "good" | "bad" | "neutral"
  if (pct === null || pct === undefined) {
    headline = "Here are some simple ways to keep your energy use low."
    tone = "neutral"
  } else if (pct < -10) {
    headline = `You're using about ${fmt(Math.abs(pct), 0)}% less than your building average — nicely efficient. Keep it up.`
    tone = "good"
  } else if (pct > 10) {
    headline = `You're using about ${fmt(pct, 0)}% more than your building average — there's room to save.`
    tone = "bad"
  } else {
    headline = "You're about average for your building — small habits can still trim your use."
    tone = "neutral"
  }

  // Generic, safe tips (typical effects — not a guarantee). Lay audience.
  const tips = [
    "Turn the thermostat down 1°C — it typically cuts heating use by around 6%.",
    "Ventilate in short bursts with windows fully open (Stoßlüften) instead of leaving them tilted.",
    "Keep radiators clear of furniture and curtains so heat reaches the room.",
  ]

  const headlineColor =
    tone === "good" ? "text-brand-emerald" : tone === "bad" ? "text-amber-400" : "text-text-primary"

  return (
    <Card>
      <div className="flex items-center gap-2">
        <Lightbulb size={14} className="shrink-0 text-brand-emerald" aria-hidden />
        <CardLabel>How you&rsquo;re doing</CardLabel>
      </div>
      <p className={`mt-3 text-base font-medium ${headlineColor}`}>{headline}</p>

      <ul className="mt-4 space-y-2">
        {tips.map((t) => (
          <li key={t} className="flex gap-2.5 text-sm leading-relaxed text-text-primary/90">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-emerald" aria-hidden />
            <span>{t}</span>
          </li>
        ))}
      </ul>

      {(band === "D" || band === "E") && (
        <p className="mt-4 flex items-start gap-1.5 rounded-md border border-border-subtle bg-white/[0.02] px-3 py-2 text-[11px] text-text-faint">
          <Info size={12} className="mt-0.5 shrink-0" aria-hidden />
          Some of your building&rsquo;s efficiency depends on its insulation and heating
          system — not just your habits. Ask your building manager about any planned upgrades.
        </p>
      )}

      <p className="mt-3 text-[11px] text-text-faint">
        General guidance — typical effects vary by home and weather.
      </p>
    </Card>
  )
}

function MonthlyUvi({ unit }: { unit: ResidenceUnit }) {
  const months = aggregateMonthly(unit.monthly)
  if (months.length === 0) {
    return (
      <Card>
        <CardLabel>Monthly consumption (UVI)</CardLabel>
        <p className="mt-3 text-sm text-text-muted">
          No monthly readings available yet.
        </p>
      </Card>
    )
  }
  const maxVal = Math.max(
    1,
    ...months.map((m) => Math.max(m.kwh, m.buildingAvg ?? 0))
  )
  const anyCost = months.some((m) => m.cost !== null)

  return (
    <Card>
      <div className="flex items-center justify-between gap-3">
        <CardLabel>Monthly consumption (UVI)</CardLabel>
        <div className="flex items-center gap-3 text-[10px] text-text-muted">
          <span className="inline-flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-sm" style={{ background: ACCENT }} />
            You
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="inline-block h-0 w-3 border-t border-dashed border-text-faint" />
            Building avg
          </span>
        </div>
      </div>
      <p className="mt-1 text-xs text-text-muted">
        Heating + hot water per month — the consumption information your building
        shares monthly (EED/HKVO).
      </p>

      <div className="mt-4 flex items-end gap-2" style={{ height: 160 }}>
        {months.map((m) => {
          const hPct = (m.kwh / maxVal) * 100
          const avgPct = m.buildingAvg != null ? (m.buildingAvg / maxVal) * 100 : null
          const title =
            `${MONTHS[m.month]} ${m.year}: ${fmt(m.kwh, 0)} kWh` +
            (m.buildingAvg != null ? ` · building avg ${fmt(m.buildingAvg, 0)} kWh` : "") +
            (m.cost != null ? ` · €${fmt(m.cost, 2)}` : "")
          return (
            <div key={`${m.year}-${m.month}`} className="flex min-w-0 flex-1 flex-col items-center">
              <div className="relative flex w-full flex-1 items-end" title={title}>
                <div
                  className="w-full rounded-t"
                  style={{ height: `${hPct}%`, background: ACCENT, minHeight: m.hasData ? 2 : 0 }}
                />
                {avgPct != null && (
                  <div
                    className="absolute left-0 right-0 border-t border-dashed border-text-faint"
                    style={{ bottom: `${avgPct}%` }}
                    aria-hidden
                  />
                )}
              </div>
              <span className="mt-1 text-[10px] text-text-faint">{MONTHS[m.month]}</span>
            </div>
          )
        })}
      </div>
      {anyCost && (
        <p className="mt-3 text-[11px] text-text-faint">
          Costs shown on hover are the allocated amounts for information — this is
          not a bill.
        </p>
      )}
    </Card>
  )
}

// ---------------------------------------------------------------------------

export function ResidenceShell({ summary, loadError, hasIdentity, residentId }: Props) {
  const units = summary?.units ?? []
  const [activeId, setActiveId] = useState<string | null>(units[0]?.unit_id ?? null)
  const active = units.find((u) => u.unit_id === activeId) ?? units[0] ?? null

  async function handleSignOut() {
    try {
      await fetch("/api/residence/session", { method: "DELETE" })
    } catch {
      // ignore — clear the client view regardless
    }
    window.location.href = "/residence"
  }

  let content: ReactNode

  if (!hasIdentity) {
    content = (
      <Card>
        <div className="flex items-start gap-3">
          <Home size={18} className="mt-0.5 shrink-0 text-brand-emerald" aria-hidden />
          <div>
            <p className="text-sm font-semibold text-text-primary">
              This is your private home-energy view.
            </p>
            <p className="mt-1 text-sm text-text-muted">
              Open the link from your invite email to see your apartment&rsquo;s
              monthly energy use, efficiency rating, and shared-area share.
            </p>
            <p className="mt-3 text-[11px] text-text-faint">
              Developer note: append <code className="text-text-muted">?resident=&lt;id&gt;</code>{" "}
              and set <code className="text-text-muted">RESIDENT_DEV_MODE=1</code> on the backend.
            </p>
          </div>
        </div>
      </Card>
    )
  } else if (loadError === "resident_unauthorized") {
    content = (
      <Card>
        <p className="text-sm font-semibold text-text-primary">
          Resident access is not switched on yet.
        </p>
        <p className="mt-1 text-sm text-text-muted">
          The resident sign-in (magic link) is coming soon. If you are testing,
          enable <code className="text-text-muted">RESIDENT_DEV_MODE=1</code> on the backend.
        </p>
      </Card>
    )
  } else if (loadError === "fabric_unavailable") {
    content = (
      <Card>
        <p className="text-sm font-semibold text-amber-400">
          Live data is temporarily unavailable.
        </p>
        <p className="mt-1 text-sm text-text-muted">
          Please check back in a little while.
        </p>
      </Card>
    )
  } else if (loadError) {
    content = (
      <Card>
        <p className="text-sm font-semibold text-red-300">
          Sorry — we couldn&rsquo;t load your home energy view.
        </p>
        <p className="mt-1 text-xs text-text-muted">{loadError}</p>
      </Card>
    )
  } else if (!active) {
    content = (
      <Card>
        <p className="text-sm font-semibold text-text-primary">
          We don&rsquo;t have energy data for your home yet.
        </p>
        <p className="mt-1 text-sm text-text-muted">
          Once your building&rsquo;s meter readings are processed, your monthly
          consumption will appear here.
        </p>
      </Card>
    )
  } else {
    content = (
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-end gap-2">
          <Link
            href={residentId ? `/residence/report?resident=${encodeURIComponent(residentId)}` : "/residence/report"}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-md border border-brand-emerald/40 bg-brand-emerald/5 px-3 py-1.5 text-xs font-medium text-brand-emerald transition-colors hover:border-brand-emerald hover:bg-brand-emerald/10"
          >
            Download monthly statement (PDF)
          </Link>
          <button
            type="button"
            onClick={handleSignOut}
            className="inline-flex items-center gap-1.5 rounded-md border border-border-subtle px-3 py-1.5 text-xs font-medium text-text-muted transition-colors hover:text-text-primary"
          >
            Sign out
          </button>
        </div>
        {units.length > 1 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] uppercase tracking-wider text-text-muted">
              Your units
            </span>
            {units.map((u) => (
              <button
                key={u.unit_id}
                onClick={() => setActiveId(u.unit_id)}
                className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                  u.unit_id === active.unit_id
                    ? "border-brand-emerald bg-brand-emerald/10 text-brand-emerald"
                    : "border-border-subtle text-text-muted hover:text-text-primary"
                }`}
              >
                {u.unit_id}
              </button>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <RatingCard unit={active} />
          <VsBuildingCard unit={active} />
          <SharedAreasCard unit={active} />
          <YearlyUseCard unit={active} />
        </div>

        <SavingsCard unit={active} />

        <MonthlyUvi unit={active} />

        <p className="text-[11px] leading-relaxed text-text-faint">
          Figures are informational and based on your metered and allocated
          readings — they are not a bill. You only ever see your own home plus an
          anonymized building average.
        </p>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen bg-bg-base bg-radial-emerald-glow">
      <div className="absolute inset-0 bg-dot-grid pointer-events-none" aria-hidden />

      <header className="relative z-10 border-b border-border-subtle bg-bg-elevated/60 backdrop-blur-sm">
        <div className="flex items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-center gap-4">
            <LogoCard iconSize={40} />
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-brand-emerald/40 bg-brand-emerald/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-brand-emerald"
            >
              <Home size={11} aria-hidden />
              My Home Energy
            </span>
          </div>
          <Link
            href="/login"
            className="hidden text-sm text-text-muted transition-colors hover:text-text-primary sm:inline"
          >
            Building manager? Sign in
          </Link>
        </div>
      </header>

      <main id="main-content" className="relative z-10 mx-auto max-w-3xl px-6 py-8">
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-text-primary">My Home Energy</h1>
          <p className="mt-1 text-sm text-text-muted">
            Your apartment&rsquo;s energy use, efficiency, and monthly consumption.
          </p>
        </div>
        {content}
      </main>
    </div>
  )
}
