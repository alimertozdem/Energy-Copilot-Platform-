"""Buildings router -- GET /buildings, GET /buildings/{fabric_id}, POST /buildings.

All endpoints require a JWT Bearer token. The frontend obtains the token
from /auth/login, /auth/register, or /auth/sync and forwards it as:
    Authorization: Bearer <jwt>

Visibility rule (enforced in app/repositories/building.py):
  * Buildings owned by orgs the user is a member of
  * Plus buildings owned by any sample/demo organization

Create (POST) writes into the org carried in the JWT (get_current_org_id)
and requires admin or manager role. It records a building.created audit row in
the same transaction (surfaced in the /settings Activity feed).
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Building
from app.repositories import audit as audit_repo
from app.repositories import bridge as bridge_repo
from app.repositories import building as building_repo
from app.repositories import user as user_repo
from app.repositories import connection as connection_repo
from app.repositories import consumption as consumption_repo
from app.repositories import organization as org_repo
from app.schemas.buildings import (
    BuildingCreateRequest,
    BuildingListResponse,
    BuildingModuleInput,
    BuildingModuleResponse,
    BuildingResponse,
    BulkImportRequest,
    BulkImportResponse,
    BulkImportRowResult,
)
from app.schemas.consumption import (
    BaselineEstimate,
    BaselineEstimateResponse,
    BaselineKPIs,
    BuildingCopResponse,
    ConsumptionSummary,
    ParsePdfRequest,
    ParsedBillResponse,
    ConsumptionUploadRequest,
)
from app.schemas.bridge import (
    BridgeReadinessResponse,
    BridgeRequestCreate,
    BridgeRequestState,
)
from app.schemas.readiness import BuildingReadiness
from app.schemas.monitoring import MonitoringResponse
from app.schemas.heating import HeatingAssessmentResponse
from app.services import access, baseline_estimate, baseline_kpi, bill_parser, bridge_readiness, building_readiness, cop as cop_service, monitoring as monitoring_service, heating_assessment
from app.utils.jwt import get_current_org_id, get_current_user_id

router = APIRouter(prefix="/buildings", tags=["buildings"])


class _SampleDataState(BaseModel):
    enabled: bool


# NOTE: declared before GET /{fabric_building_id} so "/sample-data" is not captured
# as a building id (FastAPI matches in declaration order).
@router.get("/sample-data", response_model=_SampleDataState)
def get_sample_data_visibility(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> _SampleDataState:
    """Whether the caller currently sees sample/demo buildings in their portfolio."""
    return _SampleDataState(enabled=user_repo.get_show_sample_data(db, user_id))


@router.put("/sample-data", response_model=_SampleDataState)
def set_sample_data_visibility(
    payload: _SampleDataState,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> _SampleDataState:
    """Opt in/out of seeing sample/demo buildings (load/remove from the portfolio)."""
    user_repo.set_show_sample_data(db, user_id, payload.enabled)
    return _SampleDataState(enabled=payload.enabled)


def _to_response(b: Building) -> BuildingResponse:
    """Map an ORM Building (with eager-loaded modules + organization) to API DTO."""
    return BuildingResponse(
        id=b.id,
        fabric_building_id=b.fabric_building_id,
        name=b.name,
        city=b.city,
        country_code=b.country_code,
        building_type=b.building_type,
        floor_area_m2=float(b.floor_area_m2) if b.floor_area_m2 is not None else None,
        pv_capacity_kwp=(
            float(b.pv_capacity_kwp) if b.pv_capacity_kwp is not None else None
        ),
        construction_year=b.construction_year,
        epc_class=b.epc_class,
        heating_system=b.heating_system,
        cooling_system=b.cooling_system,
        occupancy_pattern=b.occupancy_pattern,
        floors_above_ground=b.floors_above_ground,
        typical_occupants=b.typical_occupants,
        timezone=b.timezone,
        is_active=b.is_active,
        organization_id=b.organization_id,
        is_sample_org=b.organization.is_sample,
        modules=[
            BuildingModuleResponse(module_key=m.module_key, enabled=m.enabled)
            for m in b.modules
        ],
    )


@router.get("", response_model=BuildingListResponse)
def list_buildings(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingListResponse:
    """List buildings visible to the authenticated user."""
    buildings = building_repo.list_buildings_for_user(db, user_id=user_id)
    items = [_to_response(b) for b in buildings]
    return BuildingListResponse(buildings=items, total=len(items))


@router.post(
    "", response_model=BuildingResponse, status_code=status.HTTP_201_CREATED
)
def create_building(
    body: BuildingCreateRequest,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingResponse:
    """Create a building in the user's current org (onboarding wizard).

    Authorization: the user must be an admin or manager of the org. Viewers
    cannot add buildings. The new building has no Fabric data yet
    (fabric_building_id stays NULL).
    """
    membership = org_repo.get_membership(db, org_id=org_id, user_id=user_id)
    if membership is None:
        # Hide org existence from non-members (mirrors settings pattern).
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    if membership.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Adding buildings requires the admin or manager role.",
        )

    b = building_repo.create_building(
        db,
        organization_id=org_id,
        name=body.name,
        building_type=body.building_type,
        city=body.city,
        country_code=body.country_code.upper() if body.country_code else None,
        address=body.address,
        floor_area_m2=body.floor_area_m2,
        construction_year=body.construction_year,
        epc_class=body.epc_class,
        heating_system=body.heating_system,
        cooling_system=body.cooling_system,
        occupancy_pattern=body.occupancy_pattern,
        floors_above_ground=body.floors_above_ground,
        typical_occupants=body.typical_occupants,
        timezone=body.timezone,
        pv_capacity_kwp=body.pv_capacity_kwp,
        wall_u_value=body.wall_u_value,
        roof_u_value=body.roof_u_value,
        window_u_value=body.window_u_value,
        insulation_year=body.insulation_year,
        has_gas_heating=body.has_gas_heating,
    )

    # 'meters' is always present + enabled; merge any requested modules over it.
    module_map: dict[str, BuildingModuleInput] = {
        m.module_key: m for m in body.modules
    }
    if "meters" not in module_map:
        module_map["meters"] = BuildingModuleInput(module_key="meters", enabled=True)
    building_repo.create_building_modules(
        db,
        building_id=b.id,
        modules=[(m.module_key, m.enabled, m.notes) for m in module_map.values()],
    )

    # Audit in the SAME transaction as the create (atomic).
    audit_repo.record_event(
        db,
        user_id=user_id,
        organization_id=org_id,
        action="building.created",
        entity_type="building",
        entity_id=str(b.id),
        details={"name": b.name, "building_type": b.building_type},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    db.commit()
    db.refresh(b)
    return _to_response(b)


@router.post(
    "/bulk", response_model=BulkImportResponse, status_code=status.HTTP_201_CREATED
)
def bulk_import_buildings(
    body: BulkImportRequest,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BulkImportResponse:
    """Bulk-create building shells from a portfolio CSV (Hausverwaltung onboarding).

    Same admin/manager gate as POST /buildings. Each row is created in its own
    SAVEPOINT so one bad row never aborts the batch; per-row results are
    returned. 'meters' is auto-enabled on each building (no Fabric data yet --
    a baseline / live source is added per building afterwards).
    """
    membership = org_repo.get_membership(db, org_id=org_id, user_id=user_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    if membership.role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Importing buildings requires the admin or manager role.",
        )

    results: list[BulkImportRowResult] = []
    created = 0
    for i, row in enumerate(body.rows):
        try:
            with db.begin_nested():
                b = building_repo.create_building(
                    db,
                    organization_id=org_id,
                    name=row.name,
                    building_type=row.building_type,
                    city=row.city,
                    country_code=row.country_code.upper() if row.country_code else None,
                    floor_area_m2=row.floor_area_m2,
                    construction_year=row.construction_year,
                    epc_class=row.epc_class,
                    heating_system=row.heating_system,
                )
                building_repo.create_building_modules(
                    db, building_id=b.id, modules=[("meters", True, None)]
                )
            results.append(
                BulkImportRowResult(index=i, name=row.name, ok=True, id=b.id)
            )
            created += 1
        except Exception as exc:  # one bad row must not abort the batch
            results.append(
                BulkImportRowResult(
                    index=i, name=row.name, ok=False, error=str(exc)[:200]
                )
            )

    failed = len(body.rows) - created
    audit_repo.record_event(
        db,
        user_id=user_id,
        organization_id=org_id,
        action="building.bulk_imported",
        entity_type="organization",
        entity_id=str(org_id),
        details={"created": created, "failed": failed},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return BulkImportResponse(created=created, failed=failed, results=results)


@router.get("/{fabric_building_id}", response_model=BuildingResponse)
def get_building(
    fabric_building_id: str,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingResponse:
    """Get one building by its Fabric ID (e.g. "B001").

    Returns 404 when the building doesn't exist OR the user has no permission.
    Both cases are intentionally indistinguishable (prevents enumeration).
    """
    b = building_repo.get_building_for_user(
        db,
        fabric_building_id=fabric_building_id,
        user_id=user_id,
    )
    if b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{fabric_building_id}' not found",
        )
    return _to_response(b)


# ---------------------------------------------------------------------------
# Consumption baseline (CSV / bill upload) — addressed by the building's UUID
# so it works for buildings still pending a Fabric bridge (fabric_building_id
# is NULL). The CSV is parsed client-side and POSTed as JSON monthly rows.
# ---------------------------------------------------------------------------

def _building_for_write(db: Session, building_id: UUID, user_id: UUID) -> Building:
    """Load a building by UUID, gated by manage rights. 404 otherwise."""
    building = db.get(Building, building_id)
    if (
        building is None
        or not building.is_active
        or not access.can_manage_building(db, user_id=user_id, building=building)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Building not found",
        )
    return building


@router.get("/{building_id}/consumption", response_model=ConsumptionSummary)
def get_consumption(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ConsumptionSummary:
    """Summary of a building's uploaded / manual consumption baseline."""
    _building_for_write(db, building_id, user_id)
    return ConsumptionSummary(**consumption_repo.get_summary(db, building_id=building_id))


