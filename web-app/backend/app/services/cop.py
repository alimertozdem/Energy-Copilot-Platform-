"""Measured COP / SPF from landed telemetry (bronze_iot_readings).

COP = delivered heat (kWh_th) / heat-pump electricity in (kWh_el), over a window.
Requires BOTH a heat meter (sensor_type 'heat_output_kwh') AND the pump's
electricity input ('heatpump_elec_kwh') -- electricity alone can never yield COP.

Energy per metric is robust to the two common meter modes:
  * cumulative counter -> energy = max - min over the window (when >0 and >1 sample)
  * interval energy    -> energy = sum (fallback; also covers a single test batch)

If the controller instead reports COP directly ('chiller_cop'), that value is
surfaced as device-reported. Otherwise status is 'needs_heat_meter' so the UI
never invents a COP from electricity alone (energy-logic guardrail).
"""
from datetime import datetime, timedelta, timezone as dt_timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.iot_reading import IotReading

HEAT = "heat_output_kwh"
ELEC = "heatpump_elec_kwh"
DEV_COP = "chiller_cop"


def _energy(values: list[float]) -> float:
    """Energy from a metric's readings: counter-delta if increasing, else sum."""
    if not values:
        return 0.0
    delta = max(values) - min(values)
    if delta > 0 and len(values) > 1:
        return delta
    return sum(v for v in values if v and v > 0)


def compute_cop(db: Session, building, days: int = 30) -> dict:
    """Measured COP for a building, or device-reported, or needs_heat_meter."""
    days = max(1, min(int(days), 365))
    bid = building.fabric_building_id or str(building.id)
    since = datetime.now(dt_timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(
            IotReading.sensor_type,
            IotReading.reading_value,
            IotReading.source_protocol,
        ).where(
            IotReading.building_id.in_({bid, str(building.id)}),
            IotReading.sensor_type.in_({HEAT, ELEC, DEV_COP}),
            IotReading.received_at >= since,
        )
    ).all()

    heat = [float(v) for st, v, _ in rows if st == HEAT and v is not None]
    elec = [float(v) for st, v, _ in rows if st == ELEC and v is not None]
    dev = [float(v) for st, v, _ in rows if st == DEV_COP and v is not None]
    simulated = any(sp == "simulated" for _, _, sp in rows)

    heat_kwh = _energy(heat)
    elec_kwh = _energy(elec)

    if heat_kwh > 0 and elec_kwh > 0:
        return {
            "status": "measured",
            "cop": round(heat_kwh / elec_kwh, 2),
            "heat_kwh": round(heat_kwh, 1),
            "elec_kwh": round(elec_kwh, 1),
            "window_days": days,
            "basis": "heat meter / electricity",
            "simulated": simulated,
        }
    if dev:
        return {
            "status": "device_reported",
            "cop": round(sum(dev) / len(dev), 2),
            "heat_kwh": None,
            "elec_kwh": None,
            "window_days": days,
            "basis": "reported by the device controller",
            "simulated": simulated,
        }
    return {
        "status": "needs_heat_meter",
        "cop": None,
        "heat_kwh": round(heat_kwh, 1) if heat_kwh else None,
        "elec_kwh": round(elec_kwh, 1) if elec_kwh else None,
        "window_days": days,
        "basis": None,
        "simulated": simulated,
    }
