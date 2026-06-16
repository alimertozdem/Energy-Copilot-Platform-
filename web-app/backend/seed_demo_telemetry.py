"""Seed SIMULATED telemetry into bronze_iot_readings for ONE building, so the
COP / comfort / live-monitoring / HVAC-comfort panels populate on a demo account
(sample buildings can't use the in-app "Send test reading" button, which is
manage-gated). Every row is tagged source_protocol='simulated' — honest.

Usage (from web-app/backend, venv active):
    python seed_demo_telemetry.py <fabric_id_or_uuid> [days=14]

Clear later:
    DELETE FROM bronze_iot_readings WHERE source_protocol='simulated' AND building_id='<bid>';
"""
import math
import random
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select

from app.db.database import SessionLocal
from app.db.models import Building
from app.repositories import ingest as ingest_repo


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python seed_demo_telemetry.py <fabric_id_or_uuid> [days=14]")
        sys.exit(1)
    key = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 14

    db = SessionLocal()
    try:
        b = db.scalar(
            select(Building).where(
                or_(Building.fabric_building_id == key, Building.id == key)
            )
        )
        if b is None:
            print(f"No building matched '{key}' (try a fabric id like B001 or the UUID).")
            sys.exit(1)
        bid = b.fabric_building_id or str(b.id)
        now = datetime.now(timezone.utc)
        rows: list[dict] = []
        heat_ctr = 0.0   # cumulative thermal counter (kWh_th)
        elec_ctr = 0.0   # cumulative heat-pump electricity counter (kWh_el), COP ~3

        def add(st, val, unit, ts, zone=None):
            rows.append({
                "agent_building_uuid": b.id, "building_id": bid, "device_id": "sim-demo",
                "sensor_type": st, "sensor_location": zone, "reading_value": round(val, 2),
                "reading_unit": unit, "source_protocol": "simulated", "reading_quality": 1,
                "source_timestamp": ts,
            })

        hours = days * 24
        for h in range(hours):
            ts = now - timedelta(hours=hours - h)
            hod = ts.hour
            occupied = 7 <= hod <= 19
            # diurnal zone temp: ~22 base, warmer midday; ~20% of samples nudge >24
            temp = 21.5 + 2.0 * math.sin((hod - 9) / 24 * 2 * math.pi) + random.uniform(-0.8, 1.4)
            add("HVAC_temp", temp, "°C", ts, "Zone 1")
            add("CO2", (700 if occupied else 480) + random.uniform(-80, 520 if occupied else 80), "ppm", ts, "Zone 1")
            add("humidity", random.uniform(40, 55), "%", ts, "Zone 1")
            add("HVAC_supply_temp", 44 + random.uniform(-2, 3), "°C", ts)
            add("HVAC_return_temp", 37 + random.uniform(-2, 2), "°C", ts)
            power = (55 if occupied else 22) + random.uniform(-6, 14)
            add("building_kwh", power, "kW", ts)
            add("hvac_kwh", power * random.uniform(0.32, 0.45), "kW", ts)
            # cumulative counters -> COP = Δheat/Δelec ≈ 3
            heat_inc = (9.0 if occupied else 3.5) + random.uniform(-1, 1.5)
            heat_ctr += max(0.0, heat_inc)
            elec_ctr += max(0.0, heat_inc) / (3.0 + random.uniform(-0.2, 0.2))
            add("heat_output_kwh", heat_ctr, "kWh", ts)
            add("heatpump_elec_kwh", elec_ctr, "kWh", ts)

        accepted = ingest_repo.insert_readings(db, rows)
        print(f"Seeded {accepted} simulated readings for {b.name} (building_id={bid}) over {days} days.")
        print("COP, comfort, live-monitoring and the HVAC comfort layer will now populate (tagged Simulated).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
