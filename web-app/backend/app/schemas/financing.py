"""Schemas for the portfolio financing summary (GET /financing/summary).

Mirrors services/financing.py + finance_model.py. Every forward figure is a
screening-grade scenario range; SUPPORT, NOT ADVICE.
"""
from pydantic import BaseModel


class FinancingMeasure(BaseModel):
    building_name: str
    fabric_building_id: str
    title: str
    action_type: str | None
    program: str
    scheme: str
    eligible: bool
    rate_low_pct: float
    rate_high_pct: float
    eligible_cost_eur: float | None
    grant_low_eur: float | None
    grant_high_eur: float | None
    units_basis: int | None
    subsidy_note: str
    capex_gross_eur: float
    net_capex_eur: float
    assumed_lifetime_years: int
    simple_payback_years: float | None
    npv_base_eur: float | None


class FinancingScenario(BaseModel):
    scenario: str  # conservative | base | high
    total_npv_eur: float
    carbon_2030_eur_t: float
    energy_inflation_pct: float


class FinancingValueUplift(BaseModel):
    priority_buildings: int
    assumed_band_jump: int
    uplift_low_pct: float
    uplift_high_pct: float
    note: str


class FinancingPortfolio(BaseModel):
    total_capex_gross_eur: float = 0.0
    total_grant_low_eur: float = 0.0
    total_grant_high_eur: float = 0.0
    total_net_after_grant_eur: float = 0.0
    eligible_measure_count: int = 0
    scenarios: list[FinancingScenario] = []
    value_uplift: FinancingValueUplift | None = None


class FinancingResponse(BaseModel):
    measures: list[FinancingMeasure]
    portfolio: FinancingPortfolio
    assumptions: dict
    note: str
