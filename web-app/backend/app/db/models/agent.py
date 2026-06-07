"""AgentToken model -- building-scoped credential for an edge agent.

An edge gateway (Tier 2) authenticates with one of these tokens to PULL its
node-map from GET /agent/config -- NOT a user login. Tokens are building-scoped
and stored HASHED (SHA-256 of the plaintext, which is shown exactly once at
issue time). This path is entirely separate from the user JWT, so an edge agent
never holds a user credential and can be revoked independently.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.base import TimestampMixin


class AgentToken(Base, TimestampMixin):
    """A building-scoped edge-agent token (stored hashed)."""

    __tablename__ = "agent_tokens"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    building_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # SHA-256 hex of the plaintext token (the token is high-entropy random, so a
    # plain hash is appropriate -- no bcrypt salting needed for a 256-bit secret).
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    # Non-secret short prefix for display ("ely_ab12…"), to identify a token.
    token_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False, default="edge agent")
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AgentToken {self.token_prefix} for {self.building_id}>"
