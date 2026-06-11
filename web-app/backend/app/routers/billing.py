"""Billing router -- Stripe self-serve subscriptions.

  POST /billing/checkout  {tier}  -> {url}   (auth + org admin; Stripe Checkout)
  POST /billing/portal             -> {url}  (auth + org admin; Customer Portal)
  POST /billing/webhook                       (no auth; Stripe signature verified)

Checkout / portal are org-admin only (an org admin has "full access incl.
billing"). The webhook is unauthenticated but signature-verified; it updates
org.subscription_tier / status from Stripe subscription events. All Stripe work
lives in services/billing.py; this router is thin (auth + HTTP shapes).
"""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.db.models.organization import OrgMember, Organization
from app.services import billing
from app.utils.jwt import get_current_org_id, get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])

logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    tier: str
    period: str = "monthly"


class UrlResponse(BaseModel):
    url: str


def _require_org_admin(db: Session, org_id: UUID, user_id: UUID) -> Organization:
    """Load the org and assert the user is an admin of it (mirrors /settings)."""
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    member = db.scalar(
        select(OrgMember).where(
            OrgMember.organization_id == org_id,
            OrgMember.user_id == user_id,
        )
    )
    if member is None or member.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Billing requires the org admin role.",
        )
    return org


@router.post("/checkout", response_model=UrlResponse)
def create_checkout(
    body: CheckoutRequest,
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UrlResponse:
    """Start a Stripe Checkout session for a self-serve tier; return its URL."""
    if not billing.is_configured():
        raise HTTPException(status_code=503, detail="Billing is not configured")
    org = _require_org_admin(db, org_id, user.id)
    try:
        url = billing.create_checkout_session(
            db, org, tier=body.tier, email=user.email, period=body.period
        )
    except billing.BillingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UrlResponse(url=url)


@router.post("/portal", response_model=UrlResponse)
def create_portal(
    org_id: Annotated[UUID, Depends(get_current_org_id)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UrlResponse:
    """Open the Stripe Customer Portal (manage / cancel); return its URL."""
    if not billing.is_configured():
        raise HTTPException(status_code=503, detail="Billing is not configured")
    org = _require_org_admin(db, org_id, user.id)
    try:
        url = billing.create_portal_session(db, org)
    except billing.BillingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UrlResponse(url=url)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Stripe webhook: verify signature, then sync subscription -> org tier.

    Unauthenticated (Stripe calls it server-to-server) but the signature is
    verified against STRIPE_WEBHOOK_SECRET, so only Stripe can drive it.
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = billing.construct_event(payload, sig)
    except billing.BillingError as exc:
        logger.error("Stripe webhook not configured: %s", exc)
        raise HTTPException(status_code=503, detail="Billing not configured")
    except Exception as exc:  # signature mismatch / malformed payload
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        billing.handle_event(db, event)
    except Exception:
        # Return 500 so Stripe retries transient failures; logged loudly so a
        # persistent bug is visible (no silent except).
        logger.exception("Stripe webhook handling failed")
        raise HTTPException(status_code=500, detail="Webhook handling error")

    return {"received": True}
