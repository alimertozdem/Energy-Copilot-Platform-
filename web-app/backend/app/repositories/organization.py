"""DB operations for Organization and OrgMember models."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Organization, OrgMember, User


def ensure_unique_slug(db: Session, base_slug: str) -> str:
    """Return base_slug if unused, else base_slug-2, base_slug-3, etc."""
    slug = base_slug
    n = 2
    while (
        db.scalar(select(Organization).where(Organization.slug == slug))
        is not None
    ):
        slug = f"{base_slug}-{n}"
        n += 1
    return slug


def create_personal_organization(
    db: Session,
    *,
    creator: User,
    name: str,
    slug: str,
) -> Organization:
    """Insert a new Organization, owned by `creator`. Caller must commit."""
    org = Organization(
        name=name,
        slug=slug,
        created_by_user_id=creator.id,
    )
    db.add(org)
    db.flush()
    return org


def create_org_membership(
    db: Session,
    *,
    organization_id: UUID,
    user_id: UUID,
    role: str,
    invited_by_user_id: UUID | None = None,
    accept_invitation: bool = True,
) -> OrgMember:
    """Insert a new OrgMember row. If accept_invitation=True, marks accepted now."""
    member = OrgMember(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
        invited_by_user_id=invited_by_user_id,
        invitation_accepted_at=(
            datetime.now(timezone.utc) if accept_invitation else None
        ),
    )
    db.add(member)
    db.flush()
    return member


# ===========================================================================
# Day 19 -- /settings read + management helpers
# ===========================================================================

def get_organization(db: Session, org_id: UUID) -> Organization | None:
    """Return the Organization by id, or None."""
    return db.get(Organization, org_id)


def list_members(db: Session, org_id: UUID) -> list[OrgMember]:
    """All members of an org with their User eager-loaded, oldest-first.

    Oldest-first puts the founding admin at the top of the table.
    """
    stmt = (
        select(OrgMember)
        .where(OrgMember.organization_id == org_id)
        .options(joinedload(OrgMember.user))
        .order_by(OrgMember.created_at.asc())
    )
    return list(db.scalars(stmt).unique().all())


def get_membership(
    db: Session, *, org_id: UUID, user_id: UUID
) -> OrgMember | None:
    """Return the OrgMember row linking this user to this org, or None."""
    return db.scalar(
        select(OrgMember).where(
            OrgMember.organization_id == org_id,
            OrgMember.user_id == user_id,
        )
    )


def count_admins(db: Session, org_id: UUID) -> int:
    """Number of admin members in the org -- powers the last-admin guard."""
    return int(
        db.scalar(
            select(func.count())
            .select_from(OrgMember)
            .where(
                OrgMember.organization_id == org_id,
                OrgMember.role == "admin",
            )
        )
        or 0
    )


def update_organization_fields(
    db: Session,
    org: Organization,
    *,
    name: str | None = None,
    billing_email: str | None = None,
    country_code: str | None = None,
) -> Organization:
    """Patch editable org-profile fields in place. Caller commits.

    Empty strings normalize to NULL; country_code is upper-cased.
    """
    if name is not None:
        org.name = name
    if billing_email is not None:
        org.billing_email = billing_email or None
    if country_code is not None:
        org.country_code = country_code.upper() if country_code else None
    return org


def set_member_role(db: Session, member: OrgMember, role: str) -> OrgMember:
    """Change a member's role in place. Caller commits."""
    member.role = role
    return member


def delete_member(db: Session, member: OrgMember) -> None:
    """Remove a member from the org. Caller commits."""
    db.delete(member)
