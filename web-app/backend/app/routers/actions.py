"""Actions router — GET /actions + PATCH /actions/{action_id}.

JWT-protected (mirrors /portfolio, /buildings). The frontend obtains the
token from NextAuth and forwards it as Bearer.

Visibility (delegated to actions_data service):
  * Recommendations for buildings in orgs the user belongs to
  * Plus recommendations for any sample/demo org's buildings

Status lifecycle:
  open → in_progress → completed (terminal)
  open → dismissed / not_applicable

The synthetic action_id used in PATCH is the same value returned by
GET /actions: "{fabric_building_id}|{rank}".

A successful status change records a recommendation.status_changed audit row
(best-effort, after the service commits) so it surfaces in /settings Activity.
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import audit as audit_repo
from app.repositories import building as building_repo
from app.schemas.actions import (
    ActionsResponse,
    ActionStatusUpdateRequest,
    ActionStatusUpdateResponse,
)
from app.services import access
from app.services import actions_data
from app.services import sample_fallback
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/actions", tags=["actions"])

logger = logging.getLogger(__name__)


@router.get("", response_model=ActionsResponse)
def list_actions(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Optional filter: open / in_progress / completed / dismissed / not_applicable / all.",
    ),
    building_id: str | None = Query(
        default=None,
        description="Optional fabric_building_id. Filters to one building.",
    ),
    category: str | None = Query(
        default=None,
        description="Optional action_type filter (HVAC, Lighting, ...).",
    ),
    limit: int = Query(default=500, ge=1, le=2000),
) -> ActionsResponse:
    """Return the joined Fabric + Postgres recommendations view."""
    fabric_ids = [
        b.fabric_building_id
        for b in building_repo.list_buildings_for_user(db, user_id=user_id)
        if b.fabric_building_id
    ]
    return sample_fallback.serve(
        "actions", ActionsResponse, fabric_ids,
        lambda: actions_data.get_actions_for_user(
            db, user_id=user_id, status_filter=status_filter,
            building_id=building_id, category=category, limit=limit),
    )


@router.patch("/{action_id}", response_model=ActionStatusUpdateResponse)
def update_action(
    action_id: str,
    body: ActionStatusUpdateRequest,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ActionStatusUpdateResponse:
    """Update the status of one recommendation.

    Returns 404 when:
      * action_id is malformed (no `|`)
      * the building portion of action_id is not visible to the user

    Both cases return the same 404 to avoid enumeration leaks (mirrors
    /buildings/{id} pattern).
    """
    # Write-gate: a partner with read_only scope (or anyone lacking manage rights)
    # may VIEW this building but not mutate it. Own-org users always pass.
    _gate_fabric_id = action_id.split("|", 1)[0] if "|" in action_id else None
    if _gate_fabric_id:
        _gate_b = building_repo.get_building_for_user(
            db, fabric_building_id=_gate_fabric_id, user_id=user_id
        )
        if _gate_b is not None and not access.can_manage_building(
            db, user_id=user_id, building=_gate_b
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Read-only access: you cannot modify this building.",
            )

    result = actions_data.update_action_status_for_user(
        db,
        user_id=user_id,
        action_id=action_id,
        new_status=body.status,
        notes=body.notes,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action '{action_id}' not found or not accessible.",
        )

    # Best-effort audit (the service owns the main commit). Resolve the org via
    # the building portion of action_id so it surfaces in /settings Activity.
    try:
        fabric_id = action_id.split("|", 1)[0]
        building = building_repo.get_building_for_user(
            db, fabric_building_id=fabric_id, user_id=user_id
        )
        if building is not None:
            audit_repo.record_event(
                db,
                user_id=user_id,
                organization_id=building.organization_id,
                action="recommendation.status_changed",
                entity_type="recommendation",
                entity_id=action_id,
                details={"status": body.status},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            db.commit()
    except Exception:
        logger.exception("Audit write failed for recommendation.status_changed")
        db.rollback()

    return result
