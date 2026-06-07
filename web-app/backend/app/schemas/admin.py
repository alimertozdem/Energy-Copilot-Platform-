"""Pydantic DTOs for the platform admin endpoints (/admin/*).

DTOs are built explicitly in the router from repository rows (not from_attributes)
so the cross-org reads stay obvious and the wire shape is decoupled from the ORM.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PlatformStats(BaseModel):
    organizations_total: int
    organizations_sample: int
    users_total: int
    users_demo: int
    buildings_total: int
    buildings_connected: int
    iot_enabled: int
    battery_enabled: int


class AdminOrgRow(BaseModel):
    id: UUID
    name: str
    slug: str
    subscription_tier: str
    subscription_status: str
    country_code: str | None
    is_sample: bool
    member_count: int
    building_count: int
    created_at: datetime


class AdminOrganizationsResponse(BaseModel):
    organizations: list[AdminOrgRow]
    total: int


class AdminUserRow(BaseModel):
    id: UUID
    email: str
    display_name: str | None
    is_active: bool
    is_demo: bool
    is_platform_admin: bool
    providers: list[str]
    org_count: int
    last_login_at: datetime | None
    created_at: datetime


class AdminUsersResponse(BaseModel):
    users: list[AdminUserRow]
    total: int


class AdminBuildingModule(BaseModel):
    module_key: str
    enabled: bool


class AdminBuildingRow(BaseModel):
    id: UUID
    fabric_building_id: str | None
    name: str
    city: str | None
    country_code: str | None
    building_type: str | None
    organization_id: UUID
    organization_name: str
    is_connected: bool
    modules: list[AdminBuildingModule]
    created_at: datetime


class AdminBuildingsResponse(BaseModel):
    buildings: list[AdminBuildingRow]
    total: int


# --- Mutation request bodies (admin-only writes) ---


class OrgSubscriptionUpdate(BaseModel):
    subscription_tier: str | None = None
    subscription_status: str | None = None


class BuildingModuleUpdate(BaseModel):
    module_key: str
    enabled: bool


class BuildingFabricUpdate(BaseModel):
    fabric_building_id: str | None = None


class MutationResult(BaseModel):
    ok: bool = True


# --- Audit / activity (admin read) ---


class AdminAuditRow(BaseModel):
    id: UUID
    actor_email: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    details: dict | None
    created_at: datetime


class AdminAuditResponse(BaseModel):
    events: list[AdminAuditRow]
    total: int
