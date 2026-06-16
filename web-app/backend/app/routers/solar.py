"""Solar router (Solar initiative C) -- GET /solar/detail.

Reads Fabric Lakehouse via SQL Analytics Endpoint (same path as /portfolio).
Visibility: user's org buildings + sample orgs (building_repo).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import building as building_repo
from app.schemas.solar import SolarDetailResponse
from app.services import solar_detail
from app.services import sample_fallback
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/solar", tags=["solar"])


@router.get("/detail", response_model=SolarDetailResponse)
def get_solar_detail(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> SolarDetailResponse:
    """Daily portfolio solar series + summary for the /solar page."""
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    fabric_ids = [b.fabric_building_id for b in buildings if b.fabric_building_id]
    return sample_fallback.serve(
        "solar_detail", SolarDetailResponse, fabric_ids,
        lambda: solar_detail.get_solar_detail(fabric_ids, db),
    )
