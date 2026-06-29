"""Pydantic response models for the ESRS-E1-aligned compliance export.

ESRS-E1-aligned reporting SUPPORT — indicative, NOT an audited disclosure. GHG is
read from gold_ghg_scope (tCO2e, monthly per building per scope); energy from
gold_kpi_daily. Scope 3 is an estimate; Scope 2 is reported both location- and
market-based per ESRS E1-6.
"""
from pydantic import BaseModel, Field


class EsrsScopeBreakdown(BaseModel):
    """Portfolio gross GHG by scope for the reporting year (tCO2e)."""

    scope1_tco2e: float
    scope2_location_tco2e: float
    scope2_market_tco2e: float
    scope3_tco2e: float
    total_location_tco2e: float
    total_market_tco2e: float


class EsrsBuildingRow(BaseModel):
    """Per-building GHG breakdown for the reporting year."""

    fabric_building_id: str
    name: str
    building_type: str
    floor_area_m2: float
    scope1_tco2e: float
    scope2_location_tco2e: float
    scope2_market_tco2e: float
    scope3_tco2e: float
    total_location_tco2e: float
    ghg_intensity_tco2e_m2: float | None = None
    data_quality_flag: str | None = None


class EsrsDataQuality(BaseModel):
    """Count of reported buildings per data-quality flag (worst month wins)."""

    complete: int = 0
    estimated: int = 0
    missing_gas: int = 0
    other: int = 0


class EsrsReport(BaseModel):
    """ESRS-E1-aligned portfolio summary for one reporting year."""

    reporting_year: int | None = Field(
        default=None, description="Latest reporting year present in gold_ghg_scope."
    )
    reporting_months: int | None = Field(
        default=None, description="Months of data in the reporting year (<12 = partial/YTD)."
    )
    has_data: bool = False
    buildings_total: int = Field(default=0, description="Visible buildings.")
    buildings_reported: int = Field(
        default=0, description="Buildings with GHG data in the reporting year."
    )
    floor_area_m2: float = 0.0
    energy_total_mwh: float = 0.0
    energy_renewable_pct: float | None = Field(
        default=None,
        description="On-site solar self-consumed as a share of total consumption (%).",
    )
    ghg: EsrsScopeBreakdown
    ghg_intensity_tco2e_m2: float | None = Field(
        default=None, description="Total location-based GHG ÷ reported floor area."
    )
    data_quality: EsrsDataQuality
    rows: list[EsrsBuildingRow] = []
