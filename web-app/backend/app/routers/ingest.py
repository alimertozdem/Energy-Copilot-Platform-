"""Telemetry ingest router (SCADA/IoT Phase A, ADR-001).

POST /ingest/telemetry -- the on-site edge agent pushes 5-15 min micro-batches of
normalized readings here. Authenticated ONLY by the building-scoped X-Agent-Token
(reuses get_agent_building from the agent router) -- never the user JWT. A reading
is rejected if its building_id does not match the token's building, so an agent
can only ever write its own building's telemetry.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Building
from app.repositories import ingest as ingest_repo
from app.routers.agent import get_agent_building
from app.schemas.ingest import MAX_BATCH, TelemetryBatch, TelemetryIngestResponse

router = APIRouter(tags=["ingest"])


@router.post("/ingest/telemetry", response_model=TelemetryIngestResponse)
def ingest_telemetry(
    body: TelemetryBatch,
    building: Annotated[Building, Depends(get_agent_building)],
    db: Annotated[Session, Depends(get_db)],
) -> TelemetryIngestResponse:
    """Land a micro-batch of normalized readings into bronze_iot_readings."""
    if len(body.readings) > MAX_BATCH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Batch too large (> {MAX_BATCH} readings)",
        )

    bid = building.fabric_building_id or str(building.id)
    allowed = {bid, str(building.id)}

    rows: list[dict] = []
    rejected = 0
    for r in body.readings:
        # Security: an agent may only write telemetry for its own building.
        if r.building_id not in allowed:
            rejected += 1
            continue
        rows.append(
            {
                "agent_building_uuid": building.id,
                "building_id": bid,
                "device_id": r.device_id,
                "sensor_type": r.sensor_type,
                "sensor_location": r.sensor_location,
                "reading_value": r.reading_value,
                "reading_unit": r.reading_unit,
                "source_protocol": r.source_protocol,
                "reading_quality": r.reading_quality,
                "source_timestamp": r.timestamp,
            }
        )

    accepted = ingest_repo.insert_readings(db, rows)
    return TelemetryIngestResponse(building_id=bid, accepted=accepted, rejected=rejected)