@router.post("/{building_id}/consumption", response_model=ConsumptionSummary)
def upload_consumption(
    building_id: UUID,
    body: ConsumptionUploadRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ConsumptionSummary:
    """Store uploaded / manual monthly consumption (CSV parsed client-side)."""
    _building_for_write(db, building_id, user_id)
    rows = [(r.period, r.energy_kwh, r.cost_eur) for r in body.rows]
    consumption_repo.upsert_rows(db, building_id=building_id, rows=rows, source=body.source)
    db.commit()
    return ConsumptionSummary(**consumption_repo.get_summary(db, building_id=building_id))


@router.get("/{building_id}/kpis", response_model=BaselineKPIs)
def get_baseline_kpis(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BaselineKPIs:
    """Baseline KPIs (EUI, annual energy, carbon, cost) from uploaded consumption.

    Same UUID addressing + manage gate as the consumption endpoints, so it works
    for buildings still pending a Fabric bridge (fabric_building_id NULL). Pure
    Postgres-side compute -- no Fabric round-trip. Returns indicative figures with
    provenance flags; once the building is bridged, the Fabric gold KPIs take over.
    """
    building = _building_for_write(db, building_id, user_id)
    rows = consumption_repo.list_rows(db, building_id=building_id)
    return BaselineKPIs(**baseline_kpi.compute_baseline_kpis(rows, building))


@router.get("/{building_id}/readiness", response_model=BuildingReadiness)
def get_building_readiness(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingReadiness:
    """Data Score (0-100) + per-report readiness for a building the caller may see.

    Measures DATA COMPLETENESS (what reports we can produce), not building
    performance. UUID-addressed so it works before a Fabric bridge. Read-only.
    """
    building = building_repo.get_building_by_id_for_user(
        db, building_id=building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    months = len(consumption_repo.list_rows(db, building_id=building_id))
    result = building_readiness.compute_readiness(
        building_readiness.building_attrs(building), months
    )
    return BuildingReadiness(**result)


@router.get(
    "/{building_id}/baseline-estimate", response_model=BaselineEstimateResponse
)
def get_baseline_estimate(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BaselineEstimateResponse:
    """Provisional, clearly-labeled baseline estimate for a building that has
    metadata (type + area) but no uploaded consumption yet -- so the first-value
    loop is never empty. Returns available=False once real consumption exists
    (the uploaded baseline supersedes the estimate) or when we cannot estimate
    honestly (no area / an unmodeled type). UUID-addressed, read-only.
    """
    from datetime import datetime, timezone as _tz

    building = building_repo.get_building_by_id_for_user(
        db, building_id=building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    if consumption_repo.list_rows(db, building_id=building_id):
        return BaselineEstimateResponse(available=False, estimate=None)
    est = baseline_estimate.estimate_baseline(building, datetime.now(_tz.utc).year)
    if est is None:
        return BaselineEstimateResponse(available=False, estimate=None)
    return BaselineEstimateResponse(available=True, estimate=BaselineEstimate(**est))


@router.get("/{building_id}/cop", response_model=BuildingCopResponse)
def get_building_cop(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    days: int = 30,
) -> BuildingCopResponse:
    """Measured heat-pump COP from landed telemetry (heat meter / electricity).

    Returns status 'measured' only when BOTH a heat meter and the pump electricity
    are present; 'device_reported' if the controller reports COP directly; else
    'needs_heat_meter'. UUID-addressed, read-only. See services/cop.py.
    """
    building = building_repo.get_building_by_id_for_user(
        db, building_id=building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    return BuildingCopResponse(**cop_service.compute_cop(db, building, days))


@router.get("/{building_id}/monitoring", response_model=MonitoringResponse)
def get_building_monitoring(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    hours: int = 24,
) -> MonitoringResponse:
    """Latest live telemetry per sensor_type for a building (bronze_iot_readings).

    App-native monitoring (no Fabric): powers the building page's live panel from
    the same source the COP + verify-panel use. UUID-addressed, read-only.
    """
    building = building_repo.get_building_by_id_for_user(
        db, building_id=building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    return MonitoringResponse(**monitoring_service.latest_monitoring(db, building, hours))


@router.get("/{building_id}/heating", response_model=HeatingAssessmentResponse)
def get_building_heating(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> HeatingAssessmentResponse:
    """Heating & envelope assessment (demand, fuel cost/CO2, GEG, retrofit ROI).

    Postgres-native (no Fabric): works for pending buildings. Uses uploaded
    consumption when present, else an archetype estimate. Screening-grade.
    """
    building = building_repo.get_building_by_id_for_user(
        db, building_id=building_id, user_id=user_id
    )
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    rows = consumption_repo.list_rows(db, building_id=building_id)
    annual = None
    if rows:
        annual = baseline_kpi.compute_baseline_kpis(rows, building).get("annual_energy_kwh")
    return HeatingAssessmentResponse(**heating_assessment.assess(building, annual))


@router.post("/{building_id}/consumption/parse-pdf", response_model=ParsedBillResponse)
def parse_consumption_pdf(
    building_id: UUID,
    body: ParsePdfRequest,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ParsedBillResponse:
    """Extract CANDIDATE monthly rows from a digital PDF bill (base64 in JSON).

    Best-effort: the user reviews the extracted rows in the UI and then saves
    them via POST /consumption — this endpoint never persists anything. Digital
    PDFs only (selectable text); scans/photos would need OCR (a later add-on).
    pdfplumber is imported lazily so the app runs without it (503 if absent).
    """
    import base64
    import io

    _building_for_write(db, building_id, user_id)
    try:
        raw = base64.b64decode(body.pdf_base64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid base64 PDF payload"
        )
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="PDF too large (max 8 MB).",
        )
    try:
        import pdfplumber
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF parsing isn't available on the server (install pdfplumber).",
        )
    text_parts: list[str] = []
    tables: list = []
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages[:24]:  # cap pages for safety
                text_parts.append(page.extract_text() or "")
                for tbl in page.extract_tables() or []:
                    tables.append(tbl)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not read the PDF: {str(exc)[:120]}",
        )
    result = bill_parser.parse_bill(text="\n".join(text_parts), tables=tables)
    return ParsedBillResponse(**result)


# ---------------------------------------------------------------------------
# Self-serve Fabric bridging (Access Layer 3) — a customer requests the full
# Fabric analytics for a pending building. The wizard reads bridge-readiness
# (what the data earns) then files a request the founder fulfils. UUID-addressed
# + manage-gated, like the consumption endpoints.
# See docs/architecture/self-serve-fabric-bridging.md.
# ---------------------------------------------------------------------------

def _assess_building(db: Session, building: Building) -> dict:
    """Gather a building's Postgres state and run the readiness assessment."""
    summary = consumption_repo.get_summary(db, building_id=building.id)
    devices = connection_repo.list_devices(db, building_id=building.id)
    return bridge_readiness.assess_readiness(
        building_type=building.building_type,
        floor_area_m2=(
            float(building.floor_area_m2) if building.floor_area_m2 is not None else None
        ),
        pv_capacity_kwp=(
            float(building.pv_capacity_kwp) if building.pv_capacity_kwp is not None else None
        ),
        epc_class=building.epc_class,
        consumption_months=int(summary["months"]),
        has_cost=summary["total_cost_eur"] is not None,
        has_device=len(devices) > 0,
        iot_enabled=any(m.module_key == "iot" and m.enabled for m in building.modules),
        battery_enabled=any(
            m.module_key == "battery" and m.enabled for m in building.modules
        ),
    )


def _request_state(req) -> BridgeRequestState:
    return BridgeRequestState(
        id=req.id,
        status=req.status,
        target_tier=req.target_tier,
        note=req.note,
        created_at=req.created_at,
        resolved_at=req.resolved_at,
        resolution_note=req.resolution_note,
    )


@router.get("/{building_id}/bridge-readiness", response_model=BridgeReadinessResponse)
def get_bridge_readiness(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BridgeReadinessResponse:
    """Data-tier-aware readiness: which report pages this building's data earns.

    Drives the self-serve bridge wizard. Deterministic (no LLM) — see
    app/services/bridge_readiness.py. Includes the building's current/last
    request so the UI can show 'pending review' after one is filed.
    """
    building = _building_for_write(db, building_id, user_id)
    assessment = _assess_building(db, building)
    latest = bridge_repo.get_latest_request(db, building_id=building_id)
    return BridgeReadinessResponse(
        **assessment,
        request=_request_state(latest) if latest is not None else None,
        is_bridged=building.fabric_building_id is not None,
    )


@router.post(
    "/{building_id}/bridge-request",
    response_model=BridgeRequestState,
    status_code=status.HTTP_201_CREATED,
)
def create_bridge_request(
    building_id: UUID,
    body: BridgeRequestCreate,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BridgeRequestState:
    """File a self-serve request to bridge this building into Fabric.

    Stores a snapshot of the readiness assessment so the founder reviews exactly
    what the customer had. 409 if already bridged or a request is already pending;
    422 if there is nothing to bridge yet (no uploads, no device).
    """
    building = _building_for_write(db, building_id, user_id)
    if building.fabric_building_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This building is already bridged to Fabric.",
        )
    if bridge_repo.get_active_request(db, building_id=building_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A bridge request is already pending for this building.",
        )
    assessment = _assess_building(db, building)
    if not assessment["can_request"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Upload consumption or connect a device before requesting a bridge.",
        )

    req = bridge_repo.create_request(
        db,
        building_id=building_id,
        organization_id=building.organization_id,
        requested_by=user_id,
        target_tier=(body.target_tier or "full"),
        readiness=assessment,
        note=body.note,
    )
    audit_repo.record_event(
        db,
        user_id=user_id,
        organization_id=building.organization_id,
        action="bridge.requested",
        entity_type="building",
        entity_id=str(building_id),
        details={
            "target_tier": req.target_tier,
            "overall_tier": assessment["overall_tier"],
            "ready_pages": assessment["ready_pages"],
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(req)
    return _request_state(req)


@router.delete("/{building_id}/bridge-request", response_model=BridgeRequestState)
def cancel_bridge_request(
    building_id: UUID,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BridgeRequestState:
    """Cancel this building's pending bridge request (customer changed their mind)."""
    building = _building_for_write(db, building_id, user_id)
    req = bridge_repo.cancel_active(db, building_id=building_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending bridge request to cancel.",
        )
    audit_repo.record_event(
        db,
        user_id=user_id,
        organization_id=building.organization_id,
        action="bridge.cancelled",
        entity_type="building",
        entity_id=str(building_id),
        details=None,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(req)
    return _request_state(req)


@router.get("/by-id/{building_id}", response_model=BuildingResponse)
def get_building_by_uuid(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingResponse:
    """Get one building by its Postgres UUID -- for buildings still pending a
    Fabric bridge (no fabric_building_id, so they can't use GET /{fabric_id}).

    Visibility-gated (same rule as the list); 404 when absent or not permitted.
    The two-segment path '/by-id/{uuid}' doesn't collide with the one-segment
    '/{fabric_building_id}' route.
    """
    b = building_repo.get_building_by_id_for_user(
        db, building_id=building_id, user_id=user_id
    )
    if b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    return _to_response(b)
