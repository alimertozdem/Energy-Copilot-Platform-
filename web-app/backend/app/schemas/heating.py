"""Schemas for the building Heating & HVAC assessment (GET /buildings/{id}/heating).

Mirrors services/heating_assessment.py. Postgres-native (no Fabric); every figure
is screening-grade / indicative.
"""
from pydantic import BaseModel


class HeatingDemand(BaseModel):
    heating_kwh: float
    heating_eui_kwh_m2: float | None
    heating_share_pct: float
    total_kwh: float
    basis: str  # measured | estimated | unknown


class HeatingSupply(BaseModel):
    fuel_type: str
    heat_cost_eur: float
    heat_co2_kg: float
    price_eur_kwh: float
    co2_factor_kg_kwh: float


class EnvelopeElement(BaseModel):
    element: str
    u_current: float | None
    u_target: float
    status: str  # pass | fail | unknown


class HeatingMeasure(BaseModel):
    key: str
    label: str
    tier: str
    saving_kwh: float | None
    saving_eur: float
    saving_co2_kg: float
    capex_gross: float
    capex_net: float
    payback_years: float | None
    note: str


class HeatingPackage(BaseModel):
    realistic_reduction_low_pct: float
    realistic_reduction_high_pct: float
    note: str


class HeatingAssessmentResponse(BaseModel):
    demand: HeatingDemand
    supply: HeatingSupply
    envelope: list[EnvelopeElement]
    measures: list[HeatingMeasure]
    package: HeatingPackage
    assumptions: dict[str, str]
