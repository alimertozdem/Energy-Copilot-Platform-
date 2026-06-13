/**
 * EpcReportDocument — body for the per-building Energieausweis PRE-ASSESSMENT.
 *
 * Shows the building's energy rating (EPC class + EUI) against the German A–G
 * Effizienzklassen scale, plus the gap to the next band. This is a PRE-ASSESSMENT /
 * rating estimate from metered consumption — NOT the legally-valid Energieausweis, which
 * must be issued by a qualified Aussteller and registered with the DIBt (Registriernummer).
 *
 * Frontend-only: reuses the portfolio building row (epc_class + eui_kwh_m2_yr). Body-only;
 * plugs into <ReportFrame>. Inline-styled, print-safe.
 */
import type { PortfolioBuildingRow } from "@/lib/api/portfolio"

import {
  BAD,
  Chip,
  DANGER,
  EMERALD,
  FAINT,
  fmtInt,
  GOOD,
  INK,
  MUTED,
  Notice,
  SectionTitle,
  StatCard,
  tdC,
  tdL,
  tdR,
  thStyle,
} from "./reportKit"

// German Energieausweis Effizienzklassen (residential scale, final energy kWh/m²·yr).
const BANDS: { cls: string; min: number; max: number | null; color: string }[] = [
  { cls: "A+", min: 0, max: 30, color: EMERALD },
  { cls: "A", min: 30, max: 50, color: EMERALD },
  { cls: "B", min: 50, max: 75, color: GOOD },
  { cls: "C", min: 75, max: 100, color: GOOD },
  { cls: "D", min: 100, max: 130, color: BAD },
  { cls: "E", min: 130, max: 160, color: BAD },
  { cls: "F", min: 160, max: 200, color: DANGER },
  { cls: "G", min: 200, max: 250, color: DANGER },
  { cls: "H", min: 250, max: null, color: DANGER },
]

function bandFromEui(eui: number | null): (typeof BANDS)[number] | null {
  if (eui == null) return null
  return BANDS.find((b) => eui >= b.min && (b.max == null || eui < b.max)) ?? BANDS[BANDS.length - 1]
}

