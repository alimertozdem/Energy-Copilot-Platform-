"""Devices & Connections router -- Tier-2/3 connection wiring CRUD.

UUID-addressed by building (works for buildings still pending a Fabric bridge)
and manage-gated (only org admins/managers, or full_manage partners, may
mutate -- same gate as the consumption + KPI endpoints). An edge agent / poller
consumes this config to collect live data; the backend itself never reaches
on-prem devices (firewall), so there is NO live connection test here -- a
device stays 'pending' until a collector reports in.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Building
from app.db.models.connection import Device, SensorPoint
from app.repositories import connection as conn_repo
from app.schemas.connection import (
    DeviceCreate,
    DeviceListResponse,
    DeviceResponse,
    DeviceTemplateListResponse,
    DeviceUpdate,
    SensorPointCreate,
    SensorPointResponse,
    SensorPointUpdate,
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
