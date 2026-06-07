"""Pydantic schemas for edge-agent tokens + the agent config/heartbeat feed.

Token management is manage-gated (web UI). /agent/config + /agent/heartbeat are
consumed by the edge gateway, authenticated by the building-scoped agent token.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentTokenCreate(BaseModel):
    name: str = Field(default="edge agent", max_length=80)


class AgentTokenResponse(BaseModel):
    id: UUID
    building_id: UUID
    name: str
    token_prefix: str
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    is_active: bool


class AgentTokenIssued(AgentTokenResponse):
    """Returned ONCE at issue time — carries the plaintext token (never stored)."""

    token: str


class AgentTokenListResponse(BaseModel):
    tokens: list[AgentTokenResponse]


# --- agent config feed (gateway node-map) ----------------------------------


class AgentPoint(BaseModel):
    point_ref: str
    sensor_type: str
    zone: str | None
    unit: str | None
    scale: float
    enabled: bool


class AgentDevice(BaseModel):
    id: str  # device UUID — the agent echoes this in /agent/heartbeat
    name: str
    protocol: str
    connection_config: dict[str, Any] | None
    points: list[AgentPoint]


class AgentConfigResponse(BaseModel):
    """The node-map an edge gateway pulls. building_id is the Fabric id when
    bridged, else the Postgres UUID string."""

    building_id: str
    devices: list[AgentDevice]


# --- agent heartbeat (status write-back) -----------------------------------


class AgentHeartbeatRequest(BaseModel):
    """The agent reports the device ids it is actively collecting. The backend
    flips those devices to 'active' and stamps last_seen_at."""

    device_ids: list[str] = Field(default_factory=list, max_length=500)


class AgentHeartbeatResponse(BaseModel):
    building_id: str
    updated: int  # how many devices were marked active
