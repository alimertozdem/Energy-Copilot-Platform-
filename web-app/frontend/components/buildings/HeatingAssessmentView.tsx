/**
 * HeatingAssessmentView — the demand + envelope + retrofit-ROI core of the
 * Heating & HVAC page. Honest by design: every figure is screening-grade, the
 * basis (measured vs estimated) is shown with an uncertainty band, fuel
 * assumptions are surfaced, and the sequenced retrofit package (the decision
 * artifact) shows the realistic combined outcome — not additive single rows.
 */
import Link from "next/link"
import { Flame, Snowflake, Square, TrendingDown, CalendarClock, AlertTriangle, Gauge, BadgeCheck, ArrowRight } from "lucide-react"

import type { HeatingAssessment, HeatingMeasure } from "@/lib/api/heating"
import { strandingYearForIntensity, crremSource, type StrandingStatus } from "@/lib/crrem"
import { SubsidyPanel } from "@/components/buildings/SubsidyPanel"
import { InfoTip } from "@/components/ui/info-tip"
import { DataProvenanceBadge } from "@/components/ui/DataProvenanceBadge"

function fmtEnergy(kwh: number): string {
  if (kwh >= 1_000_000) return `${(kwh / 1_000_000).toFixed(1)} GWh`
  if (kwh >= 1_000) return `${(kwh / 1_000).toFixed(0)} MWh`
  return `${Math.round(kwh)} kWh`
}
function eur(n: number): string {
  return "€" + new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n)
}
function tco2(kg: number): string {
  return `${(kg / 1000).toFixed(1)} t`
}
function strandLabel(strandingYear: number | null, status: StrandingStatus): string {
  if (status === "unknown") return "—"
  if (status === "stranded_now") return "Stranded now"
  if (status === "on_track") return "On track to 2050"
  return `Strands ${strandingYear}`
}
function epcTone(cls: string | null): string {
  if (!cls) return "text-text-muted border-border-subtle bg-white/[0.02]"
  const c = cls.charAt(0)
  if (c === "F" || c === "G" || c === "H") return "text-red-300 border-red-400/30 bg-red-400/5"
  if (c === "D" || c === "E") return "text-amber-300 border-amber-400/30 bg-amber-400/5"
  return "text-brand-emerald border-brand-emerald/30 bg-brand-emerald/5"
}

const EL_LABEL: Record<string, string> = { wall: "Walls", roof: "Roof", window: "Windows" }

function Tile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-border-subtle bg-bg-elevated/40 p-4">
      <div className="text-[11px] uppercase tracking-wide text-text-faint">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums text-text-primary">{value}</div>
      {sub && <div className="mt-0.5 text-[11px] text-text-faint">{sub}</div>}
    </div>
  )
}

function EnvChip({ el }: { el: HeatingAssessment["envelope"][number] }) {
  const tone =
    el.status === "pass"
      ? "border-brand-emerald/30 bg-brand-emerald/5 text-brand-emerald"
      : el.status === "fail"
        ? "border-red-400/30 bg-red-400/5 text-red-300"
        : "border-border-subtle bg-white/[0.02] text-text-muted"
  return (
    <div className={`rounded-lg border px-3 py-2 text-xs ${tone}`}>
      <div className="flex items-center gap-1.5 font-medium">
        <Square className="h-3 w-3" aria-hidden /> {EL_LABEL[el.element] ?? el.element}
      </div>
      <div className="mt-1 tabular-nums">
        {el.u_current != null ? `U ${el.u_current}` : "U —"}
        <span className="text-text-faint"> / target {el.u_target}</span>
      </div>
      <div className="text-[10px] uppercase tracking-wide">
        {el.status === "pass" ? "GEG ok" : el.status === "fail" ? "above limit" : "unknown"}
      </div>
    </div>
  )
}

