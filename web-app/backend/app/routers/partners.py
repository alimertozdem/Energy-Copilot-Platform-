"""Partner (consultant) layer router -- /partners/*.

A partner organization (``org_type='partner'``) manages client organizations through
delegated, revocable ``PartnerClientLink`` grants:

  POST  /partners/links               partner admin invites a client   (-> pending)
  POST  /partners/links/{id}/accept   client admin consents            (-> active)
  POST  /partners/links/{id}/revoke   either side's admin revokes      (-> revoked)
  GET   /partners/links               links from the caller-org perspective
  GET   /partners/clients             active clients the caller manages (the switcher)

Every mutation records a ``partner.*`` AuditLog row in the SAME transaction. Read
visibility of client buildings is enforced centrally (see
``repositories.building._visible_org_filter``); these endpoints manage the *grants*.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.repositories import audit as audit_repo
from app.repositories import organization as org_repo
from app.repositories import partner as partner_repo
from app.schemas.partner import (
    MutationResult,
    PartnerClientRow,
    PartnerClientsResponse,
    PartnerLinkCreate,
    PartnerLinkRow,
    PartnerLinksResponse,
)
from app.utils.jwt import get_current_org_id, get_current_user

router = APIRouter(prefix="/partners", tags=["partners"])

VALID_SCOPES = {"read_only", "full_manage"}


def _client_ip_ua(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


def _require_org_admin(db: Session, *, org_id: UUID, user: User) -> None:
    """403 unless ``user`` is an admin member of ``org_id``."""
    m = org_repo.get_membership(db, org_id=org_id, user_id=user.id)
    if m is None or m.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization admin access required",
        )


def _row(link, counterparty_org) -> PartnerLinkRow:
    return PartnerLinkRow(
        id=link.id,
        partner_org_id=link.partner_org_id,
        client_org_id=link.client_org_id,
        counterparty_org_name=counterparty_org.name,
        relationship_status=link.relationship_status,
        scope=link.scope,
        client_consent_at=link.client_consent_at,
        granted_at=link.granted_at,
        revoked_at=link.revoked_at,
        created_at=link.created_at,
    )


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

@router.post("/links", response_model=MutationResult)
def create_link(
    body: PartnerLinkCreate,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    partner_org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Partner admin invites a client org. The caller's active org is the partner."""
    if body.scope not in VALID_SCOPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid scope")
    if body.client_org_id == partner_org_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "A partner cannot link to itself"
        )

    partner_org = org_repo.get_organization(db, partner_org_id)
    if partner_org is None or partner_org.org_type != "partner":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only a partner organization can invite clients"
        )
    _require_org_admin(db, org_id=partner_org_id, user=user)

    if org_repo.get_organization(db, body.client_org_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client organization not found")

    if partner_repo.get_live_link(
        db, partner_org_id=partner_org_id, client_org_id=body.client_org_id
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A live link to this client already exists"
        )

    link = partner_repo.create_link(
        db,
        partner_org_id=partner_org_id,
        client_org_id=body.client_org_id,
        invited_by_user_id=user.id,
        scope=body.scope,
        commission_model=body.commission_model,
    )
    ip, ua = _client_ip_ua(request)
    audit_repo.record_event(
        db,
        user_id=user.id,
        organization_id=partner_org_id,
        action="partner.link_invited",
        entity_type="partner_client_link",
        entity_id=str(link.id),
        details={"client_org_id": str(body.client_org_id), "scope": body.scope},
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult(ok=True, id=link.id)


@router.post("/links/{link_id}/accept", response_model=MutationResult)
def accept_link(
    link_id: UUID,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Client admin consents to a pending invite (-> active). DSGVO: the controller
    (client) authorises the processor (partner)."""
    link = partner_repo.get_link(db, link_id)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
    if link.relationship_status != "pending":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Link is '{link.relationship_status}', not pending",
        )
    # Only an admin of the CLIENT org may consent.
    _require_org_admin(db, org_id=link.client_org_id, user=user)

    partner_repo.accept_link(db, link)
    ip, ua = _client_ip_ua(request)
    audit_repo.record_event(
        db,
        user_id=user.id,
        organization_id=link.client_org_id,
        action="partner.link_accepted",
        entity_type="partner_client_link",
        entity_id=str(link.id),
        details={"partner_org_id": str(link.partner_org_id), "scope": link.scope},
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult(ok=True, id=link.id)


@router.post("/links/{link_id}/revoke", response_model=MutationResult)
def revoke_link(
    link_id: UUID,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MutationResult:
    """Revoke a link. Either side's admin may revoke; access stops on the next resolve."""
    link = partner_repo.get_link(db, link_id)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
    if link.revoked_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Link is already revoked")

    partner_m = org_repo.get_membership(db, org_id=link.partner_org_id, user_id=user.id)
    client_m = org_repo.get_membership(db, org_id=link.client_org_id, user_id=user.id)
    is_partner_admin = partner_m is not None and partner_m.role == "admin"
    is_client_admin = client_m is not None and client_m.role == "admin"
    if not (is_partner_admin or is_client_admin):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only an admin of either org may revoke"
        )
    acting_org_id = link.partner_org_id if is_partner_admin else link.client_org_id

    partner_repo.revoke_link(db, link)
    ip, ua = _client_ip_ua(request)
    audit_repo.record_event(
        db,
        user_id=user.id,
        organization_id=acting_org_id,
        action="partner.link_revoked",
        entity_type="partner_client_link",
        entity_id=str(link.id),
        details={
            "partner_org_id": str(link.partner_org_id),
            "client_org_id": str(link.client_org_id),
            "revoked_by": "partner" if is_partner_admin else "client",
        },
        ip_address=ip,
        user_agent=ua,
    )
    db.commit()
    return MutationResult(ok=True, id=link.id)


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

@router.get("/links", response_model=PartnerLinksResponse)
def list_links(
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerLinksResponse:
    """All links touching the caller's active org -- both as partner and as client."""
    as_partner = partner_repo.list_for_partner(db, partner_org_id=org_id)
    as_client = partner_repo.list_for_client(db, client_org_id=org_id)
    rows = [_row(link, client_org) for link, client_org in as_partner]
    rows += [_row(link, partner_org) for link, partner_org in as_client]
    rows.sort(key=lambda r: r.created_at, reverse=True)
    return PartnerLinksResponse(links=rows, total=len(rows))


@router.get("/clients", response_model=PartnerClientsResponse)
def list_clients(
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    db: Annotated[Session, Depends(get_db)],
) -> PartnerClientsResponse:
    """Active client orgs the caller's partner org manages -- powers the client switcher."""
    rows = partner_repo.list_for_partner(db, partner_org_id=org_id)
    clients = [
        PartnerClientRow(
            organization_id=org.id, name=org.name, slug=org.slug, scope=link.scope
        )
        for link, org in rows
        if link.relationship_status == "active" and link.revoked_at is None
    ]
    return PartnerClientsResponse(clients=clients, total=len(clients))
