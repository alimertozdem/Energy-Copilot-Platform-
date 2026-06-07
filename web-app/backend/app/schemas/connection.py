"""Pydantic schemas for the Devices & Connections (Tier-2/3) flow.

A Device (protocol + connection params) and its SensorPoints (point_ref ->
normalized sensor_type + zone). The CRUD here drives the /connections page; an
edge agent / poller later consumes the same config to collect live data.
"""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

Protocol = Literal["bacnet", "modbus", "mqtt", "rest_api", "opc_ua"]
DeviceStatus = Literal["pending", "active", "error", "disabled"]


# --- sensor points ---------------------------------------------------------


class SensorPointCreate(BaseModel):
    """Add one point to a device (point_ref -> sensor_type + zone)."""

    point_ref: str = Field(min_length=1, max_length=120)
    sensor_type: str = Field(min_length=1, max_length=40)
    zone: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, max_length=20)
    scale: float = Field(default=1.0, gt=0)
    enabled: bool = True


class SensorPointUpdate(BaseModel):
    """Patch a point. All fields optional; only provided ones change."""

    point_ref: str | None = Field(default=None, min_length=1, max_length=120)
    sensor_type: str | None = Field(default=None, min_length=1, max_length=40)
    zone: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, max_length=20)
    scale: float | None = Field(default=None, gt=0)
    enabled: bool | None = None


class SensorPointResponse(BaseModel):
    id: UUID
    device_id: UUID
    point_ref: str
    sensor_type: str
    zone: str | None
    unit: str | None
    scale: float
    enabled: bool


# --- devices ---------------------------------------------------------------


class DeviceCreate(BaseModel):
    """Create a device. Optionally seed points from a built-in template and/or
    pass inline points; both are merged (template first, then inline)."""

    name: str = Field(min_length=1, max_length=120)
    protocol: Protocol
    connection_config: dict[str, Any] | None = None
    template_key: str | None = Field(default=None, max_length=60)
    points: list[SensorPointCreate] = Field(default_factory=list)


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    connection_config: dict[str, Any] | None = None
    status: DeviceStatus | None = None


class DeviceResponse(BaseModel):
    id: UUID
    building_id: UUID
    name: str
    protocol: str
    connection_config: dict[str, Any] | None
    status: str
    template_key: str | None
    last_seen_at: datetime | None
    points: list[SensorPointResponse] = Field(default_factory=list)


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]


# --- device template catalog + sensor vocabulary (Tier 3 prefill) ----------


class SensorTypeOption(BaseModel):
    """A normalized sensor_type option for the point-mapping dropdown."""

    value: str
    label: str
    unit: str | None = None


class TemplatePoint(BaseModel):
    point_ref: str
    sensor_type: str
    unit: str | None = None
    scale: float = 1.0
    label: str | None = None


class DeviceTemplate(BaseModel):
    key: str
    label: str
    protocol: Protocol
    description: str | None = None
    default_config: dict[str, Any] = Field(default_factory=dict)
    points: list[TemplatePoint] = Field(default_factory=list)


class DeviceTemplateListResponse(BaseModel):
    templates: list[DeviceTemplate]
    sensor_types: list[SensorTypeOption]
