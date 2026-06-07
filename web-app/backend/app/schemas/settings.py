"""Pydantic schemas for the /settings (organization management) endpoints.

Mirror the TypeScript types in frontend/lib/api/settings.ts. Three concerns:
  * Organization profile (name, billing, tier -- tier is read-only in V1)
  * Members (existing OrgMember rows + their user)
  * Pending invitations (OrgInvitation rows the admin can copy/revoke)
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

OrgRole = Literal["admin", "manager", "viewer"]
InviteRole = Literal["manager", "viewer"]
SubscriptionTier = Literal["free", "basic", "monitor", "enterprise"]


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class OrganizationProfile(BaseModel):
    id: UUID
    name: str
    slug: str
    billing_email: Optional[str] = None
    country_code: Optional[str] = None
    subscription_tier: str
    subscription_status: str
    is_sample: bool


class OrgMemberItem(BaseModel):
    user_id: UUID
    email: str
    display_name: Optional[str] = None
    role: OrgRole
    # invitation_accepted_at IS NULL -> still pending acceptance.
    is_pending: bool
    joined_at: Optional[datetime] = None
    # True for the row representing the requesting user (UI hides self-remove).
    is_self: bool = False


class PendingInviteItem(BaseModel):
    id: UUID
    email: str
    role: InviteRole
    status: str
    # The capability token -- admin copies /invite/{token} to share.
    token: str
    invited_by_email: Optional[str] = None
    expires_at: datetime
    created_at: datetime


class OrgSettingsResponse(BaseModel):
    organization: OrganizationProfile
    members: list[OrgMemberItem]
    # Only populated for admins (token is sensitive). Empty for non-admins.
    pending_invites: list[PendingInviteItem]
    current_user_role: OrgRole
    # current_user_role == "admin"
    can_manage: bool


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

class OrgUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    billing_email: Optional[str] = Field(default=None, max_length=255)
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)


class MemberInviteRequest(BaseModel):
    email: EmailStr
    role: InviteRole = "viewer"


class MemberRoleUpdateRequest(BaseModel):
    role: OrgRole


# ---------------------------------------------------------------------------
# Mutation responses
# ---------------------------------------------------------------------------

class MemberInviteResponse(BaseModel):
    invite: PendingInviteItem
    # Relative path the admin shares, e.g. "/invite/AbC123...".
    invite_path: str


class SimpleOkResponse(BaseModel):
    ok: bool = True


# ---------------------------------------------------------------------------
# Public invitation preview (the /invite/{token} landing page)
# ---------------------------------------------------------------------------

class InvitationPreview(BaseModel):
    """Safe, minimal view of an invitation for the accept landing page.

    Never exposes the inviting org's members or other sensitive data --
    only what's needed to render "You've been invited to {org} as {role}".
    """
    organization_name: str
    role: InviteRole
    email: str
    status: str
    is_valid: bool
    expires_at: datetime


class InvitationAcceptResponse(BaseModel):
    ok: bool
    organization_id: UUID
    organization_slug: str
    role: OrgRole


class SettingsActivityRow(BaseModel):
    id: UUID
    actor_email: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    details: dict | None
    created_at: datetime


class SettingsActivityResponse(BaseModel):
    events: list[SettingsActivityRow]
    total: int
