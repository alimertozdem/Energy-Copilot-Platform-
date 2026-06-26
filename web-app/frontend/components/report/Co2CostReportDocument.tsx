/**
 * Co2CostReportDocument — body for the per-building CO₂ cost-allocation report.
 *
 * German CO2KostAufG landlord/tenant split: residential/mixed buildings use the
 * statutory 10-step model on kg CO₂ per m² of living area (Wohnfläche); non-residential
 * uses the flat 50/50 split. Body-only; plugs into <ReportFrame>. Inline-styled, print-safe.
 *
 * Data: GET /compliance/co2-cost/{id}. Heating-fuel CO₂ × CO₂ price. Estimates /
 * decision-support, not legal advice — see the footer disclaimer.
 */
import type { ActionItem } from "@/lib/api/actions"
import type { Co2CostAllocation } from "@/lib/api/co2cost"

import {
  BAD,
  Chip,
  DANGER,
  EMERALD,
  FAINT,
  fmtInt,
  fmtNum,
  GOOD,
  INK,
  LINE,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  tdC,
  tdL,
  tdR,
  thStyle,
  fmtPayback,
} from "./reportKit"

const eur = (v: number | null): string => (v === null ? "—" : "€" + fmtInt(v))

export function Co2CostReportDocument({
  data,
  error,
  actions = [],
}: {
  data: Co2CostAllocation | null
  error: string | null
  actions?: ActionItem[]
}) {
  if (error) {
    return <Notice error={error} label="CO₂ cost allocation" />
  }
  if (!data) {
    return (
      <div style={{ fontSize: 13, color: MUTED, padding: "8px 0" }}>
        No CO₂ cost data is available for this building yet.
      </div>
    )
  }

  const residential = data.is_residential
  const modelChip = residential
    ? "Residential — statutory 10-step model"
    : "Non-residential — flat 50/50"

  if (!data.has_data) {
    return (
      <div>
        <div style={{ marginBottom: 14, display: "flex", gap: 8 }}>
          <Chip label="CO2KostAufG cost allocation" color={EMERALD} />
          <Chip label={modelChip} color={MUTED} />
        </div>
        <div
          style={{
            padding: "12px 14px",
            borderRadius: 6,
            border: `1px solid ${LINE}`,
            backgroundColor: "#f8fafc",
            fontSize: 12,
            color: MUTED,
          }}
        >
          This building has no heating-fuel CO₂ emissions on record yet, so the
          landlord/tenant split cannot be computed. Once heating-fuel (gas/oil)
          consumption is connected, this report fills in automatically.
        </div>
        <Disclaimer data={data} />
      </div>
    )
  }

  const landlordPct = data.landlord_pct ?? 0
  const tenantPct = data.tenant_pct ?? 0
  const decarbMeasure =
    actions.find((a) => a.action_type === "INSTALL_HEAT_PUMP") ??
    actions.find((a) => a.action_type === "DEEP_RETROFIT")

  return (
    <div>
      <div style={{ marginBottom: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="CO2KostAufG cost allocation" color={EMERALD} />
        <Chip label={modelChip} color={INK} />
        {data.reporting_year != null && (
          <Chip label={`Reporting year ${data.reporting_year}`} color={MUTED} />
        )}
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Heating CO₂ intensity"
          value={fmtNum(data.co2_intensity_kg_m2)}
          hint="kg CO₂/m²·yr — drives the step"
        />
        <StatCard
          label="Total CO₂ cost (2026)"
          value={eur(data.total_co2_cost_eur)}
          hint={`at €${fmtInt(data.co2_price_eur_t)}/t CO₂`}
        />
        <StatCard
          label={`Landlord share · ${landlordPct}%`}
          value={eur(data.landlord_cost_eur)}
          color={BAD}
          hint="Vermieteranteil (borne by owner)"
        />
        <StatCard
          label={`Tenant share · ${tenantPct}%`}
          value={eur(data.tenant_cost_eur)}
          color={GOOD}
          hint="Mieteranteil (passed through)"
        />
      </div>

      <SectionTitle>How this split is determined</SectionTitle>
      <div style={{ fontSize: 12, color: INK, lineHeight: 1.6 }}>
        {residential ? (
          <>
            This building emits{" "}
            <strong>{fmtNum(data.co2_intensity_kg_m2)} kg CO₂/m²·yr</strong> from heating
            fuel (per m² of living area), placing it in{" "}
            <strong>step {data.tier} of 10</strong> of the statutory CO2KostAufG model.
            The worse the building&apos;s efficiency, the more of the CO₂ price the{" "}
            <em>landlord</em> bears — here <strong>{landlordPct}%</strong> to the landlord
            and <strong>{tenantPct}%</strong> to tenants.
          </>
        ) : (
          <>
            For non-residential buildings the CO2KostAufG applies a flat{" "}
            <strong>50/50</strong> split between landlord and tenant. (A step model for
            non-residential buildings is foreseen but not yet in force, so 50/50 stands.)
          </>
        )}
      </div>

      {residential && (
        <>
          <SectionTitle>Statutory 10-step model (kg CO₂/m²·yr, living area)</SectionTitle>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={thStyle("left")}>Step</th>
                <th style={thStyle("left")}>Emissions band</th>
                <th style={thStyle("right")}>Landlord</th>
                <th style={thStyle("right")}>Tenant</th>
                <th style={thStyle("center")}>This building</th>
              </tr>
            </thead>
            <tbody>
              {data.stair.map((s) => {
                const here = s.tier === data.tier
                const band =
                  s.max_kg_m2 === null
                    ? `≥ ${fmtInt(s.min_kg_m2)}`
                    : `${fmtInt(s.min_kg_m2)} – < ${fmtInt(s.max_kg_m2)}`
                return (
                  <tr key={s.tier} style={here ? { backgroundColor: "#ecfdf5" } : undefined}>
                    <td style={{ ...tdL, fontWeight: here ? 700 : 400 }}>{s.tier}</td>
                    <td style={tdL}>{band}</td>
                    <td style={{ ...tdR, color: BAD }}>{s.landlord_pct}%</td>
                    <td style={{ ...tdR, color: GOOD }}>{s.tenant_pct}%</td>
                    <td style={{ ...tdC, color: EMERALD, fontWeight: 700 }}>
                      {here ? "◀ here" : ""}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </>
      )}

      {residential && data.units.length > 0 && (
        <>
          <SectionTitle>Per-dwelling allocation (Est. — area pro-rata)</SectionTitle>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={thStyle("left")}>Unit</th>
                <th style={thStyle("right")}>Area (m²)</th>
                <th style={thStyle("right")}>Share</th>
                <th style={thStyle("right")}>CO₂ (kg)</th>
                <th style={thStyle("right")}>Cost</th>
                <th style={thStyle("right")}>Landlord</th>
                <th style={thStyle("right")}>Tenant</th>
              </tr>
            </thead>
            <tbody>
              {data.units.map((u) => (
                <tr key={u.unit_id}>
                  <td style={tdL}>{u.unit_id}</td>
                  <td style={tdR}>{u.area_m2 != null ? fmtInt(u.area_m2) : "\u2014"}</td>
                  <td style={tdR}>
                    {u.area_share_pct != null ? `${fmtNum(u.area_share_pct)}%` : "\u2014"}
                  </td>
                  <td style={tdR}>{u.co2_kg != null ? fmtInt(u.co2_kg) : "\u2014"}</td>
                  <td style={{ ...tdR, fontWeight: 600 }}>{eur(u.cost_eur)}</td>
                  <td style={{ ...tdR, color: BAD }}>{eur(u.landlord_cost_eur)}</td>
                  <td style={{ ...tdR, color: GOOD }}>{eur(u.tenant_cost_eur)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 6, fontSize: 10, color: FAINT }}>
            Estimated split of the {eur(data.total_co2_cost_eur)} (2026) building cost by
            each dwelling&apos;s living-area share (Wohnfläche pro-rata) — not per-unit
            metering. The same step {data.tier ?? "\u2014"} landlord/tenant ratio applies to
            every unit; the statute distributes the tenant portion by measured consumption.
            {` ${data.unit_count ?? data.units.length} units.`}
          </div>
        </>
      )}

      <SectionTitle>Forward view — EU ETS2 (from {data.ets2_year})</SectionTitle>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={thStyle("left")}>Year</th>
            <th style={thStyle("right")}>CO₂ price</th>
            <th style={thStyle("right")}>Total cost</th>
            <th style={thStyle("right")}>Landlord</th>
            <th style={thStyle("right")}>Tenant</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={tdL}>2026 (nEHS)</td>
            <td style={tdR}>€{fmtInt(data.co2_price_eur_t)}/t</td>
            <td style={{ ...tdR, fontWeight: 600 }}>{eur(data.total_co2_cost_eur)}</td>
            <td style={{ ...tdR, color: BAD }}>{eur(data.landlord_cost_eur)}</td>
            <td style={{ ...tdR, color: GOOD }}>{eur(data.tenant_cost_eur)}</td>
          </tr>
          <tr>
            <td style={tdL}>{data.ets2_year} (ETS2, indic.)</td>
            <td style={tdR}>€{fmtInt(data.co2_price_eur_t_ets2)}/t</td>
            <td style={{ ...tdR, fontWeight: 600 }}>{eur(data.total_co2_cost_eur_ets2)}</td>
            <td style={{ ...tdR, color: BAD }}>{eur(data.landlord_cost_eur_ets2)}</td>
            <td style={{ ...tdR, color: GOOD }}>{eur(data.tenant_cost_eur_ets2)}</td>
          </tr>
        </tbody>
      </table>
      <div style={{ marginTop: 6, fontSize: 11, color: DANGER }}>
        EU ETS2 starts in {data.ets2_year} (postponed from 2027); the CO₂ price is set to
        rise. Improving efficiency lowers a cost the landlord increasingly bears. The
        {` ${data.ets2_year}`} figure is indicative — the ETS2 market price is not yet fixed.
      </div>

      <SectionTitle>Inputs</SectionTitle>
      <div style={{ fontSize: 11, color: MUTED, lineHeight: 1.7 }}>
        Area ({data.area_basis || "—"}):{" "}
        <strong>{data.floor_area_m2 != null ? `${fmtInt(data.floor_area_m2)} m²` : "—"}</strong>
        {"  ·  "}Energy content:{" "}
        <strong>{data.energy_content_kwh != null ? `${fmtInt(data.energy_content_kwh)} kWh` : "—"}</strong>
        {"  ·  "}Heating-fuel CO₂:{" "}
        <strong>{data.heating_co2_tonnes != null ? `${fmtNum(data.heating_co2_tonnes)} t/yr` : "—"}</strong>
        {"  ·  "}Gas EF: <strong>{fmtNum(data.gas_emission_factor_kg_kwh)} kg/kWh</strong>
        {"  ·  "}Type: <strong>{data.building_type || "—"}</strong>
        {data.country_code ? `  ·  ${data.country_code}` : ""}
      </div>

      <SectionTitle>Decarbonisation path — remove this cost</SectionTitle>
      <div style={{ fontSize: 12, color: INK, lineHeight: 1.6 }}>
        This charge applies only to <strong>fossil heating fuel</strong>. Replacing it with
        a heat pump, biomass or a (planned) heat-network connection removes the levied
        emissions — cutting roughly <strong>{eur(data.total_co2_cost_eur)}</strong> (2026)
        and <strong>{eur(data.total_co2_cost_eur_ets2)}</strong> ({data.ets2_year} ETS2) per
        year toward zero, on top of the heating-energy savings.
      </div>
      {decarbMeasure && (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
          <thead>
            <tr>
              <th style={thStyle("left")}>Recommended measure</th>
              <th style={thStyle("right")}>Energy saving</th>
              <th style={thStyle("right")}>Net capex</th>
              <th style={thStyle("right")}>Payback</th>
              <th style={thStyle("right")}>CO₂ saving</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ ...tdL, fontWeight: 600 }}>
                {decarbMeasure.title || decarbMeasure.action_type}
              </td>
              <td style={tdR}>{eur(decarbMeasure.annual_saving_eur)}/yr</td>
              <td style={tdR}>
                {eur(decarbMeasure.net_capex_eur ?? decarbMeasure.capex_eur)}
              </td>
              <td style={tdR}>{fmtPayback(decarbMeasure.payback_years)}</td>
              <td style={tdR}>
                {decarbMeasure.co2_saving_kg != null
                  ? `${fmtInt(decarbMeasure.co2_saving_kg / 1000)} t/yr`
                  : "\u2014"}
              </td>
            </tr>
          </tbody>
        </table>
      )}
      <div style={{ marginTop: 6, fontSize: 10, color: FAINT }}>
        {decarbMeasure
          ? "Measure from the EnergyLens recommendations engine (energy-cost saving; the CO\u2082 levy above is avoided on top)."
          : "Add a heating-upgrade recommendation to quantify the switch."}
      </div>

      <Disclaimer data={data} />
    </div>
  )
}

function Disclaimer({ data }: { data: Co2CostAllocation }) {
  return (
    <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
      {data.note} Heating-fuel CO₂ is estimated from consumption × the BEHG natural-gas
      factor ({fmtNum(data.gas_emission_factor_kg_kwh)} kg CO₂/kWh, Heizwert); the legally
      binding figure is the supplier-reported Brennstoffemissionen on the heating bill.
      Source: {data.data_source}. Decision-support, not legal or tax advice.
    </div>
  )
}
