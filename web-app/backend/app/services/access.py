"""Access scope resolution -- the higher-level authorization primitives.

Building *read* visibility is enforced centrally in
``repositories.building._visible_org_filter`` (one SQL rule applied by every read path,
now partner-aware). This module exposes the scope helpers that build on that rule and that
the routers/UI consume:

  * ``partner_client_org_ids`` -- the active client orgs a user's partner org manages
    (drives the partner "client switcher").
  * ``can_manage_building``    -- the stricter *write* gate: own org, or a ``full_manage``
    partner link (``read_only`` links can view but not mutate).
  * ``resolve_resident_scope`` -- the resident path: the resident's own unit(s) and their
    building, within the tenancy window (Mieterwechsel). Returns the lakehouse keys the
    /residence view filters on.

See ``docs/architecture/unified-access-model.md`` (the 4-level scope matrix).
"""
from datetime import date
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models import Building, OrgMember, PartnerClientLink
from app.db.models.residential import Unit, UnitResident


def _active_link_filter():
    """Common predicate: the link is live (active + not revoked)."""
    return (
        PartnerClientLink.relationship_status == "active",
        PartnerClientLink.revoked_at.is_(None),
    )


def partner_client_org_ids(db: Session, *, user_id: UUID) -> list[UUID]:
    """Active client org IDs the user (as a member of a partner org) may act on.

    Drives the partner client-switcher. Empty for ordinary customer users.
    """
    stmt = (
        select(PartnerClientLink.client_org_id)
        .join(OrgMember, OrgMember.organization_id == PartnerClientLink.partner_org_id)
        .where(OrgMember.user_id == user_id, *_active_link_filter())
        .distinct()
    )
    return list(db.scalars(stmt).all())


def _full_manage_client_org_ids(db: Session, *, user_id: UUID) -> set[UUID]:
    """Client orgs the user may MUTATE via a full_manage partner link."""
    stmt = (
        select(PartnerClientLink.client_org_id)
        .join(OrgMember, OrgMember.organization_id == PartnerClientLink.partner_org_id)
        .where(
            OrgMember.user_id == user_id,
            PartnerClientLink.scope == "full_manage",
            *_active_link_filter(),
        )
    )
    return set(db.scalars(stmt).all())


def can_manage_building(db: Session, *, user_id: UUID, building: Building) -> bool:
    """Write gate -- True if the user may MUTATE data for this building.

    Stricter than read visibility (``_visible_org_filter``):
      * the building belongs to one of the user's own orgs, OR
      * the building's org is a client managed with ``scope='full_manage'``
        (``read_only`` partner links grant view, never mutate).
    """
    own_org_ids = set(
        db.scalars(
            select(OrgMember.organization_id).where(OrgMember.user_id == user_id)
        ).all()
    )
    if building.organization_id in own_org_ids:
        return True
    return building.organization_id in _full_manage_client_org_ids(db, user_id=user_id)


def resolve_resident_scope(
    db: Session, *, resident_identity_id: UUID, on_date: date | None = None
) -> dict:
    """The resident path of ``resolve_scope``.

    Returns the lakehouse keys the resident may read on ``on_date``, restricted to the
    tenancy window (``valid_from <= on_date <= valid_to``; NULL bounds are open). A resident
    sees their own unit(s) + an anonymized building benchmark -- never another named unit.

    Returns ``{"fabric_unit_ids": [...], "fabric_building_ids": [...], "as_of": "YYYY-MM-DD"}``.
    A former tenant gets an empty set once ``valid_to`` has passed; a new tenant sees nothing
    before ``valid_from``.
    """
    on_date = on_date or date.today()
    stmt = (
        select(Unit.fabric_unit_id, Building.fabric_building_id)
        .join(UnitResident, UnitResident.unit_id == Unit.id)
        .join(Building, Building.id == Unit.building_id)
        .where(
            UnitResident.resident_identity_id == resident_identity_id,
            UnitResident.status == "active",
            or_(UnitResident.valid_from.is_(None), UnitResident.valid_from <= on_date),
            or_(UnitResident.valid_to.is_(None), UnitResident.valid_to >= on_date),
        )
    )
    rows = db.execute(stmt).all()
    return {
        "fabric_unit_ids": sorted({r[0] for r in rows if r[0] is not None}),
        "fabric_building_ids": sorted({r[1] for r in rows if r[1] is not None}),
        "as_of": on_date.isoformat(),
    }