export function HeatingAssessmentView({ data, buildingId }: { data: HeatingAssessment; buildingId?: string }) {
  const d = data.demand
  const s = data.supply
  const estimated = d.basis !== "measured"
  const pkg = data.package
  const full = pkg?.full ?? null
  const steps = pkg?.steps ?? []
  const hasBand = d.heating_kwh_low != null && d.heating_kwh_high != null
  const c = data.carbon
  const reg = data.regulation
  const epc = data.epc
  const strandNow = c ? strandingYearForIntensity(c.building_type, c.total_co2_intensity_kg_m2) : null
  const strandAfter = c ? strandingYearForIntensity(c.building_type, c.total_co2_intensity_after_kg_m2) : null
  const delay =
    strandNow?.strandingYear != null && strandAfter?.strandingYear != null
      ? strandAfter.strandingYear - strandNow.strandingYear
      : null

  return (
    <div className="space-y-6">
      {/* Demand + supply hero */}
      <section>
        <div className="mb-3 flex items-center gap-2">
          <Flame className="h-4 w-4 text-amber-300" aria-hidden />
          <h2 className="text-sm font-semibold text-text-primary">Heat demand &amp; cost</h2>
          <InfoTip term="heating_demand" />
          <DataProvenanceBadge basis={estimated ? "estimated" : "measured"} />
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Tile
            label="Heating energy / yr"
            value={fmtEnergy(d.heating_kwh)}
            sub={hasBand ? `${fmtEnergy(d.heating_kwh_low)}–${fmtEnergy(d.heating_kwh_high)} (±${d.band_pct}%) · ${d.heating_share_pct}% of total` : `${d.heating_share_pct}% of total`}
          />
          <Tile label="Heating intensity" value={d.heating_eui_kwh_m2 != null ? String(d.heating_eui_kwh_m2) : "—"} sub="kWh/m²·yr" />
          <Tile label="Heat cost / yr" value={eur(s.heat_cost_eur)} sub={`${s.fuel_type}${s.fuel_assumed ? " (assumed)" : ""} · ${s.price_eur_kwh} €/kWh`} />
          <Tile label="Heat CO₂ / yr" value={tco2(s.heat_co2_kg)} sub={`${s.co2_factor_kg_kwh} kg/kWh`} />
        </div>
        {s.fuel_assumed && (
          <p className="mt-2 text-[11px] text-amber-300/80">
            Fuel assumed: natural gas. Set the building&rsquo;s actual heating system (gas / district heat /
            heat pump) to sharpen cost &amp; CO₂ — the figures recompute automatically.
          </p>
        )}
      </section>

      {/* Envelope vs GEG */}
      <section>
        <div className="mb-2 flex items-center gap-2">
          <Snowflake className="h-4 w-4 text-sky-300" aria-hidden />
          <h2 className="text-sm font-semibold text-text-primary">Envelope vs GEG</h2>
          <InfoTip term="envelope_geg" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          {data.envelope.map((el) => (
            <EnvChip key={el.element} el={el} />
          ))}
        </div>
        <p className="mt-2 text-[11px] text-text-faint">
          GEG Anlage 7 component limits (apply when a component is renovated). Unknown = U-value not
          on file; add it on the building&rsquo;s envelope details to sharpen the figures.
        </p>
      </section>

      {/* Retrofit measures (standalone) */}
      <section>
        <h2 className="mb-2 text-sm font-semibold text-text-primary">Retrofit measures — standalone, by payback</h2>
        <div className="overflow-x-auto rounded-lg border border-border-subtle">
          <table className="w-full text-xs">
            <thead className="text-left text-text-faint">
              <tr className="border-b border-border-subtle">
                <th className="px-3 py-2 font-medium">Measure</th>
                <th className="px-3 py-2 font-medium">Tier</th>
                <th className="px-3 py-2 text-right font-medium">Saves / yr</th>
                <th className="px-3 py-2 text-right font-medium">€ / yr</th>
                <th className="px-3 py-2 text-right font-medium">CO₂ / yr</th>
                <th className="px-3 py-2 text-right font-medium">Net CapEx</th>
                <th className="px-3 py-2 text-right font-medium">Payback</th>
              </tr>
            </thead>
            <tbody>
              {data.measures.map((m: HeatingMeasure) => (
                <tr key={m.key} className="border-b border-border-subtle/60">
                  <td className="px-3 py-2">
                    <div className="text-text-primary">{m.label}</div>
                    <div className="text-[10px] text-text-faint">{m.note}</div>
                  </td>
                  <td className="px-3 py-2 text-text-muted">{m.tier}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-muted">
                    {m.saving_kwh != null ? fmtEnergy(m.saving_kwh) : "switch"}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-brand-emerald">{eur(m.saving_eur)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-muted">{tco2(m.saving_co2_kg)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-muted">{eur(m.capex_net)}</td>
                  <td className="px-3 py-2 text-right tabular-nums text-text-primary">
                    {m.payback_years != null ? `${m.payback_years} yr` : "—"}
                  </td>
                </tr>
              ))}
              {data.measures.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-3 py-4 text-center text-text-faint">
                    Add floor area + envelope details to compute retrofit measures.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-text-faint">
          Standalone = each measure on its own (delivered saving, after internal/solar gains). Net CapEx
          is after subsidy. {data.assumptions.subsidy} {data.assumptions.gains}{" "}
          <span className="text-text-muted">{data.assumptions.grade}</span>
        </p>
      </section>

      {/* Sequenced retrofit package — the decision artifact */}
      {full && steps.length > 0 && (
        <section>
          <div className="mb-2 flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-brand-emerald" aria-hidden />
            <h2 className="text-sm font-semibold text-text-primary">Retrofit package — sequenced roadmap</h2>
            <InfoTip term="retrofit_package" />
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Tile label="Heat reduction" value={`${full.reduction_pct}%`} sub={`realistic ${pkg.realistic_reduction_low_pct}–${pkg.realistic_reduction_high_pct}%`} />
            <Tile label="Heating EUI" value={full.eui_after != null ? `${full.eui_after}` : "—"} sub={full.eui_before != null ? `from ${full.eui_before} kWh/m²·yr` : "kWh/m²·yr"} />
            <Tile label="Net CapEx (full)" value={eur(full.capex_net)} sub={`${eur(full.capex_net_low)}–${eur(full.capex_net_high)} · saves ${eur(full.saving_eur)}/yr`} />
            <Tile
              label="Blended payback"
              value={full.payback_years != null ? `${full.payback_years} yr` : "—"}
              sub={
                full.payback_years_low != null && full.payback_years_high != null
                  ? `${full.payback_years_low}–${full.payback_years_high} yr · ${tco2(full.co2_saved_kg)}/yr`
                  : `${tco2(full.co2_saved_kg)} CO₂/yr`
              }
            />
          </div>
          <div className="mt-3 overflow-x-auto rounded-lg border border-border-subtle">
            <table className="w-full text-xs">
              <thead className="text-left text-text-faint">
                <tr className="border-b border-border-subtle">
                  <th className="px-3 py-2 font-medium">Add measure (in order)</th>
                  <th className="px-3 py-2 text-right font-medium">Cum. heat ↓</th>
                  <th className="px-3 py-2 text-right font-medium">Heating EUI</th>
                  <th className="px-3 py-2 text-right font-medium">Cum. Net CapEx</th>
                  <th className="px-3 py-2 text-right font-medium">Cum. € / yr</th>
                  <th className="px-3 py-2 text-right font-medium">Payback</th>
                </tr>
              </thead>
              <tbody>
                {steps.map((st, i) => (
                  <tr key={st.key} className="border-b border-border-subtle/60">
                    <td className="px-3 py-2 text-text-primary">
                      <span className="text-text-faint">{i + 1}.</span> {st.label}
                      <span className="ml-1 text-[10px] text-text-faint">{st.tier}</span>
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-brand-emerald">{st.cumulative_reduction_pct}%</td>
                    <td className="px-3 py-2 text-right tabular-nums text-text-muted">
                      {st.heating_eui_after != null ? st.heating_eui_after : "—"}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums text-text-muted">{eur(st.cumulative_capex_net)}</td>
                    <td className="px-3 py-2 text-right tabular-nums text-text-muted">{eur(st.cumulative_saving_eur)}</td>
                    <td className="px-3 py-2 text-right tabular-nums text-text-primary">
                      {st.payback_years != null ? `${st.payback_years} yr` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-text-faint">
            {pkg.note} The fast, low-CapEx steps (top of the list) capture comfort and the quickest
            payback; deep-envelope steps add the largest CO₂ cut but carry long paybacks — phase them
            with subsidy windows.{" "}
            <Link href="/financing" className="text-brand-emerald hover:underline">Financing</Link>{" "}
            ·{" "}
            <Link
              href={buildingId ? `/decarbonisation?building_id=${encodeURIComponent(buildingId)}` : "/decarbonisation"}
              className="text-brand-emerald hover:underline"
            >
              Decarbonisation
            </Link>
          </p>
          {pkg.sensitivity && full.payback_years_2030_carbon != null && (
            <p className="mt-1 text-[11px] leading-relaxed text-text-faint">
              Range = CapEx &plusmn;{pkg.sensitivity.capex_band_pct}% (screening) and the energy-saving band. At the
              2030 carbon price (~&euro;{pkg.sensitivity.carbon_price_2030}/t vs &euro;{pkg.sensitivity.carbon_price_now} today),
              blended payback falls to ~{full.payback_years_2030_carbon} yr.
            </p>
          )}
        </section>
      )}

      <SubsidyPanel measures={data.measures} />

      {epc && epc.class_now && epc.class_after && (
        <section>
          <div className="mb-2 flex items-center gap-2">
            <Gauge className="h-4 w-4 text-brand-emerald" aria-hidden />
            <h2 className="text-sm font-semibold text-text-primary">EPC class &amp; EPBD MEPS</h2>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className={`flex h-16 w-16 flex-col items-center justify-center rounded-xl border ${epcTone(epc.class_now)}`}>
              <span className="text-[10px] uppercase tracking-wide text-text-faint">Now</span>
              <span className="text-2xl font-bold tabular-nums">{epc.class_now}</span>
            </div>
            <ArrowRight className="h-5 w-5 text-text-faint" aria-hidden />
            <div className={`flex h-16 w-16 flex-col items-center justify-center rounded-xl border ${epcTone(epc.class_after)}`}>
              <span className="text-[10px] uppercase tracking-wide text-text-faint">After</span>
              <span className="text-2xl font-bold tabular-nums">{epc.class_after}</span>
            </div>
            <div className="flex-1 min-w-[200px]">
              {epc.clears_meps ? (
                <div className="flex items-center gap-1.5 text-sm font-medium text-brand-emerald">
                  <BadgeCheck className="h-4 w-4" aria-hidden />
                  Clears the {epc.meps_milestone} EPBD MEPS milestone
                </div>
              ) : epc.meps_milestone ? (
                <div className="text-sm font-medium text-amber-300">
                  EPC {epc.class_now}: {epc.meps_milestone} MEPS renovation-priority — package improves to {epc.class_after}, still in F–G
                </div>
              ) : (
                <div className="text-sm text-text-muted">Not in the EPBD renovation-priority scope (F–G).</div>
              )}
              <div className="mt-0.5 text-[11px] text-text-faint">
                {epc.eui_now_kwh_m2}&nbsp;&rarr;&nbsp;{epc.eui_after_kwh_m2} kWh/m&sup2;&middot;yr (whole building)
              </div>
            </div>
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-text-faint">
            German Energieausweis (Endenergie) scale &mdash;{" "}
            {epc.anchored_to_epc ? "anchored to your registered EPC" : "estimated from energy use"}; indicative,
            and a registered Energieausweis is authoritative. MEPS milestones (EPC G&rarr;2030, F&rarr;2033) are
            EPBD triage, not a national compliance verdict.{" "}
            <Link href="/compliance" className="text-brand-emerald hover:underline">Compliance</Link>
          </p>
        </section>
      )}

      {c && c.total_co2_intensity_kg_m2 != null && strandNow && strandAfter && (
        <section>
          <div className="mb-2 flex items-center gap-2">
            <CalendarClock className="h-4 w-4 text-amber-300" aria-hidden />
            <h2 className="text-sm font-semibold text-text-primary">Stranding risk — CRREM 1.5&deg;C</h2>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-red-400/20 bg-red-400/5 p-4">
              <div className="text-[11px] uppercase tracking-wide text-text-faint">Do nothing</div>
              <div className="mt-1 text-2xl font-semibold tabular-nums text-text-primary">
                {strandLabel(strandNow.strandingYear, strandNow.status)}
              </div>
              <div className="mt-0.5 text-[11px] text-text-faint">{c.total_co2_intensity_kg_m2} kgCO&#8322;/m&sup2;&middot;yr today</div>
            </div>
            <div className="rounded-xl border border-brand-emerald/20 bg-brand-emerald/5 p-4">
              <div className="text-[11px] uppercase tracking-wide text-text-faint">After full package</div>
              <div className="mt-1 text-2xl font-semibold tabular-nums text-text-primary">
                {strandLabel(strandAfter.strandingYear, strandAfter.status)}
              </div>
              <div className="mt-0.5 text-[11px] text-text-faint">
                {c.total_co2_intensity_after_kg_m2} kgCO&#8322;/m&sup2;&middot;yr&nbsp;&middot;&nbsp;heating {c.heating_share_of_carbon_pct}% of carbon
              </div>
            </div>
          </div>
          {delay != null && delay > 0 && (
            <p className="mt-2 text-xs text-brand-emerald">The package delays stranding by ~{delay} {delay === 1 ? "year" : "years"}.</p>
          )}
          <p className="mt-2 text-[11px] leading-relaxed text-text-faint">
            {crremSource() === "official"
              ? "Official CRREM 1.5\u00b0C pathway"
              : "Indicative 1.5\u00b0C pathway (not the licensed CRREM dataset)"}{" "}
            vs the building&rsquo;s {c.basis} whole-building carbon (heating + non-heating electricity). The package cuts heating carbon
            only &mdash; for an electricity-heavy building, decarbonising power matters too.{" "}
            <Link href="/compliance" className="text-brand-emerald hover:underline">Compliance &amp; CRREM</Link>
          </p>
        </section>
      )}

      {reg && reg.status !== "met" && (
        <div
          className={`rounded-lg border p-3 text-xs ${
            reg.status === "applies"
              ? "border-amber-400/30 bg-amber-400/5 text-amber-200"
              : "border-border-subtle bg-white/[0.02] text-text-muted"
          }`}
        >
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            <div>
              <span className="font-medium">
                {reg.status === "applies"
                  ? "GEG \u00a771 — 65% renewable on heating replacement"
                  : "GEG \u00a771 — confirm the fuel"}
              </span>
              <div className="mt-0.5 leading-relaxed">{reg.note}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
