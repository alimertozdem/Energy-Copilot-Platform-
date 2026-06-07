"""Pydantic models for /abatement — the portfolio Marginal Abatement Cost Curve.

A MACC ranks decarbonisation measures by cost-effectiveness (€ per tonne CO2
avoided). Measures with a NEGATIVE marginal abatement cost pay for themselves
(energy savings exceed the annualised cost) — the classic "no-regret" left side
of the curve. The data comes from Fabric `gold_recommendations` (the same catalog
behind /actions): each row has annual CO2 saved, annual € saving, and net CapEx.

This is decision-support, not audited financials — the marginal cost uses a
simplified, undiscounted annualisation with a stated measure-lifetime assumption
(see services/abatement.py). Framed as indicative, per CLAUDE.md.
"""
from pydantic import BaseModel, Field


class MaccMeasure(BaseModel):
    """One measure (one recommendation) placed on the abatement curve."""

    action_id: str = Field(description="Synthetic id '{building_id}|{rank}'.")
    fabric_building_id: str
    building_name: str
    title: str | None = None
    action_type: str | None = None
    compliance_driver: str | None = None

    annual_co2_t: float = Field(description="Annual CO2 abated, tonnes.")
    annual_saving_eur: float = Field(description="Annual energy-cost saving, €.")
    net_capex_eur: float = Field(description="CapEx after grants, €.")
    assumed_lifetime_years: int = Field(description="Stated measure lifetime used to annualise CapEx.")

    mac_eur_per_t: float = Field(
        description="Marginal abatement cost, €/tCO2. Negative = pays for itself."
    )
    is_profitable: bool = Field(description="True when mac_eur_per_t < 0.")

    # Running total of annual_co2_t once measures are sorted cheapest-first —
    # this is the x-position (right edge) of the measure's bar on the curve.
    cumulative_co2_t: float


class MaccTotals(BaseModel):
    measure_count: int = 0
    total_annual_co2_t: float = 0.0
    profitable_annual_co2_t: float = Field(
        default=0.0, description="CO2 abated by measures with negative MAC (no-regret)."
    )
    total_net_capex_eur: float = 0.0
    profitable_net_capex_eur: float = Field(
        default=0.0, description="CapEx of the no-regret measures only."
    )
    weighted_avg_mac_eur_per_t: float | None = Field(
        default=None, description="CO2-weighted average MAC across all measures."
    )


class MaccResponse(BaseModel):
    """GET /abatement/macc payload — measures sorted by MAC ascending."""

    measures: list[MaccMeasure]
    totals: MaccTotals
    # Surfaces the assumption set to the UI so it can show an honest footnote.
    lifetime_assumptions: dict[str, int]
    note: str
