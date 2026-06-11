"""Alerts router -- GET /alerts + PATCH /alerts/{anomaly_id}.

Portfolio-wide anomaly monitoring over Fabric gold_anomaly_log, with a Postgres
acknowledge overlay (Day 31). JWT-protected (mirrors /actions, /portfolio).
Visibility is delegated to the alerts_data service.

GET is read-only over Fabric (+ ack overlay merge). PATCH writes the human
operational state (acknowledged / dismissed / new) to Postgres alert_status --
it does NOT touch Fabric is_resolved (pipeline-owned). A successful PATCH
records an `alert.status_changed` audit row (best-effort, after the service
commits) so it surfaces in /settings Activity (Day 27 pattern).
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import audit as audit_repo
from app.repositories import building as building_repo
from app.schemas.alerts import (
    AlertAckUpdateRequest,
    AlertAckUpdateResponse,
    AlertsResponse,
)
from app.services import access
from app.services import alerts_data
from app.services import sample_fallback
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/alerts", tags=["alerts"])

logger = logging.getLogger(__name__)


@router.get("", response_model=AlertsResponse)
def list_alerts(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    severity: str | None = Query(
        default=None,
        description="Optional severity filter: CRITICAL / HIGH / MEDIUM / LOW / all.",
    ),
    building_id: str | None = Query(
        default=None,
        description="Optional fabric_building_id. Filters to one building.",
    ),
    unresolved_only: bool = Query(
        default=False,
        description="Legacy: when true, only is_resolved = 0 rows (nav badge poll). Superseded by `resolution`.",
    ),
    resolution: str | None = Query(
        default=None,
        description="Row-set resolution filter: unresolved / resolved / all. Wins over unresolved_only.",
    ),
    limit: int = Query(default=500, ge=1, le=2000),
) -> AlertsResponse:
    """Return the portfolio-wide anomaly view + severity counts (+ ack overlay)."""
    fabric_ids = [
        b.fabric_building_id
        for b in building_repo.list_buildings_for_user(db, user_id=user_id)
        if b.fabric_building_id
    ]
    return sample_fallback.serve(
        "alerts", AlertsResponse, fabric_ids,
        lambda: alerts_data.get_alerts_for_user(
            db, user_id=user_id, severity=severity, building_id=building_id,
            unresolved_only=unresolved_only, resolution=resolution, limit=limit),
    )


@router.patch("/{anomaly_id}", response_model=AlertAckUpdateResponse)
def update_alert(
    anomaly_id: str,
    body: AlertAckUpdateRequest,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> AlertAckUpdateResponse:
    """Acknowledge / dismiss / reset one anomaly (Postgres overlay).

    Returns 404 when the building referenced by body.building_id is not visible
    to the user (mirrors /actions -- avoids enumeration leaks).
    """
    # Write-gate: read_only partners (or anyone lacking manage rights) may VIEW but
    # not mutate. Own-org users always pass.
    _gate_b = building_repo.get_building_for_user(
        db, fabric_building_id=body.building_id, user_id=user_id
    )
    if _gate_b is not None and not access.can_manage_building(
        db, user_id=user_id, building=_gate_b
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read-only access: you cannot modify this building.",
        )

    result = alerts_data.update_alert_ack_for_user(
        db,
        user_id=user_id,
        anomaly_id=anomaly_id,
        building_id=body.building_id,
        ack_status=body.ack_status,
        notes=body.notes,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{anomaly_id}' not found or not accessible.",
        )

    # Best-effort audit (the service owns the main commit). Resolve the org via
    # the building so it surfaces in /settings Activity.
    try:
        building = building_repo.get_building_for_user(
            db, fabric_building_id=body.building_id, user_id=user_id
        )
        if building is not None:
            audit_repo.record_event(
                db,
                user_id=user_id,
                organization_id=building.organization_id,
                action="alert.status_changed",
                entity_type="alert",
                entity_id=anomaly_id,
                details={"ack_status": body.ack_status},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            db.commit()
    except Exception:
        logger.exception("Audit write failed for alert.status_changed")
        db.rollback()

    return result
