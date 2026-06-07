"""Portfolio router — GET /portfolio/kpis + GET /portfolio/buildings.

These endpoints read directly from the Fabric Lakehouse via the SQL
Analytics Endpoint (see app/integrations/fabric_sql.py). They do NOT touch
the embedded Power BI semantic model — that's a separate read path used by
the embed pages (/buildings/[id]).

Visibility rule:
  * Same _visible_org_filter as /buildings — the user sees only buildings in
    their orgs plus any sample/demo orgs.
  * The Postgres-side fabric_building_id list is passed to Fabric SQL as a
    parameterized IN(...) clause. Nothing else gets read.

Auth:
  * JWT Bearer (same scheme as /buildings).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import building as building_repo
from app.schemas.portfolio import PortfolioBuildingsResponse, PortfolioKPIs
from app.services import access
from app.services import portfolio_metrics
from app.utils.jwt import get_current_user_id

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def _get_visible_fabric_ids(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    client: str | None = None,
) -> list[str]:
    """
    Resolve the user's visible Fabric building IDs.

    Reuses building_repo.list_buildings_for_user so authorization stays in one
    place. Returns an empty list when the user has no visible buildings (the
    service layer treats that as an empty portfolio).
    """
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    if client:
        try:
            client_org_id = UUID(client)
        except ValueError:
            return []  # malformed -> empty (no enumeration leak)
        # Only an ACTIVE client of the caller's partner org may be selected.
        if client_org_id not in set(access.partner_client_org_ids(db, user_id=user_id)):
            return []
        buildings = [b for b in buildings if b.organization_id == client_org_id]
    return [b.fabric_building_id for b in buildings if b.fabric_building_id]


@router.get("/kpis", response_model=PortfolioKPIs)
def get_portfolio_kpis(
    fabric_ids: Annotated[list[str], Depends(_get_visible_fabric_ids)],
) -> PortfolioKPIs:
    """Return the 4 portfolio-level KPI tiles + delta vs prior 30 days."""
    return portfolio_metrics.get_portfolio_kpis(fabric_ids)


@router.get("/buildings", response_model=PortfolioBuildingsResponse)
def get_portfolio_buildings(
    fabric_ids: Annotated[list[str], Depends(_get_visible_fabric_ids)],
) -> PortfolioBuildingsResponse:
    """Return one row per visible building with 30-day aggregates + module flags."""
    return portfolio_metrics.get_portfolio_buildings(fabric_ids)
