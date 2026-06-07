"""Settings service -- organization profile, members, and invitations.

Authorization model:
  * Reading settings: any member of the org (viewer included).
  * Mutations (profile edit, invite, role change, remove, revoke): admin only.
  * Last-admin guard: an org must always keep >=1 admin, so the last admin
    cannot be demoted or removed.

The service is HTTP-agnostic. It raises SettingsError(status_code, detail);
the router maps that to an HTTPException in one place.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import OrgInvitation, OrgMember, Organization, User
from app.repositories import invitation as invite_repo
from app.repositories import organization as org_repo
from app.repositories import user as user_repo
from app.schemas.settings import (
    InvitationAcceptResponse,
    InvitationPreview,
    MemberInviteResponse,
    OrganizationProfile,
    OrgMemberItem,
    OrgSettingsResponse,
    PendingInviteItem,
)

INVITE_EXPIRY_DAYS = 7
INVITE_TOKEN_BYTES = 32  # secrets.token_urlsafe(32) -> ~43 url-safe chars


class SettingsError(Exception):
    """Domain error carrying an HTTP status + a client-safe detail message."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_membership(
    db: Session, *, org_id: UUID, user_id: UUID
) -> OrgMember:
    """The user's membership in the org, or 404.

    404 (not 403) for non-members so org existence isn't leaked.
    """
    m = org_repo.get_membership(db, org_id=org_id, user_id=user_id)
    if m is None:
        raise SettingsError(404, "Organization not found")
    return m


def _require_admin(db: Session, *, org_id: UUID, user_id: UUID) -> OrgMember:
    m = _require_membership(db, org_id=org_id, user_id=user_id)
    if m.role != "admin":
        raise SettingsError(403, "This action requires the admin role.")
    return m


def _is_expired(inv: OrgInvitation) -> bool:
    exp = inv.expires_at
    if exp.tzinfo is None:  # defensive -- stored tz-aware
        exp = exp.replace(tzinfo=timezone.utc)
    return exp < _now()


def _org_profile(org: Organization) -> OrganizationProfile:
    return OrganizationProfile(
        id=org.id,
        name=org.name,
        slug=org.slug,
        billing_email=org.billing_email,
        country_code=org.country_code,
        subscription_tier=org.subscription_tier,
        subscription_status=org.subscription_status,
        is_sample=org.is_sample,
    )


def _member_item(m: OrgMember, *, current_user_id: UUID) -> OrgMemberItem:
    user: User | None = m.user
    return OrgMemberItem(
        user_id=m.user_id,
        email=user.email if user else "(unknown)",
        display_name=user.display_name if user else None,
        role=m.role,  # type: ignore[arg-type]
        is_pending=m.invitation_accepted_at is None,
        joined_at=m.invitation_accepted_at,
        is_self=(m.user_id == current_user_id),
    )


def _invite_item(inv: OrgInvitation) -> PendingInviteItem:
    return PendingInviteItem(
        id=inv.id,
        email=inv.email,
        role=inv.role,  # type: ignore[arg-type]
        status=inv.status,
        token=inv.token,
        invited_by_email=(inv.invited_by.email if inv.invited_by else None),
        expires_at=inv.expires_at,
        created_at=inv.created_at,
    )


# ---------------------------------------------------------------------------
# GET /settings/organization
# ---------------------------------------------------------------------------

def get_org_settings(
    db: Session, *, user_id: UUID, org_id: UUID
) -> OrgSettingsResponse:
    membership = _require_membership(db, org_id=org_id, user_id=user_id)
    org = org_repo.get_organization(db, org_id)
    if org is None:
        raise SettingsError(404, "Organization not found")

    members = [
        _member_item(m, current_user_id=user_id)
        for m in org_repo.list_members(db, org_id)
    ]

    can_manage = membership.role == "admin"
    pending: list[PendingInviteItem] = []
    if can_manage:
        # Lazily flip expired pending invitations so the list stays honest.
        changed = False
        for inv in invite_repo.list_pending_invitations(db, org_id):
            if _is_expired(inv):
                invite_repo.mark_status(db, inv, "expired")
                changed = True
                continue
            pending.append(_invite_item(inv))
        if changed:
            db.commit()

    return OrgSettingsResponse(
        organization=_org_profile(org),
        members=members,
        pending_invites=pending,
        current_user_role=membership.role,  # type: ignore[arg-type]
        can_manage=can_manage,
    )


