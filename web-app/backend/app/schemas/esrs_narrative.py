"""Schemas for the ESRS E-1 narrative editor (per-organization saved disclosures)."""
from pydantic import BaseModel


class EsrsNarrativeItem(BaseModel):
    datapoint_key: str
    content: str
    reporting_year: int | None = None
    updated_at: str | None = None


class EsrsNarrativeResponse(BaseModel):
    items: list[EsrsNarrativeItem]


class EsrsNarrativeUpdate(BaseModel):
    content: str
    reporting_year: int | None = None
