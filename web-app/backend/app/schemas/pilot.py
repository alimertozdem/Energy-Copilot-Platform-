"""DTOs for the public 'request a pilot' lead capture + the founder admin queue."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PilotRequestCreate(BaseModel):
    """Public submission from the landing / demo / tour. No auth."""

    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    organization: str | None = Field(default=None, max_length=200)
    country_code: str | None = Field(default=None, max_length=2)
    building_count: int | None = Field(default=None, ge=0, le=1_000_000)
    message: str | None = Field(default=None, max_length=2000)
    source: str | None = Field(default=None, max_length=40)


class PilotRequestAck(BaseModel):
    """Returned to the public submitter — minimal, no internal fields."""

    ok: bool = True
    id: UUID


# --- Founder admin queue ---

class AdminPilotRequestRow(BaseModel):
    id: UUID
    name: str
    email: str
    organization: str | None
    country_code: str | None
    building_count: int | None
    message: str | None
    source: str | None
    status: str
    created_at: datetime


class AdminPilotRequestsResponse(BaseModel):
    requests: list[AdminPilotRequestRow]
    total: int


class AdminPilotResolve(BaseModel):
    status: str  # new | contacted | qualified | closed
