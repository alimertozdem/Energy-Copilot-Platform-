"""Backfill realistic SIMULATED solar telemetry into bronze_iot_readings (DEMO).

Writes plausible inverter (pv_ac_power, irradiance) + building-load readings with a
daily solar bell curve and per-day weather variation, for the PV buildings over the
last N days, tagged source_protocol='Simulated'. The roll-up then marks those gold
rows data_source='simulated' -> /solar shows them under a distinct "Simulated demo
feed" badge (NOT real-live, NOT synthetic-sample). For demos only; not real data.

    python scripts/backfill_solar_telemetry.py [--days 30] [--interval-min 15]
        [--building B007 ...] [--keep]
"""
import argparse
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env", override=True)

from sqlalchemy import insert, text          # noqa: E402
from app.db.database import SessionLocal      # noqa: E402
from app.db.models.iot_reading import IotReading  # noqa: E402
from app.services import solar_telemetry_rollup as rollup  # noqa: E402


def _solar_frac(hour: float) -> float:
    if hour < 5.0 or hour > 21.0:
        return 0.0
    return max(0.0, math.sin(math.pi * (hour - 5.0) / 16.0))


def _build_rows(bid: str, bid_uuid, kwp: float, days: int, interval_min: int) -> list[dict]:
    rng = random.Random(abs(hash(bid)) & 0xFFFF)
    today = datetime.now(timezone.utc).date()
    dev = f"{bid}_INV1"
    rows: list[dict] = []
    for d in range(days, 0, -1):
        day = today - timedelta(days=d)
        cloud = round(rng.uniform(0.55, 1.0), 3)   # whole-day weather factor
        t = datetime(day.year, day.month, day.day, 4, 0, tzinfo=timezone.utc)
        end = datetime(day.year, day.month, day.day, 21, 0, tzinfo=timezone.utc)
        while t <= end:
            h = t.hour + t.minute / 60.0
            frac = _solar_frac(h)
            pv = 0.80 * kwp * frac * cloud * (1 + rng.uniform(-0.05, 0.05))
            pv = max(0.0, min(kwp, pv))
            irr = 1000.0 * frac * cloud
            load = 0.08 * kwp + 0.18 * kwp * frac * rng.uniform(0.9, 1.1)
            for st, val, unit, loc in (
                ("pv_ac_power", round(pv, 3), "kW", "Roof PV"),
                ("irradiance", round(irr, 1), "W/m2", "Roof PV"),
                ("building_power", round(load, 3), "kW", "Main meter"),
            ):
                rows.append({
                    "agent_building_uuid": bid_uuid,
                    "building_id": bid,
                    "device_id": dev,
                    "sensor_type": st,
                    "sensor_location": loc,
                    "reading_value": val,
                    "reading_unit": unit,
                    "source_protocol": "Simulated",
                    "reading_quality": 100,
                    "source_timestamp": t,
                })
            t += timedelta(minutes=interval_min)
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description="Backfill SIMULATED solar telemetry (demo)")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--interval-min", type=int, default=15)
    p.add_argument("--building", action="append", default=[], help="limit to building id(s); default all PV")
    p.add_argument("--keep", action="store_true", help="do NOT delete existing bronze rows for the targets first")
    a = p.parse_args()

    db = SessionLocal()
    try:
        q = ("SELECT m.building_id, m.pv_capacity_kwp, b.id AS uuid "
             "FROM mv_building_master m "
             "JOIN buildings b ON b.fabric_building_id = m.building_id "
             "WHERE m.has_pv = true")
        params: dict = {}
        if a.building:
            q += " AND m.building_id = ANY(:bids)"
            params["bids"] = a.building
        targets = db.execute(text(q), params).mappings().all()
        if not targets:
            print("No PV buildings matched (need a buildings row with that fabric_building_id).")
            return 1
        bids = [t["building_id"] for t in targets]
        print(f"targets ({len(bids)}): {bids}")

        if not a.keep:
            db.execute(text("DELETE FROM bronze_iot_readings WHERE building_id = ANY(:b)"), {"b": bids})
            db.execute(text("DELETE FROM gold_solar_daily WHERE building_id = ANY(:b)"), {"b": bids})
            db.commit()
            print(f"cleared existing bronze + gold_solar_daily rows for {len(bids)} building(s)")

        total = 0
        for t in targets:
            uuid_val = t["uuid"] if isinstance(t["uuid"], UUID) else UUID(str(t["uuid"]))
            rows = _build_rows(t["building_id"], uuid_val, float(t["pv_capacity_kwp"] or 0),
                               a.days, a.interval_min)
            for i in range(0, len(rows), 2000):
                db.execute(insert(IotReading), rows[i:i + 2000])
            db.commit()
            total += len(rows)
            print(f"  {t['building_id']}: {len(rows)} readings ({a.days}d @ {a.interval_min}min, {t['pv_capacity_kwp']} kWp)")

        print(f"inserted {total} SIMULATED readings into bronze_iot_readings")
        n = rollup.run_rollup(db, building_ids=bids)
        print(f"rolled up {n} gold_solar_daily row(s) (data_source='simulated')")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
