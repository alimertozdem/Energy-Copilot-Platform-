/**
 * Per-page visual configuration for the embedded Power BI report.
 *
 * Single source of truth used by:
 *   * BuildingReportShell   (/buildings/[id])
 *   * CompareReportShell    (/buildings/compare)
 *
 * Each entry maps a PBI page display name (the value PBI returns from
 * `report.getActivePage().displayName`) to:
 *   * title    : human-readable label shown in the HeroBand
 *   * color    : accent hex driving dot + gradient + glass-frame border
 *   * motifs   : per-page combination of decorative SVG components
 *
 * Colors were calibrated against the actual PBI dashboard renders
 * (PDF export 2026-05-27) so the web app chrome harmonises with each
 * page's dominant palette rather than fighting it.
 */
import type { ComponentType } from "react"

import { CitySkylineMotif } from "@/components/CitySkylineMotif"
import { SustainabilityMotif } from "@/components/SustainabilityMotif"
import { DataMatrixMotif } from "@/components/motifs/DataMatrixMotif"
import { EnergyFlowMotif } from "@/components/motifs/EnergyFlowMotif"
import { ScopeRingsMotif } from "@/components/motifs/ScopeRingsMotif"

export type MotifComponent = ComponentType<{ opacity?: number }>

export type PageConfig = {
  title: string
  color: string
  motifs: MotifComponent[]
}

export const PAGE_CONFIG: Record<string, PageConfig> = {
  "01_portfolio_overview": {
    title: "Portfolio Overview",
    color: "#1D9E75", // brand-emerald — neutral / brand-dominant page
    motifs: [SustainabilityMotif, CitySkylineMotif],
  },
  "02_building_detail": {
    title: "Building Detail",
    color: "#06B6D4", // accent-cyan — mint-teal tones in PBI tile borders
    motifs: [ScopeRingsMotif, CitySkylineMotif],
  },
  "03_anomalies_alerts": {
    title: "Anomalies & Alerts",
    color: "#F97316", // accent-orange — PBI uses orange-red (#F06030) for severities
    motifs: [DataMatrixMotif, SustainabilityMotif],
  },
  "04_forecast_recommendations": {
    title: "Forecast & Recommendations",
    color: "#EAB308", // accent-yellow — mostly muted; yellow accents on KPI titles
    motifs: [EnergyFlowMotif, SustainabilityMotif],
  },
  "05_occupancy_analysis": {
    title: "Occupancy Analysis",
    color: "#EAB308", // accent-yellow — heatmap dominates page in F0D070/F0E080 tones
    motifs: [DataMatrixMotif, ScopeRingsMotif],
  },
  "06_sustainability_compliance": {
    title: "Sustainability Compliance",
    color: "#06B6D4", // accent-cyan — Scope donut + CO2 trend lines render in 40A0F0
    motifs: [SustainabilityMotif, CitySkylineMotif],
  },
  "07_HVAC": {
    title: "HVAC Analysis",
    color: "#5DCAA5", // brand-mint — HVAC tiles use green-mint accents (#10A070)
    motifs: [ScopeRingsMotif, CitySkylineMotif],
  },
  "08_IoT": {
    title: "IoT Monitoring",
    color: "#3B82F6", // accent-blue — IoT page is muted; blue keeps it distinct
    motifs: [DataMatrixMotif, CitySkylineMotif],
  },
  "09_Battery_Strategy": {
    title: "Battery Strategy",
    color: "#1D9E75", // brand-emerald — Battery KPIs in pure emerald (#20B060)
    motifs: [EnergyFlowMotif, CitySkylineMotif],
  },
}

export const DEFAULT_PAGE_CONFIG: PageConfig = {
  title: "Energy Intelligence Report",
  color: "#1D9E75",
  motifs: [SustainabilityMotif, CitySkylineMotif],
}
