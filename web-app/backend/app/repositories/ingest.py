"""Bulk insert of landed telemetry readings into bronze_iot_readings."""
from typing import Any

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.db.models.iot_reading import IotReading


def insert_readings(db: Session, rows: list[dict[str, Any]]) -> int:
    """Append rows (column-name dicts) to the bronze landing. Returns count."""
    if not rows:
        return 0
    db.execute(insert(IotReading), rows)
    db.commit()
    return len(rows)
