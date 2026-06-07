"""Pydantic response models for /portfolio endpoints."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class PortfolioPeriod(BaseModel):
    """The rolling window the KPIs cover."""

    start_date: date
    end_date: date
    days: int = Field(default=30, description="Length of the rolling window in days.")


class KPITile(BaseModel):
    """One numeric value with a delta vs the prior period."""

    value: float = Field(description="Raw numeric value for the current period.")
    unit: str = Field(description="Unit label, e.g. kWh, EUR, kg CO2e.")
    delta_pct: float | None = Field(
        default=None,
        description="Percent change vs prior period; None if prior period had no data.",
    )
    direction: Literal["up", "down", "neutral"] = Field(
        default="neutral",
        description="Sign of the delta (physical: rose/fell). UI maps it to good/bad per metric.",
    )


class SolarKPIs(BaseModel):
    """On-site solar tiles. Only present when the portfolio has PV (else null).

    For these metrics 'up' is GOOD (more generation / higher renewable share /
    more CO2 avoided), the opposite of energy/cost/CO2.
    """

    generated: KPITile
    renewable_rate: KPITile
    exported: KPITile
    co2_avoided: KPITile


class PortfolioKPIs(BaseModel):
    """Four top-of-page KPI tiles + the period they cover, plus optional solar."""

    period: PortfolioPeriod
    total_energy: KPITile
    avg_eui: KPITile
    total_cost: KPITile
    total_co2: KPITile
    solar: SolarKPIs | None = None


class PortfolioBuildingRow(BaseModel):
    """One row in the buildings table on /portfolio."""

    fabric_building_id: str
    name: str
    city: str
    country: str
    building_type: str
    floor_area_m2: float
    epc_class: str | None

    kwh_30d: float
    cost_30d_eur: float
    co2_30d_kg: float
    eui_kwh_m2_yr: float | None = Field(
        default=None,
        description="Annualized EUI (kWh/m2/yr). None when floor area is zero or missing.",
    )

    open_anomalies: int = Field(description="Unresolved HIGH+CRITICAL anomalies.")
    open_recommendations: int = Field(
        description="Total recommendations on file. V1: no status filter."
    )

    has_pv: bool
    has_battery: bool
    has_iot: bool
    subscription_tier: str = Field(description="Monitor / Insight / Copilot")


class PortfolioBuildingsResponse(BaseModel):
    """Building table payload."""

    buildings: list[PortfolioBuildingRow]
