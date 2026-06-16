"""Schemas for the web-app live monitoring view (GET /buildings/{id}/monitoring).

Mirrors services/monitoring.py. Postgres-native (bronze_iot_readings), separate
from the Fabric-backed Power BI IoT page.
"""
from datetime import datetime

from pydantic import BaseModel


class MonitoringSensor(BaseModel):
    """Latest reading for one sensor_type."""

    sensor_type: str
    value: float | None
    unit: str | None
    zone: str | None
    received_at: datetime
    simulated: bool


class MonitoringResponse(BaseModel):
    sensors: list[MonitoringSensor]
    reading_count: int
    window_hours: int
    last_reading_at: datetime | None
    basis: str  # live | simulated | none
