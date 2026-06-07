"""Organization and OrgMember models -- multi-tenant layer.

Pattern:
    An Organization is the billing & access unit (typically a property
    management firm). Users join via OrgMember rows, each with a role.
    A User can belong to multiple organizations (e.g. own personal
    workspace + a client firm).
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class Organization(Base, TimestampMixin):
    """A tenant -- typically a property management firm or a personal workspace.

    Subscription, billing, and building ownership all live at the org level.
    """

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # URL-friendly identifier, auto-generated from name on create.
    slug: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        index=True,
        nullable=False,
    )
    billing_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 'free' | 'basic' | 'monitor' | 'enterprise'  (validated in API layer)
    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
    )
    # 'active' | 'past_due' | 'canceled'
    subscription_status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )
    # ISO 3166-1 alpha-2 (DE, TR, AT, NL, ...). Used for billing & pricing.
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # 'customer' (owns buildings -- every existing org) | 'partner' (a consultancy
    # that manages other orgs via partner_client_link). Validated in the API layer.
    org_type: Mapped[str] = mapped_column(
        String(20),
        default="customer",
        nullable=False,
        server_default=text("'customer'"),
    )

    # --- Stripe billing (self-serve subscriptions, Day 43) ---
    # The Stripe Customer for this org (created on first checkout). One
    # customer per org; the subscription_tier/status above are kept in sync
    # by the Stripe webhook.
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    # End of the current paid period (from Stripe) -- UI shows renewal/expiry.
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Sample/demo organization flag. Sample orgs' buildings are visible to
    # all authenticated users (V1 shared sample portfolio + V2 /demo public).
    # Real customer orgs always have is_sample=False.
    is_sample: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
    )
    # Org survives even if creator user is deleted.
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    members: Mapped[list["OrgMember"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    creator: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[created_by_user_id],
    )

    def __repr__(self) -> str:
        return f"<Organization {self.slug}>"


class OrgMember(Base, TimestampMixin):
    """Junction table linking a User to an Organization with a role.

    Roles:
      - 'admin'   --> full access incl. billing & member management
      - 'manager' --> manages buildings, cannot add/remove members
      - 'viewer'  --> read-only

    Invitations:
      - invitation_accepted_at IS NULL  --> pending (user sees "Accept" in UI)
      - invitation_accepted_at IS NOT NULL --> active member
    """

    __tablename__ = "org_members"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_org_member_identity",
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
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # 'admin' | 'manager' | 'viewer'
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    invited_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    invitation_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(  # noqa: F821
        foreign_keys=[user_id],
    )
    invited_by: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[invited_by_user_id],
    )

    def __repr__(self) -> str:
        return f"<OrgMember org={self.organization_id} user={self.user_id} role={self.role}>"
