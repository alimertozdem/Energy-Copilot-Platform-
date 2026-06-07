"""AlertStatus model -- /alerts acknowledge overlay (Day 31).

Bridge:
    Maps to Fabric Lakehouse gold_anomaly_log.anomaly_id. The Fabric table owns
    the ANALYTICAL state (is_resolved -- did the data return to normal). This
    table owns the OPERATIONAL state (has a human acknowledged or dismissed it).
    The two are independent on purpose: a human acknowledging an alarm is NOT
    the same as the underlying condition clearing (standard BMS alarm model).

Lifecycle (overlay):
    new (implicit -- no row) --> acknowledged --> dismissed (and freely back).
    'dismissed' marks a false positive / won't-action; 'acknowledged' marks
    "a human owns this". Default display when no row exists is 'new'.

Read-only Day 30 surface + this overlay = full triage workflow. Mirrors the
RecommendationStatus pattern used by /actions, keyed on the anomaly's real
surrogate id (gold_anomaly_log has one, unlike gold_recommendations).
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class AlertStatus(Base, TimestampMixin):
    """Per-organization acknowledge overlay for anomalies surfaced on /alerts."""

    __tablename__ = "alert_status"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "fabric_anomaly_id",
            name="uq_alert_status_identity",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    building_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Bridge to Fabric Lakehouse gold_anomaly_log.anomaly_id.
    fabric_anomaly_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    # 'new' | 'acknowledged' | 'dismissed'
    ack_status: Mapped[str] = mapped_column(
        String(20),
        default="new",
        server_default="new",
        nullable=False,
    )
    acknowledged_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship()  # noqa: F821
    building: Mapped["Building"] = relationship()  # noqa: F821
    acknowledged_by: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[acknowledged_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<AlertStatus {self.fabric_anomaly_id} ack={self.ack_status}>"
        )
