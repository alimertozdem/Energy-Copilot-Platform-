"""DB operations for PasswordResetToken.

Repository pattern: thin SQLAlchemy wrappers. Callers own the final db.commit().
A token is only ever consumed via get_valid_by_hash (which enforces unused +
unexpired) then mark_used -- there is no "get by id" by design.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.password_reset import PasswordResetToken

# A reset link is valid for one hour -- long enough to act, short enough to
# limit the window if an inbox is later compromised.
RESET_TTL_MINUTES = 60


def create_token(
    db: Session, *, user_id: UUID, token_hash: str, ttl_minutes: int = RESET_TTL_MINUTES
) -> PasswordResetToken:
    """Insert a reset token valid for ttl_minutes. Caller commits."""
    row = PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes),
    )
    db.add(row)
    return row


def get_valid_by_hash(
    db: Session, *, token_hash: str
) -> PasswordResetToken | None:
    """Return an UNUSED, UNEXPIRED token by hash, else None."""
    row = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
    )
    if row is None or row.used_at is not None:
        return None
    if row.expires_at <= datetime.now(timezone.utc):
        return None
    return row


def mark_used(db: Session, token: PasswordResetToken) -> None:
    """Consume a token so it cannot be reused. Caller commits."""
    token.used_at = datetime.now(timezone.utc)
    db.add(token)


def invalidate_for_user(db: Session, *, user_id: UUID) -> None:
    """Mark all of a user's outstanding tokens used -- called when a new reset
    is requested, so only the latest link works. Caller commits."""
    rows = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
    ).all()
    now = datetime.now(timezone.utc)
    for r in rows:
        r.used_at = now
        db.add(r)
