"""Pydantic schemas for the building-consumption upload (CSV / manual baseline).

The CSV is parsed client-side into normalized monthly rows and POSTed as JSON,
so the backend stays simple (no multipart / file handling).
"""
from pydantic import BaseModel, Field


class ConsumptionRow(BaseModel):
    """One month of consumption."""

    # Billing / reading period as "YYYY-MM".
    period: str = Field(min_length=7, max_length=7)
    energy_kwh: float = Field(ge=0)
    cost_eur: float | None = Field(default=None, ge=0)


class ConsumptionUploadRequest(BaseModel):
    """Payload for POST /buildings/{building_id}/consumption."""

    rows: list[ConsumptionRow] = Field(min_length=1, max_length=240)
    source: str = Field(default="csv", max_length=20)


class ConsumptionSummary(BaseModel):
    """Aggregate view returned after upload + by GET."""

    months: int
    period_start: str | None
    period_end: str | None
    total_kwh: float
    total_cost_eur: float | None
    avg_monthly_kwh: float | None


class BaselineKPIs(BaseModel):
    """Baseline KPIs computed from the uploaded consumption (Tier-1, Postgres-side).

    Indicative figures so a pending / upload-only building lights up the
    dashboard + advisor before live Fabric data. Provenance flags let the UI
    label honestly: annualized vs trailing-12, actual vs estimated cost, and the
    grid-factor source/confidence.
    """

    source: str = "uploaded_baseline"
    has_data: bool
    months_available: int
    window_months: int
    period_start: str | None
    period_end: str | None
    window: str  # "trailing_12" | "annualized_from_N" | "none"
    is_annualized: bool

    annual_energy_kwh: float | None
    eui_kwh_m2_yr: float | None
    annual_co2_kg: float | None
    annual_cost_eur: float | None

    kwh_30d: float | None
    co2_30d_kg: float | None
    cost_30d_eur: float | None

    cost_basis: str  # "actual" | "estimated" | "unknown"
    cost_rate_eur_kwh: float | None

    co2_factor_kg_kwh: float | None
    co2_factor_year: int | None
    co2_factor_confidence: str | None
    co2_factor_source: str | None

    floor_area_m2: float | None


class ParsePdfRequest(BaseModel):
    """A base64-encoded PDF bill to extract candidate monthly rows from."""

    pdf_base64: str = Field(min_length=1, max_length=12_000_000)


class ParsedBillResponse(BaseModel):
    """Candidate rows extracted from a PDF bill — shown for review, not saved."""

    rows: list[ConsumptionRow]
    source: str  # "table" | "text" | "none"
    warnings: list[str]
