"""Estimation router -- building-level + portfolio-level Tier-A estimates,
plus a screening-input update so a user can sharpen an estimate.

  GET   /buildings/{id}/estimate   -- one building's screening band (+ confidence/method).
  GET   /portfolio/estimates       -- batch: EVERY visible building scored from whatever
                                      evidence it has (lights up even with no uploads).
  PATCH /buildings/{id}/profile    -- update year / EPC / heating / area to sharpen the
                                      estimate (manage-gated; whitelisted fields only).

Deterministic, Postgres-only, EUR0; reads are read-only + partner-aware.
"""
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Building
from app.repositories import building as building_repo
from app.repositories import consumption as consumption_repo
from app.schemas.estimation import (
    BuildingProfileResponse,
    BuildingProfileUpdate,
    EngineEstimate,
    EngineEstimateResponse,
    PortfolioEstimateRow,
    PortfolioEstimatesResponse,
)
from app.services import access
from app.services.estimation import assembler
from app.services.estimation import engine as estimation_engine
from app.utils.jwt import get_current_user_id

router = APIRouter(tags=["estimation"])

_ESTIMATE_FIELDS = tuple(EngineEstimate.model_fields.keys())
_PROFILE_FIELDS = ("construction_year", "epc_class", "heating_system", "floor_area_m2")


def _estimate_for(db: Session, building):
    """Run the engine for one building from its consumption rows. Returns
    (EngineResult, has_real_data)."""
    rows = consumption_repo.list_rows(db, building_id=building.id)
    inp = assembler.build_engine_input(
        building, rows, year=datetime.now(timezone.utc).year
    )
    return estimation_engine.estimate(inp), bool(rows)


@router.get("/buildings/{building_id}/estimate", response_model=EngineEstimateResponse)
def get_engine_estimate(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> EngineEstimateResponse:
    building = building_repo.get_building_by_id_for_user(
        db, building_id=building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    res, _ = _estimate_for(db, building)
    if not res.available:
        return EngineEstimateResponse(available=False, reason=res.reason)
    return EngineEstimateResponse(
        available=True,
        estimate=EngineEstimate(**{k: getattr(res, k) for k in _ESTIMATE_FIELDS}),
    )


@router.get("/portfolio/estimates", response_model=PortfolioEstimatesResponse)
def get_portfolio_estimates(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> PortfolioEstimatesResponse:
    """Score every visible building from whatever evidence it has. The point of
    the screening engine: a portfolio that 'lights up' even with no uploads."""
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    out: list[PortfolioEstimateRow] = []
    for b in buildings:
        res, has_real = _estimate_for(db, b)
        out.append(
            PortfolioEstimateRow(
                building_id=str(b.id),
                name=getattr(b, "name", None),
                city=getattr(b, "city", None),
                building_type=getattr(b, "building_type", None),
                area_m2=res.area_m2,
                available=res.available,
                basis=res.basis,
                confidence=res.confidence,
                has_real_data=has_real,
                eui_low=res.eui_low,
                eui_point=res.eui_point,
                eui_high=res.eui_high,
                annual_cost_eur_point=res.annual_cost_eur_point,
                annual_co2_kg_point=res.annual_co2_kg_point,
            )
        )
    scored = sum(1 for r in out if r.available and r.eui_point is not None)
    actual = sum(1 for r in out if r.basis == "actual")
    estimated = sum(1 for r in out if r.available and r.basis == "estimated")
    return PortfolioEstimatesResponse(
        total=len(out), scored=scored, estimated_count=estimated,
        actual_count=actual, rows=out,
    )


@router.patch("/buildings/{building_id}/profile", response_model=BuildingProfileResponse)
def patch_building_profile(
    building_id: UUID,
    body: BuildingProfileUpdate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingProfileResponse:
    """Update a building's screening inputs (year / EPC / heating / area) so the
    estimate sharpens. Manage-gated (404 otherwise); only whitelisted fields are
    writable, and a None is ignored (never clears an existing value)."""
    building = db.get(Building, building_id)
    if (
        building is None
        or not getattr(building, "is_active", True)
        or not access.can_manage_building(db, user_id=user_id, building=building)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    data = body.model_dump(exclude_unset=True)
    for key in _PROFILE_FIELDS:
        if key in data and data[key] is not None:
            setattr(building, key, data[key])
    db.commit()
    db.refresh(building)
    area = building.floor_area_m2
    return BuildingProfileResponse(
        building_id=str(building.id),
        construction_year=getattr(building, "construction_year", None),
        epc_class=getattr(building, "epc_class", None),
        heating_system=getattr(building, "heating_system", None),
        floor_area_m2=float(area) if area is not None else None,
    )
