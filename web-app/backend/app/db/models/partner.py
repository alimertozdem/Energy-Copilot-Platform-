"""PartnerClientLink -- the consultant (partner) layer's delegated-access grant.

A partner organization (``org_type='partner'``) is granted scoped, revocable access to a
client organization's data. This is the only new control-plane table the consultant layer
needs; access resolution (``resolve_scope``) reads the *active* links to compute a partner's
visible building set. See ``docs/architecture/unified-access-model.md``.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.base import TimestampMixin


class PartnerClientLink(Base, TimestampMixin):
    """A delegated, revocable grant: a partner org may act on a client org's behalf.

    The client (data controller) must consent (``client_consent_at``) before the link
    becomes ``active``. Revoking sets ``revoked_at`` -- access disappears on the next
    ``resolve_scope`` call; no client data is ever copied to the partner.
    """

    __tablename__ = "partner_client_link"
    __table_args__ = (
        CheckConstraint(
            "partner_org_id <> client_org_id", name="ck_partner_client_not_self"
        ),
        # exactly one LIVE link per (partner, client) -- partial unique where not revoked
        Index(
            "uq_partner_client_live",
            "partner_org_id",
            "client_org_id",
            unique=True,
            postgresql_where=text("revoked_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    partner_org_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    client_org_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # pending -> active (client must consent) -> suspended | revoked
    relationship_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, server_default=text("'pending'")
    )
    # read_only (advisory) | full_manage
    scope: Mapped[str] = mapped_column(
        String(20), default="read_only", nullable=False, server_default=text("'read_only'")
    )
    # e.g. {"type": "percent", "value": 15, "currency": "EUR"} (design-time)
    commission_model: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    invited_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # DSGVO: the client (controller) authorises the partner (processor); set on accept.
    client_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    granted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<PartnerClientLink {self.partner_org_id}->{self.client_org_id} "
            f"{self.relationship_status}>"
        )
