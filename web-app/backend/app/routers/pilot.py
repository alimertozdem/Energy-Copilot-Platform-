"""Public 'request a pilot' endpoint — POST /pilot-requests (no auth).

A landing/demo/tour visitor submits interest (optionally to pilot their own
building). Stored for the founder's /admin queue. Admin read/resolve lives in
admin.py (platform-admin gated), mirroring the bridge-request pattern.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories import pilot as pilot_repo
from app.schemas.pilot import PilotRequestAck, PilotRequestCreate

router = APIRouter(prefix="/pilot-requests", tags=["pilot"])

# Soft per-email cap to blunt accidental/abusive resubmits (public endpoint).
MAX_PER_EMAIL = 25


@router.post("", response_model=PilotRequestAck, status_code=status.HTTP_201_CREATED)
def create_pilot_request(
    body: PilotRequestCreate,
    db: Annotated[Session, Depends(get_db)],
) -> PilotRequestAck:
    """Record a public pilot request. No auth; light validation + per-email cap."""
    email = body.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=422, detail="A valid email is required.")
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required.")

    if pilot_repo.recent_count_for_email(db, email=email) >= MAX_PER_EMAIL:
        # Don't reveal internals — generic 429.
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests for this email. We'll be in touch.",
        )

    row = pilot_repo.create(
        db,
        name=name,
        email=email,
        organization=(body.organization or "").strip() or None,
        country_code=(body.country_code or "").strip().upper() or None,
        building_count=body.building_count,
        message=(body.message or "").strip() or None,
        source=(body.source or "").strip() or None,
    )
    db.commit()
    return PilotRequestAck(ok=True, id=row.id)
