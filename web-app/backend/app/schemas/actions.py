"""Pydantic models for /actions endpoints.

`/actions` is the per-org tracking layer on top of Power BI Page 5
recommendations:
  * Fabric `gold_recommendations` holds the catalog (1 row = 1 surfaced
    recommendation per building).
  * Postgres `recommendation_status` holds the customer-side state (whose
    open, what's been completed, who closed it, etc.) overlayed via the
    synthetic ID `"{building_id}|{rank}"`.

The schemas below describe the joined view that the frontend table renders.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ActionStatus = Literal[
    "open", "in_progress", "completed", "dismissed", "not_applicable"
]
"""Allowed lifecycle values. `not_applicable` is reserved for false positives;
the table UI may collapse it into 'dismissed' for V1.
"""


class ActionItem(BaseModel):
    """One row on the /actions table."""

    # Synthetic identifier: "{fabric_building_id}|{rank}"
    # This is the value the frontend echoes back to PATCH /actions/{id} when
    # the user changes the status. Stable per (building, rank) — if Page 5
    # reranks recommendations the ID may shift, which is the V1 trade-off.
    action_id: str = Field(description="Synthetic id, e.g. 'B001|3'.")

    fabric_building_id: str
    building_name: str
    rank: int | None = Field(default=None, description="Position from gold_recommendations.")

    action_type: str | None = Field(default=None, description="Category: HVAC, Lighting, etc.")
    title: str | None = Field(default=None, description="title_en from Fabric.")
    description: str | None = Field(default=None, description="description_en from Fabric.")

    priority_label: str | None = None
    priority_score: float | None = None
    compliance_driver: str | None = None

    annual_saving_eur: float | None = None
    co2_saving_kg: float | None = None
    capex_eur: float | None = None
    net_capex_eur: float | None = None
    grant_eur: float | None = None
    payback_years: float | None = None
    npv_eur: float | None = None

    # Postgres overlay
    status: ActionStatus = Field(
        default="open",
        description="Defaults to 'open' when there's no recommendation_status row.",
    )
    status_updated_at: datetime | None = Field(
        default=None,
        description="Postgres recommendation_status.updated_at; None when never edited.",
    )
    completed_at: datetime | None = None
    notes: str | None = None

    can_manage: bool = Field(
        default=False,
        description=(
            "True if the caller may change this recommendation's status (own org "
            "or full-manage partner). False = read-only (e.g. sample buildings)."
        ),
    )


class ActionStatusCounts(BaseModel):
    """Aggregate counts used by the AppChrome nav badge and filter chips."""

    open: int = 0
    in_progress: int = 0
    completed: int = 0
    dismissed: int = 0
    not_applicable: int = 0
    total: int = 0


class ActionsResponse(BaseModel):
    """The /actions GET payload."""

    actions: list[ActionItem]
    status_counts: ActionStatusCounts


class ActionStatusUpdateRequest(BaseModel):
    """Body for PATCH /actions/{action_id}.

    `building_id` is also required (parsed from action_id but re-passed for
    explicit authorization). Mismatch with action_id prefix returns 400.
    """

    status: ActionStatus
    notes: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional free-text notes about the status change.",
    )


class ActionStatusUpdateResponse(BaseModel):
    """Returned after a successful PATCH."""

    action_id: str
    status: ActionStatus
    status_updated_at: datetime
    completed_at: datetime | None = None
