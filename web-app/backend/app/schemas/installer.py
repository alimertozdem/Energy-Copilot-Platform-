"""Pydantic models for /installer-requests (Execution Marketplace Phase 0)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InstallerRequestCreate(BaseModel):
    """Body for POST /installer-requests (authenticated customer)."""

    fabric_building_id: str = Field(description="The building the measure is for.")
    action_type: str | None = Field(
        default=None, description="Recommended measure token, e.g. INSTALL_HEAT_PUMP."
    )
    measure_label: str | None = Field(
        default=None, description="Human label of the measure (for the founder's queue)."
    )
    source: str | None = Field(
        default=None, description="Where it was raised: 'actions' | 'residential'."
    )


class InstallerRequestAck(BaseModel):
    """The confirmation returned to the customer."""

    id: UUID
    status: str
    message: str


class InstallerRequestRow(BaseModel):
    """One request in the founder's broker queue."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    fabric_building_id: str
    building_name: str | None = None
    action_type: str | None = None
    measure_label: str | None = None
    note: str | None = None
    source: str | None = None
    status: str
    created_at: datetime


class InstallerRequestList(BaseModel):
    """Payload for GET /installer-requests/admin."""

    requests: list[InstallerRequestRow] = Field(default_factory=list)


class InstallerStatusUpdate(BaseModel):
    """Body for PATCH /installer-requests/admin/{id}."""

    status: str = Field(description="requested | contacted | quoted | closed")
