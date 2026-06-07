"""Repository for pilot_requests (public lead capture + admin queue). Callers commit."""
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.models.pilot import PilotRequest

VALID_STATUSES = frozenset({"new", "contacted", "qualified", "closed"})


def create(
    db: Session,
    *,
    name: str,
    email: str,
    organization: str | None,
    country_code: str | None,
    building_count: int | None,
    message: str | None,
    source: str | None,
) -> PilotRequest:
    row = PilotRequest(
        name=name,
        email=email,
        organization=organization,
        country_code=country_code,
        building_count=building_count,
        message=message,
        source=source,
        status="new",
    )
    db.add(row)
    db.flush()
    return row


def recent_count_for_email(db: Session, *, email: str) -> int:
    """How many requests this email already filed (light dedupe / abuse signal)."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(PilotRequest)
            .where(PilotRequest.email == email)
        )
        or 0
    )


def list_all(db: Session, *, status: str | None = None, limit: int = 200) -> list[PilotRequest]:
    stmt = select(PilotRequest)
    if status:
        stmt = stmt.where(PilotRequest.status == status)
    stmt = stmt.order_by(
        (PilotRequest.status == "new").desc(), desc(PilotRequest.created_at)
    ).limit(limit)
    return list(db.scalars(stmt).all())


def get_by_id(db: Session, *, request_id: UUID) -> PilotRequest | None:
    return db.get(PilotRequest, request_id)
