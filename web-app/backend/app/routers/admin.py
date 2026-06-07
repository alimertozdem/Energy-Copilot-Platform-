"""Platform admin router -- /admin/* (founder-only).

Every endpoint is gated by get_current_platform_admin: a normal authenticated
user gets 403. Reads bypass the per-org visibility filter on purpose (the
founder sees every organization). Writes (PATCH) let the founder manage pilots
without touching the DB:
  * organization subscription tier/status
  * building module enablement (unlocks /reports iot/battery pages)
  * building fabric_building_id link (connects an onboarded building to data)

Every write records an AuditLog row in the SAME transaction (admin.* actions),
surfaced by GET /admin/audit and the /admin Activity table.
"""
from datetime import datetime, timezone as dt_timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.repositories import admin as admin_repo
from app.repositories import audit as audit_repo
from app.repositories import bridge as bridge_repo
from app.repositories import organization as org_repo
from app.repositories import pilot as pilot_repo
from app.schemas.bridge import (
    AdminBridgeAutomate,
    AdminBridgeRequestRow,
    AdminBridgeRequestsResponse,
    AdminBridgeResolve,
    AutomatedBridgeResult,
)
from app.schemas.pilot import (
    AdminPilotRequestRow,
    AdminPilotRequestsResponse,
    AdminPilotResolve,
)
from app.services import bridge_orchestrator
from app.schemas.admin import (
    AdminAuditResponse,
    AdminAuditRow,
    AdminBuildingModule,
    AdminBuildingRow,
    AdminBuildingsResponse,
    AdminOrganizationsResponse,
    AdminOrgRow,
    AdminUserRow,
    AdminUsersResponse,
    BuildingFabricUpdate,
    BuildingModuleUpdate,
    MutationResult,
    OrgSubscriptionUpdate,
    PlatformStats,
)
from app.utils.jwt import get_current_platform_admin

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_TIERS = {"free", "basic", "monitor", "enterprise"}
VALID_STATUSES = {"active", "past_due", "canceled"}
VALID_MODULE_KEYS = {"meters", "iot", "battery"}


