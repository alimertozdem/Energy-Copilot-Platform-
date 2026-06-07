"""AuditLog model -- compliance & security event log.

Purpose:
    Records who did what, when, from where. Drives SOC 2 readiness and
    GDPR Article 30 (record of processing activities).

Polymorphic entity reference:
    entity_type + entity_id let one table cover all event types:
        action='building.created'      entity_type='building'      entity_id=<uuid>
        action='user.login'            entity_type='user'          entity_id=<uuid>
        action='recommendation.completed' entity_type='recommendation' entity_id=<uuid>

Retention:
    IP address and user_agent are stored under 'legitimate interest =
    security' (GDPR). A future cron job should prune rows older than 90
    days unless required for an active investigation.
"""
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class AuditLog(Base, TimestampMixin):
    """A single audited event."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    # User survives even if log entries reference them; preserve audit trail.
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    # NULL for system events (e.g. scheduled jobs, no org context).
    organization_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    # Dotted notation: 'user.login', 'building.created',
    # 'recommendation.completed', 'org_member.invited', etc.
    action: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    # 'building' | 'user' | 'recommendation' | 'org_member' | ...
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # UUID string or domain ID (e.g. fabric_building_id).
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # IPv6 max length = 45 chars.
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Extra context: old/new values, request body excerpts, etc.
    details: Mapped[Any | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User | None"] = relationship()  # noqa: F821
    organization: Mapped["Organization | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user={self.user_id}>"
