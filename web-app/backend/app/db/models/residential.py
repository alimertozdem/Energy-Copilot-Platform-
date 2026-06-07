"""Residential layer -- unit grain + resident identity (control plane).

* ``Unit`` mirrors the buildings<->Fabric bridge: ``fabric_unit_id`` equals
  ``silver_unit_master.unit_id`` in the lakehouse.
* ``ResidentIdentity`` is deliberately minimal-PII (email only) and separate from the
  paying B2B NextAuth users.
* ``UnitResident`` is a tenancy window (``valid_from``/``valid_to``) so a resident's data
  access is scoped to their occupancy period (Mieterwechsel) -- DSGVO + billing correctness.
* ``ResidentInviteToken`` is a passwordless magic-link bound to a tenancy.

See ``docs/architecture/residential-data-model.md``.
"""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.models.base import TimestampMixin


class Unit(Base, TimestampMixin):
    """A unit (apartment) within a building. Bridges to Fabric ``silver_unit_master``."""

    __tablename__ = "units"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    building_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # == silver_unit_master.unit_id (the analytics bridge; mirrors fabric_building_id)
    fabric_unit_id: Mapped[str | None] = mapped_column(
        String(50), unique=True, index=True, nullable=True
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Unit {self.label or self.id}>"


class ResidentIdentity(Base, TimestampMixin):
    """A resident (tenant) -- minimal PII (email only). Magic-link first, optional account.

    Consumption data is NEVER stored here; it lives in the lakehouse and is read via the
    unit's ``fabric_unit_id``. This row holds only the identity needed to authenticate a
    resident and route them to their unit.
    """

    __tablename__ = "resident_identity"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # invited -> active | disabled
    status: Mapped[str] = mapped_column(
        String(20), default="invited", nullable=False, server_default=text("'invited'")
    )

    def __repr__(self) -> str:
        return f"<ResidentIdentity {self.email}>"


class UnitResident(Base, TimestampMixin):
    """Tenancy: which resident occupies which unit, for which period (Mieterwechsel).

    A resident sees only consumption within ``valid_from .. valid_to``; this is the
    ``resolve_scope`` resident-path filter (not just ``unit_id``).
    """

    __tablename__ = "unit_resident"
    __table_args__ = (Index("ix_unit_resident_unit_id", "unit_id", "valid_to"),)

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
    )
    resident_identity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resident_identity.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)  # move-in
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)  # move-out (NULL = current)
    # active | ended
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, server_default=text("'active'")
    )

    def __repr__(self) -> str:
        return f"<UnitResident unit={self.unit_id} resident={self.resident_identity_id}>"


class ResidentInviteToken(Base, TimestampMixin):
    """Passwordless magic-link token bound to a tenancy (``unit_resident``).

    Only a hash of the token is stored. Default resident auth path; an optional full
    account is a later, additive credential on ``ResidentIdentity``.
    """

    __tablename__ = "resident_invite_token"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    unit_resident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("unit_resident.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<ResidentInviteToken {self.id}>"
