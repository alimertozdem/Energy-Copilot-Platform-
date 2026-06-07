"""Settings router -- organization profile, members, and invitations.

All /settings/organization* endpoints are JWT-protected and scoped to the
org carried in the token (get_current_org_id). The invitation *preview* is
public (the /invite landing page may render while signed out); accepting an
invitation requires auth.

The service raises SettingsError(status_code, detail); each endpoint maps it
to an HTTPException with the same status + message.

Audit: each successful mutation records an AuditLog row via _safe_audit -- a
best-effort, post-commit write (the service owns the main transaction). The
org-scoped Activity feed (GET /settings/activity) surfaces these to admins.
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import audit as audit_repo
from app.repositories import organization as org_repo
from app.schemas.settings import (
    InvitationAcceptResponse,
    InvitationPreview,
    MemberInviteRequest,
    MemberInviteResponse,
    MemberRoleUpdateRequest,
    OrganizationProfile,
    OrgMemberItem,
    OrgSettingsResponse,
    OrgUpdateRequest,
    SettingsActivityResponse,
    SettingsActivityRow,
    SimpleOkResponse,
)
from app.services import settings_data
from app.services.settings_data import SettingsError
from app.utils.jwt import get_current_org_id, get_current_user_id

router = APIRouter(prefix="/settings", tags=["settings"])

logger = logging.getLogger(__name__)


def _safe_audit(
    db: Session,
    request: Request,
    *,
    user_id: UUID,
    organization_id: UUID,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict | None = None,
) -> None:
    """Best-effort audit write AFTER the mutation already committed.

    The settings service owns its own transaction + commit, so this records the
    audit row in a SEPARATE commit. A failure here must never surface to the
    client (the action already succeeded), so we log + roll back the audit row
    only.
    """
    try:
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        audit_repo.record_event(
            db,
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip,
            user_agent=ua,
        )
        db.commit()
    except Exception:
        logger.exception("Audit write failed for action=%s", action)
        db.rollback()


# ---- Organization profile + members (admin-gated in the service) ----

@router.get("/organization", response_model=OrgSettingsResponse)
def get_settings(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> OrgSettingsResponse:
    try:
        return settings_data.get_org_settings(db, user_id=user_id, org_id=org_id)
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/activity", response_model=SettingsActivityResponse)
def get_activity(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> SettingsActivityResponse:
    """Recent organization activity (audit log). Admin-only -- it's management
    information (who changed what)."""
    membership = org_repo.get_membership(db, org_id=org_id, user_id=user_id)
    if membership is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if membership.role != "admin":
        raise HTTPException(
            status_code=403, detail="This action requires the admin role."
        )
    events = audit_repo.list_for_org(db, org_id, limit=50)
    items = [
        SettingsActivityRow(
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
    return SettingsActivityResponse(events=items, total=len(items))


@router.patch("/organization", response_model=OrganizationProfile)
def patch_organization(
    body: OrgUpdateRequest,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> OrganizationProfile:
    try:
        result = settings_data.update_org(
            db,
            user_id=user_id,
            org_id=org_id,
            name=body.name,
            billing_email=body.billing_email,
            country_code=body.country_code,
        )
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    details = {
        k: v
        for k, v in {
            "name": body.name,
            "billing_email": body.billing_email,
            "country_code": body.country_code,
        }.items()
        if v is not None
    }
    _safe_audit(
        db,
        request,
        user_id=user_id,
        organization_id=org_id,
        action="org.profile_updated",
        entity_type="organization",
        entity_id=str(org_id),
        details=details,
    )
    return result


@router.post(
    "/organization/members/invite", response_model=MemberInviteResponse
)
def invite_member(
    body: MemberInviteRequest,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> MemberInviteResponse:
    try:
        result = settings_data.invite_member(
            db,
            user_id=user_id,
            org_id=org_id,
            email=str(body.email),
            role=body.role,
        )
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    _safe_audit(
        db,
        request,
        user_id=user_id,
        organization_id=org_id,
        action="org_member.invited",
        entity_type="invitation",
        entity_id=str(result.invite.id),
        details={"email": result.invite.email, "role": result.invite.role},
    )
    return result


@router.patch(
    "/organization/members/{target_user_id}", response_model=OrgMemberItem
)
def change_member_role(
    target_user_id: UUID,
    body: MemberRoleUpdateRequest,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> OrgMemberItem:
    try:
        result = settings_data.change_member_role(
            db,
            user_id=user_id,
            org_id=org_id,
            target_user_id=target_user_id,
            new_role=body.role,
        )
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    _safe_audit(
        db,
        request,
        user_id=user_id,
        organization_id=org_id,
        action="org_member.role_changed",
        entity_type="user",
        entity_id=str(target_user_id),
        details={"role": body.role},
    )
    return result


@router.delete(
    "/organization/members/{target_user_id}", response_model=SimpleOkResponse
)
def remove_member(
    target_user_id: UUID,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> SimpleOkResponse:
    try:
        settings_data.remove_member(
            db, user_id=user_id, org_id=org_id, target_user_id=target_user_id
        )
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    _safe_audit(
        db,
        request,
        user_id=user_id,
        organization_id=org_id,
        action="org_member.removed",
        entity_type="user",
        entity_id=str(target_user_id),
    )
    return SimpleOkResponse()


@router.delete(
    "/organization/invites/{invite_id}", response_model=SimpleOkResponse
)
def revoke_invite(
    invite_id: UUID,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> SimpleOkResponse:
    try:
        settings_data.revoke_invitation(
            db, user_id=user_id, org_id=org_id, invite_id=invite_id
        )
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    _safe_audit(
        db,
        request,
        user_id=user_id,
        organization_id=org_id,
        action="org_member.invite_revoked",
        entity_type="invitation",
        entity_id=str(invite_id),
    )
    return SimpleOkResponse()


# ---- Invitation preview (public) + accept (auth) ----

@router.get("/invitations/{token}", response_model=InvitationPreview)
def preview_invitation(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> InvitationPreview:
    """Public -- the /invite landing page may render while signed out."""
    try:
        return settings_data.get_invitation_preview(db, token=token)
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/invitations/{token}/accept", response_model=InvitationAcceptResponse
)
def accept_invitation(
    token: str,
    request: Request,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationAcceptResponse:
    try:
        result = settings_data.accept_invitation(db, user_id=user_id, token=token)
    except SettingsError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    _safe_audit(
        db,
        request,
        user_id=user_id,
        organization_id=result.organization_id,
        action="org_member.joined",
        entity_type="user",
        entity_id=str(user_id),
        details={"role": result.role},
    )
    return result
