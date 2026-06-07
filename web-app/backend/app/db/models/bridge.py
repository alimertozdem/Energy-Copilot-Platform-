"""BridgeRequest model -- a customer's self-serve request to unlock full Fabric analytics.

Access Layer 3 (see docs/architecture/self-serve-fabric-bridging.md). A *pending*
building (fabric_building_id NULL) gets value from Tier-1 Postgres-side baseline
KPIs already; this row records the customer's request to bridge it into Microsoft
Fabric for the full Power BI experience.

Phase 3.1 keeps a human (founder) in the loop: the request carries a snapshot of
the readiness assessment at request time (`readiness` JSONB), the founder reviews
it in /admin, runs the (parameterised) medallion pipeline, links the
fabric_building_id, and marks the request fulfilled. Phase 3.2 automates the
fulfilment under the same row. At most one *pending* request per building (a
partial unique index enforces it).
"""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class BridgeRequest(Base, TimestampMixin):
    """A self-serve request to bridge a building into Fabric (Access Layer 3)."""

    __tablename__ = "bridge_requests"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    building_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Denormalised owning org (for the founder's cross-org admin queries + audit).
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # The user who filed it; preserve the request even if the user is later removed.
    requested_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # pending | approved | rejected | fulfilled | cancelled
    status: Mapped[str] = mapped_column(
        String(20), default="pending", index=True, nullable=False
    )
    # What the customer wants unlocked. 'full' = the complete Fabric experience.
    target_tier: Mapped[str] = mapped_column(
        String(20), default="full", nullable=False
    )
    # Snapshot of the readiness assessment at request time (per-page ready/locked +
    # reasons). Lets the founder see exactly what the customer had without recomputing.
    readiness: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    # Optional free-text note from the customer.
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Resolution (founder action).
    resolved_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    building: Mapped["Building"] = relationship()  # noqa: F821
    organization: Mapped["Organization"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<BridgeRequest {self.status} building={self.building_id}>"
