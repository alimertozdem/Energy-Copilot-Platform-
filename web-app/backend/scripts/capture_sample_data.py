"""Capture the logged-in data pages for the demo org so the cloud backend can
serve them when Fabric is unreachable.

Run on a machine WITH Fabric access (your laptop), from web-app/backend:

    python scripts/capture_sample_data.py

Writes app/data/sample_fallback.json (bundled into the image on next deploy).
Override the org owner's email with DEMO_CAPTURE_EMAIL if needed.
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env", override=True)

from app.db.database import SessionLocal            # noqa: E402
from app.db.models.user import User                 # noqa: E402
from app.repositories import building as building_repo  # noqa: E402
from app.services import (                           # noqa: E402
    abatement,
    actions_data,
    alerts_data,
    portfolio_metrics,
    solar_detail,
)

EMAIL = os.getenv("DEMO_CAPTURE_EMAIL", "alimertozdem@gmail.com")
OUT = BACKEND_DIR / "app" / "data" / "sample_fallback.json"


def main() -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == EMAIL).first()
        if user is None:
            print(f"User not found: {EMAIL}. Set DEMO_CAPTURE_EMAIL to the org owner.")
            return 1
        buildings = building_repo.list_buildings_for_user(db, user_id=user.id)
        fabric_ids = sorted(b.fabric_building_id for b in buildings if b.fabric_building_id)
        print(f"{EMAIL} -> {len(fabric_ids)} fabric-linked buildings: {fabric_ids}")
        if not fabric_ids:
            print("No fabric-linked buildings for this user; nothing to capture.")
            return 1

        snap: dict = {"scope": fabric_ids}

        def cap(key, fn):
            try:
                snap[key] = fn().model_dump(mode="json")
                print(f"  captured {key}")
            except Exception as e:  # keep going; partial capture is still useful
                print(f"  FAILED {key}: {e!r}")

        cap("portfolio_kpis", lambda: portfolio_metrics.get_portfolio_kpis(fabric_ids))
        cap("portfolio_buildings", lambda: portfolio_metrics.get_portfolio_buildings(fabric_ids))
        cap("solar_detail", lambda: solar_detail.get_solar_detail(fabric_ids))
        cap("actions", lambda: actions_data.get_actions_for_user(
            db, user_id=user.id, status_filter=None, building_id=None,
            category=None, limit=500))
        cap("alerts", lambda: alerts_data.get_alerts_for_user(
            db, user_id=user.id, severity=None, building_id=None,
            unresolved_only=False, resolution=None, limit=500))
        cap("abatement", lambda: abatement.get_macc_for_user(
            db, user_id=user.id, building_id=None, limit=500))

        OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2, default=str)
        pages = [k for k in snap if k != "scope"]
        print(f"\nWrote {OUT}\n  scope={len(fabric_ids)} buildings, pages={pages}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
