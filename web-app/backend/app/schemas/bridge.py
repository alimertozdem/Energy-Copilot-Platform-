"""Pydantic DTOs for self-serve Fabric bridging (Access Layer 3).

Two surfaces:
  * customer  -- GET bridge-readiness + POST/DELETE bridge-request on a building,
  * founder   -- GET/PATCH /admin/bridge-requests (cross-org queue).

DTOs are built explicitly in the routers (not from_attributes), mirroring the
admin schema convention.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Customer: readiness + request state ---

class BridgeReadinessPage(BaseModel):
    key: str
    label: str
    status: str  # ready | partial | locked
    reason: str


class BridgeRequestState(BaseModel):
    """The building's current/last bridge request (None if never requested)."""
    id: UUID
    status: str  # pending | approved | rejected | fulfilled | cancelled
    target_tier: str
    note: str | None
    created_at: datetime
    resolved_at: datetime | None
    resolution_note: str | None


class BridgeReadinessResponse(BaseModel):
    overall_tier: str  # empty | baseline | monitoring | full
    can_request: bool
    ready_pages: int
    partial_pages: int
    total_pages: int
    consumption_months: int
    pages: list[BridgeReadinessPage]
    summary: str
    blocking: list[str]
    # The building's current/last request, so the wizard shows "pending review" etc.
    request: BridgeRequestState | None = None
    # True once the building has been bridged (fabric_building_id set) -- the UI
    # then points the user at the live report instead of the wizard.
    is_bridged: bool = False


class BridgeRequestCreate(BaseModel):
    note: str | None = Field(default=None, max_length=1000)
    target_tier: str = "full"


# --- Founder: admin queue ---

class AdminBridgeRequestRow(BaseModel):
    id: UUID
    building_id: UUID
    building_name: str
    fabric_building_id: str | None
    organization_id: UUID
    organization_name: str
    requested_by_email: str | None
    status: str
    target_tier: str
    note: str | None
    readiness: dict | None
    created_at: datetime
    resolved_at: datetime | None
    resolution_note: str | None


class AdminBridgeRequestsResponse(BaseModel):
    requests: list[AdminBridgeRequestRow]
    total: int


class AdminBridgeResolve(BaseModel):
    status: str  # approved | rejected | fulfilled
    resolution_note: str | None = Field(default=None, max_length=1000)
    # Optional: link the building to Fabric in the same action ("Fulfil & go live").
    fabric_building_id: str | None = None


# --- Founder: Phase 3.2 automated bridge ("armed one-click") ---

class AdminBridgeAutomate(BaseModel):
    """Trigger the automated bridge for a request (or simulate it)."""
    # When true, run the orchestrator in dry-run: plan + params, no Fabric calls,
    # €0, no capacity needed. The default live run needs an active capacity.
    dry_run: bool = False
    # Optional: pin the fabric_building_id; else the orchestrator mints the next free B0NN.
    fabric_building_id: str | None = None


class AutomatedBridgeStep(BaseModel):
    step: str
    status: str
    message: str | None = None


class AutomatedBridgeResult(BaseModel):
    ok: bool
    dry_run: bool
    fabric_building_id: str | None = None
    failed_step: str | None = None
    error: str | None = None
    steps: list[AutomatedBridgeStep]
    # Whether automation is enabled server-side; false => fall back to manual.
    automation_enabled: bool = True
