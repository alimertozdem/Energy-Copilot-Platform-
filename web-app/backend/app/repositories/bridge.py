"""Repository for bridge_requests (self-serve Fabric bridging -- Access Layer 3).

Customer-side reads/writes are keyed by building_id (the router enforces the
manage gate). The admin-side list is cross-org and must only be called behind
the platform-admin gate. Callers commit.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Building, BridgeRequest


def get_active_request(db: Session, *, building_id: UUID) -> BridgeRequest | None:
    """The building's open (pending) request, if any."""
    return db.scalar(
        select(BridgeRequest).where(
            BridgeRequest.building_id == building_id,
            BridgeRequest.status == "pending",
        )
    )


def get_latest_request(db: Session, *, building_id: UUID) -> BridgeRequest | None:
    """The building's most recent request of any status (for status display)."""
    return db.scalar(
        select(BridgeRequest)
        .where(BridgeRequest.building_id == building_id)
        .order_by(desc(BridgeRequest.created_at))
        .limit(1)
    )


def create_request(
    db: Session,
    *,
    building_id: UUID,
    organization_id: UUID,
    requested_by: UUID | None,
    target_tier: str,
    readiness: dict | None,
    note: str | None,
) -> BridgeRequest:
    """Insert a new pending bridge request. Caller commits.

    The partial unique index `uq_bridge_requests_one_pending` guarantees at most
    one pending row per building; callers should check get_active_request first
    for a clean 409 rather than relying on the IntegrityError.
    """
    req = BridgeRequest(
        building_id=building_id,
        organization_id=organization_id,
        requested_by=requested_by,
        target_tier=target_tier,
        readiness=readiness,
        note=note,
        status="pending",
    )
    db.add(req)
    db.flush()
    return req


def cancel_active(db: Session, *, building_id: UUID) -> BridgeRequest | None:
    """Mark the building's pending request cancelled. Returns it, or None if none.
    Caller commits."""
    req = get_active_request(db, building_id=building_id)
    if req is None:
        return None
    req.status = "cancelled"
    req.resolved_at = datetime.now(timezone.utc)
    db.flush()
    return req


def get_by_id(db: Session, *, request_id: UUID) -> BridgeRequest | None:
    return db.get(BridgeRequest, request_id)


def list_all(db: Session, *, status: str | None = None, limit: int = 100) -> list:
    """Cross-org list for the founder admin view. Pending first, then newest.

    PLATFORM-ADMIN ONLY -- applies no visibility filter. Returns Row tuples:
    (BridgeRequest, building_name, fabric_building_id, organization_name,
    requester_email).
    """
    from app.db.models import Organization, User

    stmt = (
        select(
            BridgeRequest,
            Building.name.label("building_name"),
            Building.fabric_building_id.label("fabric_building_id"),
            Organization.name.label("organization_name"),
            User.email.label("requester_email"),
        )
        .join(Building, Building.id == BridgeRequest.building_id)
        .join(Organization, Organization.id == BridgeRequest.organization_id)
        .join(User, User.id == BridgeRequest.requested_by, isouter=True)
    )
    if status:
        stmt = stmt.where(BridgeRequest.status == status)
    # Pending first (so the founder's queue is at the top), then newest.
    stmt = stmt.order_by(
        (BridgeRequest.status == "pending").desc(),
        desc(BridgeRequest.created_at),
    ).limit(limit)
    return list(db.execute(stmt).all())
