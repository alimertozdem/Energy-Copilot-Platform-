/**
 * On-site solar KPI row for /portfolio.
 *
 * Rendered only when the portfolio has PV (PortfolioKPIs.solar != null).
 * Uses an amber/gold accent to set solar apart from the emerald energy row,
 * and lowerIsBetter={false} so a rise in generation/renewable share reads as
 * good (emerald delta), not bad.
 */
import { KPITile } from "./KPITile"
import type { SolarKPIs } from "@/lib/api/portfolio"

const SOLAR_ACCENT = "#F59E0B" // amber/gold — solar

export function SolarKPIRow({ solar }: { solar: SolarKPIs }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span
          className="size-1.5 rounded-full"
          style={{ backgroundColor: SOLAR_ACCENT }}
        />
        <h3 className="text-sm font-medium text-text-primary">On-site Solar</h3>
        <span className="text-xs text-text-faint">last 30 days</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPITile
          label="Solar Generated"
          value={solar.generated.value}
          unit={solar.generated.unit}
          delta_pct={solar.generated.delta_pct}
          direction={solar.generated.direction}
          accent={SOLAR_ACCENT}
          lowerIsBetter={false}
        />
        <KPITile
          label="Renewable Rate"
          value={solar.renewable_rate.value}
          unit={solar.renewable_rate.unit}
          delta_pct={solar.renewable_rate.delta_pct}
          direction={solar.renewable_rate.direction}
          accent={SOLAR_ACCENT}
          lowerIsBetter={false}
        />
        <KPITile
          label="Solar Exported"
          value={solar.exported.value}
          unit={solar.exported.unit}
          delta_pct={solar.exported.delta_pct}
          direction={solar.exported.direction}
          accent={SOLAR_ACCENT}
          lowerIsBetter={false}
        />
        <KPITile
          label="CO₂ Avoided"
          value={solar.co2_avoided.value}
          unit={solar.co2_avoided.unit}
          delta_pct={solar.co2_avoided.delta_pct}
          direction={solar.co2_avoided.direction}
          accent={SOLAR_ACCENT}
          lowerIsBetter={false}
        />
      </div>
    </div>
  )
}
