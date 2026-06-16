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
    # Specific yield = generated / installed kWp. Annualized only over a ~full
    # year (see specific_yield_annualized); shorter windows are window-as-is.
    specific_yield_kwh_kwp: float | None
    # True when the yield was scaled to a full year; False/None = raw window
    # yield, so the UI can label it honestly.
    specific_yield_annualized: bool | None = None
    pv_capacity_kwp: float
    days: int
    # data provenance (honesty layer): "telemetry" (all real), "sample" (all
    # synthetic), or "mixed".
    data_basis: str = "sample"
    real_building_count: int = 0
    simulated_building_count: int = 0
    # self-consumption is only known for metered buildings; coverage = how much of
    # total generation that represents (None/unavailable when inverter-only).
    self_consumption_available: bool = True
    self_consumption_coverage_pct: float | None = None


class SolarDetailResponse(BaseModel):
    """Full payload for /solar. has_data=False when the portfolio has no PV."""

    has_data: bool
    series: list[SolarSeriesPoint]
    summary: SolarSummary | None
