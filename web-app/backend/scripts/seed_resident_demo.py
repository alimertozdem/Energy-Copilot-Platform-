"""Seed a demo resident for testing the /residence flow (P4-3 issue path).

Creates (idempotently) a resident_identity + a unit (bridged to a Fabric gold
unit) + an active tenancy, then mints a fresh single-use magic-link token and
prints BOTH sign-in paths:

  * the magic link      -> /residence/enter?token=<raw>     (the real P4-3 flow)
  * the dev direct link -> /residence?resident=<identity>   (needs RESIDENT_DEV_MODE=1)

Usage (from web-app/backend, with the venv + .env active):
    python scripts/seed_resident_demo.py
    FABRIC_UNIT_ID=B011-U0102 RESIDENT_EMAIL=tenant@example.com python scripts/seed_resident_demo.py

The fabric_unit_id must match a unit that has rows in the residential Gold tables
(the sample pipeline seeds B011-U0101.. under building B011). The unit is attached
to an existing Postgres building purely for the FK; the Gold read keys on unit_id.
"""
import hashlib
import os
import secrets
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

# Make the 'app' package importable + load .env when run directly as a script
# (works with `python scripts/seed_resident_demo.py` and `python -m scripts.seed_resident_demo`).
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env", override=True)

from sqlalchemy import select  # noqa: E402

from app.db.database import SessionLocal  # noqa: E402
from app.db.models import Building  # noqa: E402
from app.db.models.residential import (  # noqa: E402
    ResidentIdentity,
    ResidentInviteToken,
    Unit,
    UnitResident,
)
from app.db.models.building import BuildingModule  # noqa: E402

FABRIC_BUILDING_ID = os.getenv("FABRIC_BUILDING_ID", "B011")
FABRIC_UNIT_ID = os.getenv("FABRIC_UNIT_ID", "B011-U0101")
RESIDENT_EMAIL = os.getenv("RESIDENT_EMAIL", "resident.demo@example.com")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
TOKEN_TTL_DAYS = 14


def main() -> int:
    db = SessionLocal()
    try:
        # 1. Find-or-create a RESIDENTIAL Postgres building bridged to B011, so it
        #    shows on /buildings, /residential, and the building nav. The gold data
        #    lives in Fabric under building_id=B011; this row mirrors + types it.
        building = db.scalar(
            select(Building).where(Building.fabric_building_id == FABRIC_BUILDING_ID)
        )
        if building is None:
            org_id_env = os.getenv("ORG_ID")
            if org_id_env:
                org_id = UUID(org_id_env)
            else:
                refs = list(db.scalars(select(Building)).all())
                ref = next((b for b in refs if not b.organization.is_sample), None) or (
                    refs[0] if refs else None
                )
                if ref is None:
                    print("ERROR: no building/org in Postgres. Onboard one first (/onboarding).")
                    return 1
                org_id = ref.organization_id
            building = Building(
                organization_id=org_id,
                fabric_building_id=FABRIC_BUILDING_ID,
                name="Berlin Wohnanlage B011",
                building_type="Residential_MF",
                city="Berlin",
                country_code="DE",
            )
            db.add(building)
            db.flush()
        elif "residential" not in (building.building_type or "").lower():
            building.building_type = "Residential_MF"  # ensure it surfaces as residential

        # 1b. Cosmetic: fill the card fields + a 'meters' module so B011 looks like
        #     the other buildings in the list (area/year are display-only; the EUI
        #     denominator uses the per-unit area from silver_unit_master, not this).
        if building.floor_area_m2 is None:
            building.floor_area_m2 = 4200
        if building.construction_year is None:
            building.construction_year = 1994
        has_meters = db.scalar(
            select(BuildingModule).where(
                BuildingModule.building_id == building.id,
                BuildingModule.module_key == "meters",
            )
        )
        if has_meters is None:
            db.add(BuildingModule(building_id=building.id, module_key="meters", enabled=True))
        db.flush()

        # 2. Find-or-create the unit (bridged to the gold unit); repoint if it was
        #    attached to the wrong building by an earlier run.
        unit = db.scalar(select(Unit).where(Unit.fabric_unit_id == FABRIC_UNIT_ID))
        if unit is None:
            unit = Unit(building_id=building.id, fabric_unit_id=FABRIC_UNIT_ID, label=FABRIC_UNIT_ID)
            db.add(unit)
            db.flush()
        elif unit.building_id != building.id:
            unit.building_id = building.id
            db.flush()

        # 3. Find-or-create the resident identity.
        identity = db.scalar(
            select(ResidentIdentity).where(ResidentIdentity.email == RESIDENT_EMAIL)
        )
        if identity is None:
            identity = ResidentIdentity(email=RESIDENT_EMAIL, status="active")
            db.add(identity)
            db.flush()

        # 4. Find-or-create an active, open tenancy.
        tenancy = db.scalar(
            select(UnitResident).where(
                UnitResident.unit_id == unit.id,
                UnitResident.resident_identity_id == identity.id,
                UnitResident.status == "active",
            )
        )
        if tenancy is None:
            tenancy = UnitResident(
                unit_id=unit.id,
                resident_identity_id=identity.id,
                valid_from=date.today() - timedelta(days=365),
                valid_to=None,
                status="active",
            )
            db.add(tenancy)
            db.flush()

        # 5. Mint a fresh single-use magic-link token (store only the hash).
        raw = secrets.token_urlsafe(32)
        db.add(
            ResidentInviteToken(
                unit_resident_id=tenancy.id,
                token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                expires_at=datetime.now(timezone.utc) + timedelta(days=TOKEN_TTL_DAYS),
            )
        )
        db.commit()

        print("\n=== Resident demo seeded ===")
        print(f"  building          : {building.fabric_building_id or building.id} ({building.name})")
        print(f"  unit              : {unit.fabric_unit_id}")
        print(f"  resident email    : {identity.email}")
        print(f"  resident identity : {identity.id}")
        print("\n--- Sign-in paths ---")
        print(f"  Magic link (P4-3) : {FRONTEND_URL}/residence/enter?token={raw}")
        print(f"  Dev direct        : {FRONTEND_URL}/residence?resident={identity.id}   (RESIDENT_DEV_MODE=1)")
        print(f"\n  Token valid {TOKEN_TTL_DAYS} days, single use.\n")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
