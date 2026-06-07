"""DB operations for PartnerClientLink -- the consultant (partner) layer grant.

Lifecycle: invite (``pending``) -> client consent (``active``) -> ``revoke`` (``revoked``).
Authorization is enforced in the router; these are thin query wrappers and the caller
commits (matching the repository pattern used across the backend).
"""
from datetime import datetime, timezone as dt_timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Organization, PartnerClientLink


def get_link(db: Session, link_id: UUID) -> PartnerClientLink | None:
    """Return a link by id, or None."""
    return db.get(PartnerClientLink, link_id)


def get_live_link(
    db: Session, *, partner_org_id: UUID, client_org_id: UUID
) -> PartnerClientLink | None:
    """The current non-revoked link for a (partner, client) pair, if any.

    Used to prevent duplicate live invites (the DB also enforces this with a
    partial unique index where revoked_at IS NULL).
    """
    return db.scalar(
        select(PartnerClientLink).where(
            PartnerClientLink.partner_org_id == partner_org_id,
            PartnerClientLink.client_org_id == client_org_id,
            PartnerClientLink.revoked_at.is_(None),
        )
    )


def create_link(
    db: Session,
    *,
    partner_org_id: UUID,
    client_org_id: UUID,
    invited_by_user_id: UUID,
    scope: str = "read_only",
    commission_model: dict | None = None,
) -> PartnerClientLink:
    """Insert a PENDING partner->client link. Caller commits."""
    link = PartnerClientLink(
        partner_org_id=partner_org_id,
        client_org_id=client_org_id,
        relationship_status="pending",
        scope=scope,
        commission_model=commission_model,
        invited_by_user_id=invited_by_user_id,
    )
    db.add(link)
    db.flush()
    return link


def accept_link(db: Session, link: PartnerClientLink) -> PartnerClientLink:
    """Client consents: pending -> active (records consent + grant time). Caller commits."""
    now = datetime.now(dt_timezone.utc)
    link.relationship_status = "active"
    link.client_consent_at = now
    link.granted_at = now
    return link


def revoke_link(db: Session, link: PartnerClientLink) -> PartnerClientLink:
    """Revoke a link (either side may revoke). Caller commits."""
    link.relationship_status = "revoked"
    link.revoked_at = datetime.now(dt_timezone.utc)
    return link


def list_for_partner(
    db: Session, *, partner_org_id: UUID
) -> list[tuple[PartnerClientLink, Organization]]:
    """Links where this org is the PARTNER, with the client org joined. Newest first."""
    stmt = (
        select(PartnerClientLink, Organization)
        .join(Organization, Organization.id == PartnerClientLink.client_org_id)
        .where(PartnerClientLink.partner_org_id == partner_org_id)
        .order_by(PartnerClientLink.created_at.desc())
    )
    return [(link, org) for link, org in db.execute(stmt).all()]


def list_for_client(
    db: Session, *, client_org_id: UUID
) -> list[tuple[PartnerClientLink, Organization]]:
    """Links where this org is the CLIENT, with the partner org joined. Newest first."""
    stmt = (
        select(PartnerClientLink, Organization)
        .join(Organization, Organization.id == PartnerClientLink.partner_org_id)
        .where(PartnerClientLink.client_org_id == client_org_id)
        .order_by(PartnerClientLink.created_at.desc())
    )
    return [(link, org) for link, org in db.execute(stmt).all()]
