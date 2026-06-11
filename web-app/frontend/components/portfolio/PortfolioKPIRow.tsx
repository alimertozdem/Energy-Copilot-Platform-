/**
 * Four-tile row of headline portfolio KPIs.
 *
 * Consumes the typed response from fetchPortfolioKPIs() and renders one
 * KPITile per metric. Accent color is fixed to the Portfolio section
 * (brand-emerald, page section I in the cartographic atlas).
 */
import { KPITile } from "./KPITile"
import type { PortfolioKPIs } from "@/lib/api/portfolio"

// Section I — Portfolio. Matches PAGE_CONFIG["01_portfolio_overview"].color.
const PORTFOLIO_ACCENT = "#1D9E75"

export function PortfolioKPIRow({ kpis }: { kpis: PortfolioKPIs }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <KPITile
        label="Total Energy"
        value={kpis.total_energy.value}
        unit={kpis.total_energy.unit}
        delta_pct={kpis.total_energy.delta_pct}
        direction={kpis.total_energy.direction}
        accent={PORTFOLIO_ACCENT}
      />
      <KPITile
        label="Avg EUI"
        value={kpis.avg_eui.value}
        unit={kpis.avg_eui.unit}
        delta_pct={kpis.avg_eui.delta_pct}
        direction={kpis.avg_eui.direction}
        accent={PORTFOLIO_ACCENT}
        term="eui"
      />
      <KPITile
        label="Total Cost"
        value={kpis.total_cost.value}
        unit={kpis.total_cost.unit}
        delta_pct={kpis.total_cost.delta_pct}
        direction={kpis.total_cost.direction}
        accent={PORTFOLIO_ACCENT}
        term="energy_cost"
      />
      <KPITile
        label="Total CO₂"
        value={kpis.total_co2.value}
        unit={kpis.total_co2.unit}
        delta_pct={kpis.total_co2.delta_pct}
        direction={kpis.total_co2.direction}
        accent={PORTFOLIO_ACCENT}
        term="co2_emissions"
      />
    </div>
  )
}
