"""Pydantic models for the dedicated /solar detail page (Solar initiative C)."""

from datetime import date

from pydantic import BaseModel


class SolarSeriesPoint(BaseModel):
    """One day of portfolio-summed solar metrics."""

    date: date
    generated_kwh: float
    self_consumed_kwh: float
    exported_kwh: float
    performance_ratio: float | None


class SolarSummary(BaseModel):
    """Window totals + derived ratios for the solar detail page."""

    total_generated_kwh: float
    total_self_consumed_kwh: float
    total_exported_kwh: float
    avg_performance_ratio: float | None
    # self_consumed / generated (%) -- how much of generation was used on-site
    self_consumption_rate: float
    # Annualized specific yield = (generated / pv_capacity) scaled to a year
    specific_yield_kwh_kwp: float | None
    pv_capacity_kwp: float
    days: int


class SolarDetailResponse(BaseModel):
    """Full payload for /solar. has_data=False when the portfolio has no PV."""

    has_data: bool
    series: list[SolarSeriesPoint]
    summary: SolarSummary | None
