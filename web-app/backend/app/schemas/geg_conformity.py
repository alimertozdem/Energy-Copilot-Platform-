"""GEG conformity (Gebäudeenergiegesetz) report schema — per building.

Screening of a German building's conformity with the GEG: §71 renewable-heating duty
(65% renewable, on the municipal-heat-planning timeline) and §48 / Anlage 7 component
U-value limits (which apply when a component is renovated). Decision-support, not a
formal Nachweis or legal advice.
"""
from pydantic import BaseModel


class GegComponent(BaseModel):
    component: str  # "Exterior wall" | "Roof" | "Windows"
    current_u: float | None  # W/m²K
    limit_u: float  # GEG Anlage 7 limit
    compliant: bool | None
    note: str | None = None


class GegConformityResponse(BaseModel):
    fabric_building_id: str
    building_name: str
    building_type: str
    country_code: str | None
    applies: bool  # GEG is German law; False (informational) for non-DE buildings
    has_data: bool

    geg_score: float | None
    geg_status: str | None

    # §71 — renewable heating
    heating_compliant: bool | None
    heating_note: str

    # §48 / Anlage 7 — envelope components (on renovation)
    components: list[GegComponent]
    components_compliant: int
    components_total: int

    note: str
    data_source: str
