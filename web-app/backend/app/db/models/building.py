"""Building and BuildingModule models -- Fabric Lakehouse bridge layer.

Bridge:
    Building.fabric_building_id maps to Fabric Lakehouse
    silver_building_master.building_id (e.g. "B001"). This column drives
    Power BI RLS effective identity -- without it, embed token RLS fails.

Lifecycle:
    Soft-delete only (is_active=False). Buildings are never hard-deleted
    by users; time-series data in Fabric depends on the ID staying valid.
    Hard delete only occurs via organization CASCADE.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class Building(Base, TimestampMixin):
    """A commercial building owned by an Organization."""

    __tablename__ = "buildings"

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
    # Bridge to Fabric Lakehouse. Globally unique. NULL until onboarded to Fabric.
    fabric_building_id: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # ISO 3166-1 alpha-2 (DE, TR, AT, NL, ...)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    # 'Office' | 'Retail' | 'Hotel' | 'Healthcare' | 'Logistics' | 'Datacenter' | 'Mixed'
    building_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    floor_area_m2: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    # Installed solar PV capacity (kWp). NULL = no solar / unknown. Collected
    # at onboarding (Day 20); full solar analytics is a later initiative.
    pv_capacity_kwp: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    construction_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Energy profile (declared at onboarding; richer than just floor area). These
    # power the advisor + compliance even before live Fabric data is connected.
    epc_class: Mapped[str | None] = mapped_column(String(2), nullable=True)
    heating_system: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cooling_system: Mapped[str | None] = mapped_column(String(40), nullable=True)
    occupancy_pattern: Mapped[str | None] = mapped_column(String(40), nullable=True)
    floors_above_ground: Mapped[int | None] = mapped_column(Integer, nullable=True)
    typical_occupants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Declared dwelling-unit count (residential) — sharpens the per-Wohneinheit
    # subsidy cap; NULL for non-residential / unknown (units estimated from area).
    residential_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Envelope U-values (W/m²K) + insulation year + gas-heating flag — collected at
    # onboarding to unlock the GEG conformity, EPC and CO₂/Scope-1 reports. NULL = unknown.
    wall_u_value: Mapped[Decimal | None] = mapped_column(Numeric(5, 3), nullable=True)
    roof_u_value: Mapped[Decimal | None] = mapped_column(Numeric(5, 3), nullable=True)
    window_u_value: Mapped[Decimal | None] = mapped_column(Numeric(5, 3), nullable=True)
    insulation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_gas_heating: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # Geographic coordinates -- prepared for V1.5+ map UI.
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    # IANA timezone identifier (drives Fabric date joins per-building).
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Europe/Berlin",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization: Mapped["Organization"] = relationship()  # noqa: F821
    modules: Mapped[list["BuildingModule"]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Building {self.fabric_building_id or self.id} '{self.name}'>"


class BuildingModule(Base, TimestampMixin):
    """Per-building module enablement -- drives page visibility & feature unlock.

    Modules (V1):
      - 'meters'  --> Pages 1-7 (always enabled by default)
      - 'iot'     --> Page 8 (IoT Monitoring) -- requires sensor connectors
      - 'battery' --> Page 9 (Battery Strategy) -- requires battery system

    The frontend (Next.js) reads this table to grey out / unlock left-nav items.
    Power BI RLS does NOT use this -- page visibility is enforced at the web app
    layer, not the data layer.
    """

    __tablename__ = "building_modules"
    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "module_key",
            name="uq_building_module_key",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    building_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # 'meters' | 'iot' | 'battery' (V1)
    module_key: Mapped[str] = mapped_column(String(30), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    building: Mapped["Building"] = relationship(back_populates="modules")

    def __repr__(self) -> str:
        return (
            f"<BuildingModule {self.module_key}={self.enabled} "
            f"for {self.building_id}>"
        )


class BuildingConsumption(Base, TimestampMixin):
    """Uploaded / manually-entered monthly consumption.

    The baseline for a building before (or alongside) live Fabric data — fed by
    the CSV / bill upload at onboarding. One row per month (period = 'YYYY-MM').
    """

    __tablename__ = "building_consumption"
    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "period",
            name="uq_building_consumption_period",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    building_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Billing / reading period as "YYYY-MM" (monthly grain).
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    energy_kwh: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    cost_eur: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    # 'csv' | 'manual' | 'bill'
    source: Mapped[str] = mapped_column(String(20), default="csv", nullable=False)

    def __repr__(self) -> str:
        return f"<BuildingConsumption {self.building_id} {self.period}={self.energy_kwh}>"
