"""Compliance router — ESRS-E1 summary, per-building CO₂ cost split, ESRS narrative.

  * GET  /compliance/esrs                          ESRS-E1 energy + Scope 1/2/3 (portfolio)
  * GET  /compliance/co2-cost/{id}                 CO2KostAufG split (one visible building)
  * GET  /compliance/esrs/narrative               saved E1 narrative for the caller's org
  * PUT  /compliance/esrs/narrative/{datapoint}   save one E1 qualitative disclosure

Fabric reads (gold_ghg_scope + gold_kpi_daily + silver_building_master) go through the
SQL Analytics Endpoint; a pyodbc failure surfaces as the global 503 fabric_unavailable
handler. Narrative is org-scoped Postgres (the company writes the qualitative E1
disclosures; quantitative E1-5/E1-6 are auto from Fabric).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import building as building_repo
from app.repositories import esrs_narrative as esrs_narrative_repo
from app.schemas.co2_cost import Co2CostAllocationResponse
from app.schemas.esrs import EsrsReport
from app.schemas.geg_conformity import GegConformityResponse
from app.schemas.esrs_narrative import (
    EsrsNarrativeItem,
    EsrsNarrativeResponse,
    EsrsNarrativeUpdate,
)
from app.services import co2_cost_allocation, esrs_metrics, geg_conformity
from app.utils.jwt import get_current_org_id, get_current_user_id

router = APIRouter(prefix="/compliance", tags=["compliance"])

# ESRS E-1 qualitative disclosures that carry an editable narrative
# (E1-5 energy and E1-6 GHG are auto-filled from Fabric, not editable here).
_E1_NARRATIVE_KEYS = {"E1-1", "E1-2", "E1-3", "E1-4", "E1-7", "E1-8", "E1-9"}
# VSME Basic Module narrative disclosures (B3 = Energy & GHG is auto-filled, not here).
_VSME_NARRATIVE_KEYS = {
    "B1", "B2", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11",
    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9",
}
_ALLOWED_NARRATIVE_KEYS = _E1_NARRATIVE_KEYS | _VSME_NARRATIVE_KEYS


def _get_visible_fabric_ids(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> list[str]:
    """Resolve the user's visible Fabric building IDs (same rule as /portfolio)."""
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    return [b.fabric_building_id for b in buildings if b.fabric_building_id]


@router.get("/esrs", response_model=EsrsReport)
def get_esrs_report(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    building_id: str | None = None,
) -> EsrsReport:
    """ESRS-E1-aligned energy + Scope 1/2/3 GHG summary.

    Portfolio-wide by default; pass ``building_id`` to scope the report to a single
    VISIBLE building (404 if it isn't visible -- mirrors the per-building endpoints).
    The metrics service already accepts a list, so a one-element list scopes it.
    """
    if building_id:
        building = building_repo.get_building_for_user(
            db, fabric_building_id=building_id, user_id=user_id
        )
        if building is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Building '{building_id}' not found",
            )
        return esrs_metrics.get_esrs_report([building_id])
    fabric_ids = [
        b.fabric_building_id
        for b in building_repo.list_buildings_for_user(db, user_id=user_id)
        if b.fabric_building_id
    ]
    return esrs_metrics.get_esrs_report(fabric_ids)


@router.get("/co2-cost/{fabric_building_id}", response_model=Co2CostAllocationResponse)
def get_co2_cost_allocation(
    fabric_building_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> Co2CostAllocationResponse:
    """CO2KostAufG heating-fuel CO₂ cost split for one visible building (404 otherwise).

    404 (not 403) when the building isn't visible — mirrors GET /buildings/{id},
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
    return co2_cost_allocation.get_co2_cost_allocation(fabric_building_id)


@router.get("/geg/{fabric_building_id}", response_model=GegConformityResponse)
def get_geg_conformity(
    fabric_building_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> GegConformityResponse:
    """GEG (Gebäudeenergiegesetz) conformity screening for one visible building (404 otherwise)."""
    building = building_repo.get_building_for_user(
        db, fabric_building_id=fabric_building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{fabric_building_id}' not found",
        )
    return geg_conformity.get_geg_conformity(fabric_building_id)


@router.get("/esrs/narrative", response_model=EsrsNarrativeResponse)
def get_esrs_narrative(
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> EsrsNarrativeResponse:
    """Saved ESRS E-1 qualitative narrative for the caller's organization."""
    rows = esrs_narrative_repo.list_for_org(db, org_id)
    return EsrsNarrativeResponse(
        items=[
            EsrsNarrativeItem(
                datapoint_key=r.datapoint_key,
                content=r.content,
                reporting_year=r.reporting_year,
                updated_at=r.updated_at.isoformat() if r.updated_at else None,
            )
            for r in rows
        ]
    )


@router.put("/esrs/narrative/{datapoint_key}", response_model=EsrsNarrativeItem)
def put_esrs_narrative(
    datapoint_key: str,
    payload: EsrsNarrativeUpdate,
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> EsrsNarrativeItem:
    """Create or update one ESRS E-1 qualitative disclosure for the caller's org."""
    key = datapoint_key.strip().upper()
    if key not in _ALLOWED_NARRATIVE_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown ESRS E-1 narrative datapoint '{datapoint_key}'.",
        )
    row = esrs_narrative_repo.upsert(
        db,
        org_id=org_id,
        datapoint_key=key,
        content=payload.content,
        reporting_year=payload.reporting_year,
        user_id=user_id,
    )
    return EsrsNarrativeItem(
        datapoint_key=row.datapoint_key,
        content=row.content,
        reporting_year=row.reporting_year,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )
