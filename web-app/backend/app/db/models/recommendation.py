"""RecommendationStatus model -- /actions page tracking layer.

Bridge:
    Maps to Fabric Lakehouse gold_recommendations.recommendation_id.
    Power BI Page 5 displays the catalog of recommendations from Fabric.
    This table tracks what the customer DID with each one (status,
    completed_by, savings snapshot).

Snapshot principle:
    estimated_savings_eur is copied from Fabric at the moment a
    recommendation is acted upon. Fabric may recompute the live value
    later, but the historical "savings booked when completed" is frozen
    here for ROI reporting and leaderboards.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class RecommendationStatus(Base, TimestampMixin):
    """Per-organization tracking of recommendations surfaced by Power BI Page 5.

    Lifecycle:
      open --> in_progress --> completed
      open --> dismissed (with reason in notes)
      open --> not_applicable (false positive)
    """

    __tablename__ = "recommendation_status"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "fabric_recommendation_id",
            name="uq_recommendation_status_identity",
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
    # Bridge to Fabric Lakehouse gold_recommendations.recommendation_id.
    fabric_recommendation_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    # 'open' | 'in_progress' | 'completed' | 'dismissed' | 'not_applicable'
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False,
    )
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Snapshot at the moment of action -- preserves historical savings booked.
    estimated_savings_eur: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped["Organization"] = relationship()  # noqa: F821
    building: Mapped["Building"] = relationship()  # noqa: F821
    assigned_to: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[assigned_to_user_id],
    )
    completed_by: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[completed_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<RecommendationStatus {self.fabric_recommendation_id} "
            f"status={self.status}>"
        )
