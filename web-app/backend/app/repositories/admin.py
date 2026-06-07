"""Cross-organization read queries for the platform admin (/admin/*).

DELIBERATELY SEPARATE from the per-user repositories. Functions here apply NO
visibility filter -- they return data across every organization. They must only
ever be called behind get_current_platform_admin (founder-only). Keeping them in
their own module makes it obvious that these are unfiltered, platform-wide reads.
"""
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Building,
    BuildingModule,
    Organization,
    OrgMember,
    User,
)


def get_platform_stats(db: Session) -> dict[str, int]:
    """Headline platform counts for the admin dashboard."""

    def _count(stmt) -> int:
        return int(db.scalar(stmt) or 0)

    return {
        "organizations_total": _count(select(func.count(Organization.id))),
        "organizations_sample": _count(
            select(func.count(Organization.id)).where(
                Organization.is_sample.is_(True)
            )
        ),
        "users_total": _count(select(func.count(User.id))),
        "users_demo": _count(
            select(func.count(User.id)).where(User.is_demo.is_(True))
        ),
        "buildings_total": _count(
            select(func.count(Building.id)).where(Building.is_active.is_(True))
        ),
        "buildings_connected": _count(
            select(func.count(Building.id)).where(
                Building.is_active.is_(True),
                Building.fabric_building_id.is_not(None),
            )
        ),
        "iot_enabled": _count(
            select(func.count(BuildingModule.id)).where(
                BuildingModule.module_key == "iot",
                BuildingModule.enabled.is_(True),
            )
        ),
        "battery_enabled": _count(
            select(func.count(BuildingModule.id)).where(
                BuildingModule.module_key == "battery",
                BuildingModule.enabled.is_(True),
            )
        ),
    }


def list_all_organizations(db: Session) -> list[Any]:
    """Every org with its member + active-building counts. Oldest first.

    Returns Row tuples: (Organization, member_count, building_count).
    """
    member_count = (
        select(func.count(OrgMember.id))
        .where(OrgMember.organization_id == Organization.id)
        .correlate(Organization)
        .scalar_subquery()
    )
    building_count = (
        select(func.count(Building.id))
        .where(
            Building.organization_id == Organization.id,
            Building.is_active.is_(True),
        )
        .correlate(Organization)
        .scalar_subquery()
    )
    stmt = select(
        Organization,
        member_count.label("member_count"),
        building_count.label("building_count"),
    ).order_by(Organization.created_at.asc())
    return list(db.execute(stmt).all())


def list_all_users(db: Session) -> list[Any]:
    """Every user with their org count + linked auth providers. Oldest first.

    Returns Row tuples: (User, org_count) with User.auth_providers eager-loaded.
    """
    org_count = (
        select(func.count(OrgMember.id))
        .where(OrgMember.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    stmt = (
        select(User, org_count.label("org_count"))
        .options(joinedload(User.auth_providers))
        .order_by(User.created_at.asc())
    )
    return list(db.execute(stmt).unique().all())


def list_all_buildings(db: Session) -> list[Building]:
    """Every active building across all orgs, with org + modules eager-loaded."""
    stmt = (
        select(Building)
        .where(Building.is_active.is_(True))
        .options(
            joinedload(Building.organization),
            joinedload(Building.modules),
        )
        .order_by(Building.created_at.asc())
    )
    return list(db.scalars(stmt).unique().all())


# ===========================================================================
# Mutations (admin-only writes). The router orchestrates 404/409/422 checks;
# these primitives just touch the DB. Caller commits.
# ===========================================================================

def get_building_by_id(db: Session, building_id) -> Building | None:
    """Fetch a building by its UUID primary key. Admin mutations target id, not
    fabric_building_id (which may be NULL on freshly-onboarded buildings)."""
    return db.get(Building, building_id)


def upsert_building_module(
    db: Session, *, building_id, module_key: str, enabled: bool
) -> BuildingModule:
    """Enable/disable a module for a building. Inserts the row if it doesn't
    exist yet (iot/battery may have no row after onboarding). Caller commits."""
    from datetime import datetime, timezone as _tz

    existing = db.scalar(
        select(BuildingModule).where(
            BuildingModule.building_id == building_id,
            BuildingModule.module_key == module_key,
        )
    )
    now = datetime.now(_tz.utc)
    if existing is None:
        existing = BuildingModule(
            building_id=building_id,
            module_key=module_key,
            enabled=enabled,
            enabled_at=now if enabled else None,
        )
        db.add(existing)
    else:
        existing.enabled = enabled
        existing.enabled_at = now if enabled else None
    db.flush()
    return existing


def fabric_id_in_use(
    db: Session, *, fabric_building_id: str, exclude_building_id
) -> bool:
    """True if another building already uses this fabric_building_id (the column
    is globally unique)."""
    return (
        db.scalar(
            select(Building.id).where(
                Building.fabric_building_id == fabric_building_id,
                Building.id != exclude_building_id,
            )
        )
        is not None
    )
