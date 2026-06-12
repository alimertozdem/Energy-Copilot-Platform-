"""InstallerRequest -- Execution Marketplace Phase 0 (founder-brokered lead capture).

A logged-in customer asks to be connected with an installer for a recommended
measure on one of their buildings. Zero-infra by design: we capture the lead;
the founder brokers the introduction manually from /admin and works the status.

Phase 1+ (vendor registry, RFQ/quotes, lead fee, take-rate, escrow) is DEFERRED
-- see docs/strategy/execution-marketplace-plan.md. This table is intentionally
minimal so the loop can be validated before any marketplace infrastructure.
"""
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.base import TimestampMixin


class InstallerRequest(Base, TimestampMixin):
    """A customer's request to be connected with an installer for a measure."""

    __tablename__ = "installer_requests"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Bridge to the analytics building (same key the rest of the app uses).
    fabric_building_id: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    # Snapshot so the founder's queue reads without a join.
    building_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    measure_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Where the request was raised: 'actions' | 'residential'.
    source: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # requested -> contacted -> quoted -> closed
    status: Mapped[str] = mapped_column(
        String(20), default="requested", index=True, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<InstallerRequest {self.fabric_building_id} "
            f"{self.action_type} status={self.status}>"
        )
