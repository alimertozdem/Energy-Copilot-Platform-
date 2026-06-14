"""Phase 2 bridge — DRY-RUN test harness (no /admin, no Fabric, no capacity).

Calls bridge_orchestrator.run_automated_bridge(dry_run=True) directly against a
pending building, so you can validate the orchestration + the report chain
(40 -> 09 -> 05 -> 06) WITHOUT the admin UI. Prints the planned steps. €0 — it
imports no Fabric/OneLake code on the dry-run path and writes nothing to Fabric.

Run from web-app/backend with the venv active (backend can stay running):
    python test_bridge_dryrun.py

It:
  1. finds a PENDING building (no fabric_building_id) that has uploaded consumption,
  2. ensures a pending bridge_request for it (creates one if missing),
  3. picks a platform-admin user as the actor,
  4. runs the orchestrator in dry_run mode and prints the plan.
If no pending building with consumption exists, it tells you exactly what to add.
"""
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Building, User
from app.repositories import bridge as bridge_repo
from app.repositories import consumption as consumption_repo
from app.services import bridge_orchestrator


def _consumption_count(db, building_id) -> int:
    try:
        return len(consumption_repo.list_rows(db, building_id=building_id))
    except Exception:
        return 0


def main() -> None:
    db = SessionLocal()
    try:
        pending = list(
            db.scalars(select(Building).where(Building.fabric_building_id.is_(None))).all()
        )
        if not pending:
            print("No PENDING buildings — every building already has a fabric_building_id.")
            print("Create one: onboarding -> add a building -> upload a consumption CSV, then re-run.")
            return

        print("Pending buildings (no fabric_building_id):")
        target = None
        for b in pending:
            n = _consumption_count(db, b.id)
            flag = "  <-- target" if (target is None and n > 0) else ""
            print(f"  - {b.name:<28} id={b.id}  consumption_months={n}{flag}")
            if target is None and n > 0:
                target = b

        if target is None:
            print("\nNone of the pending buildings has uploaded consumption yet.")
            print("Upload a consumption CSV on a building's page (the bridge needs it), then re-run.")
            return

        req = bridge_repo.get_active_request(db, building_id=target.id)
        if req is None:
            req = bridge_repo.create_request(
                db,
                building_id=target.id,
                organization_id=target.organization_id,
                requested_by=None,
                target_tier="basic",
                readiness=None,
                note="dry-run test harness",
            )
            db.commit()
            print(f"\nCreated bridge_request {req.id}")
        else:
            print(f"\nUsing existing bridge_request {req.id}")

        admin = db.scalar(select(User).where(User.is_platform_admin.is_(True))) or db.scalar(
            select(User)
        )
        if admin is None:
            print("No users in the DB — cannot set an actor. Aborting.")
            return

        print("\n=== run_automated_bridge(dry_run=True) ===")
        result = bridge_orchestrator.run_automated_bridge(
            db, request_id=req.id, admin_id=admin.id, dry_run=True
        )

        print(
            f"\nok={result['ok']}  dry_run={result.get('dry_run')}  "
            f"fabric_building_id={result.get('fabric_building_id')}"
        )
        if result.get("error"):
            print(f"error: {result['error']}  (failed_step={result.get('failed_step')})")
        print("\nPlanned steps:")
        for s in result.get("steps", []):
            extra = {k: v for k, v in s.items() if k not in ("step", "status")}
            print(f"  [{s.get('status',''):<24}] {s.get('step',''):<20} {extra or ''}")

        print(
            "\nExpected: a minted fabric_building_id, land_bronze/run_job planned, and "
            "run_ghg / run_compliance / run_recommendations = 'skipped (id not configured)'. "
            "That means the report chain is wired correctly — they run once you set the "
            "FABRIC_*_NOTEBOOK_ID vars in .env."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
