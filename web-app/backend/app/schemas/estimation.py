"""Pydantic schemas for the Tier-A estimation engine endpoints.

Building level (GET /buildings/{id}/estimate), portfolio level
(GET /portfolio/estimates), and the screening-input update that lets a user
sharpen an estimate (PATCH /buildings/{id}/profile).
"""
from pydantic import BaseModel, Field


class EngineEstimate(BaseModel):
    basis: str                       # estimated | actual
    confidence: str                  # high | medium | low | very_low
    method: str
    building_type: str | None = None
    area_m2: float | None = None
    area_basis: str | None = None    # user | gold | footprint | none
    eui_low: float | None = None
    eui_point: float | None = None
    eui_high: float | None = None
    annual_kwh_low: float | None = None
    annual_kwh_point: float | None = None
    annual_kwh_high: float | None = None
    annual_cost_eur_low: float | None = None
    annual_cost_eur_point: float | None = None
    annual_cost_eur_high: float | None = None
    annual_co2_kg_low: float | None = None
    annual_co2_kg_point: float | None = None
    annual_co2_kg_high: float | None = None
    cost_basis: str = "fuel_split"
    editable_fields: list[str] = []


class EngineEstimateResponse(BaseModel):
    """available=False when the type isn't modeled (e.g. Datacenter)."""

    available: bool
    reason: str | None = None
    estimate: EngineEstimate | None = None


class PortfolioEstimateRow(BaseModel):
    """One building's compact screening line for the portfolio view."""

    building_id: str
    name: str | None = None
    city: str | None = None
    building_type: str | None = None
    area_m2: float | None = None
    available: bool
    basis: str                       # estimated | actual
    confidence: str
    has_real_data: bool              # any uploaded consumption rows
    eui_low: float | None = None
    eui_point: float | None = None
    eui_high: float | None = None
    annual_cost_eur_point: float | None = None
    annual_co2_kg_point: float | None = None


class PortfolioEstimatesResponse(BaseModel):
    total: int
    scored: int                      # rows with an EUI point
    estimated_count: int             # basis == 'estimated'
    actual_count: int                # basis == 'actual'
    rows: list[PortfolioEstimateRow]


class BuildingProfileUpdate(BaseModel):
    """Screening inputs a user can supply to sharpen an estimate. All optional;
    only the whitelisted fields are writable."""

    construction_year: int | None = Field(default=None, ge=1800, le=2100)
    epc_class: str | None = Field(default=None, max_length=3)
    heating_system: str | None = Field(default=None, max_length=40)
    floor_area_m2: float | None = Field(default=None, gt=0, le=10_000_000)


class BuildingProfileResponse(BaseModel):
    building_id: str
    construction_year: int | None = None
    epc_class: str | None = None
    heating_system: str | None = None
    floor_area_m2: float | None = None
