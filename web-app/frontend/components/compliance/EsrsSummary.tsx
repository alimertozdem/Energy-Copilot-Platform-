/**
 * EsrsSummary — ESRS-E1-aligned energy + GHG section for /compliance.
 *
 * Pure server component. Renders the EsrsReport fetched from the backend
 * (/compliance/esrs → gold_ghg_scope + gold_kpi_daily). ESRS-E1-aligned
 * reporting SUPPORT, indicative — not an audited disclosure (see backend).
 */
import Link from "next/link"

import { InfoTip } from "@/components/ui/info-tip"

import type { EsrsReport } from "@/lib/api/esrs"
import type { TermKey } from "@/lib/glossary"

function n(v: number, d = 0): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: d }).format(v)
}

export function EsrsSummary({ report }: { report: EsrsReport }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="inline-flex items-center gap-1.5 text-base font-semibold text-text-primary">
          ESRS-E1 summary{report.reporting_year ? ` · ${report.reporting_year}` : ""}
          <InfoTip term="esrs" />
        </h2>
        <p className="text-xs text-text-muted mt-0.5">
          Energy (E1-5) and gross GHG by scope (E1-6) for the reporting year.
        </p>
      </div>

      <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 px-4 py-3 text-sm text-sky-200/90">
        <span className="font-medium">ESRS-E1-aligned, indicative.</span> Reporting
        support, not an audited disclosure. Scope 3 is an estimate; Scope 2 is shown
        both location- and market-based.
      </div>

      {!report.has_data ? (
        <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 px-5 py-8 text-center text-sm text-text-muted">
          No GHG data for the reporting period yet. Once the GHG pipeline
          (gold_ghg_scope) is populated, energy and Scope 1/2/3 emissions appear here.
        </div>
      ) : (
        <>
          {/* Energy + headline intensity */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card label="Energy (E1-5)" value={`${n(report.energy_total_mwh)} MWh`} sub="total consumption" />
            <Card
              label="Renewable share"
              value={report.energy_renewable_pct != null ? `${n(report.energy_renewable_pct, 1)} %` : "—"}
              sub="on-site solar self-consumed"
            />
            <Card
              label="Total GHG (location)"
              value={`${n(report.ghg.total_location_tco2e, 1)} tCO₂e`}
              sub="Scope 1 + 2 + 3"
              tone="amber"
            />
            <Card
              label="GHG intensity"
              value={report.ghg_intensity_tco2e_m2 != null ? `${n(report.ghg_intensity_tco2e_m2, 3)} tCO₂e/m²` : "—"}
              sub="per floor area"
              term="ghg_intensity"
            />
          </div>

          {/* Scope breakdown (E1-6) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <Card label="Scope 1" value={`${n(report.ghg.scope1_tco2e, 1)} tCO₂e`} sub="direct (gas / fuel)" term="scope_1" />
            <Card label="Scope 2 (location)" value={`${n(report.ghg.scope2_location_tco2e, 1)} tCO₂e`} sub="grid electricity" term="scope_2" />
            <Card label="Scope 2 (market)" value={`${n(report.ghg.scope2_market_tco2e, 1)} tCO₂e`} sub="contract-based" term="scope_2" />
            <Card label="Scope 3 (est.)" value={`${n(report.ghg.scope3_tco2e, 1)} tCO₂e`} sub="value-chain estimate" term="scope_3" />
          </div>

          {/* Coverage + data quality */}
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-5 text-xs text-text-muted">
            Reported{" "}
            <span className="text-text-primary font-medium">
              {report.buildings_reported}
            </span>{" "}
            of {report.buildings_total} buildings · {n(report.floor_area_m2)} m² ·
            data quality: {report.data_quality.complete} complete,{" "}
            {report.data_quality.estimated} estimated,{" "}
            {report.data_quality.missing_gas} missing-gas.
          </div>

          {/* Per-building breakdown (tCO₂e) */}
          <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-subtle text-left text-[11px] uppercase tracking-[0.12em] text-text-faint">
                    <th className="px-5 py-2 font-medium">Building</th>
                    <th className="px-5 py-2 font-medium">Scope 1</th>
                    <th className="px-5 py-2 font-medium">Scope 2 (loc)</th>
                    <th className="px-5 py-2 font-medium">Scope 2 (mkt)</th>
                    <th className="px-5 py-2 font-medium">Scope 3</th>
                    <th className="px-5 py-2 font-medium">Total</th>
                    <th className="px-5 py-2 font-medium">Intensity</th>
                  </tr>
                </thead>
                <tbody>
                  {report.rows.map((r) => (
                    <tr
                      key={r.fabric_building_id}
                      className="border-b border-border-subtle/50 last:border-b-0 hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="px-5 py-3">
                        <Link
                          href={`/buildings/${encodeURIComponent(r.fabric_building_id)}`}
                          className="text-text-primary hover:text-brand-emerald transition-colors font-medium"
                        >
                          {r.name}
                        </Link>
                        <div className="text-[11px] text-text-faint">
                          {r.building_type.replace(/_/g, " ")}
                        </div>
                      </td>
                      <td className="px-5 py-3 tabular-nums text-text-muted">{n(r.scope1_tco2e, 1)}</td>
                      <td className="px-5 py-3 tabular-nums text-text-muted">{n(r.scope2_location_tco2e, 1)}</td>
                      <td className="px-5 py-3 tabular-nums text-text-muted">{n(r.scope2_market_tco2e, 1)}</td>
                      <td className="px-5 py-3 tabular-nums text-text-muted">{n(r.scope3_tco2e, 1)}</td>
                      <td className="px-5 py-3 tabular-nums text-text-primary font-medium">{n(r.total_location_tco2e, 1)}</td>
                      <td className="px-5 py-3 tabular-nums text-text-muted">
                        {r.ghg_intensity_tco2e_m2 != null ? n(r.ghg_intensity_tco2e_m2, 3) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function Card({
  label,
  value,
  sub,
  tone,
  term,
}: {
  label: string
  value: string
  sub: string
  tone?: "amber"
  term?: TermKey
}) {
  const valCls = tone === "amber" ? "text-amber-300" : "text-text-primary"
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 px-5 py-4">
      <div className="inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.12em] text-text-muted">
        {label}
        {term && <InfoTip term={term} />}
      </div>
      <div className={`text-2xl font-semibold mt-1 tabular-nums ${valCls}`}>
        {value}
      </div>
      <div className="text-xs text-text-faint mt-0.5">{sub}</div>
    </div>
  )
}
