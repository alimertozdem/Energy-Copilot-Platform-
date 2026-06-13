"""User and UserAuthProvider models -- multi-provider authentication.

Pattern:
    One User row = one person.
    A User can connect multiple auth providers (Microsoft + Google + Email).
    The (provider, provider_user_id) pair is globally unique.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """A platform user.

    One person = one row, regardless of how many auth providers they connect.
    Special rows:
      - is_demo=True  --> the public /demo user (shared, read-only access).
      - is_platform_admin=True --> founder / admin (Mert).
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_platform_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # Per-user toggle: include sample/demo buildings in the visible portfolio.
    show_sample_data: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    auth_providers: Mapped[list["UserAuthProvider"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class UserAuthProvider(Base, TimestampMixin):
    """A user's connection to an external auth provider.

    Examples:
      - provider='microsoft', provider_user_id=<Azure AD object id>
      - provider='google',    provider_user_id=<Google 'sub' claim>
      - provider='email',     provider_user_id=<user's email>, password_hash=<bcrypt>

    Constraint:
      (provider, provider_user_id) is globally unique -- one Microsoft
      account cannot link to two different platform users.
    """

    __tablename__ = "user_auth_providers"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_user_auth_provider_identity",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # 'microsoft' | 'google' | 'email'  (validated in Pydantic schema layer)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # Only set when provider == 'email' (bcrypt hash).
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="auth_providers")

    def __repr__(self) -> str:
        return f"<UserAuthProvider {self.provider}:{self.provider_user_id}>"
