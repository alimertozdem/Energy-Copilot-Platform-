"""Seed a throwaway PENDING test building + 12 months of consumption, so the full
bridge chain (40 -> 09 -> 05 -> 06) can be tested end-to-end without the UI.

The building has NO fabric_building_id (pending) and realistic German inputs
(gas heating, envelope U-values, EPC, area) so the GHG / GEG / recommendation
notebooks have real data to compute. Run from web-app/backend (venv active):
    python seed_test_building.py
Then:
    python test_bridge_live.py      # picks this pending building, bridges it

Delete it afterwards from the app / DB if you don't want the test row.
"""
import sys

from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Organization
from app.repositories import building as building_repo
from app.repositories import consumption as consumption_repo


def main() -> None:
    db = SessionLocal()
    try:
        org = None
        try:
            org = db.scalar(select(Organization).where(Organization.is_sample_org.is_(False)))
        except Exception:
            org = None
        if org is None:
            org = db.scalar(select(Organization))
        if org is None:
            sys.exit("No organization in the DB — sign up once so an org exists, then re-run.")

        b = building_repo.create_building(
            db,
            organization_id=org.id,
            name="BRIDGE TEST (seed)",
            building_type="office",
            city="Berlin",
            country_code="DE",
            floor_area_m2=2500,
            construction_year=1995,
            epc_class="D",
            heating_system="gas_boiler",
            has_gas_heating=True,
            wall_u_value=0.9,
            roof_u_value=0.6,
            window_u_value=2.7,
            insulation_year=2005,
            typical_occupants=120,
        )

        # 12 months of plausible office kWh (winter heating + summer cooling bumps)
        rows = []
        for m in range(1, 13):
            kwh = 22000 + (3000 if m in (1, 2, 11, 12) else 0) + (1500 if m in (6, 7, 8) else 0)
            rows.append((f"2025-{m:02d}", float(kwh), round(kwh * 0.22, 2)))
        n = consumption_repo.upsert_rows(db, building_id=b.id, rows=rows, source="seed")
        db.commit()

        print(f"OK — seeded PENDING building '{b.name}'")
        print(f"   building_id = {b.id}")
        print(f"   org_id      = {org.id}")
        print(f"   consumption = {n} months (2025-01..2025-12), gas heating + U-values + EPC D")
        print("\nNext: python test_bridge_live.py   → it will bridge THIS building")
        print("(40 baseline → 09 GHG → 05 GEG → 06 recommendations).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
