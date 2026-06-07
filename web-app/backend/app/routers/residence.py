"""Residence router — resident-view read layer + magic-link session (P4-1/P4-3).

Reads the residential Gold tables via the Fabric SQL Analytics Endpoint (same
read path as /portfolio), scoped to the resident's own unit(s). NO Power BI embed.

Resident auth (separate from NextAuth B2B — different cookie + different JWT issuer):
  * POST /residence/auth/consume — exchange a single-use magic-link token for a
    resident session JWT (validated against resident_invite_token).
  * get_current_resident_identity_id — resolves the caller's resident_identity:
      1) primary: a resident session JWT in ``Authorization: Bearer <token>``;
      2) dev fallback: ``X-Resident-Id`` header, ONLY when RESIDENT_DEV_MODE=1.
    The dev fallback (P4-1) is preserved so existing ?resident= testing keeps
    working; production uses the Bearer session. NextAuth is never touched.
"""
import hashlib
import os
from datetime import date, datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.residential import ResidentInviteToken, UnitResident
from app.schemas.residence import (
    ResidenceSummary,
    ResidentConsumeRequest,
    ResidentSession,
)
from app.services import access, residential_metrics
from app.utils.jwt import (
    RESIDENT_TOKEN_EXPIRATION_HOURS,
    create_resident_token,
    decode_resident_token,
)

router = APIRouter(prefix="/residence", tags=["residence"])


def get_current_resident_identity_id(
    authorization: Annotated[str | None, Header()] = None,
    x_resident_id: Annotated[str | None, Header(alias="X-Resident-Id")] = None,
) -> UUID:
    """Resolve the calling resident's ``resident_identity`` id.

    Primary: a resident session JWT (``Authorization: Bearer <token>``) minted by
    /residence/auth/consume. Dev fallback: ``X-Resident-Id`` header, honored ONLY
    when RESIDENT_DEV_MODE=1 (the P4-1 override, kept for curl/tests).
    """
    if authorization and authorization.lower().startswith("bearer "):
        return decode_resident_token(authorization[7:].strip())
    if os.getenv("RESIDENT_DEV_MODE") == "1" and x_resident_id:
        try:
            return UUID(x_resident_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-Resident-Id"
            )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Resident authentication required",
    )


@router.post("/auth/consume", response_model=ResidentSession)
def consume_invite(
    payload: ResidentConsumeRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ResidentSession:
    """Exchange a magic-link token for a resident session JWT (single-use)."""
    token_hash = hashlib.sha256(payload.token.strip().encode()).hexdigest()
    invite = db.scalar(
        select(ResidentInviteToken).where(ResidentInviteToken.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)
    invalid = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="This sign-in link is invalid or has expired.",
    )
    if invite is None or invite.consumed_at is not None or invite.expires_at < now:
        raise invalid
    tenancy = db.get(UnitResident, invite.unit_resident_id)
    if tenancy is None or tenancy.status != "active":
        raise invalid

    invite.consumed_at = now
    db.commit()

    token = create_resident_token(resident_identity_id=tenancy.resident_identity_id)
    return ResidentSession(
        resident_token=token, expires_in_hours=RESIDENT_TOKEN_EXPIRATION_HOURS
    )


@router.get("/summary", response_model=ResidenceSummary)
def read_residence_summary(
    resident_identity_id: Annotated[UUID, Depends(get_current_resident_identity_id)],
    db: Annotated[Session, Depends(get_db)],
) -> ResidenceSummary:
    """Return the resident's own unit(s): EUI/EPC, HKVO common-area share, monthly UVI.

    Scope (which units, on what date) comes from ``resolve_resident_scope`` — the
    tenancy window (Mieterwechsel) is enforced there, not here.
    """
    scope = access.resolve_resident_scope(db, resident_identity_id=resident_identity_id)
    return residential_metrics.get_residence_summary(
        unit_ids=scope["fabric_unit_ids"],
        as_of=date.fromisoformat(scope["as_of"]),
    )
