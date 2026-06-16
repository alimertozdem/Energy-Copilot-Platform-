"""Telemetry ingest payloads (edge-agent -> POST /ingest/telemetry).

Field names match the adapter's normalized event (00_iot_adapter_framework):
device_id, building_id, sensor_type, sensor_location, reading_value,
reading_unit, source_protocol, timestamp, reading_quality.
"""
from datetime import datetime

from pydantic import BaseModel, Field

# Cap one POST so a misbehaving agent cannot push an unbounded batch.
MAX_BATCH = 5000


class TelemetryReading(BaseModel):
    """One normalized reading as emitted by an edge adapter."""

    device_id: str
    building_id: str
    sensor_type: str
    sensor_location: str | None = None
    reading_value: float | None = None
    reading_unit: str | None = None
    source_protocol: str | None = None
    timestamp: datetime | None = None
    reading_quality: int | None = None


class TelemetryBatch(BaseModel):
    """A micro-batch of readings from one site's agent."""

    readings: list[TelemetryReading] = Field(default_factory=list)


class TelemetryIngestResponse(BaseModel):
    """Per-request ingest result."""

    building_id: str
    accepted: int
    rejected: int