# ---------------------------------------------------------------------------
# PATCH /settings/organization
# ---------------------------------------------------------------------------

def update_org(
    db: Session,
    *,
    user_id: UUID,
    org_id: UUID,
    name: str | None,
    billing_email: str | None,
    country_code: str | None,
) -> OrganizationProfile:
    _require_admin(db, org_id=org_id, user_id=user_id)
    org = org_repo.get_organization(db, org_id)
    if org is None:
        raise SettingsError(404, "Organization not found")
    if org.is_sample:
        raise SettingsError(403, "The shared sample organization is read-only.")

    org_repo.update_organization_fields(
        db,
        org,
        name=name,
        billing_email=billing_email,
        country_code=country_code,
    )
    db.commit()
    db.refresh(org)
    return _org_profile(org)


# ---------------------------------------------------------------------------
# POST /settings/organization/members/invite
# ---------------------------------------------------------------------------

def invite_member(
    db: Session,
    *,
    user_id: UUID,
    org_id: UUID,
    email: str,
    role: str,
) -> MemberInviteResponse:
    _require_admin(db, org_id=org_id, user_id=user_id)
    if role not in ("manager", "viewer"):
        raise SettingsError(422, "Invite role must be manager or viewer.")

    email_norm = email.strip().lower()

    # Already a member? (existing user with that email + a membership row)
    existing_user = user_repo.find_user_by_email(db, email_norm)
    if existing_user is not None and org_repo.get_membership(
        db, org_id=org_id, user_id=existing_user.id
    ) is not None:
        raise SettingsError(409, "That person is already a member.")

    # Already a pending invite to that email?
    if invite_repo.find_pending_for_email(
        db, org_id=org_id, email=email_norm
    ) is not None:
        raise SettingsError(
            409, "There's already a pending invitation for that email."
        )

    token = secrets.token_urlsafe(INVITE_TOKEN_BYTES)
    inv = invite_repo.create_invitation(
        db,
        organization_id=org_id,
        email=email_norm,
        role=role,
        token=token,
        invited_by_user_id=user_id,
        expires_at=_now() + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.commit()
    db.refresh(inv)
    return MemberInviteResponse(
        invite=_invite_item(inv),
        invite_path=f"/invite/{inv.token}",
    )


# ---------------------------------------------------------------------------
# PATCH /settings/organization/members/{target_user_id}
# ---------------------------------------------------------------------------

def change_member_role(
    db: Session,
    *,
    user_id: UUID,
    org_id: UUID,
    target_user_id: UUID,
    new_role: str,
) -> OrgMemberItem:
    _require_admin(db, org_id=org_id, user_id=user_id)
    if new_role not in ("admin", "manager", "viewer"):
        raise SettingsError(422, "Invalid role.")

    target = org_repo.get_membership(db, org_id=org_id, user_id=target_user_id)
    if target is None:
        raise SettingsError(404, "Member not found.")

    # Last-admin guard: don't let the only admin be demoted.
    if (
        target.role == "admin"
        and new_role != "admin"
        and org_repo.count_admins(db, org_id) <= 1
    ):
        raise SettingsError(
            409, "Can't demote the last admin. Promote someone else first."
        )

    org_repo.set_member_role(db, target, new_role)
    db.commit()
    db.refresh(target)
    return _member_item(target, current_user_id=user_id)


# ---------------------------------------------------------------------------
# DELETE /settings/organization/members/{target_user_id}
# ---------------------------------------------------------------------------

def remove_member(
    db: Session,
    *,
    user_id: UUID,
    org_id: UUID,
    target_user_id: UUID,
) -> None:
    _require_admin(db, org_id=org_id, user_id=user_id)
    target = org_repo.get_membership(db, org_id=org_id, user_id=target_user_id)
    if target is None:
        raise SettingsError(404, "Member not found.")

    # Last-admin guard applies to removal too (covers self-removal of last admin).
    if target.role == "admin" and org_repo.count_admins(db, org_id) <= 1:
        raise SettingsError(
            409, "Can't remove the last admin. Promote someone else first."
        )

    org_repo.delete_member(db, target)
    db.commit()


# ---------------------------------------------------------------------------
# DELETE /settings/organization/invites/{invite_id}
# ---------------------------------------------------------------------------

def revoke_invitation(
    db: Session,
    *,
    user_id: UUID,
    org_id: UUID,
    invite_id: UUID,
) -> None:
    _require_admin(db, org_id=org_id, user_id=user_id)
    inv = invite_repo.get_invitation(db, invite_id)
    if inv is None or inv.organization_id != org_id:
        raise SettingsError(404, "Invitation not found.")
    if inv.status != "pending":
        raise SettingsError(409, f"Invitation is already {inv.status}.")
    invite_repo.mark_status(db, inv, "revoked")
    db.commit()


# ---------------------------------------------------------------------------
# GET /settings/invitations/{token}  (PUBLIC -- landing page preview)
# ---------------------------------------------------------------------------

def get_invitation_preview(db: Session, *, token: str) -> InvitationPreview:
    inv = invite_repo.get_by_token(db, token)
    if inv is None:
        raise SettingsError(404, "Invitation not found.")

    if inv.status == "pending" and _is_expired(inv):
        invite_repo.mark_status(db, inv, "expired")
        db.commit()

    org = inv.organization
    return InvitationPreview(
        organization_name=org.name if org else "(unknown)",
        role=inv.role,  # type: ignore[arg-type]
        email=inv.email,
        status=inv.status,
        is_valid=(inv.status == "pending" and not _is_expired(inv)),
        expires_at=inv.expires_at,
    )


# ---------------------------------------------------------------------------
# POST /settings/invitations/{token}/accept  (auth required)
# ---------------------------------------------------------------------------

def accept_invitation(
    db: Session, *, user_id: UUID, token: str
) -> InvitationAcceptResponse:
    inv = invite_repo.get_by_token(db, token)
    if inv is None:
        raise SettingsError(404, "Invitation not found.")

    if inv.status == "accepted":
        raise SettingsError(409, "This invitation has already been accepted.")
    if inv.status == "revoked":
        raise SettingsError(409, "This invitation has been revoked.")
    if inv.status == "expired" or _is_expired(inv):
        invite_repo.mark_status(db, inv, "expired")
        db.commit()
        raise SettingsError(410, "This invitation has expired.")

    org = inv.organization
    if org is None:
        raise SettingsError(404, "Organization not found.")

    # Idempotent: if the user already belongs to the org, just consume the
    # invite without creating a duplicate membership.
    existing = org_repo.get_membership(
        db, org_id=inv.organization_id, user_id=user_id
    )
    if existing is None:
        org_repo.create_org_membership(
            db,
            organization_id=inv.organization_id,
            user_id=user_id,
            role=inv.role,
            invited_by_user_id=inv.invited_by_user_id,
            accept_invitation=True,
        )
        final_role = inv.role
    else:
        final_role = existing.role

    invite_repo.mark_accepted(db, inv, user_id=user_id)
    db.commit()
    return InvitationAcceptResponse(
        ok=True,
        organization_id=inv.organization_id,
        organization_slug=org.slug,
        role=final_role,  # type: ignore[arg-type]
    )
