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


# ---------------------------------------------------------------------------
# Multi-client overview (consultant cockpit) -- metadata-only EPBD/MEPS triage
# ---------------------------------------------------------------------------

class PartnerClientOverviewRow(BaseModel):
    """Per-client rollup across the buildings the partner can see for that client.

    EPC-based triage (regulation, not invented): EPBD MEPS targets the worst
    performers first (G by 2030, F by 2033), so F/G = high risk; a missing EPC
    is an assessment gap. EUI/CRREM detail lives in the client's portfolio drill-in.
    """

    organization_id: UUID
    name: str
    slug: str
    scope: str
    building_count: int
    total_area_m2: float
    epc_high_risk: int   # EPC F or G
    epc_missing: int     # no EPC on file
    epc_on_track: int    # has EPC, not F/G
    attention: int       # high_risk + missing


class PartnerOverviewTotals(BaseModel):
    client_count: int
    building_count: int
    total_area_m2: float
    epc_high_risk: int
    epc_missing: int


class PartnerOverviewResponse(BaseModel):
    clients: list[PartnerClientOverviewRow]
    totals: PartnerOverviewTotals


class OrgLookupResponse(BaseModel):
    """Resolve a client workspace slug -> org id + name (partner invite helper)."""

    organization_id: UUID
    name: str
    slug: str
