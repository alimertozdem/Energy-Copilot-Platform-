"""Installer requests -- Execution Marketplace Phase 0 (founder-brokered).

  * POST  /installer-requests            (authed customer) -- capture a
        "connect me with an installer" lead for a recommended measure.
  * GET   /installer-requests/admin       (platform admin) -- the founder's queue.
  * PATCH /installer-requests/admin/{id}   (platform admin) -- work the status.

Zero-infra by design: we capture the lead + audit it; the founder brokers the
introduction manually. Phase 1+ (vendor registry, RFQ, lead fee, take-rate,
escrow) is DEFERRED -- see docs/strategy/execution-marketplace-plan.md.
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.installer import InstallerRequest
from app.db.models.user import User
from app.repositories import audit as audit_repo
from app.repositories import building as building_repo
from app.schemas.installer import (
    InstallerRequestAck,
    InstallerRequestCreate,
    InstallerRequestList,
    InstallerRequestRow,
    InstallerStatusUpdate,
)
from app.utils.jwt import get_current_platform_admin, get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/installer-requests", tags=["installer"])

_VALID_STATUS = {"requested", "contacted", "quoted", "closed"}


@router.post("", response_model=InstallerRequestAck, status_code=status.HTTP_201_CREATED)
def create_installer_request(
    payload: InstallerRequestCreate,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> InstallerRequestAck:
    """Capture a customer's request to be connected with an installer.

    Validates building visibility (404 otherwise) -- which also yields the org +
    name. Founder-brokered: no vendor matching here, just the lead + an audit row.
    """
    building = building_repo.get_building_for_user(
        db, fabric_building_id=payload.fabric_building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{payload.fabric_building_id}' not found",
        )

    req = InstallerRequest(
        organization_id=building.organization_id,
        requested_by_user_id=user_id,
        fabric_building_id=payload.fabric_building_id,
        building_name=building.name,
        action_type=(payload.action_type or None),
        measure_label=(payload.measure_label or None),
        source=(payload.source or None),
        status="requested",
    )
    db.add(req)
    db.flush()

    try:
        audit_repo.record_event(
            db,
            user_id=user_id,
            organization_id=building.organization_id,
            action="installer.requested",
            entity_type="installer_request",
            entity_id=str(req.id),
            details={
                "action_type": req.action_type,
                "building": req.fabric_building_id,
                "source": req.source,
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.exception("Audit write failed for installer.requested")

    db.commit()
    return InstallerRequestAck(
        id=req.id,
        status=req.status,
        message="Request received — we'll connect you with a vetted installer.",
    )


@router.get("/admin", response_model=InstallerRequestList)
def list_installer_requests(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> InstallerRequestList:
    """The founder's broker queue -- every installer request, newest first."""
    rows = db.scalars(
        select(InstallerRequest)
        .order_by(InstallerRequest.created_at.desc())
        .limit(500)
    ).all()
    return InstallerRequestList(
        requests=[InstallerRequestRow.model_validate(r) for r in rows]
    )


@router.patch("/admin/{request_id}", response_model=InstallerRequestRow)
def update_installer_request_status(
    request_id: UUID,
    payload: InstallerStatusUpdate,
    request: Request,
    admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> InstallerRequestRow:
    """Work the brokering status (requested -> contacted -> quoted -> closed)."""
    new_status = payload.status.strip().lower()
    if new_status not in _VALID_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed: {', '.join(sorted(_VALID_STATUS))}.",
        )
    req = db.get(InstallerRequest, request_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    req.status = new_status
    try:
        audit_repo.record_event(
            db,
            user_id=admin.id,
            organization_id=req.organization_id,
            action="admin.installer_request_status_changed",
            entity_type="installer_request",
            entity_id=str(req.id),
            details={"status": new_status},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.exception("Audit write failed for installer status change")
    db.commit()
    db.refresh(req)
    return InstallerRequestRow.model_validate(req)
