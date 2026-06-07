"""DB operations for OrgInvitation -- the /settings invite flow (Day 19).

Thin repository functions; the settings_data service composes them with
authorization checks and the single db.commit().
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import OrgInvitation


def create_invitation(
    db: Session,
    *,
    organization_id: UUID,
    email: str,
    role: str,
    token: str,
    invited_by_user_id: UUID | None,
    expires_at: datetime,
) -> OrgInvitation:
    """Insert a pending OrgInvitation. Caller commits."""
    inv = OrgInvitation(
        organization_id=organization_id,
        email=email,
        role=role,
        token=token,
        status="pending",
        invited_by_user_id=invited_by_user_id,
        expires_at=expires_at,
    )
    db.add(inv)
    db.flush()
    return inv


def list_pending_invitations(db: Session, org_id: UUID) -> list[OrgInvitation]:
    """Pending invitations for an org, newest first.

    Includes expired-but-still-'pending' rows; the service marks them expired
    lazily. invited_by is eager-loaded for the "Invited by" column.
    """
    stmt = (
        select(OrgInvitation)
        .where(
            OrgInvitation.organization_id == org_id,
            OrgInvitation.status == "pending",
        )
        .options(joinedload(OrgInvitation.invited_by))
        .order_by(OrgInvitation.created_at.desc())
    )
    return list(db.scalars(stmt).unique().all())


def find_pending_for_email(
    db: Session, *, org_id: UUID, email: str
) -> OrgInvitation | None:
    """A still-pending invitation to this email for this org, if any."""
    return db.scalar(
        select(OrgInvitation).where(
            OrgInvitation.organization_id == org_id,
            OrgInvitation.email == email,
            OrgInvitation.status == "pending",
        )
    )


def get_invitation(db: Session, invite_id: UUID) -> OrgInvitation | None:
    """Return an invitation by primary key, or None."""
    return db.get(OrgInvitation, invite_id)


def get_by_token(db: Session, token: str) -> OrgInvitation | None:
    """Return an invitation by its capability token, org eager-loaded."""
    return db.scalar(
        select(OrgInvitation)
        .where(OrgInvitation.token == token)
        .options(joinedload(OrgInvitation.organization))
    )


def mark_status(db: Session, inv: OrgInvitation, status_: str) -> OrgInvitation:
    """Set an invitation's status in place (e.g. 'revoked', 'expired')."""
    inv.status = status_
    return inv


def mark_accepted(
    db: Session, inv: OrgInvitation, *, user_id: UUID
) -> OrgInvitation:
    """Mark an invitation accepted by `user_id`. Caller commits."""
    inv.status = "accepted"
    inv.accepted_at = datetime.now(timezone.utc)
    inv.accepted_by_user_id = user_id
    return inv
