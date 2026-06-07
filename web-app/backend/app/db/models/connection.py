"""Device + SensorPoint models -- the Tier-2/3 connection wiring layer.

Onboarding captures IoT *intent* (which protocols / sensor types a building has)
as loose JSON on the building's module notes. These tables hold the concrete
config the live-data path needs: each Device a building exposes (protocol +
connection params), and each SensorPoint on it (a register / object / topic)
mapped to a normalized sensor_type + zone. An edge agent (Tier 2) or cloud
poller (Tier 3) reads this config, talks to the device, and runs the adapter
framework to normalize readings into the standard schema -> silver -> gold.

Addressed via the building UUID, so it works for buildings still pending a
Fabric bridge (fabric_building_id NULL) -- the common state after onboarding.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.models.base import TimestampMixin


class Device(Base, TimestampMixin):
    """A physical/logical device a building exposes for data collection.

    connection_config is protocol-shaped JSONB (Modbus: host/port/unit_id;
    BACnet: device_instance/host; MQTT: broker/port/topic; REST: endpoint/auth)
    -- kept schemaless so a new protocol never needs a migration.
    """

    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    building_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # 'bacnet' | 'modbus' | 'mqtt' | 'rest_api' | 'opc_ua'
    protocol: Mapped[str] = mapped_column(String(20), nullable=False)
    # Protocol-specific connection params (host/port/unit_id/topic/endpoint/...).
    connection_config: Mapped[Any | None] = mapped_column(JSONB, nullable=True)
    # 'pending' | 'active' | 'error' | 'disabled' -- starts pending; only an edge
    # agent / poller (which can actually reach the device) flips it to active.
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    # Optional device-template this was created from (point-map provenance).
    template_key: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    points: Mapped[list["SensorPoint"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Device {self.protocol}:{self.name} for {self.building_id}>"


class SensorPoint(Base, TimestampMixin):
    """One readable point on a Device, mapped to a normalized sensor_type + zone.

    point_ref is the protocol-native address (Modbus register, BACnet object id,
    MQTT topic, REST json-path). sensor_type uses the normalized vocabulary the
    IoT pipeline expects (HVAC_temp, humidity, CO2, building_kwh, hvac_kwh, ...),
    so the adapter framework can route the reading. scale converts the raw value
    to the standard unit (e.g. Wh->kWh = 0.001).
    """

    __tablename__ = "sensor_points"
    __table_args__ = (
        UniqueConstraint("device_id", "point_ref", name="uq_sensor_point_ref"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    device_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Protocol-native address: Modbus register, BACnet object, MQTT topic, REST path.
    point_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    # Normalized sensor_type (HVAC_temp, humidity, CO2, building_kwh, hvac_kwh, ...).
    sensor_type: Mapped[str] = mapped_column(String(40), nullable=False)
    zone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Raw -> standard-unit multiplier (default 1.0).
    scale: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), default=Decimal("1"), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    device: Mapped["Device"] = relationship(back_populates="points")

    def __repr__(self) -> str:
        return f"<SensorPoint {self.point_ref}->{self.sensor_type}>"
