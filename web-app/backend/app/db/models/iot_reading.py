"""IotReading -- Phase A bronze landing for edge-agent telemetry.

One normalized reading (the OpcUaAdapter / Modbus etc. adapter output) as POSTed
by the on-site edge agent to /ingest/telemetry. Append-only landing table; no
updates. See ADR-001 (docs/architecture/scada-solar-live-ingestion.md).
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Float, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IotReading(Base):
    """A single normalized telemetry reading landed by the edge agent."""

    __tablename__ = "bronze_iot_readings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agent_building_uuid: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    building_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(Text, nullable=False)
    sensor_type: Mapped[str] = mapped_column(Text, nullable=False)
    sensor_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    reading_unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_protocol: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_quality: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<IotReading {self.device_id} {self.sensor_type}={self.reading_value}>"
