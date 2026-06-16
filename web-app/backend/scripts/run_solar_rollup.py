"""Run the solar telemetry roll-up: bronze_iot_readings -> gold_solar_daily.

Phase A (ADR-001). Schedule on the backend Container App (cron), e.g. every 15 min
or hourly. Run from web-app/backend:
    python scripts/run_solar_rollup.py [--since 2026-06-01] [--building B007 ...]
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))   # so `python scripts/x.py` finds the app package
load_dotenv(BACKEND_DIR / ".env", override=True)

from app.db.database import SessionLocal            # noqa: E402
from app.services import solar_telemetry_rollup as rollup  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Solar telemetry roll-up (Phase A)")
    p.add_argument("--since", help="only readings on/after this date (YYYY-MM-DD)")
    p.add_argument("--building", action="append", default=[], help="limit to building id(s)")
    a = p.parse_args()
    since = datetime.fromisoformat(a.since).date() if a.since else None
    db = SessionLocal()
    try:
        n = rollup.run_rollup(db, building_ids=a.building or None, since=since)
        print(f"upserted {n} building-day row(s) into gold_solar_daily")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
