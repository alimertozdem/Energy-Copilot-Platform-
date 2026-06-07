"""Compliance router — GET /compliance/esrs.

ESRS-E1-aligned energy + Scope 1/2/3 GHG summary for the user's visible
portfolio. Reads the Fabric Lakehouse (gold_ghg_scope + gold_kpi_daily +
silver_building_master) via the SQL Analytics Endpoint, same visibility rule
and auth as /portfolio. A pyodbc failure surfaces as the global 503
fabric_unavailable handler (see main.py).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import building as building_repo
from app.schemas.esrs import EsrsReport
from app.services import esrs_metrics
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/compliance", tags=["compliance"])


def _get_visible_fabric_ids(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> list[str]:
    """Resolve the user's visible Fabric building IDs (same rule as /portfolio)."""
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    return [b.fabric_building_id for b in buildings if b.fabric_building_id]


@router.get("/esrs", response_model=EsrsReport)
def get_esrs_report(
    fabric_ids: Annotated[list[str], Depends(_get_visible_fabric_ids)],
) -> EsrsReport:
    """ESRS-E1-aligned energy + Scope 1/2/3 GHG summary for the visible portfolio."""
    return esrs_metrics.get_esrs_report(fabric_ids)
