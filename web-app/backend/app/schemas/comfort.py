"""Schemas for comfort & operation analytics (GET /buildings/{id}/comfort).

Mirrors services/comfort.py. Postgres-native; standard comfort references.
"""
from pydantic import BaseModel


class TempComfort(BaseModel):
    avg: float
    in_band_pct: float
    under_pct: float
    over_pct: float
    samples: int
    band_low: float
    band_high: float


class Co2Comfort(BaseModel):
    avg: float
    good_pct: float
    fair_pct: float
    poor_pct: float
    samples: int


class HumidityComfort(BaseModel):
    avg: float
    in_band_pct: float
    samples: int


class ComfortAction(BaseModel):
    key: str
    kind: str  # savings | comfort | iaq
    title: str
    detail: str
    saving_pct_low: float | None
    saving_pct_high: float | None


class ComfortResponse(BaseModel):
    has_data: bool
    window_hours: int
    simulated: bool
    temperature: TempComfort | None
    co2: Co2Comfort | None
    humidity: HumidityComfort | None
    delta_t: float | None
    operational_hint: str | None
    actions: list[ComfortAction] = []
