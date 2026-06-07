"""Pydantic schemas for the partner (consultant) layer endpoints (/partners/*)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PartnerLinkCreate(BaseModel):
    client_org_id: UUID
    scope: str = "read_only"  # read_only | full_manage
    commission_model: dict | None = None


class PartnerLinkRow(BaseModel):
    id: UUID
    partner_org_id: UUID
    client_org_id: UUID
    # The OTHER side's org name (client name in a partner's view; partner name in a client's).
    counterparty_org_name: str
    relationship_status: str
    scope: str
    client_consent_at: datetime | None = None
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime


class PartnerLinksResponse(BaseModel):
    links: list[PartnerLinkRow]
    total: int


class PartnerClientRow(BaseModel):
    organization_id: UUID
    name: str
    slug: str
    scope: str


class PartnerClientsResponse(BaseModel):
    clients: list[PartnerClientRow]
    total: int


class MutationResult(BaseModel):
    ok: bool = True
    id: UUID | None = None