export function EpcReportDocument({
  building,
  error,
}: {
  building: PortfolioBuildingRow | null
  error: string | null
}) {
  if (error) {
    return <Notice error={error} label="building" />
  }
  if (!building) {
    return (
      <div style={{ fontSize: 13, color: MUTED, padding: "8px 0" }}>
        This building was not found in your portfolio.
      </div>
    )
  }

  const eui = building.eui_kwh_m2_yr
  const euiBand = bandFromEui(eui)
  const storedClass = building.epc_class
  // Highlight the stored class if present, else the band derived from EUI.
  const activeCls = storedClass ?? euiBand?.cls ?? null

  // Improvement: the next better band + the EUI it requires.
  const idx = BANDS.findIndex((b) => b.cls === activeCls)
  const nextBetter = idx > 0 ? BANDS[idx - 1] : null

  return (
    <div>
      <div style={{ marginBottom: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Chip label="Energieausweis — pre-assessment" color={EMERALD} />
        <Chip label="Energy rating estimate · not the legal certificate" color={BAD} />
        {building.country && <Chip label={building.country} color={MUTED} />}
      </div>

      {/* Prominent caveat */}
      <div
        style={{
          marginBottom: 12,
          padding: "10px 12px",
          borderRadius: 6,
          border: `1px solid #fcd34d`,
          backgroundColor: "#fffbeb",
          fontSize: 11,
          color: "#92400e",
          lineHeight: 1.5,
        }}
      >
        This is a <strong>pre-assessment</strong> of the building&apos;s energy rating from
        metered consumption — <strong>not</strong> the legally-valid Energieausweis. A
        certificate for sale, lease or new build must be issued by a qualified Aussteller
        (Energieberater / architect) and registered with the DIBt (Registriernummer); using
        an unregistered certificate can incur fines up to €10,000.
      </div>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard
          label="Energy class"
          value={activeCls ?? "—"}
          color={euiBand?.color ?? INK}
          hint={storedClass ? "on file" : "estimated from EUI"}
        />
        <StatCard
          label="Energy intensity (EUI)"
          value={eui != null ? `${fmtInt(eui)}` : "—"}
          hint="kWh/m²·yr (final energy)"
        />
        <StatCard
          label="Floor area"
          value={building.floor_area_m2 != null ? `${fmtInt(building.floor_area_m2)} m²` : "—"}
          hint={building.building_type?.replace(/_/g, " ") || "—"}
        />
        <StatCard
          label="Target (next band)"
          value={nextBetter ? nextBetter.cls : "—"}
          color={nextBetter?.color ?? GOOD}
          hint={nextBetter ? `EUI ≤ ${fmtInt(nextBetter.max ?? 0)}` : "best band"}
        />
        <StatCard
          label="CO₂ emissions"
          value={
            building.co2_30d_kg != null &&
            building.floor_area_m2 != null &&
            building.floor_area_m2 > 0
              ? `${fmtInt((building.co2_30d_kg * 365.25) / 30 / building.floor_area_m2)}`
              : "—"
          }
          color={BAD}
          hint="kg CO₂/m²·yr (Energieausweis field)"
        />
      </div>

      <div style={{ marginTop: 8, fontSize: 10.5, color: MUTED, lineHeight: 1.5 }}>
        A registered Energieausweis also states the <strong>primary energy</strong>{" "}
        (Primärenergiebedarf, kWh/m²·yr = final energy × the carrier&apos;s primary-energy
        factor — e.g. gas ≈ 1.1, electricity ≈ 1.8, district heat per supplier) and the
        heating <strong>energy carrier</strong> (Energieträger). These need the building&apos;s
        carrier mix — [add to complete the rating]. The CO₂ figure above is derived from the
        building&apos;s metered emissions and held flat to an annual basis.
      </div>

      {/* A–G scale */}
      <SectionTitle>A–G Effizienzklassen (residential scale)</SectionTitle>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={thStyle("left")}>Class</th>
            <th style={thStyle("left")}>Final energy (kWh/m²·yr)</th>
            <th style={thStyle("center")}>This building</th>
          </tr>
        </thead>
        <tbody>
          {BANDS.map((b) => {
            const here = b.cls === activeCls
            const band =
              b.max == null ? `≥ ${fmtInt(b.min)}` : `${fmtInt(b.min)} – < ${fmtInt(b.max)}`
            return (
              <tr key={b.cls} style={here ? { backgroundColor: "#ecfdf5" } : undefined}>
                <td style={{ ...tdL, fontWeight: 700, color: b.color }}>{b.cls}</td>
                <td style={tdL}>{band}</td>
                <td style={{ ...tdC, color: EMERALD, fontWeight: 700 }}>
                  {here ? "◀ here" : ""}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <div style={{ marginTop: 8, fontSize: 11, color: INK, lineHeight: 1.6 }}>
        {nextBetter && eui != null ? (
          <>
            To reach class <strong>{nextBetter.cls}</strong>, the building&apos;s energy
            intensity needs to fall to <strong>≤ {fmtInt(nextBetter.max ?? 0)} kWh/m²·yr</strong>{" "}
            (from {fmtInt(eui)}). The retrofit measures in the recommendations engine
            (insulation, heat pump, solar) move the building down the scale.
          </>
        ) : (
          "This building is already in the best energy class on this scale."
        )}
      </div>

      <div style={{ marginTop: 14, fontSize: 10, color: FAINT, lineHeight: 1.5 }}>
        Two certificate types exist: the consumption-based Verbrauchsausweis and the
        demand-based Bedarfsausweis. From ~July 2026 non-residential buildings must use the
        Bedarfsausweis; this estimate is consumption-based and uses the residential A–G
        scale. The figures are decision-support / preparation for a formal certificate — they
        are not the registered Energieausweis and not legal advice.
      </div>
    </div>
  )
}
