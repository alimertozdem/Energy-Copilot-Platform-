"""Pydantic models for the MANAGER residential dashboard (building grain).

Distinct from ``schemas/residence.py`` (the resident's own-unit view). Here a
manager sees ALL units of one building — per-unit, NAMED (legitimate under HKVO
cost allocation; the anonymized benchmark is the resident view, not this one).
"""
from pydantic import BaseModel, Field


class ResidentialUnitRow(BaseModel):
    """One unit's row in the manager building view."""

    unit_id: str
    area_m2: float | None = None
    is_heated: bool | None = None
    eui_kwh_m2_yr: float | None = None
    epc_band: str | None = None
    vs_building_pct: float | None = None
    heating_dhw_kwh_annual: float | None = None
    common_allocated_kwh: float | None = Field(
        default=None, description="kWh allocated to the unit via the HKVO 70/30 split."
    )
    cov_days: int | None = None


class UviStatus(BaseModel):
    """Monthly-consumption-info (UVI / EED) coverage for the building."""

    latest_year: int | None = None
    latest_month: int | None = None
    units_covered: int = Field(
        default=0, description="Units with data in the latest UVI month."
    )


class ResidentialBuildingRollup(BaseModel):
    """Building-level summary across its units."""

    units_with_data: int = 0
    building_avg_eui_kwh_m2_yr: float | None = None
    epc_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of units per EPC band, e.g. {'C': 3}."
    )
    uvi: UviStatus = Field(default_factory=UviStatus)


class ResidentialBuildingResponse(BaseModel):
    """Payload for GET /residential/buildings/{fabric_building_id}."""

    fabric_building_id: str
    rollup: ResidentialBuildingRollup
    units: list[ResidentialUnitRow] = Field(default_factory=list)


class ResidentInviteRequest(BaseModel):
    """Body for POST /residential/buildings/{id}/invites (manager invites a resident)."""

    fabric_unit_id: str = Field(description="Unit the resident occupies, e.g. 'B011-U0101'.")
    email: str = Field(description="Resident email — the only PII stored.")


class ResidentInviteResponse(BaseModel):
    """The minted magic-link invite (the manager delivers it to the tenant)."""

    token: str = Field(description="Raw token; link = /residence/enter?token=<token>.")
    email: str
    fabric_unit_id: str
    expires_at: str



class ResidentialPortfolioRow(BaseModel):
    """One residential building in the portfolio overview."""

    fabric_building_id: str
    name: str
    city: str | None = None
    country_code: str | None = None
    rollup: ResidentialBuildingRollup


class ResidentialPortfolioResponse(BaseModel):
    """Payload for GET /residential/portfolio — all visible residential buildings."""

    buildings: list[ResidentialPortfolioRow] = Field(default_factory=list)


# --- UVI / HKVO compliance readiness (R1: the residential 'why now' wedge) ---

class UviComplianceRow(BaseModel):
    """One building's monthly-consumption-info (UVI) compliance readiness.

    HKVO §6a makes monthly UVI mandatory; §12 lets a resident cut 3% of their
    consumption-based heating cost when the duty is breached. So coverage +
    recency = compliance, and the penalty exposure quantifies the risk.
    """

    fabric_building_id: str
    name: str
    total_units: int = 0
    units_covered: int = Field(default=0, description="Units with data in the latest UVI month.")
    coverage_pct: float | None = Field(default=None, description="units_covered / total_units (0–1).")
    latest_year: int | None = None
    latest_month: int | None = None
    months_since_latest: int | None = Field(
        default=None, description="Whole months between the latest UVI month and now."
    )
    annual_heat_kwh: float | None = Field(
        default=None, description="Σ unit heating+DHW kWh/yr (basis for the penalty estimate)."
    )
    penalty_exposure_eur: float | None = Field(
        default=None,
        description="Indicative HKVO §12 exposure = 3% × annual heating cost (kWh × heat tariff).",
    )
    status: str = Field(description="ready | partial | at_risk")


class UviComplianceResponse(BaseModel):
    """Payload for GET /residential/uvi-compliance."""

    deadline: str = Field(description="HKVO monthly-UVI mandatory date (ISO).")
    buildings_total: int = 0
    buildings_ready: int = 0
    buildings_at_risk: int = 0
    total_penalty_exposure_eur: float = 0.0
    # Stated assumptions surfaced for an honest footnote.
    heat_tariff_eur_kwh: float = 0.0
    note: str = ""
    rows: list[UviComplianceRow] = Field(default_factory=list)
