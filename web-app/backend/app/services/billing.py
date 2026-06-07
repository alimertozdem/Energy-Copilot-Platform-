"""Stripe self-serve billing.

Hosted Checkout + hosted Customer Portal + webhook sync. The org's
`subscription_tier` / `subscription_status` / `current_period_end` columns are
the source of truth for the rest of the app; they are kept in sync here by the
webhook (handle_event), so no Stripe call sits on a hot read path.

Tiers: free (default, no checkout) · basic + monitor (self-serve) · enterprise
(contact sales). Prices live in Stripe (price ids in env), never hardcoded.

Env (set by the operator -- see BILL-6 runbook):
  STRIPE_SECRET_KEY         sk_test_...
  STRIPE_WEBHOOK_SECRET     whsec_...
  STRIPE_PRICE_BASIC        price_...   (Basic, recurring monthly)
  STRIPE_PRICE_MONITOR      price_...   (Monitor, recurring monthly)
  STRIPE_PRICE_RESIDENTIAL  price_...   (Residential, recurring monthly; per-building base)
  BILLING_SUCCESS_URL       http://localhost:3000/settings?billing=success
  BILLING_CANCEL_URL        http://localhost:3000/settings?billing=cancel
  BILLING_PORTAL_RETURN_URL http://localhost:3000/settings
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.organization import Organization

logger = logging.getLogger(__name__)

# Tiers purchasable self-serve via Checkout (each maps to an env price id).
SELF_SERVE_TIERS: tuple[str, ...] = ("basic", "monitor", "residential")


class BillingError(Exception):
    """A billing operation cannot proceed (misconfig or invalid request)."""


def is_configured() -> bool:
    """True when a Stripe secret key is present (billing endpoints usable)."""
    return bool(os.getenv("STRIPE_SECRET_KEY"))


def _configure() -> None:
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        raise BillingError("Billing is not configured (STRIPE_SECRET_KEY missing)")
    stripe.api_key = key


def _price_id_for_tier(tier: str) -> str | None:
    return {
        "basic": os.getenv("STRIPE_PRICE_BASIC"),
        "monitor": os.getenv("STRIPE_PRICE_MONITOR"),
        "residential": os.getenv("STRIPE_PRICE_RESIDENTIAL"),
    }.get(tier)


def _tier_for_price_id(price_id: str | None) -> str | None:
    if not price_id:
        return None
    return {
        os.getenv("STRIPE_PRICE_BASIC"): "basic",
        os.getenv("STRIPE_PRICE_MONITOR"): "monitor",
        os.getenv("STRIPE_PRICE_RESIDENTIAL"): "residential",
    }.get(price_id)


def ensure_customer(db: Session, org: Organization, *, email: str | None) -> str:
    """Return the org's Stripe customer id, creating the Customer once."""
    if org.stripe_customer_id:
        return org.stripe_customer_id
    customer = stripe.Customer.create(
        name=org.name,
        email=email or org.billing_email,
        metadata={"organization_id": str(org.id), "slug": org.slug},
    )
    org.stripe_customer_id = customer["id"]
    db.commit()
    logger.info("Stripe customer created for org=%s -> %s", org.id, customer["id"])
    return customer["id"]


def create_checkout_session(
    db: Session, org: Organization, *, tier: str, email: str | None
) -> str:
    """Create a subscription Checkout Session for `tier`; return its URL."""
    _configure()
    if tier not in SELF_SERVE_TIERS:
        raise BillingError(f"Tier '{tier}' is not purchasable self-serve")
    price_id = _price_id_for_tier(tier)
    if not price_id:
        raise BillingError(f"No Stripe price configured for tier '{tier}'")

    customer_id = ensure_customer(db, org, email=email)
    success_url = os.getenv(
        "BILLING_SUCCESS_URL", "http://localhost:3000/settings?billing=success"
    )
    cancel_url = os.getenv(
        "BILLING_CANCEL_URL", "http://localhost:3000/settings?billing=cancel"
    )

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(org.id),
        metadata={"organization_id": str(org.id), "tier": tier},
        allow_promotion_codes=True,
    )
    url = session.get("url")
    if not url:
        raise BillingError("Stripe did not return a checkout URL")
    return url


def create_portal_session(db: Session, org: Organization) -> str:
    """Create a Customer Portal session (manage/cancel); return its URL."""
    _configure()
    if not org.stripe_customer_id:
        raise BillingError("No billing account yet -- subscribe to a plan first")
    return_url = os.getenv("BILLING_PORTAL_RETURN_URL", "http://localhost:3000/settings")
    session = stripe.billing_portal.Session.create(
        customer=org.stripe_customer_id,
        return_url=return_url,
    )
    url = session.get("url")
    if not url:
        raise BillingError("Stripe did not return a portal URL")
    return url


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------

def construct_event(payload: bytes, sig_header: str | None) -> Any:
    """Verify the Stripe signature and return the event (raises on mismatch)."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise BillingError("STRIPE_WEBHOOK_SECRET not set")
    _configure()
    return stripe.Webhook.construct_event(payload, sig_header, secret)


def _org_by_customer(db: Session, customer_id: str | None) -> Organization | None:
    if not customer_id:
        return None
    return db.scalar(
        select(Organization).where(Organization.stripe_customer_id == customer_id)
    )


def _apply_subscription(db: Session, sub: dict) -> None:
    """Sync an org's tier/status/period from a Stripe subscription object."""
    org = _org_by_customer(db, sub.get("customer"))
    if org is None:
        logger.warning("Billing webhook: no org for customer %s", sub.get("customer"))
        return

    status = sub.get("status")
    items = (sub.get("items") or {}).get("data") or []
    price_id = items[0]["price"]["id"] if items else None
    tier = _tier_for_price_id(price_id)

    cpe = sub.get("current_period_end")
    if cpe is None and items:
        cpe = items[0].get("current_period_end")

    org.stripe_subscription_id = sub.get("id")
    org.current_period_end = (
        datetime.fromtimestamp(int(cpe), tz=timezone.utc) if cpe else None
    )

    if status in ("active", "trialing"):
        if tier:
            org.subscription_tier = tier
        org.subscription_status = "active"
    elif status == "past_due":
        org.subscription_status = "past_due"
    elif status in ("canceled", "unpaid", "incomplete_expired"):
        org.subscription_status = "canceled"
        org.subscription_tier = "free"

    db.commit()
    logger.info(
        "Billing sync: org=%s tier=%s status=%s",
        org.id,
        org.subscription_tier,
        org.subscription_status,
    )


def handle_event(db: Session, event: dict) -> None:
    """Process a verified Stripe event (subscription lifecycle + checkout)."""
    etype = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}

    if etype in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        _apply_subscription(db, obj)
    elif etype == "checkout.session.completed":
        sub_id = obj.get("subscription")
        if sub_id:
            _configure()
            _apply_subscription(db, stripe.Subscription.retrieve(sub_id))
    else:
        logger.debug("Billing webhook: ignoring event %s", etype)
