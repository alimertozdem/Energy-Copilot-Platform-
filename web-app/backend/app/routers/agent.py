"""Edge-agent router -- agent-token management + the gateway config feed.

Two distinct auth surfaces, deliberately separated:

  * Token management (POST/GET/DELETE /buildings/{uuid}/agent-tokens) is gated by
    the user JWT + manage rights (same as the device CRUD).

  * GET /agent/config is consumed by the edge gateway and authenticated ONLY by a
    building-scoped agent token in the X-Agent-Token header -- it never touches
    the user JWT path (get_current_user_id). An agent thus holds no user
    credential and can be revoked independently.
"""
import hashlib
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Building
from app.repositories import agent as agent_repo
from app.repositories import audit as audit_repo
from app.repositories import connection as conn_repo
from app.schemas.agent import (
    AgentConfigResponse,
    AgentDevice,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentPoint,
    AgentTokenCreate,
    AgentTokenIssued,
    AgentTokenListResponse,
    AgentTokenResponse,
)
from app.services import access
from app.utils.jwt import get_current_user_id

router = APIRouter(tags=["agent"])


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _building_for_manage(db: Session, building_id: UUID, user_id: UUID) -> Building:
    building = db.get(Building, building_id)
    if (
        building is None
        or not building.is_active
        or not access.can_manage_building(db, user_id=user_id, building=building)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    return building


def _token_to_response(t) -> AgentTokenResponse:
    return AgentTokenResponse(
        id=t.id,
        building_id=t.building_id,
        name=t.name,
        token_prefix=t.token_prefix,
        last_used_at=t.last_used_at,
        revoked_at=t.revoked_at,
        created_at=t.created_at,
        is_active=t.revoked_at is None,
    )


# --- token management (user JWT + manage gate) -----------------------------


@router.post(
    "/buildings/{building_id}/agent-tokens",
    response_model=AgentTokenIssued,
    status_code=status.HTTP_201_CREATED,
)
def issue_token(
    building_id: UUID,
    body: AgentTokenCreate,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentTokenIssued:
    """Issue a building-scoped agent token. The plaintext is returned ONCE."""
    building = _building_for_manage(db, building_id, user_id)
    plaintext = "ely_" + secrets.token_urlsafe(32)
    tok = agent_repo.create_token(
        db,
        building_id=building_id,
        name=(body.name or "edge agent")[:80],
        token_hash=_hash(plaintext),
        token_prefix=plaintext[:12],
    )
    audit_repo.record_event(
        db,
        user_id=user_id,
        organization_id=building.organization_id,
        action="agent_token.issued",
        entity_type="agent_token",
        entity_id=str(tok.id),
        details={"name": tok.name},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(tok)
    return AgentTokenIssued(token=plaintext, **_token_to_response(tok).model_dump())


@router.get(
    "/buildings/{building_id}/agent-tokens", response_model=AgentTokenListResponse
)
def list_tokens(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentTokenListResponse:
    """List a building's agent tokens (never returns plaintext)."""
    _building_for_manage(db, building_id, user_id)
    tokens = agent_repo.list_tokens(db, building_id=building_id)
    return AgentTokenListResponse(tokens=[_token_to_response(t) for t in tokens])


@router.delete(
    "/buildings/{building_id}/agent-tokens/{token_id}",
    response_model=AgentTokenResponse,
)
def revoke_token(
    building_id: UUID,
    token_id: UUID,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentTokenResponse:
    """Revoke a token (idempotent). The agent using it loses access immediately."""
    building = _building_for_manage(db, building_id, user_id)
    tok = agent_repo.get_for_building(db, building_id=building_id, token_id=token_id)
    if tok is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
        )
    if tok.revoked_at is None:
        agent_repo.revoke(db, token=tok)
        audit_repo.record_event(
            db,
            user_id=user_id,
            organization_id=building.organization_id,
            action="agent_token.revoked",
            entity_type="agent_token",
            entity_id=str(tok.id),
            details={"name": tok.name},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    db.commit()
    db.refresh(tok)
    return _token_to_response(tok)


# --- agent config feed (agent-token auth ONLY; no user JWT) -----------------


def get_agent_building(
    db: Annotated[Session, Depends(get_db)],
    x_agent_token: Annotated[str | None, Header()] = None,
) -> Building:
    """Resolve the X-Agent-Token header to its building. Separate from the user
    JWT entirely; touches last_used_at on success."""
    if not x_agent_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Agent-Token"
        )
    tok = agent_repo.get_active_by_hash(db, token_hash=_hash(x_agent_token))
    if tok is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked agent token",
        )
    building = db.get(Building, tok.building_id)
    if building is None or not building.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    agent_repo.touch(db, token=tok)
    db.commit()
    return building


@router.get("/agent/config", response_model=AgentConfigResponse)
def agent_config(
    building: Annotated[Building, Depends(get_agent_building)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentConfigResponse:
    """The device + point node-map for the agent's building (gateway-ready)."""
    devices = conn_repo.list_devices(db, building_id=building.id)
    bid = building.fabric_building_id or str(building.id)
    return AgentConfigResponse(
        building_id=bid,
        devices=[
            AgentDevice(
                id=str(d.id),
                name=d.name,
                protocol=d.protocol,
                connection_config=d.connection_config,
                points=[
                    AgentPoint(
                        point_ref=p.point_ref,
                        sensor_type=p.sensor_type,
                        zone=p.zone,
                        unit=p.unit,
                        scale=float(p.scale),
                        enabled=p.enabled,
                    )
                    for p in d.points
                ],
            )
            for d in devices
        ],
    )


@router.post("/agent/heartbeat", response_model=AgentHeartbeatResponse)
def agent_heartbeat(
    body: AgentHeartbeatRequest,
    building: Annotated[Building, Depends(get_agent_building)],
    db: Annotated[Session, Depends(get_db)],
) -> AgentHeartbeatResponse:
    """The edge agent reports which devices it is actively collecting; flip those
    to 'active' + stamp last_seen_at. Building-scoped via the agent token, so the
    agent can only ever touch its own building's devices."""
    valid_ids = []
    for s in body.device_ids:
        try:
            valid_ids.append(UUID(str(s)))
        except (ValueError, AttributeError, TypeError):
            continue
    updated = conn_repo.mark_devices_active(
        db, building_id=building.id, device_ids=valid_ids
    )
    db.commit()
    bid = building.fabric_building_id or str(building.id)
    return AgentHeartbeatResponse(building_id=bid, updated=updated)
