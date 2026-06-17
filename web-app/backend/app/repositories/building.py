"""DB operations for Building and BuildingModule models.

Repository pattern: thin functions that wrap SQLAlchemy queries.
Authorization for visibility is enforced here via _visible_org_filter() so
that every read path applies the same rule -- a user can see buildings in
orgs they belong to, plus buildings in any sample/demo org.
"""
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Building,
    BuildingModule,
    Organization,
    OrgMember,
    PartnerClientLink,
    User,
)


def _visible_org_filter(user_id: UUID, include_sample: bool):
    """SQLAlchemy expression: a building's owning org is visible to this user.

    A building is visible when its org is:
      * one of the user's own orgs (OrgMember), OR
      * a client org the user's partner org is ACTIVELY linked to
        (partner_client_link, status='active', not revoked) -- the consultant layer, OR
      * a sample/demo org.

    Used by both list and detail queries so every read path applies one rule.
    The partner branch is additive: with no active links it is empty, so a
    non-partner user's visibility is unchanged.
    """
    user_orgs_subq = (
        select(OrgMember.organization_id)
        .where(OrgMember.user_id == user_id)
        .scalar_subquery()
    )
    # Client orgs reachable via an ACTIVE partner link from any org the user belongs to.
    partner_client_subq = (
        select(PartnerClientLink.client_org_id)
        .join(
            OrgMember,
            OrgMember.organization_id == PartnerClientLink.partner_org_id,
        )
        .where(
            OrgMember.user_id == user_id,
            PartnerClientLink.relationship_status == "active",
            PartnerClientLink.revoked_at.is_(None),
        )
        .scalar_subquery()
    )
    branches = [
        Building.organization_id.in_(user_orgs_subq),
        Building.organization_id.in_(partner_client_subq),
    ]
    if include_sample:
        branches.append(Organization.is_sample.is_(True))
    return or_(*branches)


def _show_sample(db: Session, user_id: UUID) -> bool:
    """Whether this user opted to see sample/demo buildings (default True)."""
    val = db.scalar(select(User.show_sample_data).where(User.id == user_id))
    return bool(val) if val is not None else True


def list_buildings_for_user(
    db: Session,
    *,
    user_id: UUID,
) -> list[Building]:
    """Return active buildings visible to this user.

    Visibility = buildings owned by orgs the user is a member of,
                 plus buildings owned by any sample/demo org.

    Includes eager-loaded modules and organization (for is_sample flag).
    """
    stmt = (
        select(Building)
        .join(Organization, Building.organization_id == Organization.id)
        .where(Building.is_active.is_(True))
        .where(_visible_org_filter(user_id, _show_sample(db, user_id)))
        .options(
            joinedload(Building.modules),
            joinedload(Building.organization),
        )
        .order_by(Building.fabric_building_id)
    )
    return list(db.scalars(stmt).unique().all())


def get_building_for_user(
    db: Session,
    *,
    fabric_building_id: str,
    user_id: UUID,
) -> Building | None:
    """Return a single building by its fabric_building_id, or None if not visible.

    None can mean either:
      * The building doesn't exist
      * The user has no permission to see it
    We do not distinguish, to prevent enumeration leaks.
    """
    stmt = (
        select(Building)
        .join(Organization, Building.organization_id == Organization.id)
        .where(Building.fabric_building_id == fabric_building_id)
        .where(Building.is_active.is_(True))
        .where(_visible_org_filter(user_id, _show_sample(db, user_id)))
        .options(
            joinedload(Building.modules),
            joinedload(Building.organization),
        )
    )
    return db.scalar(stmt)


# ===========================================================================
# Day 20 -- onboarding building creation
# ===========================================================================

def create_building(
    db: Session,
    *,
    organization_id: UUID,
    name: str,
    building_type: str | None = None,
    city: str | None = None,
    country_code: str | None = None,
    address: str | None = None,
    floor_area_m2: float | None = None,
    construction_year: int | None = None,
    epc_class: str | None = None,
    heating_system: str | None = None,
    cooling_system: str | None = None,
    occupancy_pattern: str | None = None,
    floors_above_ground: int | None = None,
    typical_occupants: int | None = None,
    residential_units: int | None = None,
    timezone: str = "Europe/Berlin",
    pv_capacity_kwp: float | None = None,
    wall_u_value: float | None = None,
    roof_u_value: float | None = None,
    window_u_value: float | None = None,
    insulation_year: int | None = None,
    has_gas_heating: bool | None = None,
) -> Building:
    """Insert a new Building owned by `organization_id`. Caller commits.

    fabric_building_id stays NULL -- the building has no Fabric data yet.
    """
    b = Building(
        organization_id=organization_id,
        fabric_building_id=None,
        name=name,
        building_type=building_type,
        city=city,
        country_code=country_code,
        address=address,
        floor_area_m2=Decimal(str(floor_area_m2)) if floor_area_m2 is not None else None,
        construction_year=construction_year,
        epc_class=epc_class,
        heating_system=heating_system,
        cooling_system=cooling_system,
        occupancy_pattern=occupancy_pattern,
        floors_above_ground=floors_above_ground,
        typical_occupants=typical_occupants,
        residential_units=residential_units,
        timezone=timezone,
        pv_capacity_kwp=(
            Decimal(str(pv_capacity_kwp)) if pv_capacity_kwp is not None else None
        ),
        wall_u_value=Decimal(str(wall_u_value)) if wall_u_value is not None else None,
        roof_u_value=Decimal(str(roof_u_value)) if roof_u_value is not None else None,
        window_u_value=Decimal(str(window_u_value)) if window_u_value is not None else None,
        insulation_year=insulation_year,
        has_gas_heating=has_gas_heating,
    )
    db.add(b)
    db.flush()
    return b


def create_building_modules(
    db: Session,
    *,
    building_id: UUID,
    modules: list[tuple[str, bool, str | None]],
) -> None:
    """Insert BuildingModule rows for a building. Caller commits.

    `modules` is a list of (module_key, enabled, notes). enabled_at is set to
    now() for enabled modules so we have an audit trail of when each unlocked.
    """
    now = datetime.now(dt_timezone.utc)
    for key, enabled, notes in modules:
        db.add(
            BuildingModule(
                building_id=building_id,
                module_key=key,
                enabled=enabled,
                enabled_at=now if enabled else None,
                notes=notes,
            )
        )
    db.flush()


def get_building_by_id_for_user(
    db: Session,
    *,
    building_id: UUID,
    user_id: UUID,
) -> Building | None:
    """Return a single building by its Postgres UUID, or None if not visible.

    The UUID-addressed counterpart to get_building_for_user -- used by the
    detail view for buildings still pending a Fabric bridge (no fabric id).
    Same visibility rule; enumeration-safe (None = absent OR not permitted).
    """
    stmt = (
        select(Building)
        .join(Organization, Building.organization_id == Organization.id)
        .where(Building.id == building_id)
        .where(Building.is_active.is_(True))
        .where(_visible_org_filter(user_id, _show_sample(db, user_id)))
        .options(
            joinedload(Building.modules),
            joinedload(Building.organization),
        )
    )
    return db.scalar(stmt)
