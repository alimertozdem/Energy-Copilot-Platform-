"""Devices & Connections router -- Tier-2/3 connection wiring CRUD.

UUID-addressed by building (works for buildings still pending a Fabric bridge)
and manage-gated (only org admins/managers, or full_manage partners, may
mutate -- same gate as the consumption + KPI endpoints). An edge agent / poller
consumes this config to collect live data; the backend itself never reaches
on-prem devices (firewall), so there is NO live connection test here -- a
device stays 'pending' until a collector reports in.
"""
from datetime import datetime, timezone as dt_timezone
import random
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Building
from app.db.models.connection import Device, SensorPoint
from app.db.models.iot_reading import IotReading
from app.repositories import connection as conn_repo
from app.repositories import ingest as ingest_repo
from app.schemas.connection import (
    DeviceCreate,
    DeviceListResponse,
    DeviceResponse,
    DeviceTemplateListResponse,
    DeviceUpdate,
    RecentReadingRow,
    RecentReadingsResponse,
    SensorPointCreate,
    SensorPointResponse,
    SensorPointUpdate,
    TestTelemetryResponse,
)
from app.services import access, device_templates
from app.utils.jwt import get_current_user_id

router = APIRouter(tags=["connections"])


def _building_for_manage(db: Session, building_id: UUID, user_id: UUID) -> Building:
    """Load a building by UUID, gated by manage rights. 404 otherwise.

    Mirrors buildings._building_for_write so the connection endpoints share the
    same visibility/authorization as the consumption + KPI endpoints.
    """
    building = db.get(Building, building_id)
    if (
        building is None
        or not building.is_active
        or not access.can_manage_building(db, user_id=user_id, building=building)
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    return building


def _point_to_response(p: SensorPoint) -> SensorPointResponse:
    return SensorPointResponse(
        id=p.id,
        device_id=p.device_id,
        point_ref=p.point_ref,
        sensor_type=p.sensor_type,
        zone=p.zone,
        unit=p.unit,
        scale=float(p.scale),
        enabled=p.enabled,
    )


def _device_to_response(d: Device) -> DeviceResponse:
    return DeviceResponse(
        id=d.id,
        building_id=d.building_id,
        name=d.name,
        protocol=d.protocol,
        connection_config=d.connection_config,
        status=d.status,
        template_key=d.template_key,
        last_seen_at=d.last_seen_at,
        points=sorted(
            (_point_to_response(p) for p in d.points), key=lambda x: x.point_ref
        ),
    )


# --- device templates (static catalog) ------------------------------------


@router.get("/device-templates", response_model=DeviceTemplateListResponse)
def get_device_templates(
    user_id: Annotated[UUID, Depends(get_current_user_id)],
) -> DeviceTemplateListResponse:
    """Built-in device templates + the normalized sensor_type vocabulary."""
    return DeviceTemplateListResponse(
        templates=device_templates.list_templates(),
        sensor_types=device_templates.SENSOR_TYPES,
    )


# --- devices ---------------------------------------------------------------


@router.get("/buildings/{building_id}/devices", response_model=DeviceListResponse)
def list_devices(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> DeviceListResponse:
    """All devices (with their points) on a building."""
    _building_for_manage(db, building_id, user_id)
    devices = conn_repo.list_devices(db, building_id=building_id)
    return DeviceListResponse(devices=[_device_to_response(d) for d in devices])


@router.post(
    "/buildings/{building_id}/devices",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_device(
    building_id: UUID,
    body: DeviceCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> DeviceResponse:
    """Create a device. template_key seeds the point map; inline points merge in."""
    _building_for_manage(db, building_id, user_id)

    merged: list[dict] = []
    if body.template_key:
        tmpl = device_templates.get_template(body.template_key)
        if tmpl is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown device template '{body.template_key}'",
            )
        for tp in tmpl.points:
            merged.append(
                {
                    "point_ref": tp.point_ref,
                    "sensor_type": tp.sensor_type,
                    "zone": None,
                    "unit": tp.unit,
                    "scale": tp.scale,
                    "enabled": True,
                }
            )
    merged.extend(p.model_dump() for p in body.points)

    device = conn_repo.create_device(
        db,
        building_id=building_id,
        name=body.name,
        protocol=body.protocol,
        connection_config=body.connection_config,
        template_key=body.template_key,
        points=merged,
    )
    db.commit()
    fresh = conn_repo.get_device(db, building_id=building_id, device_id=device.id)
    return _device_to_response(fresh)


@router.patch(
    "/buildings/{building_id}/devices/{device_id}", response_model=DeviceResponse
)
def update_device(
    building_id: UUID,
    device_id: UUID,
    body: DeviceUpdate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> DeviceResponse:
    """Patch a device (name / connection_config / status)."""
    _building_for_manage(db, building_id, user_id)
    device = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    conn_repo.update_device(db, device=device, fields=body.model_dump(exclude_unset=True))
    db.commit()
    fresh = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    return _device_to_response(fresh)


@router.delete(
    "/buildings/{building_id}/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_device(
    building_id: UUID,
    device_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a device (cascades to its points)."""
    _building_for_manage(db, building_id, user_id)
    device = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    conn_repo.delete_device(db, device=device)
    db.commit()


# --- sensor points ---------------------------------------------------------


@router.post(
    "/buildings/{building_id}/devices/{device_id}/points",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_point(
    building_id: UUID,
    device_id: UUID,
    body: SensorPointCreate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> DeviceResponse:
    """Add one point to a device. Returns the updated device."""
    _building_for_manage(db, building_id, user_id)
    device = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if any(p.point_ref == body.point_ref for p in device.points):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Point '{body.point_ref}' already exists on this device",
        )
    conn_repo.add_point(db, device_id=device_id, point=body.model_dump())
    db.commit()
    fresh = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    return _device_to_response(fresh)


@router.patch(
    "/buildings/{building_id}/devices/{device_id}/points/{point_id}",
    response_model=DeviceResponse,
)
def update_point(
    building_id: UUID,
    device_id: UUID,
    point_id: UUID,
    body: SensorPointUpdate,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> DeviceResponse:
    """Patch a point (point_ref / sensor_type / zone / unit / scale / enabled)."""
    _building_for_manage(db, building_id, user_id)
    device = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    point = conn_repo.get_point(db, device_id=device_id, point_id=point_id)
    if point is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    conn_repo.update_point(db, point=point, fields=body.model_dump(exclude_unset=True))
    db.commit()
    fresh = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    return _device_to_response(fresh)


@router.delete(
    "/buildings/{building_id}/devices/{device_id}/points/{point_id}",
    response_model=DeviceResponse,
)
def delete_point(
    building_id: UUID,
    device_id: UUID,
    point_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> DeviceResponse:
    """Delete a point. Returns the updated device."""
    _building_for_manage(db, building_id, user_id)
    device = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    point = conn_repo.get_point(db, device_id=device_id, point_id=point_id)
    if point is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Point not found")
    conn_repo.delete_point(db, point=point)
    db.commit()
    fresh = conn_repo.get_device(db, building_id=building_id, device_id=device_id)
    return _device_to_response(fresh)


# --- pipeline verification (test telemetry + recent landed readings) -------


_SIM_DEFAULTS = [
    ("power", "kW", 20.0, 80.0),
    ("temperature", "°C", 19.0, 24.0),
    ("co2", "ppm", 450.0, 900.0),
]


def _sim_reading(sensor_type: str, unit: str | None) -> tuple[float, str | None]:
    """A plausible synthetic value for a sensor_type (clearly-marked test data)."""
    st = (sensor_type or "").lower()
    # Heat-pump pair first (both contain "kwh"): plausible so a test batch shows COP ~3.
    if "heat_output" in st:
        return round(random.uniform(10, 24), 2), unit or "kWh"
    if "heatpump_elec" in st:
        return round(random.uniform(3, 8), 2), unit or "kWh"
    if "co2" in st:
        return round(random.uniform(450, 900), 1), unit or "ppm"
    if "humid" in st:
        return round(random.uniform(40, 60), 1), unit or "%"
    if "temp" in st:
        return round(random.uniform(19, 24), 1), unit or "°C"
    if "kwh" in st or "energy" in st:
        return round(random.uniform(5, 40), 2), unit or "kWh"
    if "solar" in st or "pv" in st or "gen" in st:
        return round(random.uniform(0, 50), 2), unit or "kW"
    if "power" in st or "kw" in st or "load" in st:
        return round(random.uniform(20, 80), 2), unit or "kW"
    return round(random.uniform(1, 100), 2), unit


@router.post(
    "/buildings/{building_id}/test-telemetry", response_model=TestTelemetryResponse
)
def send_test_telemetry(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> TestTelemetryResponse:
    """Push a few SIMULATED readings through the live ingest path (bronze_iot_readings).

    Lets a manager confirm the pipeline end-to-end without hardware. Readings are
    tagged source_protocol='simulated' and DO NOT change any device status --
    device status only ever reflects a real on-site agent reporting in.
    """
    building = _building_for_manage(db, building_id, user_id)
    bid = building.fabric_building_id or str(building.id)
    now = datetime.now(dt_timezone.utc)

    rows: list[dict] = []
    for d in conn_repo.list_devices(db, building_id=building_id):
        for pt in d.points:
            if not pt.enabled:
                continue
            value, unit = _sim_reading(pt.sensor_type, pt.unit)
            rows.append(
                {
                    "agent_building_uuid": building.id,
                    "building_id": bid,
                    "device_id": str(d.id),
                    "sensor_type": pt.sensor_type,
                    "sensor_location": pt.zone,
                    "reading_value": value,
                    "reading_unit": unit,
                    "source_protocol": "simulated",
                    "reading_quality": 1,
                    "source_timestamp": now,
                }
            )

    if not rows:  # no points mapped yet -- emit a small default set so the path still proves out
        for st, unit, lo, hi in _SIM_DEFAULTS:
            rows.append(
                {
                    "agent_building_uuid": building.id,
                    "building_id": bid,
                    "device_id": "sim",
                    "sensor_type": st,
                    "sensor_location": "test",
                    "reading_value": round(random.uniform(lo, hi), 2),
                    "reading_unit": unit,
                    "source_protocol": "simulated",
                    "reading_quality": 1,
                    "source_timestamp": now,
                }
            )

    accepted = ingest_repo.insert_readings(db, rows)
    return TestTelemetryResponse(accepted=accepted, building_id=bid)


@router.get(
    "/buildings/{building_id}/recent-readings", response_model=RecentReadingsResponse
)
def recent_readings(
    building_id: UUID,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
) -> RecentReadingsResponse:
    """Most recent landed readings for the building (real + simulated, tagged)."""
    building = _building_for_manage(db, building_id, user_id)
    bid = building.fabric_building_id or str(building.id)
    stmt = (
        select(IotReading)
        .where(IotReading.building_id.in_({bid, str(building.id)}))
        .order_by(IotReading.received_at.desc())
        .limit(max(1, min(limit, 100)))
    )
    rows = db.execute(stmt).scalars().all()
    return RecentReadingsResponse(
        readings=[
            RecentReadingRow(
                sensor_type=r.sensor_type,
                reading_value=r.reading_value,
                reading_unit=r.reading_unit,
                sensor_location=r.sensor_location,
                source_protocol=r.source_protocol,
                received_at=r.received_at,
                simulated=(r.source_protocol == "simulated"),
            )
            for r in rows
        ]
    )
