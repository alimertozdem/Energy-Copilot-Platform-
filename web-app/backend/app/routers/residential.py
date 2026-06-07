"""Residential MANAGER router — building KPIs + resident invites.

Manager-facing (B2B JWT), distinct from the resident-auth ``residence`` router.

  * GET  /residential/buildings/{id}          per-unit KPIs + rollup (read; visible buildings)
  * POST /residential/buildings/{id}/invites  mint a resident magic-link (write; can_manage)

Visibility/authorization reuses the buildings repo + access service (partner-aware):
read needs the building visible; invite needs ``can_manage_building`` (own org, or a
``full_manage`` partner link). NO Power BI embed — a custom read like /portfolio.
"""
import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.residential import (
    ResidentIdentity,
    ResidentInviteToken,
    Unit,
    UnitResident,
)
from app.repositories import building as building_repo
from app.schemas.residential import (
    ResidentialBuildingResponse,
    ResidentialBuildingRollup,
    ResidentialPortfolioResponse,
    ResidentialPortfolioRow,
    ResidentInviteRequest,
    ResidentInviteResponse,
    UviComplianceResponse,
)
from app.services import access, residential_manager_metrics
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/residential", tags=["residential"])

INVITE_TTL_DAYS = 14


@router.get(
    "/buildings/{fabric_building_id}", response_model=ResidentialBuildingResponse
)
def get_building_residential(
    fabric_building_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidentialBuildingResponse:
    """Per-unit residential KPIs + rollup for one visible building (404 otherwise).

    404 (not 403) when the building is not visible — mirrors GET /buildings/{id},
    preventing existence enumeration.
    """
    building = building_repo.get_building_for_user(
        db, fabric_building_id=fabric_building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{fabric_building_id}' not found",
        )
    return residential_manager_metrics.get_building_residential(fabric_building_id)


@router.post(
    "/buildings/{fabric_building_id}/invites",
    response_model=ResidentInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resident_invite(
    fabric_building_id: str,
    payload: ResidentInviteRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidentInviteResponse:
    """Mint a single-use magic-link for a resident of one unit (manager delivers it).

    Authorization: the building must be visible AND writable (``can_manage_building``
    — own org, or a ``full_manage`` partner link; read-only partners get 403). The
    unit/identity/tenancy are find-or-created so no separate unit-management UI is
    needed for V1. Only a hash of the token is stored; the raw token is returned once.
    """
    building = building_repo.get_building_for_user(
        db, fabric_building_id=fabric_building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{fabric_building_id}' not found",
        )
    if not access.can_manage_building(db, user_id=user_id, building=building):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managing residents requires manage (not read-only) access.",
        )

    email = payload.email.strip().lower()
    if "@" not in email or len(email) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="A valid email is required."
        )
    fabric_unit_id = payload.fabric_unit_id.strip()
    if not fabric_unit_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="fabric_unit_id is required."
        )

    # find-or-create the unit (bridged to Fabric) under this building
    unit = db.scalar(select(Unit).where(Unit.fabric_unit_id == fabric_unit_id))
    if unit is None:
        unit = Unit(building_id=building.id, fabric_unit_id=fabric_unit_id, label=fabric_unit_id)
        db.add(unit)
        db.flush()
    elif unit.building_id != building.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That unit belongs to another building.",
        )

    # find-or-create the resident identity (email is the only PII)
    identity = db.scalar(select(ResidentIdentity).where(ResidentIdentity.email == email))
    if identity is None:
        identity = ResidentIdentity(email=email, status="invited")
        db.add(identity)
        db.flush()

    # find-or-create an active tenancy
    tenancy = db.scalar(
        select(UnitResident).where(
            UnitResident.unit_id == unit.id,
            UnitResident.resident_identity_id == identity.id,
            UnitResident.status == "active",
        )
    )
    if tenancy is None:
        tenancy = UnitResident(
            unit_id=unit.id,
            resident_identity_id=identity.id,
            valid_from=date.today(),
            valid_to=None,
            status="active",
        )
        db.add(tenancy)
        db.flush()

    # mint a fresh single-use token (store only the hash)
    raw = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS)
    db.add(
        ResidentInviteToken(
            unit_resident_id=tenancy.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=expires_at,
        )
    )
    db.commit()

    return ResidentInviteResponse(
        token=raw,
        email=identity.email,
        fabric_unit_id=unit.fabric_unit_id or fabric_unit_id,
        expires_at=expires_at.isoformat(),
    )



@router.get("/portfolio", response_model=ResidentialPortfolioResponse)
def get_residential_portfolio(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidentialPortfolioResponse:
    """All residential buildings the caller may see, each with a rollup."""
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    residential = [
        b
        for b in buildings
        if b.fabric_building_id and "residential" in (b.building_type or "").lower()
    ]
    rollups = residential_manager_metrics.get_portfolio_rollups(
        [b.fabric_building_id for b in residential]
    )
    rows = [
        ResidentialPortfolioRow(
            fabric_building_id=b.fabric_building_id,
            name=b.name,
            city=b.city,
            country_code=b.country_code,
            rollup=rollups.get(b.fabric_building_id) or ResidentialBuildingRollup(),
        )
        for b in residential
    ]
    return ResidentialPortfolioResponse(buildings=rows)


@router.get("/uvi-compliance", response_model=UviComplianceResponse)
def get_uvi_compliance(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> UviComplianceResponse:
    """Portfolio UVI/HKVO compliance readiness across visible residential buildings.

    The 'why now' wedge: which buildings meet the monthly-consumption-info duty,
    how exposed the portfolio is to the §12 3% reduction, and the Jan-2027 deadline.
    """
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    residential = [
        b
        for b in buildings
        if b.fabric_building_id and "residential" in (b.building_type or "").lower()
    ]
    names = {b.fabric_building_id: b.name for b in residential}
    return residential_manager_metrics.get_uvi_compliance(
        [b.fabric_building_id for b in residential], names
    )
