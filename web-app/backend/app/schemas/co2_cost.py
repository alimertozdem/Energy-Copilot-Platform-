"""CO₂ cost-allocation (CO2KostAufG) report schema.

Per-building landlord/tenant split of the heating-fuel CO₂ price under the German
Kohlendioxidkostenaufteilungsgesetz (CO2KostAufG). Residential/mixed buildings use
the statutory 10-step model on kg CO₂ per m² of LIVING AREA (Wohnfläche); non-
residential buildings use the flat 50/50 split (the NWG step model is not yet in
force). Decision-support, not legal advice — see ``note`` / ``data_source`` and the
report disclaimer.
"""
from pydantic import BaseModel


class Co2StairTier(BaseModel):
    """One step of the statutory residential 10-step model (Anlage zu § 7 CO2KostAufG)."""

    tier: int
    min_kg_m2: float
    max_kg_m2: float | None  # None = open-ended top step (≥ 52)
    landlord_pct: int
    tenant_pct: int


class Co2UnitAllocation(BaseModel):
    """One dwelling's area-pro-rata share of the building heating-CO₂ cost (Est.).

    The split is by living-area share (Wohnfläche pro-rata), NOT per-unit metering;
    the same building-wide step landlord/tenant ratio applies to every unit.
    """

    unit_id: str
    area_m2: float | None
    area_share_pct: float | None
    co2_kg: float | None
    cost_eur: float | None
    landlord_cost_eur: float | None
    tenant_cost_eur: float | None


class Co2CostAllocationResponse(BaseModel):
    fabric_building_id: str
    building_name: str
    building_type: str
    country_code: str | None
    is_residential: bool
    reporting_year: int | None
    has_data: bool

    # Inputs (heating-fuel basis: only fuels that incur the CO₂ price)
    floor_area_m2: float | None  # area used for the intensity (see area_basis)
    area_basis: str  # "Wohnfläche (living area)" | "gross floor area"
    heating_co2_tonnes: float | None  # Scope-1 gas + oil/diesel (levied fuels)
    energy_content_kwh: float | None  # delivered heating energy (Energiegehalt, kWh)
    co2_intensity_kg_m2: float | None  # = heating CO₂ ÷ area — drives the step
    gas_emission_factor_kg_kwh: float  # BEHG natural-gas EF used for estimates

    # Prices: 2026 national nEHS corridor (€55–65/t), and the EU ETS2 onset (2028).
    co2_price_eur_t: float
    co2_price_eur_t_ets2: float
    ets2_year: int

    total_co2_cost_eur: float | None
    total_co2_cost_eur_ets2: float | None

    # Allocation result
    model: str  # "stair_10" (residential) | "flat_50_50" (non-residential)
    tier: int | None  # 1..10 for residential, else None
    landlord_pct: int | None
    tenant_pct: int | None
    landlord_cost_eur: float | None
    tenant_cost_eur: float | None
    landlord_cost_eur_ets2: float | None
    tenant_cost_eur_ets2: float | None

    # Reference + provenance
    # Per-unit (dwelling) breakdown — residential only, area pro-rata ESTIMATE
    # (Wohnfläche share, not per-unit metering). Empty for non-residential or
    # buildings without unit data.
    units: list[Co2UnitAllocation] = []
    unit_count: int | None = None

    stair: list[Co2StairTier]
    note: str
    data_source: str
