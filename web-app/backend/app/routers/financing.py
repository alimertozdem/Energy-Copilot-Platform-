"""Financing router — GET /financing/summary.

JWT-protected (mirrors /actions, /abatement). Portfolio financing & subsidy
summary computed from gold_recommendations × the building master, via the pure
finance_model. Read-only; visibility delegated to the service.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.financing import FinancingResponse
from app.services import financing
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/financing", tags=["financing"])


@router.get("/summary", response_model=FinancingResponse)
def get_financing_summary(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    building_id: str | None = Query(
        default=None, description="Optional fabric_building_id; restricts to one building."
    ),
    has_isfp: bool = Query(
        default=False, description="Apply the iSFP bonus (raises BAFA rate + cap)."
    ),
    limit: int = Query(default=500, ge=1, le=2000),
) -> FinancingResponse:
    """Indicative portfolio financing: unit-aware subsidy, scenario NPV, value uplift."""
    return financing.get_financing_for_user(
        db, user_id=user_id, building_id=building_id, has_isfp=has_isfp, limit=limit
    )
