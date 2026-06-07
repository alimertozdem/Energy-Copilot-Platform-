"""Pydantic response models for the /residence (resident-view) endpoints.

The resident sees ONLY their own unit(s): per-unit heating/DHW EUI + EPC band, the
HKVO common-area allocation, and the monthly UVI series. The building benchmark is
already anonymized + pre-aggregated INTO each unit's own Gold row
(``building_avg_*`` + ``vs_building_pct``) -- so these models never carry another
named unit's data. See ``docs/architecture/residential-data-model.md`` (privacy
posture) and ``unified-access-model.md`` (resident scope).
"""
from datetime import date

from pydantic import BaseModel, Field


class ResidenceKpi(BaseModel):
    """Per-unit headline KPIs (from ``gold_residential_unit_kpi``)."""

    eui_kwh_m2_yr: float | None = Field(
        default=None, description="Heating+DHW energy use intensity, annualized."
    )
    eui_climate_adjusted_kwh_m2_yr: float | None = Field(
        default=None,
        description="HDD-normalized EUI. Equals raw EUI while climate_adjustment_factor=1.0.",
    )
    climate_adjustment_factor: float | None = Field(
        default=None,
        description="HDD normalization factor. 1.0 = not yet wired (no weather for the building).",
    )
    epc_band: str | None = Field(
        default=None, description="A-E band on the RESIDENTIAL_MF scale (50/80/120/180)."
    )
    heating_dhw_kwh_annual: float | None = Field(
        default=None, description="Annualized heating+DHW consumption (kWh)."
    )
    building_avg_eui_kwh_m2_yr: float | None = Field(
        default=None, description="Anonymized building-average EUI (benchmark)."
    )
    vs_building_pct: float | None = Field(
        default=None, description="This unit's EUI vs the building average, percent."
    )
    coverage_start: date | None = None
    coverage_end: date | None = None
    cov_days: int | None = Field(
        default=None, description="Days of metered coverage behind the annualization."
    )


class ResidenceCommonArea(BaseModel):
    """The unit's share of building energy under the HKVO split (from
    ``gold_residential_common_split``). Default weighting is 70% consumption /
    30% area (``cons_weight`` / ``area_weight``)."""

    unit_metered_kwh: float | None = None
    unit_allocated_kwh: float | None = Field(
        default=None, description="kWh allocated to this unit after the HKVO split."
    )
    allocation_share: float | None = Field(
        default=None, description="This unit's fraction of the building total (0..1)."
    )
    cons_weight: float | None = Field(default=None, description="HKVO consumption weight (default 0.70).")
    area_weight: float | None = Field(default=None, description="HKVO area weight (default 0.30).")
    cons_share: float | None = None
    area_share: float | None = None
    building_total_kwh: float | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None


class ResidenceMonthlyPoint(BaseModel):
    """One UVI series point: a (year, month, energy_type) row from
    ``gold_residential_uvi_monthly``. This is the data behind the legally-required
    monthly consumption information (EED/HKVO)."""

    year: int
    month: int
    energy_type: str = Field(description="'heating' or 'dhw'.")
    kwh: float | None = None
    cost_eur: float | None = None
    building_avg_kwh: float | None = Field(
        default=None, description="Anonymized building-average for this month/type."
    )
    vs_building_pct: float | None = None


class ResidenceUnit(BaseModel):
    """Everything the resident sees for one of their units."""

    unit_id: str
    area_m2: float | None = None
    is_heated: bool | None = None
    kpi: ResidenceKpi | None = Field(
        default=None, description="None when the unit has no Gold KPI row yet."
    )
    common_area: ResidenceCommonArea | None = None
    monthly: list[ResidenceMonthlyPoint] = Field(default_factory=list)


class ResidenceSummary(BaseModel):
    """The /residence/summary payload.

    A resident usually occupies one unit, but ``resolve_resident_scope`` returns a
    set (a resident could hold more than one tenancy), so this is a list.
    """

    as_of: date = Field(description="Date the tenancy-window scope was resolved for.")
    units: list[ResidenceUnit] = Field(default_factory=list)


class ResidentConsumeRequest(BaseModel):
    """Body for POST /residence/auth/consume — the raw magic-link token."""

    token: str = Field(description="The raw token from the magic-link URL.")


class ResidentSession(BaseModel):
    """Resident session JWT returned by /residence/auth/consume."""

    resident_token: str
    expires_in_hours: int
