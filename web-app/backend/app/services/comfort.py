"""Comfort & operation analytics from bronze_iot_readings (Postgres-native).

Turns raw climate telemetry into operational insight for the Heating & HVAC page:
zone-temperature setpoint compliance, over-/under-heating share, supply/return
delta-T, CO2 air-quality, humidity. When over-heating is significant it surfaces
the operational savings lever (setback / setpoint / heating curve, ~7-11%).

Comfort references are STANDARD, not invented (stated in the UI):
  * Heating comfort band 20-24 C  (DIN EN 16798-1 Category II)
  * CO2  good < 800, fair 800-1200, poor > 1200 ppm  (DIN EN 16798 / common IAQ)
  * Relative humidity comfort 30-60 %
delta-T is reported as measured (no hard pass/fail); interpretation is contextual.
"""
from datetime import datetime, timedelta, timezone as dt_timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.iot_reading import IotReading

TEMP_LOW, TEMP_HIGH = 20.0, 24.0
CO2_GOOD, CO2_POOR = 800.0, 1200.0
RH_LOW, RH_HIGH = 30.0, 60.0


def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total else 0.0


def assess_comfort(db: Session, building, hours: int = 168) -> dict:
    """Comfort/operation summary over the last `hours` (default 7 days)."""
    hours = max(1, min(int(hours), 24 * 90))
    bid = building.fabric_building_id or str(building.id)
    since = datetime.now(dt_timezone.utc) - timedelta(hours=hours)
    rows = db.execute(
        select(IotReading.sensor_type, IotReading.reading_value, IotReading.source_protocol)
        .where(
            IotReading.building_id.in_({bid, str(building.id)}),
            IotReading.sensor_type.in_(
                {"HVAC_temp", "HVAC_supply_temp", "HVAC_return_temp", "CO2", "humidity"}
            ),
            IotReading.received_at >= since,
        )
    ).all()

    temp = [float(v) for st, v, _ in rows if st == "HVAC_temp" and v is not None]
    supply = [float(v) for st, v, _ in rows if st == "HVAC_supply_temp" and v is not None]
    ret = [float(v) for st, v, _ in rows if st == "HVAC_return_temp" and v is not None]
    co2 = [float(v) for st, v, _ in rows if st == "CO2" and v is not None]
    rh = [float(v) for st, v, _ in rows if st == "humidity" and v is not None]
    simulated = any(sp == "simulated" for _, _, sp in rows)

    temp_block = None
    if temp:
        under = sum(1 for v in temp if v < TEMP_LOW)
        over = sum(1 for v in temp if v > TEMP_HIGH)
        in_band = len(temp) - under - over
        temp_block = {
            "avg": round(sum(temp) / len(temp), 1),
            "in_band_pct": _pct(in_band, len(temp)),
            "under_pct": _pct(under, len(temp)),
            "over_pct": _pct(over, len(temp)),
            "samples": len(temp),
            "band_low": TEMP_LOW,
            "band_high": TEMP_HIGH,
        }

    co2_block = None
    if co2:
        good = sum(1 for v in co2 if v < CO2_GOOD)
        poor = sum(1 for v in co2 if v > CO2_POOR)
        fair = len(co2) - good - poor
        co2_block = {
            "avg": round(sum(co2) / len(co2)),
            "good_pct": _pct(good, len(co2)),
            "fair_pct": _pct(fair, len(co2)),
            "poor_pct": _pct(poor, len(co2)),
            "samples": len(co2),
        }

    rh_block = None
    if rh:
        in_band = sum(1 for v in rh if RH_LOW <= v <= RH_HIGH)
        rh_block = {"avg": round(sum(rh) / len(rh)), "in_band_pct": _pct(in_band, len(rh)), "samples": len(rh)}

    delta_t = None
    if supply and ret:
        delta_t = round(sum(supply) / len(supply) - sum(ret) / len(ret), 1)

    # Operational savings hook: meaningful over-heating => setback/curve opportunity.
    op_hint = None
    if temp_block and temp_block["over_pct"] >= 15.0:
        op_hint = (
            f"{temp_block['over_pct']}% of readings are above {TEMP_HIGH}°C — lowering setpoints / "
            "night setback / a heating-curve tune typically cuts heating ~7-11% (see retrofit measures)."
        )

    has_any = any([temp_block, co2_block, rh_block, delta_t is not None])
    return {
        "has_data": has_any,
        "window_hours": hours,
        "simulated": simulated,
        "temperature": temp_block,
        "co2": co2_block,
        "humidity": rh_block,
        "delta_t": delta_t,
        "operational_hint": op_hint,
    }
