"""Schemas for the building Heating & HVAC assessment (GET /buildings/{id}/heating).

Mirrors services/heating_assessment.py. Postgres-native (no Fabric); every figure
is screening-grade / indicative, shown with an uncertainty band and a sequenced
retrofit package (the decision artifact).
"""
from pydantic import BaseModel


class HeatingDemand(BaseModel):
    heating_kwh: float
    heating_kwh_low: float
    heating_kwh_high: float
    heating_eui_kwh_m2: float | None
    heating_share_pct: float
    total_kwh: float
    basis: str  # measured | estimated | unknown
    band_pct: float


class HeatingSupply(BaseModel):
    fuel_type: str
    fuel_assumed: bool
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
    saving_kwh_gross: float | None
    saving_eur: float
    saving_co2_kg: float
    capex_gross: float
    capex_net: float
    payback_years: float | None
    note: str


class PackageStep(BaseModel):
    key: str
    label: str
    tier: str
    cumulative_reduction_pct: float
    cumulative_capex_net: float
    cumulative_saving_eur: float
    cumulative_co2_saved_kg: float
    heating_eui_after: float | None
    payback_years: float | None


class PackageFull(BaseModel):
    reduction_pct: float
    capex_net: float
    capex_net_low: float
    capex_net_high: float
    saving_eur: float
    co2_saved_kg: float
    payback_years: float | None
    payback_years_low: float | None
    payback_years_high: float | None
    payback_years_2030_carbon: float | None
    eui_before: float | None
    eui_after: float | None


class PackageSensitivity(BaseModel):
    capex_band_pct: float
    value_band_pct: float
    carbon_price_now: float
    carbon_price_2030: float
    note: str


class HeatingPackage(BaseModel):
    realistic_reduction_low_pct: float
    realistic_reduction_high_pct: float
    note: str
    steps: list[PackageStep]
    full: PackageFull | None
    sensitivity: PackageSensitivity | None = None


class HeatingCarbon(BaseModel):
    building_type: str
    total_co2_intensity_kg_m2: float | None
    total_co2_intensity_after_kg_m2: float | None
    heating_co2_kg: float
    heating_share_of_carbon_pct: float | None
    package_co2_saved_kg: float
    basis: str  # measured | estimated | unknown


class HeatingRegulation(BaseModel):
    status: str  # applies | check_fuel | met
    note: str


class HeatingEpc(BaseModel):
    scale: str
    eui_now_kwh_m2: float | None
    eui_after_kwh_m2: float | None
    class_now: str | None
    class_after: str | None
    meps_milestone: str | None   # "2030" | "2033" | None
    clears_meps: bool
    anchored_to_epc: bool
    basis: str


class HeatingAssessmentResponse(BaseModel):
    demand: HeatingDemand
    supply: HeatingSupply
    envelope: list[EnvelopeElement]
    measures: list[HeatingMeasure]
    package: HeatingPackage
    carbon: HeatingCarbon
    regulation: HeatingRegulation
    epc: HeatingEpc
    assumptions: dict[str, str]
