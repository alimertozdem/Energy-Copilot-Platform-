"""Repository for devices + sensor_points (Tier-2/3 connection wiring).

Building-scoped: every read/write is keyed by building_id so a user can only
ever touch devices on a building they manage (the router enforces the gate).
Callers commit.
"""
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.connection import Device, SensorPoint


def _scale(value) -> Decimal:
    return Decimal(str(value)) if value not in (None, "") else Decimal("1")


def list_devices(db: Session, *, building_id: UUID) -> list[Device]:
    return list(
        db.scalars(
            select(Device)
            .where(Device.building_id == building_id)
            .options(selectinload(Device.points))
            .order_by(Device.created_at)
        ).all()
    )


def get_device(db: Session, *, building_id: UUID, device_id: UUID) -> Device | None:
    return db.scalar(
        select(Device)
        .where(Device.id == device_id, Device.building_id == building_id)
        .options(selectinload(Device.points))
    )


def create_device(
    db: Session,
    *,
    building_id: UUID,
    name: str,
    protocol: str,
    connection_config: dict | None,
    template_key: str | None,
    points: list[dict],
) -> Device:
    """Create a device + its points (already merged). Caller commits."""
    device = Device(
        building_id=building_id,
        name=name,
        protocol=protocol,
        connection_config=connection_config,
        template_key=template_key,
        status="pending",
    )
    db.add(device)
    db.flush()  # assign device.id for the point FKs
    seen: set[str] = set()
    for p in points:
        ref = p["point_ref"]
        if ref in seen:
            continue  # de-dupe within the batch (unique device_id+point_ref)
        seen.add(ref)
        db.add(
            SensorPoint(
                device_id=device.id,
                point_ref=ref,
                sensor_type=p["sensor_type"],
                zone=p.get("zone"),
                unit=p.get("unit"),
                scale=_scale(p.get("scale")),
                enabled=bool(p.get("enabled", True)),
            )
        )
    return device


def update_device(db: Session, *, device: Device, fields: dict) -> Device:
    """Patch device columns from a dict (already exclude_unset)."""
    if fields.get("name") is not None:
        device.name = fields["name"]
    if "connection_config" in fields and fields["connection_config"] is not None:
        device.connection_config = fields["connection_config"]
    if fields.get("status") is not None:
        device.status = fields["status"]
    return device


def delete_device(db: Session, *, device: Device) -> None:
    db.delete(device)


def get_point(db: Session, *, device_id: UUID, point_id: UUID) -> SensorPoint | None:
    return db.scalar(
        select(SensorPoint).where(
            SensorPoint.id == point_id, SensorPoint.device_id == device_id
        )
    )


def add_point(db: Session, *, device_id: UUID, point: dict) -> SensorPoint:
    sp = SensorPoint(
        device_id=device_id,
        point_ref=point["point_ref"],
        sensor_type=point["sensor_type"],
        zone=point.get("zone"),
        unit=point.get("unit"),
        scale=_scale(point.get("scale")),
        enabled=bool(point.get("enabled", True)),
    )
    db.add(sp)
    return sp


def update_point(db: Session, *, point: SensorPoint, fields: dict) -> SensorPoint:
    if fields.get("point_ref") is not None:
        point.point_ref = fields["point_ref"]
    if fields.get("sensor_type") is not None:
        point.sensor_type = fields["sensor_type"]
    if "zone" in fields:
        point.zone = fields["zone"]
    if "unit" in fields:
        point.unit = fields["unit"]
    if fields.get("scale") is not None:
        point.scale = _scale(fields["scale"])
    if fields.get("enabled") is not None:
        point.enabled = bool(fields["enabled"])
    return point


def delete_point(db: Session, *, point: SensorPoint) -> None:
    db.delete(point)


def mark_devices_active(
    db: Session, *, building_id: UUID, device_ids: list[UUID]
) -> int:
    """Set status='active' + last_seen_at=now for the given devices in a building.

    Called from the agent heartbeat. Only touches devices that belong to the
    building (the agent token is building-scoped). Caller commits. Returns the
    number of devices updated.
    """
    from datetime import datetime, timezone

    if not device_ids:
        return 0
    devices = list(
        db.scalars(
            select(Device).where(
                Device.building_id == building_id, Device.id.in_(device_ids)
            )
        ).all()
    )
    now = datetime.now(timezone.utc)
    for d in devices:
        d.status = "active"
        d.last_seen_at = now
    return len(devices)
