"""Abatement router — GET /abatement/macc.

JWT-protected (mirrors /actions, /portfolio). Returns the portfolio Marginal
Abatement Cost Curve computed from Fabric gold_recommendations. Read-only;
visibility is delegated to the service (same rule as /actions).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.abatement import MaccResponse
from app.repositories import building as building_repo
from app.services import abatement
from app.services import sample_fallback
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/abatement", tags=["abatement"])


@router.get("/macc", response_model=MaccResponse)
def get_macc(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    building_id: str | None = Query(
        default=None,
        description="Optional fabric_building_id. Restricts the curve to one building.",
    ),
    limit: int = Query(default=500, ge=1, le=2000),
) -> MaccResponse:
    """Portfolio marginal abatement cost curve (measures sorted cheapest-first)."""
    fabric_ids = [
        b.fabric_building_id
        for b in building_repo.list_buildings_for_user(db, user_id=user_id)
        if b.fabric_building_id
    ]
    return sample_fallback.serve(
        "abatement", MaccResponse, fabric_ids,
        lambda: abatement.get_macc_for_user(
            db, user_id=user_id, building_id=building_id, limit=limit),
    )
