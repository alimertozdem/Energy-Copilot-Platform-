"""Live monitoring summary from bronze_iot_readings (web-app-native, Postgres).

The latest value per sensor_type for a building over a recent window, plus
freshness and a real/simulated basis. This is the app-native counterpart to the
Power BI IoT page (which stays on the Fabric embed path) -- same bronze source
the COP + verify-panel use, so a building with connected devices OR test data
shows live data here without Fabric.
"""
from datetime import datetime, timedelta, timezone as dt_timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.iot_reading import IotReading

# Display order for known sensor types (power first, then climate, then the rest).
_POWER = ["building_kwh", "hvac_kwh", "lighting_kwh", "plug_load_kwh", "building_energy_kwh"]
_CLIMATE = ["HVAC_temp", "HVAC_supply_temp", "HVAC_return_temp", "humidity", "CO2"]


def latest_monitoring(db: Session, building, hours: int = 24) -> dict:
    """Latest reading per sensor_type for a building in the last `hours`."""
    hours = max(1, min(int(hours), 24 * 30))
    bid = building.fabric_building_id or str(building.id)
    since = datetime.now(dt_timezone.utc) - timedelta(hours=hours)
    rows = db.execute(
        select(
            IotReading.sensor_type,
            IotReading.reading_value,
            IotReading.reading_unit,
            IotReading.sensor_location,
            IotReading.source_protocol,
            IotReading.received_at,
        )
        .where(
            IotReading.building_id.in_({bid, str(building.id)}),
            IotReading.received_at >= since,
        )
        .order_by(IotReading.received_at.desc())
    ).all()

    latest: dict[str, dict] = {}
    count = 0
    last_at = None
    has_real = False
    has_sim = False
    for st, val, unit, loc, sp, rec in rows:
        count += 1
        if last_at is None:
            last_at = rec
        if sp == "simulated":
            has_sim = True
        else:
            has_real = True
        if st not in latest:  # desc order -> first seen is the most recent
            latest[st] = {
                "sensor_type": st,
                "value": float(val) if val is not None else None,
                "unit": unit,
                "zone": loc,
                "received_at": rec,
                "simulated": sp == "simulated",
            }

    def order_key(item: dict):
        st = item["sensor_type"]
        if st in _POWER:
            return (0, _POWER.index(st))
        if st in _CLIMATE:
            return (1, _CLIMATE.index(st))
        return (2, st)

    sensors = sorted(latest.values(), key=order_key)
    basis = "live" if has_real else ("simulated" if has_sim else "none")
    return {
        "sensors": sensors,
        "reading_count": count,
        "window_hours": hours,
        "last_reading_at": last_at,
        "basis": basis,
    }
