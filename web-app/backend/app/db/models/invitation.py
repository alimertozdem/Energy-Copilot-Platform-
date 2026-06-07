"""OrgInvitation model -- pending invitations to join an organization.

Flow (V1 -- "copy invite link"; automated email delivery is V1.5 backlog):
    1. An org admin creates an invitation (email + role). A random capability
       token is generated. The admin copies the link /invite/{token} and
       shares it manually (Slack, email, etc.).
    2. The invited person opens the link, signs in or signs up, and accepts.
       On accept an OrgMember row is created and the invitation is marked
       'accepted'.

Status lifecycle:
    pending   -- created, not yet accepted (and not expired/revoked)
    accepted  -- converted into an OrgMember row
    revoked   -- admin cancelled it before acceptance
    expired   -- past expires_at (we flip the stored state when an accept is
                 attempted after expiry, so the list reflects reality)

Token is a capability: whoever holds a valid, non-expired token AND is signed
in can accept. Requiring the invite email to equal the signed-in email is a
deliberate V1.5 hardening step (documented in day_19 memory).

Why a dedicated table (vs. just inserting a pending OrgMember):
    The invited person may not have an EnergyLens account yet, so there is no
    user_id to attach. The invitation lives independently of users until
    acceptance, then it spawns the OrgMember.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class OrgInvitation(Base, TimestampMixin):
    """A pending invitation for someone to join an organization with a role."""

    __tablename__ = "org_invitations"
    __table_args__ = (
        # Globally-unique capability token. The unique constraint doubles as
        # the lookup index used by the /invite/{token} accept path.
        UniqueConstraint("token", name="uq_org_invitation_token"),
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
    # Invited person's email -- not necessarily an existing user yet.
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    # 'manager' | 'viewer'. Admins are never invited; ownership is explicit.
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    # URL-safe capability token (secrets.token_urlsafe(32) -> ~43 chars).
    token: Mapped[str] = mapped_column(String(64), nullable=False)
    # 'pending' | 'accepted' | 'revoked' | 'expired'
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
    )
    invited_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Who accepted -- may differ from the invited email in V1 (token = bearer).
    accepted_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship()  # noqa: F821
    invited_by: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[invited_by_user_id],
    )
    accepted_by: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[accepted_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<OrgInvitation org={self.organization_id} email={self.email} "
            f"role={self.role} status={self.status}>"
        )