def _client_ip_ua(request: Request) -> tuple[str | None, str | None]:
    """Best-effort client IP + user-agent for the audit trail."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=PlatformStats)
def get_stats(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> PlatformStats:
    """Headline platform counts."""
    return PlatformStats(**admin_repo.get_platform_stats(db))


@router.get("/organizations", response_model=AdminOrganizationsResponse)
def list_organizations(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminOrganizationsResponse:
    """Every organization with member + active-building counts."""
    rows = admin_repo.list_all_organizations(db)
    items = [
        AdminOrgRow(
            id=org.id,
            name=org.name,
            slug=org.slug,
            subscription_tier=org.subscription_tier,
            subscription_status=org.subscription_status,
            country_code=org.country_code,
            is_sample=org.is_sample,
            member_count=member_count,
            building_count=building_count,
            created_at=org.created_at,
        )
        for org, member_count, building_count in rows
    ]
    return AdminOrganizationsResponse(organizations=items, total=len(items))


@router.get("/users", response_model=AdminUsersResponse)
def list_users(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUsersResponse:
    """Every user with linked auth providers + org count."""
    rows = admin_repo.list_all_users(db)
    items = [
        AdminUserRow(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            is_demo=user.is_demo,
            is_platform_admin=user.is_platform_admin,
            providers=sorted({p.provider for p in user.auth_providers}),
            org_count=org_count,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
        for user, org_count in rows
    ]
    return AdminUsersResponse(users=items, total=len(items))


@router.get("/buildings", response_model=AdminBuildingsResponse)
def list_buildings(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminBuildingsResponse:
    """Every active building with owning org + module flags."""
    buildings = admin_repo.list_all_buildings(db)
    items = [
        AdminBuildingRow(
            id=b.id,
            fabric_building_id=b.fabric_building_id,
            name=b.name,
            city=b.city,
            country_code=b.country_code,
            building_type=b.building_type,
            organization_id=b.organization_id,
            organization_name=b.organization.name,
            is_connected=b.fabric_building_id is not None,
            modules=[
                AdminBuildingModule(module_key=m.module_key, enabled=m.enabled)
                for m in b.modules
            ],
            created_at=b.created_at,
        )
        for b in buildings
    ]
    return AdminBuildingsResponse(buildings=items, total=len(items))


@router.get("/audit", response_model=AdminAuditResponse)
def list_audit(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminAuditResponse:
    """Most-recent admin actions (admin.* events) for the Activity view."""
    events = audit_repo.list_recent(db, limit=50, action_prefix="admin.")
    items = [
        AdminAuditRow(
            id=e.id,
            actor_email=e.user.email if e.user else None,
            action=e.action,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            details=e.details,
            created_at=e.created_at,
        )
        for e in events
    ]
    return AdminAuditResponse(events=items, total=len(items))


# ---------------------------------------------------------------------------
# Writes (admin mutations). Each records an audit row in the same transaction.
# router.refresh() on the client re-reads the tables.
# ---------------------------------------------------------------------------

@router.patch("/organizations/{org_id}", response_model=MutationResult)
def update_organization_subscription(
    org_id: UUID,
    body: OrgSubscriptionUpdate,
    request: Request,
    admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Set an org's subscription tier and/or status."""
    org = org_repo.get_organization(db, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")

    changed: dict = {}
    if body.subscription_tier is not None:
        if body.subscription_tier not in VALID_TIERS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid tier. Allowed: {sorted(VALID_TIERS)}",
            )
        org.subscription_tier = body.subscription_tier
        changed["subscription_tier"] = body.subscription_tier

    if body.subscription_status is not None:
        if body.subscription_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status. Allowed: {sorted(VALID_STATUSES)}",
            )
        org.subscription_status = body.subscription_status
        changed["subscription_status"] = body.subscription_status

    ip, ua = _client_ip_ua(request)
    audit_repo.record_event(
        db,
        user_id=admin.id,
        organization_id=org.id,
        action="admin.org.subscription_updated",
        entity_type="organization",
        entity_id=str(org_id),
        details=changed,
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult()


@router.patch("/buildings/{building_id}/modules", response_model=MutationResult)
def update_building_module(
    building_id: UUID,
    body: BuildingModuleUpdate,
    request: Request,
    admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Enable/disable a module for a building (unlocks the matching report)."""
    if body.module_key not in VALID_MODULE_KEYS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid module_key. Allowed: {sorted(VALID_MODULE_KEYS)}",
        )
    building = admin_repo.get_building_by_id(db, building_id)
    if building is None:
        raise HTTPException(status_code=404, detail="Building not found")

    admin_repo.upsert_building_module(
        db,
        building_id=building_id,
        module_key=body.module_key,
        enabled=body.enabled,
    )
    ip, ua = _client_ip_ua(request)
    audit_repo.record_event(
        db,
        user_id=admin.id,
        organization_id=building.organization_id,
        action="admin.building.module_updated",
        entity_type="building",
        entity_id=str(building_id),
        details={"module_key": body.module_key, "enabled": body.enabled},
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult()


@router.patch("/buildings/{building_id}", response_model=MutationResult)
def update_building_fabric_id(
    building_id: UUID,
    body: BuildingFabricUpdate,
    request: Request,
    admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Link (or clear) a building's fabric_building_id. Empty -> NULL."""
    building = admin_repo.get_building_by_id(db, building_id)
    if building is None:
        raise HTTPException(status_code=404, detail="Building not found")

    fabric = (body.fabric_building_id or "").strip() or None
    if fabric is not None and admin_repo.fabric_id_in_use(
        db, fabric_building_id=fabric, exclude_building_id=building_id
    ):
        raise HTTPException(
            status_code=409,
            detail=f"fabric_building_id '{fabric}' is already in use",
        )

    building.fabric_building_id = fabric
    ip, ua = _client_ip_ua(request)
    audit_repo.record_event(
        db,
        user_id=admin.id,
        organization_id=building.organization_id,
        action="admin.building.fabric_linked",
        entity_type="building",
        entity_id=str(building_id),
        details={"fabric_building_id": fabric},
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult()


# ---------------------------------------------------------------------------
# Bridge requests (self-serve Fabric bridging -- Access Layer 3, Phase 3.1).
# The founder's review queue: customers file requests on pending buildings; the
# founder reviews the readiness snapshot, runs the pipeline + links the fabric_id
# (the existing PATCH /buildings/{id}), then marks the request fulfilled here.
# ---------------------------------------------------------------------------

VALID_BRIDGE_STATUSES = {"approved", "rejected", "fulfilled"}


@router.get("/bridge-requests", response_model=AdminBridgeRequestsResponse)
def list_bridge_requests(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminBridgeRequestsResponse:
    """Cross-org bridge-request queue (pending first, then newest)."""
    rows = bridge_repo.list_all(db, limit=200)
    items = [
        AdminBridgeRequestRow(
            id=req.id,
            building_id=req.building_id,
            building_name=building_name,
            fabric_building_id=fabric_building_id,
            organization_id=req.organization_id,
            organization_name=organization_name,
            requested_by_email=requester_email,
            status=req.status,
            target_tier=req.target_tier,
            note=req.note,
            readiness=req.readiness,
            created_at=req.created_at,
            resolved_at=req.resolved_at,
            resolution_note=req.resolution_note,
        )
        for req, building_name, fabric_building_id, organization_name, requester_email in rows
    ]
    return AdminBridgeRequestsResponse(requests=items, total=len(items))


@router.patch("/bridge-requests/{request_id}", response_model=MutationResult)
def resolve_bridge_request(
    request_id: UUID,
    body: AdminBridgeResolve,
    request: Request,
    admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Approve / reject / fulfil a bridge request.

    Records the founder's decision. If `fabric_building_id` is supplied, the
    building is linked to Fabric in the SAME action ("Fulfil & go live"); else the
    link can still be set separately via PATCH /buildings/{id}. Phase 3.2 will
    automate the pipeline run under this same row.
    """
    if body.status not in VALID_BRIDGE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed: {sorted(VALID_BRIDGE_STATUSES)}",
        )
    req = bridge_repo.get_by_id(db, request_id=request_id)
    if req is None:
        raise HTTPException(status_code=404, detail="Bridge request not found")

    ip, ua = _client_ip_ua(request)

    # Optionally link the building to Fabric in the same action ("Fulfil & go
    # live") — saves the founder hopping to the Buildings table to set the id.
    fabric = (body.fabric_building_id or "").strip() or None
    if fabric is not None:
        building = admin_repo.get_building_by_id(db, req.building_id)
        if building is None:
            raise HTTPException(status_code=404, detail="Building not found")
        if admin_repo.fabric_id_in_use(
            db, fabric_building_id=fabric, exclude_building_id=req.building_id
        ):
            raise HTTPException(
                status_code=409,
                detail=f"fabric_building_id '{fabric}' is already in use",
            )
        building.fabric_building_id = fabric
        audit_repo.record_event(
            db,
            user_id=admin.id,
            organization_id=req.organization_id,
            action="admin.building.fabric_linked",
            entity_type="building",
            entity_id=str(req.building_id),
            details={"fabric_building_id": fabric, "via": "bridge_request"},
            ip_address=ip,
            user_agent=ua,
        )

    req.status = body.status
    req.resolved_by = admin.id
    req.resolved_at = datetime.now(dt_timezone.utc)
    req.resolution_note = body.resolution_note
    audit_repo.record_event(
        db,
        user_id=admin.id,
        organization_id=req.organization_id,
        action="admin.bridge.resolved",
        entity_type="building",
        entity_id=str(req.building_id),
        details={"request_id": str(req.id), "status": body.status},
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult()


@router.post(
    "/bridge-requests/{request_id}/automate",
    response_model=AutomatedBridgeResult,
)
def automate_bridge_request(
    request_id: UUID,
    body: AdminBridgeAutomate,
    request: Request,
    admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AutomatedBridgeResult:
    """Phase 3.2 — run the automated Fabric bridge for a request ("armed one-click").

    The orchestrator lands the building's baseline in OneLake, runs the
    parameterised notebook, refreshes the model, and links the fabric_building_id
    — all under the founder's click. `dry_run=true` simulates the plan with no
    Fabric calls (€0, no capacity). When automation is disabled server-side, this
    returns ok=False + automation_enabled=False so the UI points back at the
    manual "Fulfil & go live".
    """
    ip, ua = _client_ip_ua(request)
    try:
        result = bridge_orchestrator.run_automated_bridge(
            db,
            request_id=request_id,
            admin_id=admin.id,
            fabric_building_id_override=body.fabric_building_id,
            dry_run=body.dry_run,
            ip=ip,
            ua=ua,
        )
    except bridge_orchestrator.BridgeDisabled as e:
        return AutomatedBridgeResult(
            ok=False, dry_run=body.dry_run, error=str(e),
            failed_step="disabled", steps=[], automation_enabled=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return AutomatedBridgeResult(
        ok=result["ok"],
        dry_run=result["dry_run"],
        fabric_building_id=result.get("fabric_building_id"),
        failed_step=result.get("failed_step"),
        error=result.get("error"),
        steps=[
            {"step": s["step"], "status": s["status"], "message": s.get("message")}
            for s in result.get("steps", [])
        ],
        automation_enabled=bridge_orchestrator.automation_enabled(),
    )


# =====================================================================
# Pilot requests (public lead capture) — founder queue
# =====================================================================

VALID_PILOT_STATUSES = {"new", "contacted", "qualified", "closed"}


@router.get("/pilot-requests", response_model=AdminPilotRequestsResponse)
def list_pilot_requests(
    _admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminPilotRequestsResponse:
    """Public pilot-request leads (new first, then newest)."""
    rows = pilot_repo.list_all(db, limit=200)
    items = [
        AdminPilotRequestRow(
            id=r.id,
            name=r.name,
            email=r.email,
            organization=r.organization,
            country_code=r.country_code,
            building_count=r.building_count,
            message=r.message,
            source=r.source,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return AdminPilotRequestsResponse(requests=items, total=len(items))


@router.patch("/pilot-requests/{request_id}", response_model=MutationResult)
def resolve_pilot_request(
    request_id: UUID,
    body: AdminPilotResolve,
    request: Request,
    admin: Annotated[User, Depends(get_current_platform_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Move a pilot lead along the pipeline (new → contacted → qualified → closed)."""
    if body.status not in VALID_PILOT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed: {sorted(VALID_PILOT_STATUSES)}",
        )
    row = pilot_repo.get_by_id(db, request_id=request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Pilot request not found")
    row.status = body.status
    ip, ua = _client_ip_ua(request)
    audit_repo.record_event(
        db,
        user_id=admin.id,
        organization_id=None,
        action="admin.pilot.resolved",
        entity_type="pilot_request",
        entity_id=str(row.id),
        details={"status": body.status},
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult()
