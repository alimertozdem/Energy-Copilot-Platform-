"""PasswordResetToken model -- single-use, expiring credential for the
self-service password-reset flow.

Mirrors the AgentToken hashing philosophy: the plaintext token is high-entropy
random (secrets.token_urlsafe), emailed to the user exactly once, and stored
only as a SHA-256 hex digest. A token is valid until it expires or is used.
Tied to a User; a reset always targets that user's 'email' provider link.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.base import TimestampMixin


class PasswordResetToken(Base, TimestampMixin):
    """A single-use, expiring password-reset token (stored hashed)."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # SHA-256 hex of the plaintext token (256-bit random -> a plain hash is fine,
    # no bcrypt salting needed; same approach as AgentToken).
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        used = self.used_at is not None
        return f"<PasswordResetToken user={self.user_id} used={used}>"
